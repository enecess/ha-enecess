"""Navigation and draft handling shared by configuration and options flows."""

from copy import deepcopy
from functools import wraps

from homeassistant.helpers import selector
from homeassistant.helpers.selector import SelectSelectorMode
import voluptuous as vol

from .const import CONST_EXTRA_ACTION

FLOW_ACTION = "flow_action"
MENU_STEPS = {"user", "init", "extra_entities"}
CANCEL_MENUS = {"init", "extra_entities"}
SAVE_STEPS = {
    "extra_formula_expression",
    "extra_transform",
    "extra_aggregate",
    "measurement_types",
    "measurement_types_local",
    "measurement_types_legacy",
    "channel_phases",
    "ecoplug_select",
}
BRANCH_STEPS = {
    "user",
    "ecomain_mode",
    "ecomain_auto_scan",
    "ecomain_manual",
    "ecomain_cloud_login",
    "ecoplug_cloud_login",
    "ecomain_cloud_master",
    "phase_device",
    "extra_formula_edit",
    "extra_aggregate_kind",
}
STATE_FIELDS = (
    "_device_type",
    "_mode",
    "_discovered",
    "_cloud_token",
    "_cloud_username",
    "_cloud_password",
    "_ecomain_local_config",
    "_ecomain_cloud_config",
    "_ecoplug_devices",
    "_entry_data",
    "_measurement_types",
    "_options",
    "_extra_entities",
    "_firmware_version",
    "_available_slaves",
    "_phase_device",
    "_phase_values",
    "_cloud_slave_map",
    "_formula_edit_key",
    "_formula_draft",
)


def navigable_step(handler):
    """Handle navigation before validation, network requests or state changes."""

    @wraps(handler)
    async def wrapped(self, user_input=None):
        if getattr(self, "_navigation_depth", 0):
            return await handler(self, user_input)
        self._navigation_init()
        self._navigation_depth = 1
        try:
            step = handler.__name__.removeprefix("async_step_")
            rollback = None
            if user_input is not None:
                values = {
                    key: value
                    for key, value in user_input.items()
                    if key != FLOW_ACTION
                }
                action = user_input.get(FLOW_ACTION, "continue")
                if step in CANCEL_MENUS and values.get(CONST_EXTRA_ACTION) in (
                    "back",
                    "cancel",
                ):
                    action = values.pop(CONST_EXTRA_ACTION)
                old_values = self._navigation_inputs.get(step, {})
                if action in ("back", "cancel"):
                    self._navigation_inputs[step] = {**old_values, **deepcopy(values)}
                    return await self._async_navigate(action)
                self._navigation_inputs[step] = deepcopy(values)
                form = self._navigation_forms.get(step)
                if form is not None and self._navigation_history[-1:] == [step]:
                    try:
                        values = form["data_schema"](values)
                    except vol.Invalid as error:
                        field = str(error.path[0]) if error.path else "base"
                        return self.async_show_form(
                            **{**form, "errors": {field: "invalid_input"}}
                        )
                previous_choice = self._navigation_choices.get(step)
                if (
                    step in BRANCH_STEPS
                    and previous_choice is not None
                    and values != previous_choice
                ):
                    rollback = (
                        self._navigation_snapshot(),
                        {
                            name: dict(getattr(self, name))
                            for name in (
                                "_navigation_forms",
                                "_navigation_states",
                                "_navigation_inputs",
                                "_navigation_choices",
                            )
                        },
                    )
                    self._discard_forward_drafts()
                    if self._navigation_root == "user" and step in {
                        "user",
                        "ecomain_mode",
                        "ecomain_auto_scan",
                        "ecomain_manual",
                        "ecomain_cloud_login",
                        "ecoplug_cloud_login",
                        "ecomain_cloud_master",
                    }:
                        self._entry_data = {}
                        self._extra_entities = []
                        self._measurement_types = None
                if step in BRANCH_STEPS:
                    self._navigation_choices[step] = deepcopy(values)
                user_input = values
            result = await handler(self, user_input)
            if (
                rollback is not None
                and result.get("step_id") == step
                and result.get("errors")
            ):
                # A rejected change must not erase completed work from the old branch.
                current_form = self._navigation_forms.get(step)
                self._navigation_restore(rollback[0])
                for name, saved in rollback[1].items():
                    setattr(self, name, saved)
                if current_form is not None:
                    self._navigation_forms[step] = current_form
            return result
        finally:
            self._navigation_depth = 0

    return wrapped


class FlowNavigationMixin:
    """Keep only wizard data in snapshots; never copy clients or HA objects."""

    _navigation_root = "user"

    def _navigation_init(self):
        if not hasattr(self, "_navigation_history"):
            self._navigation_history = []
            self._navigation_forms = {}
            self._navigation_states = {}
            self._navigation_inputs = {}
            self._navigation_choices = {}

    def _navigation_snapshot(self):
        return {
            name: deepcopy(self.__dict__[name])
            for name in STATE_FIELDS
            if name in self.__dict__
        }

    def _navigation_restore(self, state, *, preserve_completed=False):
        retained = {}
        if preserve_completed:
            retained = {
                name: deepcopy(self.__dict__[name])
                for name in (
                    "_entry_data",
                    "_options",
                    "_extra_entities",
                    "_measurement_types",
                    "_formula_draft",
                    "_formula_edit_key",
                )
                if name in self.__dict__
            }
        for name in STATE_FIELDS:
            if name in state:
                setattr(self, name, deepcopy(state[name]))
            elif name in self.__dict__:
                delattr(self, name)
        for name, value in retained.items():
            setattr(self, name, value)

    def _discard_forward_drafts(self):
        active = set(self._navigation_history)
        for step in list(self._navigation_forms):
            if step not in active:
                self._navigation_forms.pop(step, None)
                self._navigation_states.pop(step, None)
                self._navigation_inputs.pop(step, None)
                self._navigation_choices.pop(step, None)

    def async_show_form(self, **kwargs):
        """Save the current step and render its navigation controls."""
        self._navigation_init()
        step = kwargs["step_id"]
        if step in self._navigation_history:
            index = self._navigation_history.index(step)
            self._navigation_history = self._navigation_history[: index + 1]
        else:
            self._navigation_history.append(step)
        if step in MENU_STEPS:
            self._discard_forward_drafts()
            self._navigation_inputs.pop(step, None)
        self._navigation_forms[step] = dict(kwargs)
        self._navigation_states[step] = self._navigation_snapshot()
        return self._render_navigation_form(kwargs)

    def _render_navigation_form(self, form):
        step = form["step_id"]
        if hasattr(self, "context"):
            self.context.pop("confirm_only", None)
        if step == "ecomain_local_confirm" and hasattr(
            self, "_navigation_discovery_state"
        ):
            return super().async_show_form(**form)
        fields = {}
        values = self._navigation_inputs.get(step, {})
        for key, validator in form["data_schema"].schema.items():
            name = str(key)
            default = vol.UNDEFINED
            if isinstance(key, vol.Marker) and key.default is not vol.UNDEFINED:
                default = key.default()
            candidate = values.get(name, default)
            if candidate is not vol.UNDEFINED:
                try:
                    default = vol.Schema(validator)(candidate)
                except vol.Invalid:
                    default = vol.UNDEFINED
            # Required fields are checked on Continue, so empty forms can go Back.
            marker = (
                vol.Required
                if step == "user" and isinstance(key, vol.Required)
                else vol.Optional
            )
            fields[
                marker(
                    name, default=default, description=getattr(key, "description", None)
                )
            ] = validator
        if step == "user":
            return super().async_show_form(
                **{**form, "data_schema": vol.Schema(fields)}
            )
        action = "save" if step in SAVE_STEPS else "continue"
        actions = [action]
        if (
            len(self._navigation_history) > 1
            and step not in {"init", self._navigation_root}
            and not (self._navigation_root == "init" and step == "ecoplug_select")
        ):
            actions.append("back")
        actions.append("cancel")
        if step in CANCEL_MENUS:
            for key, validator in fields.items():
                if str(key) == CONST_EXTRA_ACTION:
                    fields[key] = selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            **{
                                **validator.config,
                                "options": [*validator.config["options"], *actions[1:]],
                            }
                        )
                    )
                    return super().async_show_form(
                        **{**form, "data_schema": vol.Schema(fields)}
                    )
        fields[vol.Required(FLOW_ACTION, default=action)] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=actions,
                translation_key=FLOW_ACTION,
                mode=SelectSelectorMode.LIST,
            )
        )
        return super().async_show_form(**{**form, "data_schema": vol.Schema(fields)})

    async def _async_navigate(self, action):
        history = self._navigation_history
        if action == "back" and len(history) > 1:
            target_index = len(history) - 2
        elif action == "cancel":
            target_index = next(
                (
                    index
                    for index in range(len(history) - 2, -1, -1)
                    if history[index] in CANCEL_MENUS
                ),
                None,
            )
        else:
            target_index = None
        if target_index is None:
            if action == "back" and history:
                return self._render_navigation_form(self._navigation_forms[history[-1]])
            self._reset_navigation_drafts()
            if hasattr(self, "_navigation_discovery_state"):
                # Keep the pending discovery flow and its device identity alive.
                self._navigation_restore(self._navigation_discovery_state)
                return await self.async_step_ecomain_local_confirm()
            return self.async_abort(reason="user_cancelled")
        target = history[target_index]
        self._navigation_restore(
            self._navigation_states[target], preserve_completed=action == "back"
        )
        self._navigation_history = history[: target_index + 1]
        if action == "cancel":
            self._discard_forward_drafts()
        return self._render_navigation_form(
            {**self._navigation_forms[target], "errors": {}}
        )

    def _reset_navigation_drafts(self):
        self._navigation_history.clear()
        self._navigation_forms.clear()
        self._navigation_states.clear()
        self._navigation_inputs.clear()
        self._navigation_choices.clear()
        if self._navigation_root == "user":
            self._navigation_restore(self._navigation_initial_state)
        if hasattr(self, "_reset_formula"):
            self._reset_formula()
