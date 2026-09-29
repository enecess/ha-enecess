"""Guide device discovery, cloud authentication, and entry options."""

import asyncio
from dataclasses import dataclass
from typing import Any, cast

from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.const import Platform
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import device_registry as dr, entity_registry as er, selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import SelectSelectorMode
import voluptuous as vol
from zeroconf import ServiceStateChange
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo

from .client_api import EnecessApi, EnecessApiError, EnecessAuthError
from .client_modbus import EnecessModbusClient, decode_int16
from .const import (
    CONF_CLOUD_BASE_URL,
    CONF_ECOMAIN_FIRMWARE_READ_TIMEOUT,
    CONF_ECOMAIN_FIRMWARE_VERSION_REGISTER,
    CONF_ECOMAIN_MIN_FIRMWARE_VERSION,
    CONF_ECOMAIN_PHASE_FIRMWARE_VERSION,
    CONF_ECOMAIN_PORT,
    CONF_ECOMAIN_SLAVE_ONLINE_REGISTER_COUNT,
    CONF_ECOMAIN_SLAVE_ONLINE_REGISTER_START,
    CONF_LOCAL_MDNS_SCAN_INTERVAL,
    CONST_ADD_MODE,
    CONST_ADD_MODE_CLOUD,
    CONST_ADD_MODE_LOCAL,
    CONST_ADD_MODE_LOCAL_AUTO,
    CONST_ADD_MODE_LOCAL_MANUAL,
    CONST_CLOUD_PASSWORD,
    CONST_CLOUD_TOKEN,
    CONST_CLOUD_USERNAME,
    CONST_DEVICE_ECOMAIN,
    CONST_DEVICE_ECOPLUG,
    CONST_DEVICE_TYPE,
    CONST_ECOMAIN_CLOUD_MASTER,
    CONST_ECOMAIN_CLOUD_MASTER_ID,
    CONST_ECOMAIN_CLOUD_SLAVE_MAP,
    CONST_ECOMAIN_CLOUD_SLAVES,
    CONST_ECOMAIN_FIRMWARE_VERSION,
    CONST_ECOMAIN_HOST,
    CONST_ECOMAIN_MASTERS,
    CONST_ECOMAIN_ONLINE_SLAVES,
    CONST_ECOMAIN_PORT,
    CONST_ECOMAIN_SELECTED_SLAVES,
    CONST_ECOMAIN_SERIAL,
    CONST_ECOPLUG_DEVICES,
    CONST_ECOPLUG_SELECTED,
    CONST_EXTRA_ACTION,
    CONST_EXTRA_ACTION_ADD_AGGREGATE,
    CONST_EXTRA_ACTION_ADD_TRANSFORM,
    CONST_EXTRA_ACTION_FINISH,
    CONST_EXTRA_ACTION_REMOVE,
    CONST_EXTRA_ENTITIES,
    CONST_EXTRA_ENTITY_NAME,
    CONST_EXTRA_ENTITY_OPERATION,
    CONST_EXTRA_ENTITY_REMOVE,
    CONST_EXTRA_ENTITY_SOURCE,
    CONST_EXTRA_ENTITY_SOURCE_KIND,
    CONST_EXTRA_ENTITY_SOURCES,
    CONST_MDNS_IP,
    CONST_MEASUREMENT_TYPES,
    DEVICE_CONFIGS,
    DOMAIN,
    DiscoveryConfig,
    EcoMainDeviceTyp,
)
from .ecomain.model import CLOUD_MEASUREMENTS, available_local_measurements
from .ecomain.phase import async_read_phases, async_write_phases
from .ecoplug.model import build_plug_options, select_plugs
from .extra import (
    EXTRA_AGGREGATE_OPERATIONS,
    EXTRA_SOURCE_KINDS,
    EXTRA_TRANSFORM_OPERATIONS,
    build_entry_device_identifiers,
    build_entry_sensor_unique_ids,
    build_entry_specs,
    build_source_options,
    get_entry_extra_entities,
    get_entry_measurement_types,
    get_entry_slaves,
    normalize_extra_entity,
)
from .flow_navigation import FlowNavigationMixin, navigable_step
from .formula_flow import FormulaFlowMixin
from .local_validation import async_validate_local_device
from .registry import async_remove_unconfigured_registry_entries

try:
    from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
except ImportError:
    from homeassistant.components.zeroconf import ZeroconfServiceInfo


@dataclass(frozen=True)
class DiscoveredDevice:
    """Describe a local device found through multicast discovery."""

    serial: str
    hostname: str
    service_name: str
    ip: str | None


def _measurement_schema(entry_data: dict, selected: list[str]) -> vol.Schema:
    choices = (
        CLOUD_MEASUREMENTS
        if entry_data.get(CONST_ADD_MODE) == CONST_ADD_MODE_CLOUD
        else available_local_measurements(
            entry_data.get(CONST_ECOMAIN_FIRMWARE_VERSION)
        )
    )
    return vol.Schema(
        {
            vol.Required(
                CONST_MEASUREMENT_TYPES,
                default=[item for item in selected if item in choices],
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=list(choices),
                    multiple=True,
                    translation_key=CONST_MEASUREMENT_TYPES,
                    mode=SelectSelectorMode.LIST,
                )
            )
        }
    )


def _selection_removes_extra_sources(
    entry_data: dict, current: dict, proposed: dict
) -> bool:
    old_keys = {
        spec.key
        for spec in build_entry_specs(entry_data, current, include_unsupported=True)
    }
    new_keys = {
        spec.key
        for spec in build_entry_specs(entry_data, proposed, include_unsupported=True)
    }
    removed = old_keys - new_keys
    return any(
        removed.intersection(extra.get("sources") or [])
        for extra in current.get(CONST_EXTRA_ENTITIES, [])
    )


def _extra_entity_errors(
    user_input: dict[str, Any], *, aggregate: bool = False
) -> dict[str, str]:
    """Validate names and aggregate source counts before saving an extra entity."""
    errors = {}
    if not user_input.get(CONST_EXTRA_ENTITY_NAME, "").strip():
        errors[CONST_EXTRA_ENTITY_NAME] = "extra_name_required"
    if aggregate and len(user_input.get(CONST_EXTRA_ENTITY_SOURCES) or []) < 2:
        errors[CONST_EXTRA_ENTITY_SOURCES] = "aggregate_sources_required"
    return errors


def _extra_source_counts(entry_data: dict, options: dict) -> dict[str, int]:
    """Count usable sources for each supported transform/aggregate kind."""
    return {
        kind: len(build_source_options(entry_data, options, source_kind=kind))
        for kind in EXTRA_SOURCE_KINDS
    }


def _extra_creation_actions(entry_data: dict, options: dict) -> list[str]:
    """Offer creation actions only when their minimum inputs are available."""
    counts = _extra_source_counts(entry_data, options)
    actions = [CONST_EXTRA_ACTION_FINISH]
    if counts["power"]:
        actions.append(CONST_EXTRA_ACTION_ADD_TRANSFORM)
    if any(count >= 2 for count in counts.values()):
        actions.append(CONST_EXTRA_ACTION_ADD_AGGREGATE)
    return actions


class ConfigFlow(
    FlowNavigationMixin, FormulaFlowMixin, config_entries.ConfigFlow, domain=DOMAIN
):
    """Configure local and cloud devices while preserving navigation drafts."""

    VERSION = 1

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Renew credentials for the existing cloud account."""
        return await self.async_step_reauth_confirm()

    @navigable_step
    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Validate replacement credentials for the original cloud account."""
        entry = self._get_reauth_entry()
        errors = {}
        if user_input is not None:
            username = user_input.get(CONST_CLOUD_USERNAME, "").strip()
            password = user_input.get(CONST_CLOUD_PASSWORD, "")
            if not username or not password.strip():
                errors["base"] = "invalid_input"
            elif username != entry.data[CONST_CLOUD_USERNAME].strip():
                errors["base"] = "account_mismatch"
            else:
                api = EnecessApi(
                    async_get_clientsession(self.hass), CONF_CLOUD_BASE_URL
                )
                try:
                    token = await api.generate_token(username, password)
                except EnecessAuthError:
                    errors["base"] = "auth_failed"
                except (EnecessApiError, OSError, TimeoutError, ValueError):
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            CONST_CLOUD_USERNAME: username,
                            CONST_CLOUD_PASSWORD: password,
                            CONST_CLOUD_TOKEN: token,
                        },
                    )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONST_CLOUD_USERNAME, default=entry.data[CONST_CLOUD_USERNAME]
                    ): str,
                    vol.Required(CONST_CLOUD_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    def __init__(self) -> None:
        """Initialize the flow state and configuration drafts."""
        self._discovered: list[DiscoveredDevice] = []
        self._device_type: str | None = None
        self._mode: str | None = None
        self._cloud_api: EnecessApi | None = None
        self._cloud_token: str | None = None
        self._cloud_username: str | None = None
        self._cloud_password: str | None = None
        self._ecomain_local_config: dict[str, Any] = {}
        self._ecomain_cloud_config: dict[str, Any] = {}
        self._ecoplug_devices: list[dict[str, Any]] = []
        self._entry_data: dict[str, Any] = {}
        self._extra_entities: list[dict[str, Any]] = []
        self._measurement_types: list[str] | None = None
        self._navigation_initial_state = self._navigation_snapshot()

    @property
    def _ecomain_available_slaves(self) -> list[str]:
        return (
            cast(
                EcoMainDeviceTyp, DEVICE_CONFIGS[CONST_DEVICE_ECOMAIN]
            ).available_slaves
            or []
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow for an existing config entry."""
        return EnecessOptionsFlow(config_entry)

    @navigable_step
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select the device family to configure."""
        if user_input is None:
            return self.async_show_form(  # type: ignore[return-value]
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONST_DEVICE_TYPE): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=list(DEVICE_CONFIGS.keys()),
                                translation_key=CONST_DEVICE_TYPE,
                                mode=SelectSelectorMode.LIST,
                            )
                        )
                    }
                ),
            )

        device_type = user_input[CONST_DEVICE_TYPE]
        self._device_type = device_type
        if device_type == CONST_DEVICE_ECOMAIN:
            return await self.async_step_ecomain_mode()  # type: ignore[return-value]
        if device_type == CONST_DEVICE_ECOPLUG:
            self._mode = CONST_ADD_MODE_CLOUD
            return await self.async_step_ecoplug_cloud_login()  # type: ignore[return-value]

        return self.async_abort(reason="unsupported_device_type")  # type: ignore[return-value]

    @navigable_step
    async def async_step_ecomain_mode(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select cloud access or local discovery for ecoMain."""
        if user_input is None:
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_mode",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONST_ADD_MODE, default=CONST_ADD_MODE_LOCAL_AUTO
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=[
                                    CONST_ADD_MODE_LOCAL_AUTO,
                                    CONST_ADD_MODE_LOCAL_MANUAL,
                                    CONST_ADD_MODE_CLOUD,
                                ],
                                translation_key=CONST_ADD_MODE,
                                mode=SelectSelectorMode.LIST,
                            )
                        )
                    }
                ),
            )

        mode = user_input[CONST_ADD_MODE]
        self._mode = mode
        if mode == CONST_ADD_MODE_LOCAL_AUTO:
            return await self.async_step_ecomain_auto_scan()  # type: ignore[return-value]
        if mode == CONST_ADD_MODE_LOCAL_MANUAL:
            return await self.async_step_ecomain_manual()  # type: ignore[return-value]
        if mode == CONST_ADD_MODE_CLOUD:
            return await self.async_step_ecomain_cloud_login()  # type: ignore[return-value]
        return self.async_abort(reason="unsupported_add_mode")  # type: ignore[return-value]

    async def _async_mdns_scan(
        self, discovery_config: DiscoveryConfig
    ) -> list[DiscoveredDevice]:
        zc_inst = await zeroconf.async_get_async_instance(self.hass)
        found_names: set[str] = set()

        mdns_type = discovery_config.mdns_type
        mdns_prefix = discovery_config.mdns_prefix

        def _on_service_state_change(
            zeroconf,
            service_type: str,
            name: str,
            state_change: ServiceStateChange,
            **kwargs,
        ) -> None:
            if (
                state_change is ServiceStateChange.Added
                and service_type == mdns_type
                and name.startswith(mdns_prefix)
            ):
                found_names.add(name)

        browser = AsyncServiceBrowser(
            zc_inst.zeroconf,
            mdns_type,
            handlers=[_on_service_state_change],
        )

        try:
            await asyncio.sleep(CONF_LOCAL_MDNS_SCAN_INTERVAL)
        finally:
            await browser.async_cancel()

        results: list[DiscoveredDevice] = []

        for name in sorted(found_names):
            # name format like: "{mdns_prefix}XXXX._http._tcp.local."
            instance = name.split(".", 1)[0]
            serial = instance[len(mdns_prefix) :]
            if not serial:
                continue

            info = AsyncServiceInfo(mdns_type, name)
            ok = await info.async_request(zc_inst.zeroconf, timeout=2000)
            if not ok or not info.server:
                continue

            hostname = info.server.rstrip(".")
            ip: str | None = None
            addrs = info.parsed_addresses()
            if addrs:
                ip = next((addr for addr in addrs if "." in addr), addrs[0])

            results.append(
                DiscoveredDevice(
                    serial=serial,
                    hostname=hostname,
                    service_name=name,
                    ip=ip,
                )
            )

        return results

    @navigable_step
    async def async_step_ecomain_auto_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Discover local ecoMain devices and select a serial number."""
        discovery_config = DEVICE_CONFIGS[CONST_DEVICE_ECOMAIN].discovery
        if discovery_config is None:
            return self.async_abort(reason="auto_discovery_not_supported")  # type: ignore[return-value]

        if user_input is None or CONST_ECOMAIN_SERIAL not in user_input:
            self._discovered = await self._async_mdns_scan(discovery_config)
            if not self._discovered:
                return self.async_show_form(  # type: ignore[return-value]
                    step_id="ecomain_auto_scan",
                    data_schema=vol.Schema({}),
                    errors={"base": "no_devices_found"},
                    description_placeholders={},
                )

            options = {
                d.serial: f"ecoMain {d.serial} ({d.ip})" for d in self._discovered
            }
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_auto_scan",
                data_schema=vol.Schema(
                    {vol.Required(CONST_ECOMAIN_SERIAL): vol.In(options)}
                ),
                errors={},
            )

        selected_serial = user_input[CONST_ECOMAIN_SERIAL]
        selected = next(
            (d for d in self._discovered if d.serial == selected_serial), None
        )

        if selected is None:
            return self.async_abort(reason="no_devices_found")  # type: ignore[return-value]

        self._ecomain_local_config = {
            CONST_ECOMAIN_SERIAL: selected.serial,
            CONST_MDNS_IP: selected.ip,
        }

        return await self.async_step_ecomain_local_confirm()  # type: ignore[return-value]

    @navigable_step
    async def async_step_ecomain_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Validate a manually entered local ecoMain address."""
        if user_input is None:
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_manual",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONST_ECOMAIN_SERIAL): str,
                        vol.Required(CONST_ECOMAIN_HOST): str,
                    }
                ),
                errors={},
            )

        host = user_input[CONST_ECOMAIN_HOST].strip()
        serial = user_input[CONST_ECOMAIN_SERIAL].strip()

        if not host or not serial:
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_manual",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONST_ECOMAIN_SERIAL): str,
                        vol.Required(CONST_ECOMAIN_HOST): str,
                    }
                ),
                errors={"base": "invalid_input"},
            )

        self._ecomain_local_config = {
            CONST_ECOMAIN_SERIAL: serial,
            CONST_ECOMAIN_HOST: host,
        }

        return await self.async_step_ecomain_local_confirm()  # type: ignore[return-value]

    @staticmethod
    def _extract_serial_from_service_name(
        service_name: str,
        mdns_prefix: str,
    ) -> str | None:
        instance = service_name.partition(".")[0]
        if not instance.startswith(mdns_prefix):
            return None
        serial = instance[len(mdns_prefix) :]
        return serial or None

    def _match_discovery(
        self,
        discovery_info: ZeroconfServiceInfo,
    ) -> tuple[str, DiscoveredDevice] | None:
        svc_type = discovery_info.type
        svc_name = discovery_info.name

        for device_type, config in DEVICE_CONFIGS.items():
            discovery = config.discovery
            if (
                not discovery
                or svc_type != discovery.mdns_type
                or not svc_name.startswith(discovery.mdns_prefix)
            ):
                continue

            serial = self._extract_serial_from_service_name(
                svc_name, discovery.mdns_prefix
            )
            if serial is None:
                continue

            hostname = discovery_info.hostname or discovery_info.host or ""
            hostname = hostname.rstrip(".") if hostname else ""

            device = DiscoveredDevice(
                serial=serial,
                hostname=hostname,
                service_name=svc_name,
                ip=discovery_info.host,
            )
            return device_type, device
        return None

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle an announced device and update its discovered address."""
        match = self._match_discovery(discovery_info)
        if match is None:
            return self.async_abort(reason="no_matching_discovery")  # type: ignore[return-value]

        self._device_type, selected = match
        self._mode = CONST_ADD_MODE_LOCAL_AUTO
        self._ecomain_local_config = {
            CONST_ECOMAIN_SERIAL: selected.serial,
            CONST_MDNS_IP: selected.ip,
        }

        self.context["title_placeholders"] = {
            CONST_ECOMAIN_SERIAL: selected.serial,
            CONST_ECOMAIN_HOST: selected.ip,
        }

        unique_id = f"ecomain:{selected.serial}:mode_local"
        existing_entry = await self.async_set_unique_id(unique_id)
        updates = None
        if existing_entry is not None:
            updates = {CONST_MDNS_IP: selected.ip}
            if existing_entry.data.get(CONST_ADD_MODE) == CONST_ADD_MODE_LOCAL_AUTO:
                updates[CONST_ECOMAIN_HOST] = selected.ip
        self._abort_if_unique_id_configured(updates=updates, reload_on_update=False)

        self._navigation_discovery_state = self._navigation_snapshot()
        return await self.async_step_ecomain_local_confirm()  # type: ignore[return-value]

    async def _async_validate_local_device(
        self, host: str, port: int
    ) -> dict[str, str] | None:
        client = EnecessModbusClient(host, port)
        result = await async_validate_local_device(
            client,
            firmware_register=CONF_ECOMAIN_FIRMWARE_VERSION_REGISTER,
            minimum_firmware=CONF_ECOMAIN_MIN_FIRMWARE_VERSION,
            slave_register_start=CONF_ECOMAIN_SLAVE_ONLINE_REGISTER_START,
            slave_register_count=CONF_ECOMAIN_SLAVE_ONLINE_REGISTER_COUNT,
            allowed_slaves=set(self._ecomain_available_slaves),
            firmware_timeout=CONF_ECOMAIN_FIRMWARE_READ_TIMEOUT,
        )
        if result.error is not None:
            return {"base": result.error}
        self._ecomain_local_config[CONST_ECOMAIN_ONLINE_SLAVES] = (
            result.online_slaves or []
        )
        self._ecomain_local_config[CONST_ECOMAIN_FIRMWARE_VERSION] = (
            result.firmware_version
        )
        return None

    @navigable_step
    async def async_step_ecomain_local_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm the identity of a discovered local device."""
        if user_input is None:
            self._set_confirm_only()
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_local_confirm",
                data_schema=vol.Schema({}),
                description_placeholders={
                    CONST_ECOMAIN_SERIAL: self._ecomain_local_config.get(
                        CONST_ECOMAIN_SERIAL
                    ),
                    CONST_ECOMAIN_HOST: self._ecomain_local_config.get(CONST_MDNS_IP)
                    or self._ecomain_local_config.get(CONST_ECOMAIN_HOST),
                },
            )
        return await self.async_step_ecomain_local_setup()  # type: ignore[return-value]

    @navigable_step
    async def async_step_ecomain_local_setup(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose local slave devices after validating firmware."""
        host = self._ecomain_local_config.get(
            CONST_MDNS_IP
        ) or self._ecomain_local_config.get(CONST_ECOMAIN_HOST)
        ecomain_serial = self._ecomain_local_config.get(CONST_ECOMAIN_SERIAL)

        if CONST_ECOMAIN_ONLINE_SLAVES in self._ecomain_local_config:
            if user_input is not None:
                selected = user_input.get(CONST_ECOMAIN_SELECTED_SLAVES) or []
                options = self._options_data()
                proposed = {
                    **options,
                    CONST_ECOMAIN_SELECTED_SLAVES: self._normalize_slaves(selected),
                }
                if _selection_removes_extra_sources(
                    self._entry_data, options, proposed
                ):
                    result = await self.async_step_ecomain_local_setup()
                    result["errors"] = {"base": "slave_in_use"}
                    return result

                if (
                    self._entry_by_unique_id(f"ecomain:{ecomain_serial}:mode_local")
                    is not None
                ):
                    return self.async_abort(reason="already_configured")  # type: ignore[return-value]

                self._entry_data = {
                    CONST_DEVICE_TYPE: CONST_DEVICE_ECOMAIN,
                    CONST_ADD_MODE: self._mode,
                    CONST_ECOMAIN_HOST: host,
                    CONST_ECOMAIN_PORT: CONF_ECOMAIN_PORT,
                    CONST_ECOMAIN_SERIAL: ecomain_serial,
                    CONST_ECOMAIN_FIRMWARE_VERSION: self._ecomain_local_config.get(
                        CONST_ECOMAIN_FIRMWARE_VERSION
                    ),
                    CONST_ECOMAIN_SELECTED_SLAVES: self._normalize_slaves(selected),
                }
                return await self.async_step_measurement_types()

            online_slaves = self._ecomain_local_config.get(CONST_ECOMAIN_ONLINE_SLAVES)
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_local_setup",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONST_ECOMAIN_SELECTED_SLAVES, default=online_slaves
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=online_slaves,
                                multiple=True,
                                translation_key=CONST_ECOMAIN_SELECTED_SLAVES,
                                mode=SelectSelectorMode.LIST,
                            )
                        )
                    }
                    if online_slaves
                    else {}
                ),
                description_placeholders={
                    CONST_ECOMAIN_SERIAL: self._ecomain_local_config.get(
                        CONST_ECOMAIN_SERIAL
                    ),
                    CONST_ECOMAIN_HOST: host,
                },
            )
        errors = await self._async_validate_local_device(host, CONF_ECOMAIN_PORT)

        if errors:
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_local_setup",
                data_schema=vol.Schema({}),
                errors=errors,
                description_placeholders={
                    CONST_ECOMAIN_SERIAL: self._ecomain_local_config.get(
                        CONST_ECOMAIN_SERIAL
                    ),
                    CONST_ECOMAIN_HOST: host,
                },
            )

        online_slaves = self._ecomain_local_config.get(CONST_ECOMAIN_ONLINE_SLAVES)
        if not online_slaves:
            if (
                self._entry_by_unique_id(f"ecomain:{ecomain_serial}:mode_local")
                is not None
            ):
                return self.async_abort(reason="already_configured")  # type: ignore[return-value]

            self._entry_data = {
                CONST_DEVICE_TYPE: CONST_DEVICE_ECOMAIN,
                CONST_ADD_MODE: self._mode,
                CONST_ECOMAIN_HOST: host,
                CONST_ECOMAIN_PORT: CONF_ECOMAIN_PORT,
                CONST_ECOMAIN_SERIAL: ecomain_serial,
                CONST_ECOMAIN_FIRMWARE_VERSION: self._ecomain_local_config.get(
                    CONST_ECOMAIN_FIRMWARE_VERSION
                ),
                CONST_ECOMAIN_SELECTED_SLAVES: [],
            }
            return await self.async_step_measurement_types()

        return self.async_show_form(  # type: ignore[return-value]
            step_id="ecomain_local_setup",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONST_ECOMAIN_SELECTED_SLAVES, default=online_slaves
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=online_slaves,
                            multiple=True,
                            translation_key=CONST_ECOMAIN_SELECTED_SLAVES,
                            mode=SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
            description_placeholders={
                CONST_ECOMAIN_SERIAL: ecomain_serial,
                CONST_ECOMAIN_HOST: host,
            },
        )

    def _get_cloud_api(self) -> EnecessApi:
        if self._cloud_api is None:
            session = async_get_clientsession(self.hass)
            self._cloud_api = EnecessApi(session=session, base_url=CONF_CLOUD_BASE_URL)
        return self._cloud_api

    @navigable_step
    async def async_step_ecomain_cloud_login(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Authenticate the cloud account and discover ecoMain devices."""
        if user_input is None:
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_cloud_login",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONST_CLOUD_USERNAME): str,
                        vol.Required(CONST_CLOUD_PASSWORD): str,
                    }
                ),
                errors={},
            )

        username = str(user_input[CONST_CLOUD_USERNAME]).strip()
        password = str(user_input[CONST_CLOUD_PASSWORD])

        api = self._get_cloud_api()
        try:
            token = await api.generate_token(username, password)
            masters = await api.get_hardware_list(token, hardware_type=0)
        except EnecessAuthError:
            error = "auth_failed"
        except (EnecessApiError, OSError, TimeoutError, ValueError):
            error = "cannot_connect"
        else:
            if not masters:
                error = "no_devices_found"
            else:
                self._cloud_username = username
                self._cloud_password = password
                self._cloud_token = token
                self._ecomain_cloud_config[CONST_ECOMAIN_MASTERS] = masters
                return await self.async_step_ecomain_cloud_master()  # type: ignore[return-value]
        result = await self.async_step_ecomain_cloud_login()
        result["errors"] = {"base": error}
        return result

    def _show_ecoplug_cloud_login_form(
        self, errors: dict[str, str] | None = None
    ) -> FlowResult:
        return self.async_show_form(  # type: ignore[return-value]
            step_id="ecoplug_cloud_login",
            data_schema=vol.Schema(
                {
                    vol.Required(CONST_CLOUD_USERNAME): str,
                    vol.Required(CONST_CLOUD_PASSWORD): str,
                }
            ),
            errors=errors or {},
        )

    @navigable_step
    async def async_step_ecoplug_cloud_login(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Authenticate the cloud account and discover ecoPlug devices."""
        if user_input is None:
            return self._show_ecoplug_cloud_login_form()

        username = str(user_input[CONST_CLOUD_USERNAME])
        password = str(user_input[CONST_CLOUD_PASSWORD])
        api = self._get_cloud_api()
        try:
            token = await api.generate_token(username, password)
            devices = await api.get_hardware_list(token, hardware_type=2)
        except EnecessAuthError:
            return self._show_ecoplug_cloud_login_form({"base": "auth_failed"})
        except (EnecessApiError, OSError, TimeoutError, ValueError):
            return self._show_ecoplug_cloud_login_form({"base": "cannot_connect"})

        if not build_plug_options(devices):
            return self._show_ecoplug_cloud_login_form({"base": "no_devices_found"})

        self._cloud_username = username
        self._cloud_password = password
        self._cloud_token = token
        self._ecoplug_devices = devices
        return await self.async_step_ecoplug_select()  # type: ignore[return-value]

    @navigable_step
    async def async_step_ecoplug_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose which cloud ecoPlug devices belong to the entry."""
        options = build_plug_options(self._ecoplug_devices)
        if user_input is None:
            return self._show_ecoplug_select_form(options)

        selected = user_input.get(CONST_ECOPLUG_SELECTED) or []
        devices = select_plugs(self._ecoplug_devices, selected)
        if not devices:
            return self._show_ecoplug_select_form(
                options,
                errors={"base": "no_devices_found"},
            )

        assert self._cloud_username is not None
        assert self._cloud_password is not None
        assert self._cloud_token is not None
        unique_username = self._cloud_username.strip().casefold()
        existing_entry = await self.async_set_unique_id(
            f"ecoplug:{unique_username}:mode_cloud"
        )
        if existing_entry is not None:
            return self.async_abort(reason="already_configured")  # type: ignore[return-value]

        return self.async_create_entry(
            title=f"ecoPlug ({self._cloud_username})",
            data={
                CONST_DEVICE_TYPE: CONST_DEVICE_ECOPLUG,
                CONST_ADD_MODE: CONST_ADD_MODE_CLOUD,
                CONST_CLOUD_USERNAME: self._cloud_username,
                CONST_CLOUD_PASSWORD: self._cloud_password,
                CONST_CLOUD_TOKEN: self._cloud_token,
                CONST_ECOPLUG_DEVICES: devices,
            },
            options={},
        )

    def _show_ecoplug_select_form(
        self,
        options: dict[str, str],
        errors: dict[str, str] | None = None,
    ) -> FlowResult:
        return self.async_show_form(  # type: ignore[return-value]
            step_id="ecoplug_select",
            data_schema=vol.Schema(
                {
                    vol.Required(CONST_ECOPLUG_SELECTED): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": serial, "label": label}
                                for serial, label in options.items()
                            ],
                            multiple=True,
                            mode=SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
            errors=errors or {},
        )

    @navigable_step
    async def async_step_ecomain_cloud_master(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose the cloud master and discover its slave devices."""
        assert self._cloud_token is not None
        assert self._cloud_username is not None
        assert self._cloud_password is not None

        masters = self._ecomain_cloud_config.get(CONST_ECOMAIN_MASTERS, [])
        api = self._get_cloud_api()

        if user_input is None:
            options = {
                str(int(m["id"])): str(
                    m.get("name") or m.get("hardware_number") or m["id"]
                )
                for m in masters
                if "id" in m
            }
            default_master = next(iter(options)) if options else None
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_cloud_master",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONST_ECOMAIN_CLOUD_MASTER_ID, default=default_master
                        ): vol.In(options)
                    }
                ),
                errors={},
            )

        master_id = int(user_input[CONST_ECOMAIN_CLOUD_MASTER_ID])
        ecomain_cloud_master = next(
            (m for m in masters if int(m.get("id", -1)) == master_id), None
        )
        self._ecomain_cloud_config[CONST_ECOMAIN_CLOUD_MASTER] = ecomain_cloud_master
        if ecomain_cloud_master is None:
            return self.async_abort(reason="no_devices_found")  # type: ignore[return-value]

        serial = str(ecomain_cloud_master.get("hardware_number"))
        self._ecomain_cloud_config[CONST_ECOMAIN_SERIAL] = serial

        try:
            ecomain_cloud_slaves = await api.get_hardware_list(
                self._cloud_token,
                hardware_type=1,
                parent_id=master_id,
            )
        except EnecessAuthError:
            result = await self.async_step_ecomain_cloud_master()
            result["errors"] = {"base": "auth_failed"}
            return result
        except (EnecessApiError, OSError, TimeoutError, ValueError):
            result = await self.async_step_ecomain_cloud_master()
            result["errors"] = {"base": "cannot_connect"}
            return result
        for slave in ecomain_cloud_slaves:
            slave_index = self._get_slave_index(slave)
            if slave_index is not None:
                slave["index"] = slave_index
        self._ecomain_cloud_config[CONST_ECOMAIN_CLOUD_SLAVES] = ecomain_cloud_slaves

        return await self.async_step_ecomain_cloud_confirm()  # type: ignore[return-value]

    @navigable_step
    async def async_step_ecomain_cloud_confirm(
        self, user_input: dict[str, Any] | None = None
    ):
        """Confirm the selected cloud ecoMain devices."""
        if user_input is None:
            self._set_confirm_only()

            ecomain_cloud_slaves = self._ecomain_cloud_config[
                CONST_ECOMAIN_CLOUD_SLAVES
            ]
            salve_indices = [
                slave["index"] for slave in ecomain_cloud_slaves if "index" in slave
            ]
            slave_options = sorted(map(str, salve_indices))
            slave_options = [
                s for s in slave_options if s in self._ecomain_available_slaves
            ]

            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_cloud_confirm",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONST_ECOMAIN_SELECTED_SLAVES, default=slave_options
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=slave_options,
                                multiple=True,
                                translation_key=CONST_ECOMAIN_SELECTED_SLAVES,
                                mode=SelectSelectorMode.LIST,
                            )
                        )
                    }
                    if slave_options
                    else {}
                ),
                description_placeholders={
                    CONST_ECOMAIN_SERIAL: self._ecomain_cloud_config.get(
                        CONST_ECOMAIN_SERIAL
                    ),
                },
            )
        options = self._options_data()
        proposed = {
            **options,
            CONST_ECOMAIN_SELECTED_SLAVES: self._normalize_slaves(
                user_input.get(CONST_ECOMAIN_SELECTED_SLAVES) or []
            ),
        }
        if _selection_removes_extra_sources(self._entry_data, options, proposed):
            result = await self.async_step_ecomain_cloud_confirm()
            result["errors"] = {"base": "slave_in_use"}
            return result
        assert self._cloud_username is not None
        assert self._cloud_password is not None
        assert self._cloud_token is not None

        cloud_master = self._ecomain_cloud_config.get(CONST_ECOMAIN_CLOUD_MASTER)
        assert cloud_master is not None
        serial = str(cloud_master.get("hardware_number"))

        cloud_slaves = self._ecomain_cloud_config.get(CONST_ECOMAIN_CLOUD_SLAVES)

        selected_slaves = user_input.get(CONST_ECOMAIN_SELECTED_SLAVES, [])
        slave_map = {}
        for sid_str in selected_slaves:
            slave = next(
                (s for s in cloud_slaves if self._get_slave_index(s) == int(sid_str)),
                {},
            )
            if slave:
                slave_map[int(sid_str)] = slave.get("hardware_number")

        if self._entry_by_unique_id(f"ecomain:{serial}:mode_cloud") is not None:
            return self.async_abort(reason="already_configured")  # type: ignore[return-value]

        self._entry_data = {
            CONST_DEVICE_TYPE: CONST_DEVICE_ECOMAIN,
            CONST_ADD_MODE: CONST_ADD_MODE_CLOUD,
            CONST_CLOUD_USERNAME: self._cloud_username,
            CONST_CLOUD_PASSWORD: self._cloud_password,
            CONST_CLOUD_TOKEN: self._cloud_token,
            CONST_ECOMAIN_SERIAL: serial,
            CONST_ECOMAIN_SELECTED_SLAVES: self._normalize_slaves(selected_slaves),
            CONST_ECOMAIN_CLOUD_SLAVE_MAP: slave_map,
        }
        return await self.async_step_measurement_types()

    @navigable_step
    async def async_step_measurement_types(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select measurements while retaining sources used by extra entities."""
        selected = self._measurement_types
        if selected is None:
            selected = get_entry_measurement_types(self._entry_data)
        errors = {}
        if user_input is not None:
            selected = user_input.get(CONST_MEASUREMENT_TYPES)
            error = "no_measurements_selected" if not selected else None
            if not error:
                options = self._options_data()
                proposed = {**options, CONST_MEASUREMENT_TYPES: selected}
                if _selection_removes_extra_sources(
                    self._entry_data, options, proposed
                ):
                    error = "measurement_in_use"
            if error:
                errors["base"] = error
            else:
                self._measurement_types = list(selected)
                return await self.async_step_extra_entities()
        return self.async_show_form(
            step_id="measurement_types",
            data_schema=_measurement_schema(self._entry_data, selected or []),
            errors=errors,
        )

    @navigable_step
    async def async_step_extra_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose an additional entity operation or finish configuration."""
        if user_input is None:
            return self._show_extra_entities_menu("extra_entities")

        action = user_input.get(CONST_EXTRA_ACTION)
        if action == "add_formula":
            self._reset_formula()
            return await self.async_step_extra_formula()
        if action == "edit_formula":
            return await self.async_step_extra_formula_edit()
        if action == CONST_EXTRA_ACTION_ADD_TRANSFORM:
            if CONST_EXTRA_ENTITY_OPERATION not in user_input:
                return self._show_extra_transform_form()
            return self._handle_extra_transform(user_input)
        if CONST_EXTRA_ENTITY_SOURCE in user_input:
            return self._handle_extra_transform(user_input)
        if action == CONST_EXTRA_ACTION_ADD_AGGREGATE:
            if CONST_EXTRA_ENTITY_OPERATION not in user_input:
                if CONST_EXTRA_ENTITY_SOURCE_KIND in user_input:
                    return self._show_extra_aggregate_form(
                        user_input[CONST_EXTRA_ENTITY_SOURCE_KIND]
                    )
                return self._show_extra_aggregate_kind_form()
            return self._handle_extra_aggregate(user_input)
        if CONST_EXTRA_ENTITY_SOURCES in user_input:
            return self._handle_extra_aggregate(user_input)
        if CONST_EXTRA_ENTITY_SOURCE_KIND in user_input:
            return self._show_extra_aggregate_form(
                user_input[CONST_EXTRA_ENTITY_SOURCE_KIND]
            )
        if action == CONST_EXTRA_ACTION_REMOVE:
            if CONST_EXTRA_ENTITY_REMOVE not in user_input:
                return self._show_extra_remove_form()
            return self._handle_extra_remove(user_input)
        if CONST_EXTRA_ENTITY_REMOVE in user_input:
            return self._handle_extra_remove(user_input)
        return await self._create_config_entry()

    @navigable_step
    async def async_step_extra_transform(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure a derived entity using a selected power source."""
        if user_input is None:
            return self._show_extra_transform_form()
        return await self.async_step_extra_entities(
            {**user_input, CONST_EXTRA_ACTION: CONST_EXTRA_ACTION_ADD_TRANSFORM}
        )

    def _show_extra_transform_form(
        self, errors: dict[str, str] | None = None
    ) -> FlowResult:
        source_options = build_source_options(
            self._entry_data, self._options_data(), source_kind="power", power_only=True
        )
        return self.async_show_form(
            step_id="extra_transform",
            data_schema=vol.Schema(
                {
                    vol.Required(CONST_EXTRA_ENTITY_NAME): str,
                    vol.Required(CONST_EXTRA_ENTITY_OPERATION): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=EXTRA_TRANSFORM_OPERATIONS,
                            translation_key=CONST_EXTRA_ENTITY_OPERATION,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                    vol.Required(CONST_EXTRA_ENTITY_SOURCE): vol.In(source_options),
                }
            ),
            errors=errors or ({} if source_options else {"base": "no_source_entities"}),
            description_placeholders={
                CONST_EXTRA_ENTITIES: str(len(self._extra_entities))
            },
        )

    def _handle_extra_transform(self, user_input: dict[str, Any]) -> FlowResult:
        if errors := _extra_entity_errors(user_input):
            return self._show_extra_transform_form(errors)
        self._extra_entities.append(
            normalize_extra_entity(user_input, self._extra_entities)
        )
        return self._show_extra_entities_menu("extra_entities")

    @navigable_step
    async def async_step_extra_aggregate_kind(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose the measurement kind for an aggregate entity."""
        if user_input is None:
            return self._show_extra_aggregate_kind_form()
        return await self.async_step_extra_entities(
            {**user_input, CONST_EXTRA_ACTION: CONST_EXTRA_ACTION_ADD_AGGREGATE}
        )

    def _show_extra_aggregate_kind_form(self) -> FlowResult:
        kinds = [
            kind
            for kind, count in _extra_source_counts(
                self._entry_data, self._options_data()
            ).items()
            if count >= 2
        ]
        return self.async_show_form(
            step_id="extra_aggregate_kind",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONST_EXTRA_ENTITY_SOURCE_KIND
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=kinds,
                            translation_key=CONST_EXTRA_ENTITY_SOURCE_KIND,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
            errors={},
            description_placeholders={
                CONST_EXTRA_ENTITIES: str(len(self._extra_entities))
            },
        )

    @navigable_step
    async def async_step_extra_aggregate(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Validate and add an aggregate of selected source entities."""
        if user_input is None:
            return self._show_extra_aggregate_form("power")
        return await self.async_step_extra_entities(
            {**user_input, CONST_EXTRA_ACTION: CONST_EXTRA_ACTION_ADD_AGGREGATE}
        )

    def _show_extra_aggregate_form(
        self, source_kind: str, errors: dict[str, str] | None = None
    ) -> FlowResult:
        source_options = build_source_options(
            self._entry_data, self._options_data(), source_kind=source_kind
        )
        return self.async_show_form(
            step_id="extra_aggregate",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONST_EXTRA_ENTITY_SOURCE_KIND, default=source_kind
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[source_kind],
                            translation_key=CONST_EXTRA_ENTITY_SOURCE_KIND,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                    vol.Required(CONST_EXTRA_ENTITY_NAME): str,
                    vol.Required(CONST_EXTRA_ENTITY_OPERATION): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=EXTRA_AGGREGATE_OPERATIONS,
                            translation_key=CONST_EXTRA_ENTITY_OPERATION,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                    vol.Required(CONST_EXTRA_ENTITY_SOURCES): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": key, "label": label}
                                for key, label in source_options.items()
                            ],
                            multiple=True,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
            errors=errors or ({} if source_options else {"base": "no_source_entities"}),
            description_placeholders={
                CONST_EXTRA_ENTITIES: str(len(self._extra_entities))
            },
        )

    def _handle_extra_aggregate(self, user_input: dict[str, Any]) -> FlowResult:
        source_kind = (
            user_input.get(CONST_EXTRA_ENTITY_SOURCE_KIND, "power")
            if user_input
            else "power"
        )
        errors = _extra_entity_errors(user_input, aggregate=True)
        if errors:
            return self._show_extra_aggregate_form(source_kind, errors)
        self._extra_entities.append(
            normalize_extra_entity(user_input, self._extra_entities)
        )
        return self._show_extra_entities_menu("extra_entities")

    @navigable_step
    async def async_step_extra_remove(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Remove a selected extra entity from the configuration draft."""
        if user_input is None:
            return self._show_extra_remove_form()
        return await self.async_step_extra_entities(
            {**user_input, CONST_EXTRA_ACTION: CONST_EXTRA_ACTION_REMOVE}
        )

    def _show_extra_remove_form(self) -> FlowResult:
        options = {
            extra["key"]: extra.get("name") or extra["key"]
            for extra in self._extra_entities
        }
        return self.async_show_form(
            step_id="extra_remove",
            data_schema=vol.Schema(
                {
                    vol.Required(CONST_EXTRA_ENTITY_REMOVE): vol.In(options),
                }
            ),
            errors={} if options else {"base": "no_extra_entities"},
            description_placeholders={
                CONST_EXTRA_ENTITIES: str(len(self._extra_entities))
            },
        )

    def _handle_extra_remove(self, user_input: dict[str, Any]) -> FlowResult:
        remove_key = user_input[CONST_EXTRA_ENTITY_REMOVE]
        self._extra_entities = [
            extra for extra in self._extra_entities if extra.get("key") != remove_key
        ]
        return self._show_extra_entities_menu("extra_entities")

    @property
    def _formula_context(self):
        return self._entry_data, self._options_data()

    async def _async_formula_done(self):
        return self._show_extra_entities_menu("extra_entities")

    def _options_data(self) -> dict[str, Any]:
        return {
            CONST_ECOMAIN_SELECTED_SLAVES: self._entry_data.get(
                CONST_ECOMAIN_SELECTED_SLAVES, []
            ),
            CONST_EXTRA_ENTITIES: self._extra_entities,
            CONST_MEASUREMENT_TYPES: list(self._measurement_types)
            if self._measurement_types is not None
            else get_entry_measurement_types(self._entry_data),
        }

    def _show_extra_entities_menu(self, step_id: str) -> FlowResult:
        actions = _extra_creation_actions(self._entry_data, self._options_data())
        if self._formula_result_types():
            actions.append("add_formula")
        if any(extra.get("operation") == "formula" for extra in self._extra_entities):
            actions.append("edit_formula")
        if self._extra_entities:
            actions.append(CONST_EXTRA_ACTION_REMOVE)
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONST_EXTRA_ACTION, default=CONST_EXTRA_ACTION_FINISH
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=actions,
                            translation_key=CONST_EXTRA_ACTION,
                            mode=SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
            description_placeholders={
                CONST_EXTRA_ENTITIES: str(len(self._extra_entities))
            },
        )

    async def _create_config_entry(self) -> FlowResult:
        serial = self._entry_data.get(CONST_ECOMAIN_SERIAL)
        mode = self._entry_data.get(CONST_ADD_MODE)
        mode_key = (
            CONST_ADD_MODE_CLOUD
            if mode == CONST_ADD_MODE_CLOUD
            else CONST_ADD_MODE_LOCAL
        )
        existing_entry = await self.async_set_unique_id(
            f"ecomain:{serial}:mode_{mode_key}",
            raise_on_progress=False,
        )
        if existing_entry is not None:
            return self.async_abort(reason="already_configured")  # type: ignore[return-value]

        options = self._options_data()
        return self.async_create_entry(
            title=self._build_title(),
            data=self._entry_data,
            options=options,
        )

    def _build_title(self) -> str:
        ecomain_serial = self._ecomain_local_config.get(
            CONST_ECOMAIN_SERIAL
        ) or self._ecomain_cloud_config.get(CONST_ECOMAIN_SERIAL)
        mode_key = (
            CONST_ADD_MODE_CLOUD
            if self._mode == CONST_ADD_MODE_CLOUD
            else CONST_ADD_MODE_LOCAL
        )
        return f"ecoMain {ecomain_serial} ({mode_key.title()})"

    def _normalize_slaves(self, slaves: list[str] | None) -> list[int]:
        if not slaves:
            return []
        allowed = set(self._ecomain_available_slaves)
        return sorted({int(s) for s in slaves if s in allowed})

    def _get_slave_index(self, slave: dict[str, Any]) -> int | None:
        hardware_number = str(slave.get("hardware_number") or "")
        suffix = hardware_number.rsplit("_", maxsplit=1)[-1] if hardware_number else ""
        if suffix.isdigit():
            return int(suffix)
        return None

    def _entry_by_unique_id(self, unique_id: str):
        return next(
            (
                entry
                for entry in self._async_current_entries()
                if entry.unique_id == unique_id
            ),
            None,
        )


class EnecessOptionsFlow(
    FlowNavigationMixin, FormulaFlowMixin, config_entries.OptionsFlow
):
    """Handle mutable enecess options."""

    _navigation_root = "init"

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Initialize the flow state and configuration drafts."""
        self._entry = entry
        self._cloud_token: str | None = entry.data.get(CONST_CLOUD_TOKEN)
        if entry.data.get(CONST_DEVICE_TYPE) == CONST_DEVICE_ECOPLUG:
            self._options: dict[str, Any] = {}
            self._ecoplug_devices: list[dict[str, Any]] = []
            return

        self._options = {
            **entry.options,
            CONST_MEASUREMENT_TYPES: get_entry_measurement_types(
                entry.data, entry.options
            ),
            CONST_ECOMAIN_SELECTED_SLAVES: get_entry_slaves(entry.data, entry.options),
            CONST_EXTRA_ENTITIES: get_entry_extra_entities(entry.options),
        }
        self._firmware_version = entry.data.get(CONST_ECOMAIN_FIRMWARE_VERSION)
        self._available_slaves: list[str] = []
        self._phase_device: int | None = None
        self._phase_values: dict[str, str | None] = {}
        self._cloud_slave_map: dict[int, Any] = self._normalize_slave_map(
            entry.data.get(CONST_ECOMAIN_CLOUD_SLAVE_MAP, {})
        )

    @property
    def _formula_context(self):
        return self._measurement_entry_data, self._options

    async def _async_formula_done(self):
        return await self._show_options_menu()

    @property
    def _measurement_entry_data(self) -> dict[str, Any]:
        return {
            **self._entry.data,
            CONST_ECOMAIN_FIRMWARE_VERSION: self._firmware_version,
        }

    @property
    def _extra_entities(self) -> list[dict[str, Any]]:
        return self._options[CONST_EXTRA_ENTITIES]

    @_extra_entities.setter
    def _extra_entities(self, value: list[dict[str, Any]]) -> None:
        self._options[CONST_EXTRA_ENTITIES] = value

    @navigable_step
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Refresh available devices and present the entry options."""
        if self._entry.data.get(CONST_DEVICE_TYPE) == CONST_DEVICE_ECOPLUG:
            return await self.async_step_ecoplug_select(user_input)

        if user_input is None:
            errors = await self._async_refresh_available_slaves()
            return await self._show_options_menu(errors)

        if CONST_ECOMAIN_SELECTED_SLAVES in user_input:
            selected = sorted(
                int(index) for index in user_input[CONST_ECOMAIN_SELECTED_SLAVES]
            )
            proposed = {**self._options, CONST_ECOMAIN_SELECTED_SLAVES: selected}
            if _selection_removes_extra_sources(
                self._entry.data, self._options, proposed
            ):
                return await self._show_options_menu({"base": "slave_in_use"})
            self._options[CONST_ECOMAIN_SELECTED_SLAVES] = selected
        action = user_input[CONST_EXTRA_ACTION]
        if action == "add_formula":
            self._reset_formula()
            return await self.async_step_extra_formula()
        if action == "edit_formula":
            return await self.async_step_extra_formula_edit()
        if action == "measurement_types":
            return await self.async_step_measurement_types()
        if action == "channel_phases":
            return await self.async_step_phase_device()
        if action == CONST_EXTRA_ACTION_ADD_TRANSFORM:
            return await self.async_step_extra_transform()
        if action == CONST_EXTRA_ACTION_ADD_AGGREGATE:
            return await self.async_step_extra_aggregate_kind()
        if action == CONST_EXTRA_ACTION_REMOVE:
            return await self.async_step_extra_remove()

        self._async_remove_stale_sensor_entries()
        self._update_entry_data()
        return self.async_create_entry(title="", data=self._options)

    @navigable_step
    async def async_step_measurement_types(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select measurements while retaining sources used by extra entities."""
        selected = self._options[CONST_MEASUREMENT_TYPES]
        errors = {}
        if user_input is not None:
            selected = user_input.get(CONST_MEASUREMENT_TYPES)
            error = "no_measurements_selected" if not selected else None
            if not error:
                proposed = {**self._options, CONST_MEASUREMENT_TYPES: selected}
                if _selection_removes_extra_sources(
                    self._measurement_entry_data, self._options, proposed
                ):
                    error = "measurement_in_use"
            if error:
                errors["base"] = error
            else:
                self._options[CONST_MEASUREMENT_TYPES] = list(selected)
                return await self._show_options_menu()
        return self.async_show_form(
            step_id="measurement_types",
            data_schema=_measurement_schema(
                self._measurement_entry_data, selected or []
            ),
            errors=errors,
        )

    @navigable_step
    async def async_step_phase_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select the local device whose channel phases will be edited."""
        choices = [
            "0",
            *[
                str(index)
                for index in get_entry_slaves(self._entry.data, self._options)
                if str(index) in self._available_slaves
            ],
        ]
        if user_input is not None:
            self._phase_device = int(user_input["phase_device"])
            self._phase_values = {}
            return await self.async_step_channel_phases()
        return self.async_show_form(
            step_id="phase_device",
            data_schema=vol.Schema(
                {
                    vol.Required("phase_device", default="0"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=choices,
                            translation_key="phase_device",
                            mode=SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
            errors={},
        )

    @navigable_step
    async def async_step_channel_phases(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Read channel phases and verify requested register updates."""
        if self._entry.data.get(CONST_ADD_MODE) == CONST_ADD_MODE_CLOUD:
            return self.async_abort(reason="phase_unavailable")
        available = [
            0,
            *[
                index
                for index in get_entry_slaves(self._entry.data, self._options)
                if str(index) in self._available_slaves
            ],
        ]
        if self._phase_device not in available:
            return await self.async_step_phase_device()
        errors = {}
        runtime = getattr(self._entry, "runtime_data", None)
        client = runtime.modbus_client if runtime is not None else None
        if client is None:
            errors["base"] = "phase_unavailable"
        else:
            try:
                response = await client.read_holding_registers(
                    CONF_ECOMAIN_FIRMWARE_VERSION_REGISTER, 1
                )
                if (
                    decode_int16(response.registers, signed=False)
                    < CONF_ECOMAIN_PHASE_FIRMWARE_VERSION
                ):
                    errors["base"] = "phase_firmware_too_old"
            except Exception:  # noqa: BLE001 - Convert driver and malformed-register failures into form errors.
                errors["base"] = "phase_read_failed"
        if not errors and user_input is not None and self._phase_values:
            desired = {
                f"channel_{channel}": user_input.get(f"channel_{channel}")
                for channel in range(1, 11)
            }
            try:
                errors = await async_write_phases(client, self._phase_device, desired)
            except Exception:  # noqa: BLE001 - Convert driver and malformed-register failures into form errors.
                errors = {"base": "phase_write_failed"}
            if not errors:
                return await self._show_options_menu()
            self._phase_values = desired
        elif not errors:
            try:
                self._phase_values = await async_read_phases(client, self._phase_device)
            except Exception:  # noqa: BLE001 - Convert driver and malformed-register failures into form errors.
                errors["base"] = "phase_read_failed"
        fields = {}
        # A failed read must never turn a default phase into an unintended write.
        if self._phase_values:
            for channel in range(1, 11):
                key = f"channel_{channel}"
                value = self._phase_values.get(key)
                field = (
                    vol.Required(key, default=value)
                    if value in ("L1", "L2", "L3")
                    else vol.Required(key)
                )
                fields[field] = selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["L1", "L2", "L3"], mode=SelectSelectorMode.DROPDOWN
                    )
                )
        return self.async_show_form(
            step_id="channel_phases",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={
                "device": "ecoMain"
                if self._phase_device == 0
                else f"ecoSub {self._phase_device}"
            },
        )

    @navigable_step
    async def async_step_ecoplug_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose which cloud ecoPlug devices belong to the entry."""
        if user_input is None:
            errors = await self._async_refresh_ecoplug_devices()
            return self._show_ecoplug_select_form(errors=errors)

        selected = user_input.get(CONST_ECOPLUG_SELECTED) or []
        devices = select_plugs(self._ecoplug_devices, selected)
        if not devices:
            return self._show_ecoplug_select_form(
                errors={"base": "no_devices_selected"},
            )

        assert self._cloud_token is not None
        data = {
            **self._entry.data,
            CONST_CLOUD_TOKEN: self._cloud_token,
            CONST_ECOPLUG_DEVICES: devices,
        }
        async_remove_unconfigured_registry_entries(
            self.hass,
            self._entry,
            data=data,
        )
        self.hass.config_entries.async_update_entry(self._entry, data=data)
        return self.async_create_entry(title="", data={})

    async def _async_refresh_ecoplug_devices(self) -> dict[str, str] | None:
        api = EnecessApi(
            session=async_get_clientsession(self.hass),
            base_url=CONF_CLOUD_BASE_URL,
        )
        try:
            token = await api.generate_token(
                self._entry.data[CONST_CLOUD_USERNAME],
                self._entry.data[CONST_CLOUD_PASSWORD],
            )
            devices = await api.get_hardware_list(token, hardware_type=2)
        except EnecessAuthError:
            self._ecoplug_devices = []
            return {"base": "auth_failed"}
        except (EnecessApiError, OSError, TimeoutError, ValueError):
            self._ecoplug_devices = []
            return {"base": "cannot_connect"}

        if not build_plug_options(devices):
            self._ecoplug_devices = []
            return {"base": "no_devices_found"}

        self._cloud_token = token
        self._ecoplug_devices = devices
        return None

    def _show_ecoplug_select_form(
        self, errors: dict[str, str] | None = None
    ) -> FlowResult:
        options = build_plug_options(self._ecoplug_devices)
        current = {
            str(device.get("hardware_number"))
            for device in self._entry.data.get(CONST_ECOPLUG_DEVICES, [])
        }
        default = [serial for serial in options if serial in current]
        return self.async_show_form(
            step_id="ecoplug_select",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONST_ECOPLUG_SELECTED,
                        default=default,
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": serial, "label": label}
                                for serial, label in options.items()
                            ],
                            multiple=True,
                            mode=SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
            errors=errors or {},
        )

    @navigable_step
    async def async_step_extra_transform(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure a derived entity using a selected power source."""
        source_options = build_source_options(
            self._measurement_entry_data,
            self._options,
            source_kind="power",
            power_only=True,
        )
        errors = _extra_entity_errors(user_input) if user_input is not None else {}
        if user_input is None or errors:
            return self.async_show_form(
                step_id="extra_transform",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONST_EXTRA_ENTITY_NAME): str,
                        vol.Required(
                            CONST_EXTRA_ENTITY_OPERATION
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=EXTRA_TRANSFORM_OPERATIONS,
                                translation_key=CONST_EXTRA_ENTITY_OPERATION,
                                mode=SelectSelectorMode.LIST,
                            )
                        ),
                        vol.Required(CONST_EXTRA_ENTITY_SOURCE): vol.In(source_options),
                    }
                ),
                errors=errors
                or ({} if source_options else {"base": "no_source_entities"}),
            )

        self._extra_entities.append(
            normalize_extra_entity(user_input, self._extra_entities)
        )
        return await self._show_options_menu()

    @navigable_step
    async def async_step_extra_aggregate_kind(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose the measurement kind for an aggregate entity."""
        if user_input is None:
            kinds = [
                kind
                for kind, count in _extra_source_counts(
                    self._measurement_entry_data, self._options
                ).items()
                if count >= 2
            ]
            return self.async_show_form(
                step_id="extra_aggregate_kind",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONST_EXTRA_ENTITY_SOURCE_KIND
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=kinds,
                                translation_key=CONST_EXTRA_ENTITY_SOURCE_KIND,
                                mode=SelectSelectorMode.LIST,
                            )
                        ),
                    }
                ),
                errors={},
            )
        return await self.async_step_extra_aggregate(user_input)

    @navigable_step
    async def async_step_extra_aggregate(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Validate and add an aggregate of selected source entities."""
        source_kind = (
            user_input.get(CONST_EXTRA_ENTITY_SOURCE_KIND, "power")
            if user_input
            else "power"
        )
        source_options = build_source_options(
            self._measurement_entry_data, self._options, source_kind=source_kind
        )
        submitted = (
            user_input is not None and CONST_EXTRA_ENTITY_OPERATION in user_input
        )
        errors = _extra_entity_errors(user_input, aggregate=True) if submitted else {}
        if not submitted or errors:
            return self.async_show_form(
                step_id="extra_aggregate",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONST_EXTRA_ENTITY_SOURCE_KIND, default=source_kind
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=[source_kind],
                                translation_key=CONST_EXTRA_ENTITY_SOURCE_KIND,
                                mode=SelectSelectorMode.LIST,
                            )
                        ),
                        vol.Required(CONST_EXTRA_ENTITY_NAME): str,
                        vol.Required(
                            CONST_EXTRA_ENTITY_OPERATION
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=EXTRA_AGGREGATE_OPERATIONS,
                                translation_key=CONST_EXTRA_ENTITY_OPERATION,
                                mode=SelectSelectorMode.LIST,
                            )
                        ),
                        vol.Required(
                            CONST_EXTRA_ENTITY_SOURCES
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=[
                                    {"value": key, "label": label}
                                    for key, label in source_options.items()
                                ],
                                multiple=True,
                                mode=SelectSelectorMode.LIST,
                            )
                        ),
                    }
                ),
                errors=errors
                or ({} if source_options else {"base": "no_source_entities"}),
            )

        self._extra_entities.append(
            normalize_extra_entity(user_input, self._extra_entities)
        )
        return await self._show_options_menu()

    @navigable_step
    async def async_step_extra_remove(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Remove a selected extra entity from the configuration draft."""
        options = {
            extra["key"]: extra.get("name") or extra["key"]
            for extra in self._extra_entities
        }
        if user_input is None:
            return self.async_show_form(
                step_id="extra_remove",
                data_schema=vol.Schema(
                    {vol.Required(CONST_EXTRA_ENTITY_REMOVE): vol.In(options)}
                ),
                errors={} if options else {"base": "no_extra_entities"},
            )

        remove_key = user_input[CONST_EXTRA_ENTITY_REMOVE]
        self._extra_entities = [
            extra for extra in self._extra_entities if extra.get("key") != remove_key
        ]
        return await self._show_options_menu()

    async def _show_options_menu(
        self, errors: dict[str, str] | None = None
    ) -> FlowResult:
        actions = _extra_creation_actions(self._measurement_entry_data, self._options)
        if self._formula_result_types():
            actions.append("add_formula")
        if any(extra.get("operation") == "formula" for extra in self._extra_entities):
            actions.append("edit_formula")
        actions.append("measurement_types")
        if (
            self._entry.data.get(CONST_ADD_MODE) != CONST_ADD_MODE_CLOUD
            and (self._firmware_version or 0) >= CONF_ECOMAIN_PHASE_FIRMWARE_VERSION
        ):
            actions.append("channel_phases")
        if self._extra_entities:
            actions.append(CONST_EXTRA_ACTION_REMOVE)
        selected_slaves = [
            str(index) for index in self._options.get(CONST_ECOMAIN_SELECTED_SLAVES, [])
        ]
        slave_choices = sorted(
            set(self._available_slaves) | set(selected_slaves), key=int
        )
        schema_fields: dict[Any, Any] = {}
        if slave_choices:
            schema_fields[
                vol.Optional(
                    CONST_ECOMAIN_SELECTED_SLAVES,
                    default=selected_slaves,
                )
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=slave_choices,
                    multiple=True,
                    translation_key=CONST_ECOMAIN_SELECTED_SLAVES,
                    mode=SelectSelectorMode.LIST,
                )
            )
        schema_fields[
            vol.Required(CONST_EXTRA_ACTION, default=CONST_EXTRA_ACTION_FINISH)
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=actions,
                translation_key=CONST_EXTRA_ACTION,
                mode=SelectSelectorMode.LIST,
            )
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_fields),
            description_placeholders={
                CONST_DEVICE_TYPE: {"ecomain": "ecoMain", "ecoplug": "ecoPlug"}.get(
                    self._entry.data.get(CONST_DEVICE_TYPE), ""
                ),
                CONST_ADD_MODE: str(self._entry.data.get(CONST_ADD_MODE)),
                CONST_ECOMAIN_SERIAL: str(self._entry.data.get(CONST_ECOMAIN_SERIAL)),
                CONST_EXTRA_ENTITIES: str(len(self._extra_entities)),
            },
            errors=errors or {},
        )

    async def _async_refresh_available_slaves(self) -> dict[str, str] | None:
        if self._entry.data.get(CONST_ADD_MODE) == CONST_ADD_MODE_CLOUD:
            return await self._async_refresh_cloud_slaves()
        return await self._async_refresh_local_slaves()

    async def _async_refresh_local_slaves(self) -> dict[str, str] | None:
        self._firmware_version = None
        host = self._entry.data.get(CONST_ECOMAIN_HOST)
        port = self._entry.data.get(CONST_ECOMAIN_PORT, CONF_ECOMAIN_PORT)
        if not host:
            self._available_slaves = []
            return {"base": "cannot_connect_local"}

        client = EnecessModbusClient(host, port)
        result = await async_validate_local_device(
            client,
            firmware_register=CONF_ECOMAIN_FIRMWARE_VERSION_REGISTER,
            minimum_firmware=CONF_ECOMAIN_MIN_FIRMWARE_VERSION,
            slave_register_start=CONF_ECOMAIN_SLAVE_ONLINE_REGISTER_START,
            slave_register_count=CONF_ECOMAIN_SLAVE_ONLINE_REGISTER_COUNT,
            allowed_slaves=set(self._ecomain_available_slaves),
            firmware_timeout=CONF_ECOMAIN_FIRMWARE_READ_TIMEOUT,
        )
        self._firmware_version = result.firmware_version
        self._available_slaves = result.online_slaves or []
        return {"base": result.error} if result.error is not None else None

    async def _async_refresh_cloud_slaves(self) -> dict[str, str] | None:
        api = EnecessApi(
            session=async_get_clientsession(self.hass), base_url=CONF_CLOUD_BASE_URL
        )
        try:
            token = await api.generate_token(
                self._entry.data[CONST_CLOUD_USERNAME],
                self._entry.data[CONST_CLOUD_PASSWORD],
            )
            masters = await api.get_hardware_list(token, hardware_type=0)
            serial = str(self._entry.data[CONST_ECOMAIN_SERIAL])
            master = next(
                (m for m in masters if str(m.get("hardware_number")) == serial), None
            )
            if master is None:
                self._available_slaves = []
                return {"base": "no_devices_found"}
            cloud_slaves = await api.get_hardware_list(
                token, hardware_type=1, parent_id=int(master["id"])
            )
        except EnecessAuthError:
            self._available_slaves = []
            return {"base": "auth_failed"}
        except (EnecessApiError, OSError, TimeoutError, ValueError):
            self._available_slaves = []
            return {"base": "cannot_connect"}

        allowed = set(self._ecomain_available_slaves)
        self._cloud_token = token
        self._available_slaves = []
        # A missing discovery result must not erase a selected device's identity.
        for slave in cloud_slaves:
            slave_index = self._get_slave_index(slave)
            if slave_index is not None and str(slave_index) in allowed:
                self._available_slaves.append(str(slave_index))
                self._cloud_slave_map[slave_index] = slave.get("hardware_number")
        self._available_slaves = sorted(set(self._available_slaves), key=int)
        return None

    def _update_entry_data(self) -> None:
        if self._entry.data.get(CONST_ADD_MODE) != CONST_ADD_MODE_CLOUD:
            if self._firmware_version is not None:
                self.hass.config_entries.async_update_entry(
                    self._entry, data=self._measurement_entry_data
                )
            return

        selected = {
            int(s) for s in self._options.get(CONST_ECOMAIN_SELECTED_SLAVES, [])
        }
        slave_map = {
            idx: hardware_number
            for idx, hardware_number in self._cloud_slave_map.items()
            if idx in selected
        }
        data = {
            **self._entry.data,
            CONST_CLOUD_TOKEN: self._cloud_token
            or self._entry.data.get(CONST_CLOUD_TOKEN),
            CONST_ECOMAIN_CLOUD_SLAVE_MAP: slave_map,
        }
        self.hass.config_entries.async_update_entry(self._entry, data=data)

    def _async_remove_stale_sensor_entries(self) -> None:
        old_unique_ids = build_entry_sensor_unique_ids(
            self._entry.data, self._entry.options
        )
        verified_data = (
            self._entry.data
            if self._firmware_version is None
            else self._measurement_entry_data
        )
        new_unique_ids = build_entry_sensor_unique_ids(verified_data, self._options)
        stale_unique_ids = old_unique_ids - new_unique_ids
        registry = er.async_get(self.hass)
        for unique_id in stale_unique_ids:
            entity_id = registry.async_get_entity_id(Platform.SENSOR, DOMAIN, unique_id)
            if entity_id is not None:
                registry.async_remove(entity_id)

        old_identifiers = build_entry_device_identifiers(
            self._entry.data, self._entry.options
        )
        new_identifiers = build_entry_device_identifiers(
            self._entry.data, self._options
        )
        stale_identifiers = old_identifiers - new_identifiers
        if not stale_identifiers:
            return

        device_registry = dr.async_get(self.hass)
        for device_entry in dr.async_entries_for_config_entry(
            device_registry, self._entry.entry_id
        ):
            if device_entry.identifiers.isdisjoint(stale_identifiers):
                continue
            device_registry.async_remove_device(device_entry.id)

    @property
    def _ecomain_available_slaves(self) -> list[str]:
        return (
            cast(
                EcoMainDeviceTyp, DEVICE_CONFIGS[CONST_DEVICE_ECOMAIN]
            ).available_slaves
            or []
        )

    def _normalize_slaves(self, slaves: list[str] | None) -> list[int]:
        if not slaves:
            return []
        allowed = set(self._available_slaves or self._ecomain_available_slaves)
        return sorted({int(s) for s in slaves if str(s) in allowed})

    def _get_slave_index(self, slave: dict[str, Any]) -> int | None:
        hardware_number = str(slave.get("hardware_number") or "")
        suffix = hardware_number.rsplit("_", maxsplit=1)[-1] if hardware_number else ""
        if suffix.isdigit():
            return int(suffix)
        return None

    def _normalize_slave_map(self, slave_map: dict[Any, Any]) -> dict[int, Any]:
        normalized = {}
        for idx, hardware_number in (slave_map or {}).items():
            try:
                normalized[int(idx)] = hardware_number
            except (TypeError, ValueError):
                continue
        return normalized
