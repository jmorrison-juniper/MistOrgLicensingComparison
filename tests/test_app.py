"""Offline HTTP contracts: real Flask routes with a mocked Mist boundary."""

import os
import unittest
from unittest.mock import Mock, patch

with patch("dotenv.load_dotenv"):
    import app


class RouteTests(unittest.TestCase):
    def setUp(self):
        app.app.config["TESTING"] = True
        self.client = app.app.test_client()
        self.mist = Mock()
        self.connection = patch.object(
            app, "get_mist_connection", return_value=self.mist
        )
        self.connection.start()
        self.addCleanup(self.connection.stop)
        self.network = patch(
            "requests.sessions.Session.send",
            side_effect=AssertionError("Live API access is forbidden"),
        )
        self.network.start()
        self.addCleanup(self.network.stop)

    def test_page_and_health_do_not_initialize_sdk(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"bootstrap@5.3.8", response.data)
        self.assertIn(b"bootstrap-icons@1.13.1", response.data)
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertEqual(self.client.get("/health").json, {"status": "healthy"})
        app.get_mist_connection.assert_not_called()

    def test_all_read_routes_return_data_and_report_failures(self):
        endpoints = {
            "/api/organizations": "get_organizations",
            "/api/organization/org1": "get_organization_info",
            "/api/licenses/org1": "get_org_licenses",
            "/api/license-usage/org1": "get_org_license_usage",
            "/api/inventory/org1": "get_org_inventory_counts",
        }
        for endpoint, method in endpoints.items():
            with self.subTest(endpoint=endpoint):
                operation = getattr(self.mist, method)
                operation.return_value = {"fixture": 7}
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json, {"success": True, "data": {"fixture": 7}}
                )
                operation.side_effect = RuntimeError("Fixture failure")
                with self.assertLogs(app.logger, level="ERROR") as logs:
                    response = self.client.get(endpoint)
                self.assertEqual(response.status_code, 500)
                self.assertEqual(
                    response.json,
                    {"success": False, "error": app.INTERNAL_ERROR_MESSAGE},
                )
                self.assertNotIn("Fixture failure", response.get_data(as_text=True))
                self.assertIn("Fixture failure", "\n".join(logs.output))
                operation.side_effect = None

    def test_comparison_rejects_invalid_payloads_before_connecting(self):
        for payload in (
            [],
            ["org1"],
            7,
            "org1",
            {},
            {"org_ids": []},
            {"org_ids": "org1"},
            {"org_ids": [None]},
            {"org_ids": [""]},
            {"org_ids": ["  "]},
        ):
            with self.subTest(payload=payload):
                response = self.client.post("/api/compare", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertFalse(response.json["success"])
        response = self.client.post(
            "/api/compare", data="{broken", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        app.get_mist_connection.assert_not_called()

    def test_comparison_preserves_order_and_partial_failures(self):
        def org_info(org_id):
            if org_id == "bad":
                raise RuntimeError("Unavailable organization")
            return {"org_name": "Fixture organization"}

        self.mist.get_organization_info.side_effect = org_info
        self.mist.get_org_licenses.return_value = {"entitled": {"SUB-MAN": 10}}
        self.mist.get_org_inventory_counts.return_value = {"aps": 8}
        with self.assertLogs(app.logger, level="WARNING"):
            response = self.client.post(
                "/api/compare", json={"org_ids": ["good", "bad", "good"]}
            )
        self.assertEqual(response.status_code, 200)
        rows = response.json["data"]
        self.assertEqual([row["org_id"] for row in rows], ["good", "bad", "good"])
        self.assertEqual(rows[0]["licenses"]["entitled"]["SUB-MAN"], 10)
        self.assertEqual(rows[0]["inventory"]["aps"], 8)
        self.assertIsNone(rows[0]["error"])
        self.assertEqual(rows[1]["error"], app.ORGANIZATION_ERROR_MESSAGE)
        self.assertNotIn("Unavailable organization", response.get_data(as_text=True))
        self.assertIsNone(rows[1]["inventory"])

    def test_initialization_failure_is_json(self):
        app.get_mist_connection.side_effect = ValueError("Missing token")
        with self.assertLogs(app.logger, level="ERROR"):
            response = self.client.post("/api/compare", json={"org_ids": ["org1"]})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json, {"success": False, "error": app.INTERNAL_ERROR_MESSAGE}
        )

    def test_error_responses_keep_exception_text_in_the_server_log_only(self):
        """Regression for issue #25 (CodeQL py/stack-trace-exposure)."""
        secret_detail = "Traceback detail /srv/app/mist_connection.py token=abc"
        app.get_mist_connection.side_effect = RuntimeError(secret_detail)
        with self.assertLogs(app.logger, level="ERROR") as logs:
            response = self.client.get("/api/organizations")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn(secret_detail, response.get_data(as_text=True))
        self.assertEqual(logs.records[0].levelname, "ERROR")
        self.assertIs(logs.records[0].exc_info[1], app.get_mist_connection.side_effect)
        self.assertIn(secret_detail, "\n".join(logs.output))


class ConnectionConfigurationTests(unittest.TestCase):
    def test_missing_token_and_legacy_fallback_and_lazy_cache(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(app, "_mist_connection", None),
            patch.object(app, "MistConnection") as constructor,
        ):
            with self.assertRaisesRegex(ValueError, "MIST_API_TOKEN"):
                app.get_mist_connection()
            os.environ["MIST_APITOKEN"] = "offline-fixture"
            os.environ["MIST_HOST"] = "api.fixture.invalid"
            first = app.get_mist_connection()
            self.assertIs(first, app.get_mist_connection())
            constructor.assert_called_once_with(
                api_token="offline-fixture",
                org_id=None,
                host="api.fixture.invalid",
            )
