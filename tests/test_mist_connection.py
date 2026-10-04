"""Exercise SDK dispatch and aggregation, without credentials or API traffic."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import mistapi

from mist_connection import MistConnection, MistConnectionError


def response(data, status=200):
    return SimpleNamespace(status_code=status, data=data)


class MistTests(unittest.TestCase):
    def setUp(self):
        self.network = patch(
            "requests.sessions.Session.send",
            side_effect=AssertionError("Live API access is forbidden"),
        )
        self.network.start()
        self.addCleanup(self.network.stop)
        self.session = Mock()
        self.constructor = patch.object(
            mistapi, "APISession", return_value=self.session
        )
        self.constructor.start()
        self.addCleanup(self.constructor.stop)
        self.self_api = patch.object(
            mistapi.api.v1.self.self,
            "getSelf",
            return_value=response(
                {
                    "privileges": [
                        {"org_id": "org1", "org_name": "Zulu", "role": "admin"}
                    ]
                }
            ),
        )
        self.get_self = self.self_api.start()
        self.addCleanup(self.self_api.stop)

    def test_multiple_tokens_skip_failures_deduplicate_sort_and_dispatch(self):
        first, second = Mock(), Mock()
        mistapi.APISession.side_effect = [Mock(), first, second]
        self.get_self.side_effect = [
            response({}, 429),
            response({"privileges": [{"org_id": "org1", "org_name": "Zulu"}]}),
            response(
                {
                    "privileges": [
                        {"org_id": "org1", "org_name": "Duplicate"},
                        {"org_id": "org2", "name": "Alpha"},
                        {"scope": "site"},
                    ]
                }
            ),
        ]
        with patch.dict(os.environ, {"MIST_APITOKEN": "saved-fixture"}):
            connection = MistConnection("limited, first, ,second")
            self.assertEqual(os.environ["MIST_APITOKEN"], "saved-fixture")
        self.assertEqual(connection.org_id, "org1")
        self.assertEqual(
            [org["name"] for org in connection.get_organizations()], ["Alpha", "Zulu"]
        )
        self.assertIs(connection._get_session_for_org("org1"), first)
        self.assertIs(connection._get_session_for_org("org2"), second)
        self.assertIs(connection._get_session_for_org("unknown"), first)

    def test_empty_and_failed_tokens_restore_environment(self):
        for tokens, expected in (
            (" , ", ValueError),
            ("failed", MistConnectionError),
        ):
            with (
                self.subTest(tokens=tokens),
                patch.dict(os.environ, {"MIST_APITOKEN": "saved-fixture"}),
            ):
                self.get_self.return_value = response({}, 401)
                with self.assertRaises(expected):
                    MistConnection(tokens)
                self.assertEqual(os.environ["MIST_APITOKEN"], "saved-fixture")

    def test_session_exception_does_not_discard_working_tokens(self):
        self.get_self.side_effect = [
            RuntimeError("offline failure"),
            response({"privileges": []}),
        ]
        connection = MistConnection("bad, good", org_id="explicit")
        self.assertEqual(connection.org_id, "explicit")
        self.assertEqual(connection.get_organizations(), [])

    def test_real_updated_sdk_constructor_accepts_application_arguments(self):
        self.constructor.stop()
        transport_response = Mock(status_code=200)
        transport_response.json.return_value = {"privileges": []}
        with patch("requests.get", return_value=transport_response) as transport:
            connection = MistConnection("0" * 32, org_id="org1")
        transport.assert_called_once()
        self.assertIsInstance(connection._sessions[0][0], mistapi.APISession)

    def test_read_endpoints_use_updated_sdk_names_and_report_status(self):
        connection = MistConnection("fixture")
        cases = [
            (
                mistapi.api.v1.orgs.orgs,
                "getOrg",
                connection.get_organization_info,
                {"id": "org1", "name": "Example"},
                {
                    "org_id": "org1",
                    "org_name": "Example",
                    "created_time": 0,
                    "updated_time": 0,
                },
            ),
            (
                mistapi.api.v1.orgs.licenses,
                "getOrgLicensesSummary",
                connection.get_org_licenses,
                {"entitled": {"SUB-MAN": 10}},
                {"entitled": {"SUB-MAN": 10}},
            ),
            (
                mistapi.api.v1.orgs.licenses,
                "getOrgLicensesBySite",
                connection.get_org_license_usage,
                [{"site_id": "site1", "usage": 3}],
                [{"site_id": "site1", "usage": 3}],
            ),
        ]
        for module, name, operation, data, expected in cases:
            with self.subTest(endpoint=name), patch.object(module, name) as endpoint:
                endpoint.return_value = response(data)
                self.assertEqual(operation(), expected)
                endpoint.assert_called_once_with(self.session, "org1")
                for status in (401, 429, 500):
                    endpoint.return_value = response({}, status)
                    with self.assertRaisesRegex(MistConnectionError, str(status)):
                        operation("org1")

    def test_missing_org_and_missing_sessions_are_explicit_errors(self):
        self.get_self.return_value = response({"privileges": []})
        connection = MistConnection("fixture")
        with self.assertRaisesRegex(MistConnectionError, "Organization ID"):
            connection.get_org_licenses()
        connection._sessions.clear()
        with self.assertRaisesRegex(MistConnectionError, "No valid API sessions"):
            connection.get_org_licenses("org1")

    def test_inventory_sums_physical_counts_and_empty_results(self):
        connection = MistConnection("fixture")
        with patch.object(mistapi.api.v1.orgs.inventory, "countOrgInventory") as count:
            count.side_effect = [
                response({"results": [{"count": 5}, {"count": 3}]}),
                response({"results": [{"count": 4}, {}]}),
                response({"results": []}),
            ]
            self.assertEqual(
                connection.get_org_inventory_counts(),
                {"aps": 8, "switches": 4, "gateways": 0, "total": 12},
            )
            self.assertEqual(
                [call.kwargs["type"] for call in count.call_args_list],
                ["ap", "switch", "gateway"],
            )

    def test_failed_inventory_never_looks_like_zero_devices(self):
        connection = MistConnection("fixture")
        with patch.object(mistapi.api.v1.orgs.inventory, "countOrgInventory") as count:
            for status in (401, 429, 500):
                with self.subTest(status=status):
                    count.return_value = response({}, status)
                    with self.assertRaisesRegex(MistConnectionError, str(status)):
                        connection.get_org_inventory_counts()
