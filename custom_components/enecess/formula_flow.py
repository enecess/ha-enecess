"""Shared formula configuration steps for initial and options flows."""

from typing import Any

from homeassistant.helpers import selector
from homeassistant.helpers.selector import SelectSelectorMode
import voluptuous as vol

from .const import CONST_EXTRA_ENTITY_NAME
from .extra import build_entry_descriptions, make_extra_key
from .flow_navigation import navigable_step
from .formula import (
    FORMULA_RESULT_TYPES,
    FormulaError,
    build_formula_variables,
    validate_formula,
)

RESULT_TYPE = "extra_formula_result_type"
EXPRESSION = "extra_formula_expression"
EDIT_ENTITY = "extra_formula_entity"
SOURCE_PREFIX = "extra_formula_sources_"
SOURCE_KINDS = (
    *[kind for kind in FORMULA_RESULT_TYPES if kind != "number"],
    "energy_delta",
)


class FormulaFlowMixin:
    """Host flows provide _formula_context and _async_formula_done."""

    def _reset_formula(self) -> None:
        self._formula_edit_key = None
        self._formula_draft = None

    def _formula_source_groups(self) -> dict[str, dict[str, str]]:
        """Group enabled, supported measurements independently of result type."""
        data, options = self._formula_context
        groups = {kind: {} for kind in SOURCE_KINDS}
        for desc in build_entry_descriptions(data, options):
            kind = desc.spec.kind
            if kind == "energy_accumulated":
                kind = "energy"
            if kind in groups:
                groups[kind][desc.key] = (
                    f"{desc.name or desc.key} ({desc.native_unit_of_measurement or '—'})"
                )
        return {kind: sources for kind, sources in groups.items() if sources}

    def _formula_result_types(self) -> list[str]:
        """Offer available result types and preserve the locked type during edits."""
        data, options = self._formula_context
        available = {
            desc.device_class for desc in build_entry_descriptions(data, options)
        }
        if available:
            available.add("number")
        editing = getattr(self, "_formula_edit_key", None)
        if editing:
            available.update(
                extra.get("result_type")
                for extra in self._extra_entities
                if extra.get("key") == editing and extra.get("operation") == "formula"
            )
        return [kind for kind in FORMULA_RESULT_TYPES if kind in available]

    def _formula_draft_error(self, draft: dict[str, Any]) -> str | None:
        if not draft.get("name", "").strip():
            return "formula_name_required"
        if draft.get("result_type") not in self._formula_result_types():
            return "formula_sources_invalid"
        editing = getattr(self, "_formula_edit_key", None)
        if editing:
            existing = next(
                (
                    extra
                    for extra in self._extra_entities
                    if extra.get("key") == editing
                ),
                None,
            )
            if existing is None:
                return "no_formula_entities"
            if existing.get("result_type") != draft["result_type"]:
                return "formula_result_type_locked"
        return None

    @navigable_step
    async def async_step_extra_formula(self, user_input=None):
        """Choose result metadata before selecting source measurements."""
        draft = getattr(self, "_formula_draft", None) or {}
        result_types = self._formula_result_types()
        errors = {}
        if user_input is not None:
            proposed = {
                **draft,
                "name": user_input.get(CONST_EXTRA_ENTITY_NAME),
                "result_type": user_input.get(RESULT_TYPE),
            }
            error = self._formula_draft_error(proposed)
            if error:
                errors["base"] = error
                draft = proposed
            else:
                if proposed["result_type"] != draft.get("result_type"):
                    proposed = {
                        "name": proposed["name"],
                        "result_type": proposed["result_type"],
                    }
                    self._discard_forward_drafts()
                self._formula_draft = {
                    **proposed,
                    "name": proposed["name"].strip(),
                }
                return await self.async_step_extra_formula_sources()
        return self.async_show_form(
            step_id="extra_formula",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONST_EXTRA_ENTITY_NAME, default=draft.get("name") or ""
                    ): str,
                    vol.Required(
                        RESULT_TYPE,
                        default=draft["result_type"]
                        if draft.get("result_type") in result_types
                        else next(iter(result_types), vol.UNDEFINED),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=result_types,
                            translation_key=RESULT_TYPE,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors
            or ({} if result_types else {"base": "formula_sources_invalid"}),
        )

    @navigable_step
    async def async_step_extra_formula_sources(self, user_input=None):
        """Select sources using a multi-select dropdown for each measurement kind."""
        draft = getattr(self, "_formula_draft", None)
        if not draft:
            return await self.async_step_extra_formula()
        groups = self._formula_source_groups()
        errors = {}
        if user_input is not None:
            sources = [
                source
                for kind in groups
                for source in (user_input.get(SOURCE_PREFIX + kind) or [])
            ]
            if not sources or any(
                source not in available
                for kind, available in groups.items()
                for source in (user_input.get(SOURCE_PREFIX + kind) or [])
            ):
                errors["base"] = "formula_sources_invalid"
            else:
                sources = list(dict.fromkeys(sources))
                self._formula_draft = {
                    **draft,
                    "sources": sources,
                    "variables": build_formula_variables(sources),
                    "expression": "",
                }
                # Navigation also remembers unsaved text; discard it before rebinding.
                self._discard_forward_drafts()
                return await self.async_step_extra_formula_expression()
        return self.async_show_form(
            step_id="extra_formula_sources",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        SOURCE_PREFIX + kind,
                        default=[
                            source
                            for source in (draft.get("sources") or [])
                            if source in available
                        ],
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": key, "label": label}
                                for key, label in available.items()
                            ],
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                    for kind, available in groups.items()
                }
            ),
            errors=errors or ({} if groups else {"base": "formula_sources_invalid"}),
        )

    @navigable_step
    async def async_step_extra_formula_expression(self, user_input=None):
        """Validate the arithmetic expression and save the formula draft."""
        draft = getattr(self, "_formula_draft", None)
        if not draft:
            return await self.async_step_extra_formula()
        errors = {}
        expression = draft.get("expression", "")
        if user_input is not None:
            expression = user_input.get(EXPRESSION, "")
            try:
                validated = validate_formula(expression, draft["variables"])
            except FormulaError:
                errors["base"] = "formula_invalid"
            else:
                variables = {
                    alias: source
                    for alias, source in draft["variables"].items()
                    if alias in validated.referenced_variables
                }
                sources = list(dict.fromkeys(variables.values()))
                editing = getattr(self, "_formula_edit_key", None)
                extra = {
                    "key": editing
                    or make_extra_key("formula", sources, self._extra_entities),
                    "name": draft["name"],
                    "operation": "formula",
                    "sources": sources,
                    "variables": variables,
                    "expression": expression.strip(),
                    "result_type": draft["result_type"],
                    "device_index": 0,
                }
                if editing:
                    self._extra_entities = [
                        extra if item.get("key") == editing else item
                        for item in self._extra_entities
                    ]
                else:
                    self._extra_entities.append(extra)
                self._reset_formula()
                return await self._async_formula_done()
        available = {
            key: label
            for group in self._formula_source_groups().values()
            for key, label in group.items()
        }
        return self.async_show_form(
            step_id="extra_formula_expression",
            data_schema=vol.Schema(
                {
                    vol.Required(EXPRESSION, default=expression): selector.TextSelector(
                        selector.TextSelectorConfig(multiline=True)
                    )
                }
            ),
            description_placeholders={
                "variables": "\n".join(
                    f"{alias} = {available.get(source, source)}"
                    for alias, source in draft["variables"].items()
                )
            },
            errors=errors,
        )

    @navigable_step
    async def async_step_extra_formula_edit(self, user_input=None):
        """Select an existing formula and load its draft for editing."""
        formulas = {
            extra["key"]: extra
            for extra in self._extra_entities
            if extra.get("operation") == "formula"
        }
        errors = {}
        if user_input is not None:
            key = user_input.get(EDIT_ENTITY)
            if key in formulas:
                self._formula_edit_key = key
                self._formula_draft = dict(formulas[key])
                return await self.async_step_extra_formula()
            errors["base"] = "no_formula_entities"
        return self.async_show_form(
            step_id="extra_formula_edit",
            data_schema=vol.Schema(
                {
                    vol.Required(EDIT_ENTITY): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": key, "label": extra.get("name") or key}
                                for key, extra in formulas.items()
                            ],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            errors=errors or ({} if formulas else {"base": "no_formula_entities"}),
        )
