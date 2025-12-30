import asyncio
from dataclasses import dataclass
from typing import Any, cast, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import SelectSelectorMode
from zeroconf import ServiceStateChange
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo

from .client_api import EnecessApi, EnecessAuthError
from .client_modbus import EnecessModbusClient, decode_int16
from .const import (
    CONST_DEVICE_TYPE, CONST_ADD_MODE, CONST_ECOMAIN_SERIAL, CONST_ECOMAIN_SELECTED_SLAVES, CONST_CLOUD_USERNAME, CONST_CLOUD_PASSWORD, CONST_CLOUD_TOKEN,
    CONST_ECOMAIN_CLOUD_MASTER_ID, CONST_ECOMAIN_CLOUD_SLAVE_MAP, DiscoveryConfig, DEVICE_CONFIGS, CONF_ECOMAIN_PORT, CONF_LOCAL_MDNS_SCAN_INTERVAL, DOMAIN,
    CONST_DEVICE_ECOMAIN, CONF_CLOUD_BASE_URL, CONST_ADD_MODE_LOCAL_AUTO, CONST_ADD_MODE_LOCAL_MANUAL, CONST_ADD_MODE_CLOUD, EcoMainDeviceTyp,
    CONST_ECOMAIN_PORT, CONST_ECOMAIN_MASTERS, CONST_ECOMAIN_CLOUD_MASTER, CONST_ECOMAIN_CLOUD_SLAVES, CONST_ADD_MODE_LOCAL, CONST_MDNS_IP,
    CONF_ECOMAIN_SLAVE_ONLINE_REGISTER_START, CONF_ECOMAIN_SLAVE_ONLINE_REGISTER_COUNT,
    CONST_ECOMAIN_ONLINE_SLAVES, CONST_ECOMAIN_HOST, CONF_ECOMAIN_FIRMWARE_VERSION_REGISTER, CONF_ECOMAIN_MIN_FIRMWARE_VERSION
)

try:
    from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
except ImportError:
    from homeassistant.components.zeroconf import ZeroconfServiceInfo


@dataclass(frozen=True)
class DiscoveredDevice:
    serial: str
    hostname: str
    service_name: str
    ip: Optional[str]


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._discovered: list[DiscoveredDevice] = []
        self._device_type: Optional[str] = None
        self._mode: Optional[str] = None
        self._cloud_api: Optional[EnecessApi] = None
        self._cloud_token: Optional[str] = None
        self._cloud_username: Optional[str] = None
        self._cloud_password: Optional[str] = None
        self._ecomain_local_config: dict[str, Any] = {}
        self._ecomain_cloud_config: dict[str, Any] = {}

    @property
    def _ecomain_available_slaves(self) -> list[str]:
        return cast(EcoMainDeviceTyp, DEVICE_CONFIGS[CONST_DEVICE_ECOMAIN]).available_slaves or []

    async def async_step_user(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
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
        if device_type not in DEVICE_CONFIGS:
            return self.async_abort(reason="unsupported_device_type")  # type: ignore[return-value]

        self._device_type = device_type
        if device_type == CONST_DEVICE_ECOMAIN:
            return await self.async_step_ecomain_mode()  # type: ignore[return-value]

        return self.async_abort(reason="unsupported_device_type")  # type: ignore[return-value]

    async def async_step_ecomain_mode(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_mode",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONST_ADD_MODE, default=CONST_ADD_MODE_LOCAL_AUTO): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=[CONST_ADD_MODE_LOCAL_AUTO, CONST_ADD_MODE_LOCAL_MANUAL, CONST_ADD_MODE_CLOUD],
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
        elif mode == CONST_ADD_MODE_LOCAL_MANUAL:
            return await self.async_step_ecomain_manual()  # type: ignore[return-value]
        elif mode == CONST_ADD_MODE_CLOUD:
            return await self.async_step_ecomain_cloud_login()  # type: ignore[return-value]
        return self.async_abort(reason="unsupported_add_mode")  # type: ignore[return-value]

    async def _async_mdns_scan(self, discovery_config: DiscoveryConfig) -> list[DiscoveredDevice]:
        zc_inst = await zeroconf.async_get_async_instance(self.hass)
        found_names: set[str] = set()
        done = asyncio.Event()

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

        async def _wait() -> None:
            try:
                await asyncio.sleep(CONF_LOCAL_MDNS_SCAN_INTERVAL)
            finally:
                done.set()

        waiter = asyncio.create_task(_wait())
        await done.wait()

        await browser.async_cancel()
        waiter.cancel()

        results: list[DiscoveredDevice] = []

        for name in sorted(found_names):
            # name format like: "{mdns_prefix}XXXX._http._tcp.local."
            instance = name.split(".", 1)[0]
            serial = instance[len(mdns_prefix):]
            if not serial:
                continue

            info = AsyncServiceInfo(mdns_type, name)
            ok = await info.async_request(zc_inst.zeroconf, timeout=2000)
            if not ok or not info.server:
                continue

            hostname = info.server.rstrip(".")
            ip: Optional[str] = None
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

    async def async_step_ecomain_auto_scan(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
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

            options = {d.serial: f'EcoMain {d.serial} ({d.ip})' for d in self._discovered}
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_auto_scan",
                data_schema=vol.Schema({vol.Required(CONST_ECOMAIN_SERIAL): vol.In(options)}),
                errors={},
            )

        selected_serial = user_input[CONST_ECOMAIN_SERIAL]
        selected = next((d for d in self._discovered if d.serial == selected_serial), None)

        if selected is None:
            return self.async_abort(reason="no_devices_found")  # type: ignore[return-value]

        self._ecomain_local_config = {
            CONST_ECOMAIN_SERIAL: selected.serial,
            CONST_MDNS_IP: selected.ip,
        }

        return await self.async_step_ecomain_local_confirm()  # type: ignore[return-value]

    async def async_step_ecomain_manual(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_manual",
                data_schema=vol.Schema({vol.Required(CONST_ECOMAIN_SERIAL): str, vol.Required(CONST_ECOMAIN_HOST): str}),
                errors={},
            )

        host = user_input[CONST_ECOMAIN_HOST].strip()
        serial = user_input[CONST_ECOMAIN_SERIAL].strip()

        if not host or not serial:
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_manual",
                data_schema=vol.Schema({vol.Required(CONST_ECOMAIN_SERIAL): str, vol.Required(CONST_ECOMAIN_HOST): str}),
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
    ) -> Optional[str]:
        instance = service_name.partition(".")[0]
        if not instance.startswith(mdns_prefix):
            return None
        serial = instance[len(mdns_prefix):]
        return serial or None

    def _match_discovery(
            self,
            discovery_info: ZeroconfServiceInfo,
    ) -> Optional[tuple[str, DiscoveredDevice]]:
        svc_type = discovery_info.type
        svc_name = discovery_info.name

        for device_type, config in DEVICE_CONFIGS.items():
            discovery = config.discovery
            if not discovery or svc_type != discovery.mdns_type or not svc_name.startswith(discovery.mdns_prefix):
                continue

            serial = self._extract_serial_from_service_name(svc_name, discovery.mdns_prefix)
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

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> FlowResult:
        match = self._match_discovery(discovery_info)
        if match is None:
            return self.async_abort(reason="no_matching_discovery")  # type: ignore[return-value]

        self._device_type, selected = match
        self._mode = CONST_ADD_MODE_LOCAL_AUTO
        self._ecomain_local_config = {
            CONST_ECOMAIN_SERIAL: selected.serial,
            CONST_MDNS_IP: selected.ip,
        }

        self.context["title_placeholders"] = {CONST_ECOMAIN_SERIAL: selected.serial, CONST_ECOMAIN_HOST: selected.ip}

        existing_entry = await self.async_set_unique_id(f"ecomain:{selected.serial}:mode_local", raise_on_progress=False)
        if existing_entry is not None:
            self._abort_if_unique_id_configured(updates={CONST_MDNS_IP: selected.ip})

        return await self.async_step_ecomain_local_confirm()  # type: ignore[return-value]

    async def _async_validate_local_device(self, host: str, port: int) -> Optional[dict[str, str]]:
        client = EnecessModbusClient(host, port)
        try:
            rr = await client.read_holding_registers(CONF_ECOMAIN_FIRMWARE_VERSION_REGISTER, 1)
            firmware_version = decode_int16(rr.registers, signed=False)
            if firmware_version < CONF_ECOMAIN_MIN_FIRMWARE_VERSION:
                return {"base": "firmware_too_old"}
        except Exception:
            return {"base": "firmware_too_old"}
        try:
            rr = await client.read_holding_registers(
                CONF_ECOMAIN_SLAVE_ONLINE_REGISTER_START,
                CONF_ECOMAIN_SLAVE_ONLINE_REGISTER_COUNT,
            )
            allowed = set(self._ecomain_available_slaves)
            online_slaves = []
            for idx, reg in enumerate(rr.registers, start=1):
                if decode_int16([reg], signed=False) == 1 and str(idx) in allowed:
                    online_slaves.append(str(idx))
            self._ecomain_local_config[CONST_ECOMAIN_ONLINE_SLAVES] = online_slaves
            return None
        except Exception:
            return {"base": "cannot_connect_local"}
        finally:
            await client.async_close()

    async def async_step_ecomain_local_confirm(
            self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        if user_input is None:
            self._set_confirm_only()
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_local_confirm",
                data_schema=vol.Schema({}),
                description_placeholders={
                    CONST_ECOMAIN_SERIAL: self._ecomain_local_config.get(CONST_ECOMAIN_SERIAL),
                    CONST_ECOMAIN_HOST: self._ecomain_local_config.get(CONST_MDNS_IP) or self._ecomain_local_config.get(CONST_ECOMAIN_HOST),
                },
            )
        return await self.async_step_ecomain_local_setup()  # type: ignore[return-value]

    async def async_step_ecomain_local_setup(
            self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        host = self._ecomain_local_config.get(CONST_MDNS_IP) or self._ecomain_local_config.get(CONST_ECOMAIN_HOST)
        ecomain_serial = self._ecomain_local_config.get(CONST_ECOMAIN_SERIAL)

        if CONST_ECOMAIN_ONLINE_SLAVES in self._ecomain_local_config:
            if user_input is not None:
                selected = user_input.get(CONST_ECOMAIN_SELECTED_SLAVES) or []

                existing_entry = await self.async_set_unique_id(
                    f"ecomain:{ecomain_serial}:mode_local",
                    raise_on_progress=False,
                )
                if existing_entry is not None:
                    return self.async_abort(reason="already_configured")  # type: ignore[return-value]

                return self.async_create_entry(  # type: ignore[return-value]
                    title=self._build_title(),
                    data={
                        CONST_DEVICE_TYPE: CONST_DEVICE_ECOMAIN,
                        CONST_ADD_MODE: self._mode,
                        CONST_ECOMAIN_HOST: host,
                        CONST_ECOMAIN_PORT: CONF_ECOMAIN_PORT,
                        CONST_ECOMAIN_SERIAL: ecomain_serial,
                        CONST_ECOMAIN_SELECTED_SLAVES: self._normalize_slaves(selected),
                    },
                )

            online_slaves = self._ecomain_local_config.get(CONST_ECOMAIN_ONLINE_SLAVES)
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_local_setup",
                data_schema=vol.Schema(
                    {
                        vol.Optional(CONST_ECOMAIN_SELECTED_SLAVES, default=online_slaves): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=online_slaves,
                                multiple=True,
                                translation_key=CONST_ECOMAIN_SELECTED_SLAVES,
                                mode=SelectSelectorMode.LIST,
                            )
                        )
                    } if online_slaves else {}
                ),
                description_placeholders={
                    CONST_ECOMAIN_SERIAL: self._ecomain_local_config.get(CONST_ECOMAIN_SERIAL),
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
                    CONST_ECOMAIN_SERIAL: self._ecomain_local_config.get(CONST_ECOMAIN_SERIAL),
                    CONST_ECOMAIN_HOST: host,
                },
            )

        online_slaves = self._ecomain_local_config.get(CONST_ECOMAIN_ONLINE_SLAVES)
        if not online_slaves:
            existing_entry = await self.async_set_unique_id(
                f"ecomain:{ecomain_serial}:mode_local",
                raise_on_progress=False,
            )
            if existing_entry is not None:
                return self.async_abort(reason="already_configured")  # type: ignore[return-value]

            return self.async_create_entry(  # type: ignore[return-value]
                title=self._build_title(),
                data={
                    CONST_DEVICE_TYPE: CONST_DEVICE_ECOMAIN,
                    CONST_ADD_MODE: self._mode,
                    CONST_ECOMAIN_HOST: host,
                    CONST_ECOMAIN_PORT: CONF_ECOMAIN_PORT,
                    CONST_ECOMAIN_SERIAL: ecomain_serial,
                    CONST_ECOMAIN_SELECTED_SLAVES: [],
                },
            )

        return self.async_show_form(  # type: ignore[return-value]
            step_id="ecomain_local_setup",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONST_ECOMAIN_SELECTED_SLAVES, default=online_slaves): selector.SelectSelector(
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

    async def async_step_ecomain_cloud_login(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
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
        password = str(user_input[CONST_CLOUD_PASSWORD]).strip()

        api = self._get_cloud_api()
        try:
            token = await api.generate_token(username, password)
            masters = await api.get_hardware_list(token, hardware_type=0)
        except EnecessAuthError:
            return self.async_abort(reason="auth_failed")  # type: ignore[return-value]
        except Exception:
            return self.async_abort(reason="cannot_connect")  # type: ignore[return-value]
        else:
            if not masters:
                return self.async_abort(reason="no_devices_found")  # type: ignore[return-value]
            else:
                self._cloud_username = username
                self._cloud_password = password
                self._cloud_token = token
                self._ecomain_cloud_config[CONST_ECOMAIN_MASTERS] = masters
                return await self.async_step_ecomain_cloud_master()  # type: ignore[return-value]

    async def async_step_ecomain_cloud_master(self, user_input: Optional[dict[str, Any]] = None) -> FlowResult:
        assert self._cloud_token is not None
        assert self._cloud_username is not None
        assert self._cloud_password is not None

        masters = self._ecomain_cloud_config.get(CONST_ECOMAIN_MASTERS, [])
        api = self._get_cloud_api()

        if user_input is None:
            options = {
                int(m["id"]): str(m.get("name") or m.get("hardware_number") or m["id"])
                for m in masters
                if "id" in m
            }
            default_master = next(iter(options)) if options else None
            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_cloud_master",
                data_schema=vol.Schema({vol.Required(CONST_ECOMAIN_CLOUD_MASTER_ID, default=default_master): vol.In(options)}),
                errors={},
            )

        master_id = int(user_input[CONST_ECOMAIN_CLOUD_MASTER_ID])
        ecomain_cloud_master = next((m for m in masters if int(m.get("id", -1)) == master_id), None)
        self._ecomain_cloud_config[CONST_ECOMAIN_CLOUD_MASTER] = ecomain_cloud_master
        if ecomain_cloud_master is None:
            return self.async_abort(reason="no_devices_found")  # type: ignore[return-value]

        serial = str(ecomain_cloud_master.get("hardware_number"))
        self._ecomain_cloud_config[CONST_ECOMAIN_SERIAL] = serial

        ecomain_cloud_slaves = await api.get_hardware_list(
            self._cloud_token,
            hardware_type=1,
            parent_id=master_id,
        )
        for slave in ecomain_cloud_slaves:
            slave_index = self._get_slave_index(slave)
            if slave_index is not None:
                slave["index"] = slave_index
        self._ecomain_cloud_config[CONST_ECOMAIN_CLOUD_SLAVES] = ecomain_cloud_slaves

        return await self.async_step_ecomain_cloud_confirm()  # type: ignore[return-value]

    async def async_step_ecomain_cloud_confirm(
            self, user_input: Optional[dict[str, Any]] = None
    ):
        if user_input is None:
            self._set_confirm_only()

            ecomain_cloud_slaves = self._ecomain_cloud_config[CONST_ECOMAIN_CLOUD_SLAVES]
            salve_indices = [slave["index"] for slave in ecomain_cloud_slaves if "index" in slave]
            slave_options = sorted(map(str, salve_indices))
            slave_options = [s for s in slave_options if s in self._ecomain_available_slaves]

            return self.async_show_form(  # type: ignore[return-value]
                step_id="ecomain_cloud_confirm",
                data_schema=vol.Schema(
                    {
                        vol.Optional(CONST_ECOMAIN_SELECTED_SLAVES, default=slave_options): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=slave_options,
                                multiple=True,
                                translation_key=CONST_ECOMAIN_SELECTED_SLAVES,
                                mode=SelectSelectorMode.LIST,
                            )
                        )
                    } if slave_options else {}
                ),
                description_placeholders={
                    CONST_ECOMAIN_SERIAL: self._ecomain_cloud_config.get(CONST_ECOMAIN_SERIAL),
                },
            )
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
            slave = next((s for s in cloud_slaves if self._get_slave_index(s) == int(sid_str)), {})
            if slave:
                slave_map[int(sid_str)] = slave.get("hardware_number")

        existing_entry = await self.async_set_unique_id(
            f"ecomain:{serial}:mode_cloud", raise_on_progress=False
        )
        if existing_entry is not None:
            return self.async_abort(reason="already_configured")  # type: ignore[return-value]

        return self.async_create_entry(  # type: ignore[return-value]
            title=self._build_title(),
            data={
                CONST_DEVICE_TYPE: CONST_DEVICE_ECOMAIN,
                CONST_ADD_MODE: CONST_ADD_MODE_CLOUD,
                CONST_CLOUD_USERNAME: self._cloud_username,
                CONST_CLOUD_PASSWORD: self._cloud_password,
                CONST_CLOUD_TOKEN: self._cloud_token,
                CONST_ECOMAIN_SERIAL: serial,
                CONST_ECOMAIN_SELECTED_SLAVES: self._normalize_slaves(selected_slaves),
                CONST_ECOMAIN_CLOUD_SLAVE_MAP: slave_map,
            },
        )

    def _build_title(self) -> str:
        ecomain_serial = self._ecomain_local_config.get(CONST_ECOMAIN_SERIAL) or self._ecomain_cloud_config.get(CONST_ECOMAIN_SERIAL)
        mode_key = CONST_ADD_MODE_CLOUD if self._mode == CONST_ADD_MODE_CLOUD else CONST_ADD_MODE_LOCAL
        return f"EcoMain {ecomain_serial} ({mode_key.title()})"

    def _normalize_slaves(self, slaves: Optional[list[str]]) -> list[int]:
        if not slaves:
            return []
        allowed = set(self._ecomain_available_slaves)
        return sorted({int(s) for s in slaves if s in allowed})

    def _get_slave_index(self, slave: dict[str, Any]) -> Optional[int]:
        hardware_number = str(slave.get("hardware_number") or "")
        suffix = hardware_number.rsplit("_", maxsplit=1)[-1] if hardware_number else ""
        if suffix.isdigit():
            return int(suffix)
        return None
