"""
Mist API Connection Wrapper for MistOrgLicensingComparison

Provides methods for fetching organization licensing data from multiple Mist orgs.
Supports multiple API tokens, each potentially accessing different organizations.
"""

import logging
import os
from typing import Any

# mistapi does not publish type hints, so mypy cannot inspect the SDK.
import mistapi  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class MistConnectionError(RuntimeError):
    """Raised when Mist API communication cannot complete."""


type MistResponseData = dict[str, Any]
type MistJsonData = Any


class MistConnection:
    """Handles connections to Mist API for licensing data retrieval.

    Supports multiple API tokens where each token may have access to different
    organizations. Organizations are aggregated from all working tokens.
    """

    def __init__(
        self, api_token: str, org_id: str | None = None, host: str = "api.mist.com"
    ):
        """
        Initialize Mist API connection with support for multiple tokens.

        Args:
            api_token: Mist API token (can be comma-separated for multiple tokens)
            org_id: Optional organization ID (auto-detected if not provided)
            host: Mist API host (default: api.mist.com)
        """
        self.host = host
        self.org_id = org_id

        # Store all working sessions and their associated orgs
        self._sessions: list[tuple[mistapi.APISession, MistResponseData]] = []
        # Map org_id to session for quick lookup
        self._org_to_session: dict[str, mistapi.APISession] = {}

        # Initialize all API sessions
        self._init_sessions(api_token)

        # Auto-detect org_id if not provided (use first available)
        if not self.org_id and self._sessions:
            self._auto_detect_org()

        logger.info(
            f"Initialized Mist connection to {self.host} with {len(self._sessions)} working token(s)"
        )

    def _init_sessions(self, api_token: str) -> None:
        """Initialize mistapi sessions for all provided tokens"""
        # Save and temporarily clear env var to prevent SDK auto-loading
        saved_token = os.environ.get("MIST_APITOKEN")
        if saved_token:
            del os.environ["MIST_APITOKEN"]

        try:
            # Parse tokens (support comma-separated)
            token_list = [t.strip() for t in api_token.split(",") if t.strip()]

            if not token_list:
                raise ValueError("No valid API tokens provided")

            # Try each token and keep all working ones
            for idx, token in enumerate(token_list):
                try:
                    # Create session with token directly (mistapi 0.58+ API)
                    session = mistapi.APISession(
                        host=self.host,
                        apitoken=token,
                        console_log_level=30,  # WARNING level
                        show_cli_notif=False,
                    )

                    # Test the token and get user info
                    test_response = mistapi.api.v1.self.self.getSelf(session)

                    if test_response.status_code == 200:
                        self_data = test_response.data
                        self._sessions.append((session, self_data))

                        # Map each org to this session
                        if "privileges" in self_data:
                            for priv in self_data["privileges"]:
                                org_id = priv.get("org_id")
                                if org_id and org_id not in self._org_to_session:
                                    self._org_to_session[org_id] = session

                        logger.info(
                            f"Token {idx + 1}/{len(token_list)} initialized successfully"
                        )
                    elif test_response.status_code == 429:
                        logger.warning(f"Token {idx + 1} rate limited, skipping...")
                    else:
                        logger.warning(
                            f"Token {idx + 1} returned {test_response.status_code}"
                        )

                except Exception as e:  # noqa: BLE001 - SDK token failover.
                    logger.warning(f"Token {idx + 1} failed: {e}")
                    continue

            if not self._sessions:
                raise MistConnectionError("All tokens failed to initialize")

        finally:
            # Restore the environment variable
            if saved_token is not None:
                os.environ["MIST_APITOKEN"] = saved_token

    def _auto_detect_org(self) -> None:
        """Auto-detect organization ID from first available session"""
        if self._sessions:
            _session, self_data = self._sessions[0]
            if "privileges" in self_data and len(self_data["privileges"]) > 0:
                self.org_id = self_data["privileges"][0].get("org_id")
                logger.info(f"Auto-detected org_id: {self.org_id}")

    def _resolve_org_id(self, org_id: str | None) -> str:
        """Resolve an explicit or default organization ID."""
        target_org = org_id or self.org_id
        if not target_org:
            raise MistConnectionError("Organization ID is required")
        return target_org

    def _get_session_for_org(self, org_id: str) -> mistapi.APISession:
        """Get the appropriate session for accessing an organization"""
        if org_id in self._org_to_session:
            return self._org_to_session[org_id]
        # Fallback to first session
        if self._sessions:
            return self._sessions[0][0]
        raise MistConnectionError("No valid API sessions available")

    def _get_response_data(self, response: Any, context: str) -> MistJsonData:
        """Return response data or raise a typed connection error."""
        status_code = getattr(response, "status_code", None)
        if status_code == 200:
            return getattr(response, "data", None)
        raise MistConnectionError(f"{context} failed with status {status_code}")

    def get_organizations(self) -> list[MistResponseData]:
        """Get list of all organizations accessible from all tokens (deduplicated)"""
        orgs_seen = set()
        orgs: list[MistResponseData] = []

        for _session, self_data in self._sessions:
            if "privileges" in self_data:
                for priv in self_data["privileges"]:
                    org_id = priv.get("org_id")
                    if org_id and org_id not in orgs_seen:
                        orgs_seen.add(org_id)
                        org_name = priv.get("org_name") or priv.get("name", "Unknown")
                        orgs.append(
                            {
                                "id": org_id,
                                "name": org_name,
                                "role": priv.get("role", "unknown"),
                                "scope": priv.get("scope", "unknown"),
                            }
                        )

        # Sort by name
        orgs.sort(key=lambda x: x["name"].lower())
        return orgs

    def get_organization_info(self, org_id: str | None = None) -> MistResponseData:
        """Get organization information"""
        target_org = self._resolve_org_id(org_id)
        session = self._get_session_for_org(target_org)

        response = mistapi.api.v1.orgs.orgs.getOrg(session, target_org)
        data = self._get_response_data(response, "Organization info request")
        return {
            "org_id": data.get("id"),
            "org_name": data.get("name", "Unknown Organization"),
            "created_time": data.get("created_time", 0),
            "updated_time": data.get("updated_time", 0),
        }

    def get_org_licenses(self, org_id: str | None = None) -> MistResponseData:
        """
        Get organization license information

        Args:
            org_id: Organization ID (uses default if not provided)

        Returns:
            Dict with license summary and details
        """
        target_org = self._resolve_org_id(org_id)
        session = self._get_session_for_org(target_org)

        response = mistapi.api.v1.orgs.licenses.getOrgLicensesSummary(
            session, target_org
        )
        return self._get_response_data(response, "License summary request")

    def get_org_license_usage(self, org_id: str | None = None) -> MistJsonData:
        """
        Get organization license usage details

        Args:
            org_id: Organization ID (uses default if not provided)

        Returns:
            Dict with license usage by type
        """
        target_org = self._resolve_org_id(org_id)
        session = self._get_session_for_org(target_org)

        response = mistapi.api.v1.orgs.licenses.getOrgLicensesBySite(
            session, target_org
        )
        return self._get_response_data(response, "License usage request")

    def get_org_inventory_counts(self, org_id: str | None = None) -> MistResponseData:
        """
        Get inventory counts by device type (physical device counts for licensing)

        Args:
            org_id: Organization ID (uses default if not provided)

        Returns:
            Dict with physical device counts by type
        """
        target_org = self._resolve_org_id(org_id)
        session = self._get_session_for_org(target_org)

        counts: MistResponseData = {"aps": 0, "switches": 0, "gateways": 0, "total": 0}

        # Use countOrgInventory to get physical device counts
        # This returns the actual physical count (e.g., all members in a VC stack)
        # which aligns with licensing requirements
        for device_type in ["ap", "switch", "gateway"]:
            count_response = mistapi.api.v1.orgs.inventory.countOrgInventory(
                session, target_org, type=device_type
            )

            if count_response.status_code == 200:
                total = 0
                results = count_response.data.get("results", [])
                for result in results:
                    total += result.get("count", 0)

                if device_type == "ap":
                    counts["aps"] = total
                elif device_type == "switch":
                    counts["switches"] = total
                elif device_type == "gateway":
                    counts["gateways"] = total

        counts["total"] = counts["aps"] + counts["switches"] + counts["gateways"]
        return counts
