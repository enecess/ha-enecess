"""Commission local ecoMain channels and master-owned solar settings."""

from decimal import Decimal

from homeassistant.data_entry_flow import section
from homeassistant.helpers import selector
from pymodbus.exceptions import ModbusException
import voluptuous as vol

from .const import (
    CONF_ECOMAIN_FIRMWARE_VERSION_REGISTER,
    CONF_ECOMAIN_SOLAR_CAPACITY_MAX,
    CONF_ECOMAIN_SOLAR_FIRMWARE_VERSION,
    CONST_ADD_MODE,
    CONST_ADD_MODE_LOCAL,
    CONST_ADD_MODE_LOCAL_AUTO,
    CONST_ADD_MODE_LOCAL_MANUAL,
)
from .ecomain.settings import (
    ChannelSettings,
    SolarSettings,
    async_read_channel_settings,
    async_read_solar_settings,
    async_write_channel_settings,
    async_write_solar_settings,
)
from .extra import get_entry_slaves
from .flow_navigation import navigable_step


class SettingsFlowMixin:
    """Keep installation drafts independent from measurement and phase choices."""

    async def _async_settings_access(self):
        """Confirm current firmware through the entry's owned local client."""
        runtime = getattr(self._entry, "runtime_data", None)
        client = runtime.modbus_client if runtime is not None else None
        if client is None:
            return None, "settings_unavailable"
        try:
            response = await client.read_holding_registers(
                CONF_ECOMAIN_FIRMWARE_VERSION_REGISTER, 1
            )
        except (ModbusException, OSError, TimeoutError):
            return None, "settings_read_failed"
        self._firmware_version = response.registers[0]
        self._firmware_target = self._local_target
        if self._firmware_version < CONF_ECOMAIN_SOLAR_FIRMWARE_VERSION:
            return None, "settings_firmware_too_old"
        return client, None

    @navigable_step
    async def async_step_channel_device(self, user_input=None):
        """Offer selected online meters, excluding ecoSolarMonitor."""
        choices = [
            "0",
            *[
                str(index)
                for index in get_entry_slaves(self._entry.data, self._options)
                if index in (1, 2, 3) and str(index) in self._available_slaves
            ],
        ]
        if user_input is not None:
            device = int(user_input["channel_device"])
            if self._channel_device != device:
                self._channel_values = {}
            self._channel_device = device
            return await self.async_step_channel_configuration()
        return self.async_show_form(
            step_id="channel_device",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "channel_device", default="0"
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=choices,
                            translation_key="phase_device",
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
            errors={},
        )

    @navigable_step
    async def async_step_channel_configuration(self, user_input=None):
        """Render native channel sections and verify immediate hardware changes."""
        if self._entry.data.get(CONST_ADD_MODE) not in (
            CONST_ADD_MODE_LOCAL,
            CONST_ADD_MODE_LOCAL_AUTO,
            CONST_ADD_MODE_LOCAL_MANUAL,
        ):
            return self.async_abort(reason="settings_unavailable")
        if self._channel_device not in [
            0,
            *[
                index
                for index in get_entry_slaves(self._entry.data, self._options)
                if index in (1, 2, 3) and str(index) in self._available_slaves
            ],
        ]:
            return await self.async_step_channel_device()
        client, error = await self._async_settings_access()
        errors = {"base": error} if error else {}
        if not errors and user_input is not None and self._channel_values:
            self._channel_values = user_input
            write_errors = await async_write_channel_settings(
                client,
                self._channel_device,
                ChannelSettings(
                    phases={
                        f"channel_{n}": user_input[f"channel_{n}"]["phase"]
                        for n in range(1, 11)
                    },
                    transformers={
                        f"channel_{n}": user_input[f"channel_{n}"]["transformer"]
                        for n in range(1, 11)
                    },
                    main_transformers=user_input.get("main_transformers", {}),
                ),
            )
            for key, category in write_errors.items():
                if key.startswith("main_transformer_"):
                    group = "main_transformers"
                    detail = f"main_{key.rsplit('_', 1)[1]}"
                else:
                    group, detail = key.rsplit("_", 1)
                # A native section can display one parent error; prefer a write failure.
                if group not in errors or category == "write_failed":
                    errors[group] = f"settings_{detail}_{category}"
            if not errors:
                return await self._show_options_menu()
        elif not errors and not self._channel_values:
            try:
                current = await async_read_channel_settings(
                    client, self._channel_device
                )
            except (ModbusException, OSError, TimeoutError):
                errors["base"] = "settings_read_failed"
            else:
                self._channel_values = {
                    f"channel_{n}": {
                        "phase": current.phases[f"channel_{n}"],
                        "transformer": current.transformers[f"channel_{n}"],
                    }
                    for n in range(1, 11)
                }
                if self._channel_device == 0:
                    self._channel_values["main_transformers"] = (
                        current.main_transformers
                    )
        fields = {}
        for group, values in self._channel_values.items():
            controls = {}
            for key, value in values.items():
                choices = (
                    ["L1", "L2", "L3"]
                    if key == "phase"
                    else (["100"] if group == "main_transformers" else ["30", "100"])
                )
                marker = (
                    vol.Required(key, default=value)
                    if value in choices
                    else vol.Required(key)
                )
                controls[marker] = selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=choices,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        **(
                            {"translation_key": "current_transformer"}
                            if key != "phase"
                            else {}
                        ),
                    )
                )
            fields[vol.Required(group, default={})] = section(
                vol.Schema(controls), {"collapsed": True}
            )
        return self.async_show_form(
            step_id="channel_configuration",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={
                "device": "ecoMain"
                if self._channel_device == 0
                else f"ecoSub {self._channel_device}"
            },
        )

    @navigable_step
    async def async_step_solar_configuration(self, user_input=None):
        """Configure the current ecoMain and all detected online inverter groups."""
        if self._entry.data.get(CONST_ADD_MODE) not in (
            CONST_ADD_MODE_LOCAL,
            CONST_ADD_MODE_LOCAL_AUTO,
            CONST_ADD_MODE_LOCAL_MANUAL,
        ) or 4 not in get_entry_slaves(self._entry.data, self._options):
            return self.async_abort(reason="settings_unavailable")
        errors = {}
        if user_input is not None and self._solar_values:
            for field, minimum, maximum, scale in [
                ("capacity", 0, CONF_ECOMAIN_SOLAR_CAPACITY_MAX, 1),
                ("temperature_coefficient", -32.768, 32.767, 1000),
            ]:
                value = Decimal(str(user_input[field]))
                if (
                    type(self._navigation_inputs["solar_configuration"].get(field))
                    is bool
                    or not value.is_finite()
                    or not Decimal(str(minimum)) <= value <= Decimal(str(maximum))
                    or value * scale != (value * scale).to_integral_value()
                ):
                    errors[field] = "invalid_input"
                    if not value.is_finite():
                        self._navigation_inputs["solar_configuration"].pop(field, None)
        if not errors:
            client, error = await self._async_settings_access()
            if error:
                errors["base"] = error
            elif user_input is not None and self._solar_values:
                self._solar_values = user_input
                errors = {
                    key: f"settings_{category}"
                    for key, category in (
                        await async_write_solar_settings(
                            client,
                            SolarSettings(
                                capacity=int(user_input["capacity"]),
                                temperature_coefficient=user_input[
                                    "temperature_coefficient"
                                ],
                                inverter_channels={
                                    int(key.rsplit("_", 1)[1]): value
                                    for key, value in user_input.items()
                                    if key.startswith("inverter_channels_")
                                },
                            ),
                        )
                    ).items()
                }
                if not errors:
                    return await self._show_options_menu()
            elif not self._solar_values:
                try:
                    current = await async_read_solar_settings(
                        client,
                        [
                            0,
                            *[
                                index
                                for index in (1, 2, 3)
                                if str(index) in self._available_slaves
                            ],
                        ],
                    )
                except (ModbusException, OSError, TimeoutError):
                    errors["base"] = "settings_read_failed"
                else:
                    self._solar_values = {
                        "capacity": current.capacity,
                        "temperature_coefficient": current.temperature_coefficient,
                        **{
                            f"inverter_channels_{index}": channels
                            for index, channels in current.inverter_channels.items()
                        },
                    }
        fields = {}
        if self._solar_values:
            for key, minimum, maximum, step, unit in [
                ("capacity", 0, CONF_ECOMAIN_SOLAR_CAPACITY_MAX, 1, "W"),
                ("temperature_coefficient", -32.768, 32.767, 0.001, "%/°C"),
            ]:
                fields[vol.Required(key, default=self._solar_values[key])] = (
                    selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=minimum,
                            max=maximum,
                            step=step,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement=unit,
                        )
                    )
                )
            for key, value in self._solar_values.items():
                if key.startswith("inverter_channels_"):
                    fields[vol.Required(key, default=value)] = selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[str(n) for n in range(1, 11)],
                            multiple=True,
                            translation_key="inverter_channels",
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    )
        return self.async_show_form(
            step_id="solar_configuration", data_schema=vol.Schema(fields), errors=errors
        )
