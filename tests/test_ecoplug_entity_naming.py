from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "custom_components/enecess/ecoplug/model.py"


def load_model():
    name = "enecess_ecoplug_model_test"
    spec = spec_from_file_location(name, MODEL_PATH)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _package(name: str, path: Path) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    sys.modules[name] = module
    return module


def _module(name: str) -> types.ModuleType:
    module = types.ModuleType(name)
    sys.modules[name] = module
    return module


def _load_module(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_ecoplug_runtime():
    for name in tuple(sys.modules):
        if name == "custom_components" or name.startswith(
            ("custom_components.enecess", "homeassistant")
        ):
            sys.modules.pop(name)

    aiohttp = _module("aiohttp")

    class ClientError(Exception):
        pass

    aiohttp.ClientError = ClientError

    homeassistant = _package("homeassistant", ROOT)
    components = _package("homeassistant.components", ROOT)
    helpers = _package("homeassistant.helpers", ROOT)
    homeassistant.components = components
    homeassistant.helpers = helpers

    sensor = _module("homeassistant.components.sensor")

    class SensorDeviceClass:
        POWER = "power"
        ENERGY = "energy"

    class SensorStateClass:
        MEASUREMENT = "measurement"
        TOTAL_INCREASING = "total_increasing"

    class SensorEntity:
        pass

    class SensorEntityDescription:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    sensor.SensorDeviceClass = SensorDeviceClass
    sensor.SensorStateClass = SensorStateClass
    sensor.SensorEntity = SensorEntity
    sensor.SensorEntityDescription = SensorEntityDescription

    const = _module("homeassistant.const")

    class UnitOfPower:
        WATT = "W"

    class UnitOfEnergy:
        KILO_WATT_HOUR = "kWh"

    const.UnitOfPower = UnitOfPower
    const.UnitOfEnergy = UnitOfEnergy

    config_entries = _module("homeassistant.config_entries")

    class ConfigEntry:
        pass

    config_entries.ConfigEntry = ConfigEntry

    core = _module("homeassistant.core")

    class HomeAssistant:
        pass

    core.HomeAssistant = HomeAssistant

    device_registry = _module("homeassistant.helpers.device_registry")

    class DeviceInfo:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    device_registry.DeviceInfo = DeviceInfo

    entity_platform = _module("homeassistant.helpers.entity_platform")

    class AddEntitiesCallback:
        pass

    entity_platform.AddEntitiesCallback = AddEntitiesCallback

    update_coordinator = _module("homeassistant.helpers.update_coordinator")

    class CoordinatorEntity:
        def __init__(self, coordinator):
            self.coordinator = coordinator

    class DataUpdateCoordinator:
        @classmethod
        def __class_getitem__(cls, _item):
            return cls

    class UpdateFailed(Exception):
        pass

    update_coordinator.CoordinatorEntity = CoordinatorEntity
    update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
    update_coordinator.UpdateFailed = UpdateFailed

    custom_components = _package("custom_components", ROOT / "custom_components")
    enecess = _package(
        "custom_components.enecess",
        ROOT / "custom_components/enecess",
    )
    ecoplug = _package(
        "custom_components.enecess.ecoplug",
        ROOT / "custom_components/enecess/ecoplug",
    )
    custom_components.enecess = enecess
    enecess.ecoplug = ecoplug

    client_api = _module("custom_components.enecess.client_api")

    class EnecessApi:
        pass

    class EnecessApiError(Exception):
        pass

    class EnecessAuthError(Exception):
        pass

    client_api.EnecessApi = EnecessApi
    client_api.EnecessApiError = EnecessApiError
    client_api.EnecessAuthError = EnecessAuthError

    _load_module(
        "custom_components.enecess.const",
        ROOT / "custom_components/enecess/const.py",
    )
    model = _load_module(
        "custom_components.enecess.ecoplug.model",
        ROOT / "custom_components/enecess/ecoplug/model.py",
    )
    sensor_module = _load_module(
        "custom_components.enecess.ecoplug.sensor",
        ROOT / "custom_components/enecess/ecoplug/sensor.py",
    )
    coordinator_module = _load_module(
        "custom_components.enecess.ecoplug.coordinator",
        ROOT / "custom_components/enecess/ecoplug/coordinator.py",
    )
    return coordinator_module, model, sensor_module


def load_registry_runtime(unique_ids, *, other_entry_unique_ids=()):
    for name in tuple(sys.modules):
        if name == "custom_components" or name.startswith(
            ("custom_components.enecess", "homeassistant")
        ):
            sys.modules.pop(name)

    homeassistant = _package("homeassistant", ROOT)
    helpers = _package("homeassistant.helpers", ROOT)
    homeassistant.helpers = helpers

    const = _module("homeassistant.const")

    class Platform:
        SENSOR = "sensor"
        SWITCH = "switch"

    const.Platform = Platform

    config_entries = _module("homeassistant.config_entries")

    class ConfigEntry:
        pass

    config_entries.ConfigEntry = ConfigEntry

    core = _module("homeassistant.core")

    class HomeAssistant:
        pass

    core.HomeAssistant = HomeAssistant

    old_entity_ids = {
        "ecoplug:TEST-ECOPLUG-0001:power:mode_cloud": "sensor.old_power",
        "ecoplug:TEST-ECOPLUG-0001:total_energy:mode_cloud": (
            "sensor.old_energy"
        ),
        "ecoplug:TEST-ECOPLUG-0002:power:mode_cloud": (
            "sensor.other_entry_old_power"
        ),
    }

    class FakeEntityRegistry:
        def __init__(self):
            entry_specs = [
                ("entry-1", unique_id) for unique_id in unique_ids
            ] + [
                ("entry-2", unique_id)
                for unique_id in other_entry_unique_ids
            ]
            self.entries = [
                types.SimpleNamespace(
                    config_entry_id=config_entry_id,
                    domain=(
                        Platform.SWITCH
                        if ":switch:" in unique_id
                        else Platform.SENSOR
                    ),
                    entity_id=old_entity_ids.get(
                        unique_id,
                        f"sensor.configured_{index}",
                    ),
                    unique_id=unique_id,
                )
                for index, (config_entry_id, unique_id) in enumerate(
                    entry_specs
                )
            ]
            self.removed = []

        def async_remove(self, entity_id):
            self.removed.append(entity_id)
            self.entries = [
                entry for entry in self.entries if entry.entity_id != entity_id
            ]

    entity_registry = _module("homeassistant.helpers.entity_registry")
    test_entity_registry = FakeEntityRegistry()
    entity_registry.async_get = lambda _hass: test_entity_registry
    entity_registry.async_entries_for_config_entry = (
        lambda registry, entry_id: [
            entry
            for entry in registry.entries
            if entry.config_entry_id == entry_id
        ]
    )

    class FakeDeviceRegistry:
        entries = []

        def async_remove_device(self, _device_id):
            raise AssertionError("No device registry entry should be removed")

    device_registry = _module("homeassistant.helpers.device_registry")
    test_device_registry = FakeDeviceRegistry()
    device_registry.async_get = lambda _hass: test_device_registry
    device_registry.async_entries_for_config_entry = (
        lambda registry, entry_id: [
            entry
            for entry in registry.entries
            if entry_id in entry.config_entries
        ]
    )

    custom_components = _package("custom_components", ROOT / "custom_components")
    enecess = _package(
        "custom_components.enecess",
        ROOT / "custom_components/enecess",
    )
    ecoplug = _package(
        "custom_components.enecess.ecoplug",
        ROOT / "custom_components/enecess/ecoplug",
    )
    custom_components.enecess = enecess
    enecess.ecoplug = ecoplug

    extra = _module("custom_components.enecess.extra")
    extra.build_entry_sensor_unique_ids = lambda _data, _options: set()
    extra.build_entry_device_identifiers = lambda _data, _options: set()

    _load_module(
        "custom_components.enecess.const",
        ROOT / "custom_components/enecess/const.py",
    )
    _load_module(
        "custom_components.enecess.ecoplug.model",
        ROOT / "custom_components/enecess/ecoplug/model.py",
    )
    registry_module = _load_module(
        "custom_components.enecess.registry",
        ROOT / "custom_components/enecess/registry.py",
    )
    registry_module.TEST_HASS = HomeAssistant()
    registry_module.TEST_ENTRY = types.SimpleNamespace(
        entry_id="entry-1",
        data={
            "device_type": "ecoplug",
            "ecoplug_devices": [
                {"hardware_number": "TEST-ECOPLUG-0001"}
            ],
        },
        options={},
    )
    registry_module.TEST_ENTITY_REGISTRY = test_entity_registry
    return registry_module


class FakeCoordinator:
    def __init__(self, data):
        self.data = data
        self.last_update_success = True


class EcoPlugModelNamingTests(unittest.TestCase):
    def test_snapshot_uses_unified_measurement_fields(self):
        model = load_model()
        snapshot = model.EcoPlugSnapshot(power_rt=123.4, energy_total=56.7)
        self.assertEqual(123.4, snapshot.power_rt)
        self.assertEqual(56.7, snapshot.energy_total)
        self.assertFalse(hasattr(snapshot, "power"))
        self.assertFalse(hasattr(snapshot, "total_energy"))

    def test_cloud_payload_keeps_api_names_at_parse_boundary(self):
        model = load_model()
        payload = {
            "data": [
                {
                    "time": "2026-07-29T08:00:00Z",
                    "power": "123.4",
                    "total_energy": "56.7",
                }
            ]
        }
        self.assertEqual((123.4, 56.7), model.parse_latest_plug_data(payload))

    def test_sensor_unique_ids_follow_ecomain_key_format(self):
        model = load_model()
        serial = "TEST-ECOPLUG-0001"
        self.assertEqual(
            "ecoplug:TEST-ECOPLUG-0001:key_power_rt:mode_cloud",
            model.sensor_unique_id(serial, "power_rt"),
        )
        self.assertEqual(
            "ecoplug:TEST-ECOPLUG-0001:key_energy_total:mode_cloud",
            model.sensor_unique_id(serial, "energy_total"),
        )

    def test_switch_unique_id_is_unchanged(self):
        model = load_model()
        self.assertEqual(
            "ecoplug:TEST-ECOPLUG-0001:switch:mode_cloud",
            model.switch_unique_id("TEST-ECOPLUG-0001"),
        )


class EcoPlugRuntimeNamingTests(unittest.TestCase):
    def test_coordinator_builds_snapshot_with_unified_fields(self):
        coordinator_module, model, _sensor_module = load_ecoplug_runtime()
        coordinator = object.__new__(coordinator_module.EcoPlugCloudCoordinator)
        plug = model.EcoPlugConfig(
            hardware_number="TEST-ECOPLUG-0001",
            name="Test Plug",
        )
        snapshot = coordinator._build_snapshot(
            plug,
            {
                "data": [
                    {
                        "time": "2026-07-29T08:00:00Z",
                        "power": 123.4,
                        "total_energy": 56.7,
                    }
                ]
            },
            {"response": {"data": {"p": [{"id": 106, "val": 1}]}}},
        )
        self.assertEqual(123.4, snapshot.power_rt)
        self.assertEqual(56.7, snapshot.energy_total)
        self.assertTrue(snapshot.is_on)

    def test_sensor_descriptions_and_values_use_unified_names(self):
        _coordinator_module, model, sensor_module = load_ecoplug_runtime()
        descriptions = {item.key: item for item in sensor_module.SENSOR_DESCRIPTIONS}
        self.assertEqual({"power_rt", "energy_total"}, set(descriptions))
        self.assertEqual("power_rt", descriptions["power_rt"].name)
        self.assertEqual("energy_total", descriptions["energy_total"].name)

        coordinator = FakeCoordinator(
            {
                "TEST-ECOPLUG-0001": model.EcoPlugSnapshot(
                    power_rt=123.4,
                    energy_total=56.7,
                )
            }
        )
        plug = model.EcoPlugConfig("TEST-ECOPLUG-0001", "Test Plug")
        power = sensor_module.EcoPlugSensor(
            coordinator,
            plug,
            descriptions["power_rt"],
        )
        energy = sensor_module.EcoPlugSensor(
            coordinator,
            plug,
            descriptions["energy_total"],
        )
        self.assertEqual(123.4, power.native_value)
        self.assertEqual(56.7, energy.native_value)
        self.assertTrue(power.available)
        self.assertTrue(energy.available)
        self.assertEqual(
            "ecoplug:TEST-ECOPLUG-0001:key_power_rt:mode_cloud",
            power.unique_id,
        )
        self.assertEqual(
            "ecoplug:TEST-ECOPLUG-0001:key_energy_total:mode_cloud",
            energy.unique_id,
        )


class EcoPlugRegistryNamingTests(unittest.TestCase):
    def test_registry_keeps_new_sensor_ids_and_switch_id(self):
        registry_module = load_registry_runtime(
            unique_ids=[
                "ecoplug:TEST-ECOPLUG-0001:key_power_rt:mode_cloud",
                "ecoplug:TEST-ECOPLUG-0001:key_energy_total:mode_cloud",
                "ecoplug:TEST-ECOPLUG-0001:switch:mode_cloud",
            ]
        )
        registry_module.async_remove_unconfigured_registry_entries(
            registry_module.TEST_HASS,
            registry_module.TEST_ENTRY,
        )
        self.assertEqual(
            [
                "ecoplug:TEST-ECOPLUG-0001:key_power_rt:mode_cloud",
                "ecoplug:TEST-ECOPLUG-0001:key_energy_total:mode_cloud",
                "ecoplug:TEST-ECOPLUG-0001:switch:mode_cloud",
            ],
            [
                entry.unique_id
                for entry in registry_module.TEST_ENTITY_REGISTRY.entries
            ],
        )

    def test_registry_removes_old_ids_only_from_target_config_entry(self):
        registry_module = load_registry_runtime(
            unique_ids=[
                "ecoplug:TEST-ECOPLUG-0001:power:mode_cloud",
                "ecoplug:TEST-ECOPLUG-0001:total_energy:mode_cloud",
            ],
            other_entry_unique_ids=[
                "ecoplug:TEST-ECOPLUG-0002:power:mode_cloud",
            ],
        )
        registry_module.async_remove_unconfigured_registry_entries(
            registry_module.TEST_HASS,
            registry_module.TEST_ENTRY,
        )
        self.assertEqual(
            ["ecoplug:TEST-ECOPLUG-0002:power:mode_cloud"],
            [
                entry.unique_id
                for entry in registry_module.TEST_ENTITY_REGISTRY.entries
            ],
        )
