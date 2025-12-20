# MistOrgLicensingComparison - Copilot Instructions

## Project Overview
Flask web application for comparing Juniper Mist organization licensing information across multiple organizations.
Helps administrators visualize and compare license allocations, device counts, and subscription details.

## Key Architecture Patterns
- Python 3.13 in Docker containers
- Flask with application factory pattern
- mistapi SDK for Mist API integration
- Bootstrap 5.3.2 dark theme with T-Mobile magenta accent (#E20074)
- Single-page application with vanilla JavaScript
- Multi-architecture Docker containers (amd64/arm64)

## Core Components
- `app.py` - Flask web app with REST API endpoints
- `mist_connection.py` - Mist API connection wrapper
- `templates/index.html` - Frontend SPA with comparison UI

## Environment Variables
- MIST_API_TOKEN (required): Mist API token (comma-separated for multiple)
- MIST_ORG_ID (optional): Auto-detected from token
- MIST_HOST (default: api.mist.com)
- PORT (default: 5000)
- LOG_LEVEL (default: INFO)

## API Endpoints
- `GET /` - Main page
- `GET /health` - Health check
- `GET /api/organizations` - List accessible organizations
- `GET /api/organization/<org_id>` - Organization details
- `GET /api/licenses/<org_id>` - License summary
- `GET /api/license-usage/<org_id>` - License usage by site
- `GET /api/inventory/<org_id>` - Device inventory counts
- `POST /api/compare` - Compare multiple organizations

## Development Guidelines
- Use type hints for function parameters and return values
- Handle Optional types properly (provide defaults or validate)
- Use proper error handling with specific error messages
- Validate environment variables before use
- Non-root container user for security

## mistapi SDK Usage
- API responses have `.status_code` and `.data` attributes
- Check status_code == 200 for successful responses
- Key endpoints:
  - `mistapi.api.v1.self.self.getSelf()` - Get user info
  - `mistapi.api.v1.orgs.licenses.getOrgLicencesSummary()` - License summary
  - `mistapi.api.v1.orgs.licenses.getOrgLicencesBySite()` - License usage
  - `mistapi.api.v1.orgs.inventory.getOrgInventory()` - Device inventory

## Dependency Management
- `mistapi` requires `python-dotenv>=1.1.0`
- Always check for dependency conflicts when updating

## CI/CD
- GitHub Actions builds on push to main and tags
- Publishes to ghcr.io/jmorrison-juniper/mistorglicensingcomparison
- Multi-arch builds: linux/amd64, linux/arm64

## Container Development
- Local builds: Use `docker build -t mist-licensing .` (builds for native arch)
- Apple Silicon Macs: Native arm64 builds, no emulation needed
- For cross-platform testing: `docker buildx build --platform linux/amd64 -t mist-licensing .`
- Use `docker compose up` for local development with .env file
- Production images from ghcr.io support both amd64 and arm64

## Release Management
- Use YY.MM.DD.HH.MM format for version tags
- Create annotated tags: `git tag -a 25.12.19.12.00 -m "Release notes"`
- Push tags to trigger builds: `git push origin 25.12.19.12.00`

## Git Configuration
- Repository: https://github.com/jmorrison-juniper/MistOrgLicensingComparison
- Use `gh` CLI for GitHub operations (authenticated via keyring)
- Git protocol: HTTPS
