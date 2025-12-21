# MistOrgLicensingComparison

A Flask web application for comparing Juniper Mist organization licensing information across multiple organizations.

## Features

- **Multi-Organization Support**: Compare licenses across multiple Mist organizations
- **Multi-Token Support**: Use comma-separated API tokens to access organizations from different accounts
- **License Comparison Table**: Side-by-side view of license usage vs entitlements
- **Purchased License Tracking**: Enter purchased license counts to calculate remaining (unapplied) licenses
- **SUB-AI Bundle Support**: Automatically calculates bundle contributions to component licenses
- **Device Inventory**: View AP, Switch, and Gateway counts per organization
- **License Tooltips**: Hover over license types to see descriptions (documented vs undocumented)
- **Export to CSV**: Download comparison data for reporting
- **Dark Theme**: Bootstrap 5.3.2 dark theme with T-Mobile magenta accent

## Supported License Types

### Documented (from Juniper Mist Management Guide)
- **Wireless**: SUB-MAN, SUB-VNA, SUB-AST, SUB-ENG, SUB-PMA, SUB-AI (bundle)
- **Wired**: SUB-EX12, SUB-EX24, SUB-EX48, SUB-EX-VNA, SUB-SVNA
- **WAN**: SUB-WAN, SUB-WVNA
- **Mist Edge**: SUB-ME
- **Access Assurance**: S-CLIENT-S, S-CLIENT-A

### Undocumented (observed in API)
- SUB-SSR, SUB-SPRM2, SUB-WAN1-5 (tiered WAN subscriptions)

## Screenshots

![Dashboard](docs/screenshots/dashboard.png)

## Quick Start

### Prerequisites

- Python 3.13+ (or 3.11+)
- Mist API Token with access to target organizations

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/jmorrison-juniper/MistOrgLicensingComparison.git
   cd MistOrgLicensingComparison
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env and add your MIST_API_TOKEN
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Open http://localhost:5000 in your browser

### Docker

Build and run with Docker:

```bash
# Build
docker build -t mist-licensing .

# Run
docker run -d -p 5000:5000 \
  -e MIST_API_TOKEN=your_token_here \
  mist-licensing
```

Or use Docker Compose:

```bash
# Create .env file with your token
cp .env.example .env
# Edit .env

# Run
docker compose up -d
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| MIST_API_TOKEN | Yes | - | Mist API token (comma-separated for multiple tokens) |
| MIST_ORG_ID | No | Auto-detect | Default organization ID |
| MIST_HOST | No | api.mist.com | Mist API host |
| PORT | No | 5000 | Web server port |
| LOG_LEVEL | No | INFO | Logging level |

### Multi-Token Configuration

To access organizations from multiple Mist accounts, provide comma-separated tokens:

```env
MIST_API_TOKEN=token1,token2,token3
```

Each token's accessible organizations will be aggregated and deduplicated.

## Mist API Endpoints Used

This application uses the following Juniper Mist API endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/self` | Validate API token and get user info |
| `GET /api/v1/orgs/{org_id}` | Get organization details |
| `GET /api/v1/orgs/{org_id}/licenses` | Get license summary (entitled, usage, amendments) |
| `GET /api/v1/orgs/{org_id}/licenses/usages` | Get license usage breakdown by site |
| `GET /api/v1/orgs/{org_id}/inventory` | Get device inventory |
| `GET /api/v1/orgs/{org_id}/inventory/count` | Get device inventory counts by type |

## Multi-Architecture Support

The Docker image is built for both `linux/amd64` and `linux/arm64` platforms, supporting:
- x86_64 servers and desktops
- Apple Silicon Macs (M1/M2/M3)
- ARM-based cloud instances

## Development

### Project Structure

```
MistOrgLicensingComparison/
├── app.py                 # Flask application
├── mist_connection.py     # Mist API wrapper
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container build
├── docker-compose.yml    # Docker Compose config
├── .env.example          # Environment template
├── templates/
│   └── index.html        # Frontend SPA
└── .github/
    ├── copilot-instructions.md
    └── workflows/
        └── build.yml     # CI/CD workflow
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest
```

## License

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International - See [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Related Projects

- [MistCircuitStats](https://github.com/jmorrison-juniper/MistCircuitStats) - Mist Gateway WAN port statistics
- [MistCircuitStats-Redis](https://github.com/jmorrison-juniper/MistCircuitStats-Redis) - Redis-cached version
