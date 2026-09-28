"""Small HA boundary doubles for offline config-flow behavior tests."""

from dataclasses import dataclass
import importlib
from pathlib import Path
import sys
import types
from unittest.mock import patch

import voluptuous as vol

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.superpowers/test-deps'))


def submit_values(result, values):
    """Select navigation from the action field actually displayed by the form."""
    values = dict(values)
    fields = {str(key) for key in result['data_schema'].schema}
    if 'flow_action' in values and 'flow_action' not in fields and 'extra_action' in fields:
        values['extra_action'] = values.pop('flow_action')
    return result['data_schema'](values)


def load_flow(test):
    saved = patch.dict(sys.modules)
    saved.start()
    test.addCleanup(saved.stop)
    for name in tuple(sys.modules):
        if name.startswith(('homeassistant', 'custom_components.enecess', 'aiohttp')):
            sys.modules.pop(name)

    def module(name, path=None, **attributes):
        item = types.ModuleType(name)
        if path is not None:
            item.__path__ = [str(path)]
        item.__dict__.update(attributes)
        sys.modules[name] = item
        return item

    module('custom_components', ROOT / 'custom_components')
    module('custom_components.enecess', ROOT / 'custom_components/enecess')
    module('homeassistant', ROOT)
    module('homeassistant.components', ROOT)
    module('homeassistant.helpers', ROOT)

    class Flow:
        def __init_subclass__(cls, **kwargs):
            pass

        def async_show_form(self, **kwargs):
            return {'type': 'form', **kwargs}

        def async_create_entry(self, **kwargs):
            return {'type': 'create_entry', **kwargs}

        def async_abort(self, **kwargs):
            return {'type': 'abort', **kwargs}

        def _async_current_entries(self):
            return []

        async def async_set_unique_id(self, unique_id, **kwargs):
            self.context['unique_id'] = unique_id
            return None

        def _set_confirm_only(self):
            self.context["confirm_only"] = True

    module('homeassistant.config_entries', ConfigFlow=Flow, OptionsFlow=Flow,
           ConfigEntry=types.SimpleNamespace)
    module('homeassistant.data_entry_flow', FlowResult=dict)
    module('homeassistant.core', HomeAssistant=object, callback=lambda f: f)
    module('homeassistant.components.zeroconf', ZeroconfServiceInfo=object)
    module('homeassistant.helpers.device_registry')
    module('homeassistant.helpers.entity_registry')
    module('homeassistant.helpers.aiohttp_client', async_get_clientsession=lambda h: None)

    class Selector:
        def __init__(self, config):
            self.config = config

        def __call__(self, value):
            options = self.config.get('options')
            if options is None:
                if not isinstance(value, str):
                    raise vol.Invalid('expected text')
                return value
            allowed = [item['value'] if isinstance(item, dict) else item for item in options]
            if self.config.get('multiple'):
                if not isinstance(value, list):
                    raise vol.Invalid('expected a list')
                values = value
            else:
                values = [value]
            if any(not isinstance(item, str) or item not in allowed for item in values):
                raise vol.Invalid('not an offered choice')
            return value

    module('homeassistant.helpers.selector', SelectSelector=Selector,
           SelectSelectorConfig=lambda **kwargs: kwargs,
           TextSelector=Selector, TextSelectorConfig=lambda **kwargs: kwargs,
           SelectSelectorMode=types.SimpleNamespace(LIST='list', DROPDOWN='dropdown'))

    @dataclass(frozen=True, kw_only=True)
    class Description:
        key: str
        name: str | None = None
        native_unit_of_measurement: str | None = None
        device_class: str | None = None
        state_class: str | None = None
        suggested_display_precision: int | None = None

    classes = types.SimpleNamespace(**{n: n.lower() for n in (
        'POWER', 'ENERGY', 'REACTIVE_ENERGY', 'APPARENT_POWER', 'REACTIVE_POWER',
        'VOLTAGE', 'CURRENT', 'POWER_FACTOR', 'FREQUENCY')})
    module('homeassistant.components.sensor', SensorDeviceClass=classes,
           SensorEntityDescription=Description,
           SensorStateClass=types.SimpleNamespace(MEASUREMENT='measurement', TOTAL_INCREASING='total_increasing', TOTAL='total'))
    module('homeassistant.const', Platform=types.SimpleNamespace(SENSOR='sensor', SWITCH='switch'),
           UnitOfEnergy=types.SimpleNamespace(WATT_HOUR='Wh', KILO_WATT_HOUR='kWh'),
           UnitOfPower=types.SimpleNamespace(WATT='W', VOLT_AMPERE='VA'),
           UnitOfApparentPower=types.SimpleNamespace(VOLT_AMPERE='VA'),
           UnitOfReactivePower=types.SimpleNamespace(VOLT_AMPERE_REACTIVE='var'),
           UnitOfReactiveEnergy=types.SimpleNamespace(VOLT_AMPERE_REACTIVE_HOUR='varh'),
           UnitOfElectricPotential=types.SimpleNamespace(VOLT='V'),
           UnitOfElectricCurrent=types.SimpleNamespace(AMPERE='A'),
           UnitOfFrequency=types.SimpleNamespace(HERTZ='Hz'), PERCENTAGE='%')
    module('custom_components.enecess.client_api', EnecessApi=object,
           EnecessAuthError=type('AuthError', (Exception,), {}),
           EnecessApiError=type('ApiError', (Exception,), {}))
    return importlib.import_module('custom_components.enecess.config_flow')
