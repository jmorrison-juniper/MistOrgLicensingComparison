"""
MistOrgLicensingComparison - Flask Web Application

Compares licensing information across multiple Juniper Mist organizations.
"""

import os
import logging
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global Mist connection (lazy initialization)
_mist_connection = None


def get_mist_connection():
    """Get or create Mist API connection"""
    global _mist_connection
    
    if _mist_connection is None:
        from mist_connection import MistConnection
        
        api_token = os.environ.get('MIST_API_TOKEN') or os.environ.get('MIST_APITOKEN')
        if not api_token:
            raise ValueError("MIST_API_TOKEN environment variable is required")
        
        org_id = os.environ.get('MIST_ORG_ID')
        host = os.environ.get('MIST_HOST', 'api.mist.com')
        
        _mist_connection = MistConnection(api_token=api_token, org_id=org_id, host=host)
    
    return _mist_connection


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


@app.route('/api/organizations')
def get_organizations():
    """Get list of accessible organizations"""
    try:
        mist = get_mist_connection()
        orgs = mist.get_organizations()
        return jsonify({'success': True, 'data': orgs})
    except Exception as e:
        logger.error(f"Error getting organizations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/organization/<org_id>')
def get_organization(org_id: str):
    """Get organization details"""
    try:
        mist = get_mist_connection()
        org_info = mist.get_organization_info(org_id)
        return jsonify({'success': True, 'data': org_info})
    except Exception as e:
        logger.error(f"Error getting organization {org_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/licenses/<org_id>')
def get_licenses(org_id: str):
    """Get license summary for an organization"""
    try:
        mist = get_mist_connection()
        licenses = mist.get_org_licenses(org_id)
        return jsonify({'success': True, 'data': licenses})
    except Exception as e:
        logger.error(f"Error getting licenses for org {org_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/license-usage/<org_id>')
def get_license_usage(org_id: str):
    """Get license usage by site for an organization"""
    try:
        mist = get_mist_connection()
        usage = mist.get_org_license_usage(org_id)
        return jsonify({'success': True, 'data': usage})
    except Exception as e:
        logger.error(f"Error getting license usage for org {org_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/inventory/<org_id>')
def get_inventory(org_id: str):
    """Get inventory counts for an organization"""
    try:
        mist = get_mist_connection()
        counts = mist.get_org_inventory_counts(org_id)
        return jsonify({'success': True, 'data': counts})
    except Exception as e:
        logger.error(f"Error getting inventory for org {org_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/compare', methods=['POST'])
def compare_organizations():
    """
    Compare licensing across multiple organizations
    
    Request body: {"org_ids": ["org1", "org2", ...]}
    """
    try:
        data = request.get_json()
        org_ids = data.get('org_ids', [])
        
        if not org_ids:
            return jsonify({'success': False, 'error': 'No organization IDs provided'}), 400
        
        mist = get_mist_connection()
        results = []
        
        for org_id in org_ids:
            try:
                org_info = mist.get_organization_info(org_id)
                licenses = mist.get_org_licenses(org_id)
                inventory = mist.get_org_inventory_counts(org_id)
                
                results.append({
                    'org_id': org_id,
                    'org_name': org_info.get('org_name', 'Unknown'),
                    'licenses': licenses,
                    'inventory': inventory,
                    'error': None
                })
            except Exception as e:
                logger.warning(f"Error fetching data for org {org_id}: {e}")
                results.append({
                    'org_id': org_id,
                    'org_name': 'Error',
                    'licenses': None,
                    'inventory': None,
                    'error': str(e)
                })
        
        return jsonify({'success': True, 'data': results})
        
    except Exception as e:
        logger.error(f"Error comparing organizations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting MistOrgLicensingComparison on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
