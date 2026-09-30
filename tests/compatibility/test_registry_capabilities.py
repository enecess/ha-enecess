"""Keep real HA registry settings when selected measurements become unsupported."""

from homeassistant.helpers import entity_registry

from custom_components.enecess.config_flow import ConfigFlow
from custom_components.enecess.registry import async_remove_unconfigured_registry_entries
from test_runtime import RealHARuntimeFixture, SERIAL


class RegistryCapabilitiesTests(RealHARuntimeFixture):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.entry = self.make_entry("local")
        self.hass.config_entries.async_update_entry(
            self.entry,
            options={"measurement_types": ["power", "voltage"],
                     "ecomain_selected_slaves": [], "extra_entities": []},
        )
        self.registry = entity_registry.async_get(self.hass)
        registered = self.registry.async_get_or_create(
            "sensor", "enecess",
            f"ecomain:{SERIAL}:key_main_l1_voltage_rt:mode_local",
            config_entry=self.entry,
            suggested_object_id="my_existing_voltage",
        )
        self.record = self.registry.async_update_entity(
            registered.entity_id, name="My retained voltage",
            disabled_by=entity_registry.RegistryEntryDisabler.USER,
        )

    async def test_downgrade_and_upgrade_keep_registry_id_name_and_disabled_choice(self):
        for version in (138, 139):
            self.hass.config_entries.async_update_entry(
                self.entry, data={**self.entry.data, "ecomain_firmware_version": version}
            )
            async_remove_unconfigured_registry_entries(self.hass, self.entry)
            current = self.registry.async_get(self.record.entity_id)
            self.assertIsNotNone(current)
            self.assertEqual(current.id, self.record.id)
            self.assertEqual(current.name, "My retained voltage")
            self.assertEqual(current.disabled_by, entity_registry.RegistryEntryDisabler.USER)
        self.hass.config_entries.async_update_entry(
            self.entry, options={**self.entry.options, "measurement_types": ["power"]}
        )
        async_remove_unconfigured_registry_entries(self.hass, self.entry)
        self.assertIsNone(self.registry.async_get(self.record.entity_id))

    async def test_offline_displayed_options_save_keeps_real_registry_and_selections(self):
        self.mocks["read_holding_registers"].side_effect = ConnectionError("offline fixture")
        flow = ConfigFlow.async_get_options_flow(self.entry)
        flow.hass = self.hass
        flow.handler = self.entry.entry_id
        flow.context = {}
        result = await flow.async_step_init()
        self.assertEqual(result["errors"], {"base": "cannot_connect_local"})
        result = await flow.async_step_init(
            result["data_schema"]({"extra_action": "measurement_types"})
        )
        self.assertEqual(result["data_schema"]({})["measurement_types"], ["power", "voltage"])
        result = await getattr(flow, "async_step_" + result["step_id"])(
            result["data_schema"]({"flow_action": "save"})
        )
        result = await flow.async_step_init(result["data_schema"]({"extra_action": "finish"}))
        self.assertEqual(result["data"]["measurement_types"], ["power", "voltage"])
        self.assertEqual(self.registry.async_get(self.record.entity_id).id, self.record.id)
