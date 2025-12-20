"""
Mist API Connection Wrapper for MistOrgLicensingComparison

Provides methods for fetching organization licensing data from multiple Mist orgs.
"""

import os
import logging
from typing import Dict, List, Optional
import mistapi

logger = logging.getLogger(__name__)


class MistConnection:
    """Handles connections to Mist API for licensing data retrieval"""
    
    def __init__(self, api_token: str, org_id: Optional[str] = None, host: str = 'api.mist.com'):
        """
        Initialize Mist API connection
        
        Args:
            api_token: Mist API token (can be comma-separated for multiple tokens)
            org_id: Optional organization ID (auto-detected if not provided)
            host: Mist API host (default: api.mist.com)
        """
        self.host = host
        self.org_id = org_id
        self.apisession = None
        self._self_data = None
        
        # Initialize the API session
        self._init_session(api_token)
        
        # Auto-detect org_id if not provided
        if not self.org_id:
            self._auto_detect_org()
        
        logger.info(f"Initialized Mist connection to {self.host} for org {self.org_id}")
    
    def _init_session(self, api_token: str):
        """Initialize the mistapi session with token"""
        # Save and temporarily clear env var to prevent SDK auto-loading
        saved_token = os.environ.get('MIST_APITOKEN')
        if saved_token:
            del os.environ['MIST_APITOKEN']
        
        try:
            # Parse tokens (support comma-separated)
            token_list = [t.strip() for t in api_token.split(',') if t.strip()]
            
            if not token_list:
                raise ValueError("No valid API tokens provided")
            
            # Test first working token
            for idx, token in enumerate(token_list):
                try:
                    # Create session with token directly (mistapi 0.58+ API)
                    self.apisession = mistapi.APISession(
                        host=self.host,
                        apitoken=token,
                        console_log_level=30,  # WARNING level
                        show_cli_notif=False
                    )
                    
                    # Test the token
                    test_response = mistapi.api.v1.self.self.getSelf(self.apisession)
                    
                    if test_response.status_code == 200:
                        self._self_data = test_response.data
                        logger.info(f"Using token {idx + 1}/{len(token_list)}")
                        break
                    elif test_response.status_code == 429:
                        logger.warning(f"Token {idx + 1} rate limited, trying next...")
                        continue
                    else:
                        logger.warning(f"Token {idx + 1} returned {test_response.status_code}")
                        continue
                        
                except Exception as e:
                    logger.warning(f"Token {idx + 1} failed: {e}")
                    continue
            else:
                raise Exception("All tokens failed to initialize")
                
        finally:
            # Restore the environment variable
            if saved_token is not None:
                os.environ['MIST_APITOKEN'] = saved_token
    
    def _auto_detect_org(self):
        """Auto-detect organization ID from user privileges"""
        try:
            if self._self_data:
                data = self._self_data
            else:
                response = mistapi.api.v1.self.self.getSelf(self.apisession)
                if response.status_code != 200:
                    raise Exception(f"Failed to get self info: {response.status_code}")
                data = response.data
            
            if 'privileges' in data and len(data['privileges']) > 0:
                self.org_id = data['privileges'][0].get('org_id')
                logger.info(f"Auto-detected org_id: {self.org_id}")
            else:
                raise ValueError("No organizations found in user privileges")
        except Exception as e:
            logger.error(f"Error auto-detecting org_id: {str(e)}")
            raise
    
    def get_organizations(self) -> List[Dict]:
        """Get list of organizations the user has access to"""
        try:
            response = mistapi.api.v1.self.self.getSelf(self.apisession)
            if response.status_code == 200:
                data = response.data
                orgs = []
                if 'privileges' in data:
                    for priv in data['privileges']:
                        # Handle different privilege structures
                        org_id = priv.get('org_id')
                        # org_name can be in 'org_name' or 'name' field
                        org_name = priv.get('org_name') or priv.get('name', 'Unknown')
                        if org_id:
                            orgs.append({
                                'id': org_id,
                                'name': org_name,
                                'role': priv.get('role', 'unknown'),
                                'scope': priv.get('scope', 'unknown')
                            })
                return orgs
            else:
                raise Exception(f"API error: {response.status_code}")
        except Exception as e:
            logger.error(f"Error getting organizations: {str(e)}")
            raise
    
    def get_organization_info(self, org_id: Optional[str] = None) -> Dict:
        """Get organization information"""
        target_org = org_id or self.org_id
        try:
            response = mistapi.api.v1.orgs.orgs.getOrg(self.apisession, target_org)
            if response.status_code == 200:
                data = response.data
                return {
                    'org_id': data.get('id'),
                    'org_name': data.get('name', 'Unknown Organization'),
                    'created_time': data.get('created_time', 0),
                    'updated_time': data.get('updated_time', 0)
                }
            else:
                raise Exception(f"API error: {response.status_code}")
        except Exception as e:
            logger.error(f"Error getting organization info: {str(e)}")
            raise
    
    def get_org_licenses(self, org_id: Optional[str] = None) -> Dict:
        """
        Get organization license information
        
        Args:
            org_id: Organization ID (uses default if not provided)
            
        Returns:
            Dict with license summary and details
        """
        target_org = org_id or self.org_id
        try:
            # Get license summary
            response = mistapi.api.v1.orgs.licenses.getOrgLicensesSummary(
                self.apisession, target_org
            )
            
            if response.status_code == 200:
                return response.data
            else:
                raise Exception(f"API error: {response.status_code}")
        except Exception as e:
            logger.error(f"Error getting licenses for org {target_org}: {str(e)}")
            raise
    
    def get_org_license_usage(self, org_id: Optional[str] = None) -> Dict:
        """
        Get organization license usage details
        
        Args:
            org_id: Organization ID (uses default if not provided)
            
        Returns:
            Dict with license usage by type
        """
        target_org = org_id or self.org_id
        try:
            response = mistapi.api.v1.orgs.licenses.getOrgLicensesBySite(
                self.apisession, target_org
            )
            
            if response.status_code == 200:
                return response.data
            else:
                raise Exception(f"API error: {response.status_code}")
        except Exception as e:
            logger.error(f"Error getting license usage for org {target_org}: {str(e)}")
            raise
    
    def get_org_inventory_counts(self, org_id: Optional[str] = None) -> Dict:
        """
        Get inventory counts by device type
        
        Args:
            org_id: Organization ID (uses default if not provided)
            
        Returns:
            Dict with device counts by type
        """
        target_org = org_id or self.org_id
        counts = {
            'aps': 0,
            'switches': 0,
            'gateways': 0,
            'total': 0
        }
        
        try:
            # Get inventory with type counts
            for device_type in ['ap', 'switch', 'gateway']:
                response = mistapi.api.v1.orgs.inventory.getOrgInventory(
                    self.apisession, target_org,
                    type=device_type,
                    limit=1
                )
                
                if response.status_code == 200:
                    # Get total from response headers or count
                    total = getattr(response, 'total', 0)
                    if hasattr(response, 'data') and isinstance(response.data, list):
                        # If we got paginated response, check for total in headers
                        if hasattr(response, 'headers'):
                            total = int(response.headers.get('X-Page-Total', len(response.data)))
                        else:
                            # Make a count-only request
                            count_response = mistapi.api.v1.orgs.inventory.countOrgInventory(
                                self.apisession, target_org,
                                type=device_type
                            )
                            if count_response.status_code == 200:
                                total = count_response.data.get('count', 0)
                    
                    if device_type == 'ap':
                        counts['aps'] = total
                    elif device_type == 'switch':
                        counts['switches'] = total
                    elif device_type == 'gateway':
                        counts['gateways'] = total
            
            counts['total'] = counts['aps'] + counts['switches'] + counts['gateways']
            return counts
            
        except Exception as e:
            logger.error(f"Error getting inventory counts for org {target_org}: {str(e)}")
            raise
