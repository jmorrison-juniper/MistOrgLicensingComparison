# MistOrgLicensingComparison

A Flask web application for comparing Juniper Mist organization licensing information across multiple organizations.

## Features

- **Multi-Organization View**: See all organizations your API token has access to
- **License Comparison**: Compare license allocations across organizations
- **Device Inventory**: View AP, Switch, and Gateway counts per organization
- **Export to CSV**: Download comparison data for reporting
- **Dark Theme**: Bootstrap 5.3.2 dark theme with T-Mobile magenta accent

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
| MIST_API_TOKEN | Yes | - | Mist API token |
| MIST_ORG_ID | No | Auto-detect | Default organization ID |
| MIST_HOST | No | api.mist.com | Mist API host |
| PORT | No | 5000 | Web server port |
| LOG_LEVEL | No | INFO | Logging level |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/health` | GET | Health check |
| `/api/organizations` | GET | List accessible organizations |
| `/api/organization/<org_id>` | GET | Organization details |
| `/api/licenses/<org_id>` | GET | License summary |
| `/api/license-usage/<org_id>` | GET | License usage by site |
| `/api/inventory/<org_id>` | GET | Device inventory counts |
| `/api/compare` | POST | Compare multiple organizations |

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

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Related Projects

- [MistCircuitStats](https://github.com/jmorrison-juniper/MistCircuitStats) - Mist Gateway WAN port statistics
- [MistCircuitStats-Redis](https://github.com/jmorrison-juniper/MistCircuitStats-Redis) - Redis-cached version
