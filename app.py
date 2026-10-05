"""
MistOrgLicensingComparison - Flask Web Application

Compares licensing information across multiple Juniper Mist organizations.
"""

import logging
import os

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request

from mist_connection import MistConnection

# Load environment variables
load_dotenv()

# Configure logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# The client gets these fixed messages, because exception text can expose
# internal details (CodeQL py/stack-trace-exposure, CWE-209).
INTERNAL_ERROR_MESSAGE = (
    "The server could not complete the request. Examine the server log."
)
ORGANIZATION_ERROR_MESSAGE = (
    "The server could not read the data for this organization. Examine the server log."
)

# Global Mist connection (lazy initialization)
_mist_connection: MistConnection | None = None


def get_mist_connection() -> MistConnection:
    """Get or create Mist API connection"""
    global _mist_connection

    if _mist_connection is None:
        api_token = os.environ.get("MIST_API_TOKEN") or os.environ.get("MIST_APITOKEN")
        if not api_token:
            raise ValueError("MIST_API_TOKEN environment variable is required")

        org_id = os.environ.get("MIST_ORG_ID")
        host = os.environ.get("MIST_HOST", "api.mist.com")

        _mist_connection = MistConnection(api_token=api_token, org_id=org_id, host=host)

    return _mist_connection


def internal_error_response(
    error: Exception, action: str, *action_args: object
) -> tuple[Response, int]:
    """Log a failed request on the server and return a generic JSON error.

    The log keeps the exception and its traceback for the operator. The client
    gets a fixed message, so the response exposes no internal detail. The
    action is a log template, for example "getting licenses for org %s".
    """
    # The action is a log template, and the values fill it, so the log stays structured.
    logger.error("Error " + action, *action_args, exc_info=error)
    # The response keeps the previous status code and JSON shape for the page.
    return jsonify({"success": False, "error": INTERNAL_ERROR_MESSAGE}), 500


@app.route("/")
def index():
    """Render main page"""
    response = app.make_response(render_template("index.html"))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


@app.route("/api/organizations")
def get_organizations():
    """Get list of accessible organizations"""
    try:
        mist = get_mist_connection()
        orgs = mist.get_organizations()
        return jsonify({"success": True, "data": orgs})
    except Exception as e:
        return internal_error_response(e, "getting organizations")


@app.route("/api/organization/<org_id>")
def get_organization(org_id: str):
    """Get organization details"""
    try:
        mist = get_mist_connection()
        org_info = mist.get_organization_info(org_id)
        return jsonify({"success": True, "data": org_info})
    except Exception as e:
        return internal_error_response(e, "getting organization %s", org_id)


@app.route("/api/licenses/<org_id>")
def get_licenses(org_id: str):
    """Get license summary for an organization"""
    try:
        mist = get_mist_connection()
        licenses = mist.get_org_licenses(org_id)
        return jsonify({"success": True, "data": licenses})
    except Exception as e:
        return internal_error_response(e, "getting licenses for org %s", org_id)


@app.route("/api/license-usage/<org_id>")
def get_license_usage(org_id: str):
    """Get license usage by site for an organization"""
    try:
        mist = get_mist_connection()
        usage = mist.get_org_license_usage(org_id)
        return jsonify({"success": True, "data": usage})
    except Exception as e:
        return internal_error_response(e, "getting license usage for org %s", org_id)


@app.route("/api/inventory/<org_id>")
def get_inventory(org_id: str):
    """Get inventory counts for an organization"""
    try:
        mist = get_mist_connection()
        counts = mist.get_org_inventory_counts(org_id)
        return jsonify({"success": True, "data": counts})
    except Exception as e:
        return internal_error_response(e, "getting inventory for org %s", org_id)


@app.route("/api/compare", methods=["POST"])
def compare_organizations():
    """
    Compare licensing across multiple organizations

    Request body: {"org_ids": ["org1", "org2", ...]}
    """
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "Expected a JSON object"}), 400
    org_ids = data.get("org_ids", [])

    if (
        not org_ids
        or not isinstance(org_ids, list)
        or not all(isinstance(item, str) and item.strip() for item in org_ids)
    ):
        return (
            jsonify({"success": False, "error": "No organization IDs provided"}),
            400,
        )

    try:
        mist = get_mist_connection()
    except Exception as e:
        return internal_error_response(e, "comparing organizations")

    results = []
    for org_id in org_ids:
        try:
            org_info = mist.get_organization_info(org_id)
            licenses = mist.get_org_licenses(org_id)
            inventory = mist.get_org_inventory_counts(org_id)

            results.append(
                {
                    "org_id": org_id,
                    "org_name": org_info.get("org_name", "Unknown"),
                    "licenses": licenses,
                    "inventory": inventory,
                    "error": None,
                }
            )
        except Exception as e:
            # The log keeps the detail. The row gets a fixed message only.
            logger.warning("Error fetching data for org %s", org_id, exc_info=e)
            results.append(
                {
                    "org_id": org_id,
                    "org_name": "Error",
                    "licenses": None,
                    "inventory": None,
                    "error": ORGANIZATION_ERROR_MESSAGE,
                }
            )

    return jsonify({"success": True, "data": results})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")

    logger.info(f"Starting MistOrgLicensingComparison on port {port}")
    app.run(host=host, port=port, debug=debug)
