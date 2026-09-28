"""Cloud authentication regressions using real Home Assistant contracts."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.enecess.client_api import (
    EnecessApi,
    EnecessApiError,
    EnecessAuthError,
)
from custom_components.enecess.config_flow import ConfigFlow
from custom_components.enecess.ecomain.coordinator import EcoMainCloudCoordinator
from custom_components.enecess.ecoplug.coordinator import EcoPlugCloudCoordinator
from custom_components.enecess import const as c
import test_runtime as runtime


class CloudAuthTests(runtime.RealHARuntimeFixture):
    async def test_unexpected_cloud_bug_is_not_disguised_as_request_failure(self):
        for cls in (EcoMainCloudCoordinator, EcoPlugCloudCoordinator):
            api = AsyncMock()
            api.get_passageway.side_effect = TypeError("fictional decoder bug")
            api.get_plug_data.side_effect = TypeError("fictional decoder bug")
            api.get_plug_state.return_value = {}
            coordinator = cls(self.hass, self.make_entry("plug"), api)
            with self.assertRaisesRegex(TypeError, "fictional decoder bug"):
                await coordinator._async_update_data()

    async def test_permanent_auth_failure_requires_reauth(self):
        for kind, cls in (
            ("main", EcoMainCloudCoordinator),
            ("plug", EcoPlugCloudCoordinator),
        ):
            with self.subTest(kind=kind):
                entry = self.make_entry(kind)
                api = AsyncMock()
                api.get_passageway.side_effect = EnecessAuthError("expired")
                api.get_plug_data.side_effect = EnecessAuthError("expired")
                api.get_plug_state.side_effect = EnecessAuthError("expired")
                api.generate_token.side_effect = EnecessAuthError("bad credentials")
                coordinator = cls(self.hass, entry, api)
                with self.assertRaises(ConfigEntryAuthFailed):
                    await coordinator._async_update_data()
                api.generate_token.assert_awaited_once()
                self.assertIs(coordinator.config_entry, entry)

    async def test_refresh_temporary_failure_is_update_failed(self):
        for cls in (EcoMainCloudCoordinator, EcoPlugCloudCoordinator):
            api = AsyncMock()
            api.get_passageway.side_effect = EnecessAuthError("expired")
            api.get_plug_data.side_effect = EnecessAuthError("expired")
            api.get_plug_state.side_effect = EnecessAuthError("expired")
            api.generate_token.side_effect = EnecessApiError("temporary")
            coordinator = cls(self.hass, self.make_entry("plug"), api)
            with self.assertRaises(UpdateFailed):
                await coordinator._async_update_data()

    async def test_rejected_retry_requires_reauth_and_stops(self):
        for cls in (EcoMainCloudCoordinator, EcoPlugCloudCoordinator):
            api = AsyncMock()
            api.get_passageway.side_effect = EnecessAuthError("expired")
            api.get_plug_data.side_effect = EnecessAuthError("expired")
            api.get_plug_state.side_effect = EnecessAuthError("expired")
            api.generate_token.return_value = "fictional-new-token"
            coordinator = cls(self.hass, self.make_entry("plug"), api)
            with self.assertRaises(ConfigEntryAuthFailed):
                await coordinator._async_update_data()
            api.generate_token.assert_awaited_once()
            request = (
                api.get_passageway
                if cls is EcoMainCloudCoordinator
                else api.get_plug_data
            )
            self.assertEqual(request.await_count, 2)

    async def test_successful_refresh_updates_token_and_retries(self):
        for cls in (EcoMainCloudCoordinator, EcoPlugCloudCoordinator):
            api = AsyncMock()
            api.get_passageway.side_effect = [EnecessAuthError("expired"), {}]
            api.get_plug_data.side_effect = [EnecessAuthError("expired"), {"data": []}]
            api.get_plug_state.return_value = {}
            api.generate_token.return_value = "fictional-refreshed-token"
            entry = self.make_entry("plug")
            coordinator = cls(self.hass, entry, api)
            await coordinator._async_update_data()
            self.assertEqual(
                entry.data[c.CONST_CLOUD_TOKEN], "fictional-refreshed-token"
            )
            api.generate_token.assert_awaited_once()

    async def test_temporary_retry_failure_is_not_auth(self):
        api = AsyncMock()
        api.get_passageway.side_effect = [
            EnecessAuthError("expired"),
            OSError("temporary"),
        ]
        api.generate_token.return_value = "fictional-refreshed-token"
        coordinator = EcoMainCloudCoordinator(self.hass, self.make_entry("main"), api)
        with self.assertRaises(UpdateFailed):
            await coordinator._async_update_data()

    async def test_reauth_failure_preserves_credentials(self):
        entry = self.make_entry("plug")
        original = dict(entry.data)
        flow = ConfigFlow()
        flow.hass = self.hass
        flow.context = {"entry_id": entry.entry_id, "source": "reauth"}
        for error, expected in (
            (EnecessAuthError("invalid"), "auth_failed"),
            (EnecessApiError("temporary"), "cannot_connect"),
        ):
            self.mocks["generate_token"].side_effect = error
            result = await flow.async_step_reauth_confirm(
                {
                    c.CONST_CLOUD_USERNAME: original[c.CONST_CLOUD_USERNAME],
                    c.CONST_CLOUD_PASSWORD: "fictional-new-password",
                }
            )
            self.assertEqual(result["errors"]["base"], expected)
            self.assertEqual(entry.data, original)

    async def test_reauth_preserves_entry_and_rejects_other_account(self):
        entry = self.make_entry("plug")
        self.hass.config_entries.async_update_entry(
            entry, options={"fictional_option": 1}
        )
        original = dict(entry.data)
        flow = ConfigFlow()
        flow.hass = self.hass
        flow.context = {"entry_id": entry.entry_id, "source": "reauth"}
        result = await flow.async_step_reauth(entry.data)
        self.assertEqual(result["step_id"], "reauth_confirm")
        result = await flow.async_step_reauth_confirm(
            {
                c.CONST_CLOUD_USERNAME: "other@example.invalid",
                c.CONST_CLOUD_PASSWORD: "fictional-new-password",
            }
        )
        self.assertEqual(result["errors"]["base"], "account_mismatch")
        with patch.object(
            self.hass.config_entries, "async_reload", new=AsyncMock(return_value=True)
        ):
            result = await flow.async_step_reauth_confirm(
                {
                    c.CONST_CLOUD_USERNAME: original[c.CONST_CLOUD_USERNAME],
                    c.CONST_CLOUD_PASSWORD: "fictional-new-password",
                }
            )
        self.assertEqual(result["reason"], "reauth_successful")
        self.assertEqual(entry.options, {"fictional_option": 1})
        self.assertEqual(
            entry.data, {**original, c.CONST_CLOUD_PASSWORD: "fictional-new-password"}
        )

    async def test_reauth_cancel_from_rendered_schema_makes_no_request(self):
        entry = self.make_entry("plug")
        original = dict(entry.data)
        flow = ConfigFlow()
        flow.hass = self.hass
        flow.context = {"entry_id": entry.entry_id, "source": "reauth"}
        result = await flow.async_step_reauth(entry.data)
        submitted = result["data_schema"]({"flow_action": "cancel"})
        result = await flow.async_step_reauth_confirm(submitted)
        self.assertEqual(result["reason"], "user_cancelled")
        self.mocks["generate_token"].assert_not_awaited()
        self.assertEqual(entry.data, original)

    async def test_reauth_missing_and_blank_credentials_makes_no_request(self):
        entry = self.make_entry("plug")
        original = dict(entry.data)
        flow = ConfigFlow()
        flow.hass = self.hass
        flow.context = {"entry_id": entry.entry_id, "source": "reauth"}
        result = await flow.async_step_reauth(entry.data)
        for values in (
            {},
            {c.CONST_CLOUD_USERNAME: " ", c.CONST_CLOUD_PASSWORD: "fictional"},
            {c.CONST_CLOUD_PASSWORD: " "},
        ):
            submitted = result["data_schema"](values)
            result = await flow.async_step_reauth_confirm(submitted)
            self.assertEqual(result["step_id"], "reauth_confirm")
            self.assertTrue(result["errors"])
        self.mocks["generate_token"].assert_not_awaited()
        self.assertEqual(entry.data, original)

    async def test_reauth_same_account_trims_whitespace_without_case_folding(self):
        entry = self.make_entry("plug")
        flow = ConfigFlow()
        flow.hass = self.hass
        flow.context = {"entry_id": entry.entry_id, "source": "reauth"}
        result = await flow.async_step_reauth(entry.data)
        submitted = result["data_schema"](
            {
                c.CONST_CLOUD_USERNAME: " " + entry.data[c.CONST_CLOUD_USERNAME] + " ",
                c.CONST_CLOUD_PASSWORD: "fictional-new-password",
            }
        )
        with patch.object(
            self.hass.config_entries, "async_reload", new=AsyncMock(return_value=True)
        ):
            result = await flow.async_step_reauth_confirm(submitted)
        self.assertEqual(result["reason"], "reauth_successful")
        self.mocks["generate_token"].assert_awaited_once_with(
            "compatibility@example.invalid", "fictional-new-password"
        )

    async def test_partial_outage_logs_once_and_recovers(self):
        api = AsyncMock()
        api.get_plug_data.side_effect = EnecessApiError("temporary")
        api.get_plug_state.return_value = {
            "response": {"data": {"p": [{"id": 106, "val": 1}]}}
        }
        coordinator = EcoPlugCloudCoordinator(self.hass, self.make_entry("plug"), api)
        with self.assertLogs(
            "custom_components.enecess.ecoplug.coordinator", level="INFO"
        ) as logs:
            first = await coordinator._async_update_data()
            await coordinator._async_update_data()
            api.get_plug_data.side_effect = None
            api.get_plug_data.return_value = {"data": []}
            await coordinator._async_update_data()
        self.assertEqual(len(logs.records), 2)
        self.assertIn("recovered", logs.output[-1])
        self.assertTrue(first[runtime.PLUG_SERIAL].is_on)


class CloudApiTests(unittest.IsolatedAsyncioTestCase):
    def api(self, status, payload):
        response = MagicMock(status=status)
        response.json = AsyncMock(return_value=payload)
        session = MagicMock()
        session.get.return_value.__aenter__.return_value = response
        session.post.return_value.__aenter__.return_value = response
        return EnecessApi(session, "https://example.invalid")

    async def test_login_server_failure_is_not_auth(self):
        with self.assertRaises(EnecessApiError):
            await self.api(503, {"status": 503}).generate_token(
                "fictional", "fictional"
            )

    async def test_business_auth_codes_are_auth(self):
        for method in ("get_hardware_list", "get_passageway"):
            with self.subTest(method=method), self.assertRaises(EnecessAuthError):
                await getattr(self.api(200, {"status": 401}), method)("fictional", 0)

    async def test_invalid_payload_is_api_error(self):
        for payload in (None, [], {"status": 200, "data": "invalid"}):
            for method in ("get_hardware_list", "get_passageway", "generate_token"):
                with (
                    self.subTest(method=method, payload=payload),
                    self.assertRaises(EnecessApiError),
                ):
                    await getattr(self.api(200, payload), method)("fictional", 0)

    async def test_api_errors_do_not_echo_response_secrets(self):
        with self.assertRaises(EnecessApiError) as error:
            await self.api(
                200, {"status": 500, "msg": "fictional-secret-token"}
            ).get_passageway("fictional", "fictional")
        self.assertNotIn("fictional-secret-token", str(error.exception))

    async def test_transport_auth_is_distinct_from_temporary_errors(self):
        for status in (401, 403):
            with self.assertRaises(EnecessAuthError):
                await self.api(status, None).get_passageway("fictional", "fictional")
        for status in (429, 500, 503):
            with self.assertRaises(EnecessApiError):
                await self.api(status, None).get_passageway("fictional", "fictional")
        api = self.api(200, {})
        api.session.get.return_value.__aenter__.side_effect = TimeoutError(
            "fictional-secret"
        )
        with self.assertRaises(EnecessApiError) as error:
            await api.get_passageway("fictional", "fictional")
        self.assertNotIn("fictional-secret", str(error.exception))
