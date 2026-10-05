# Deployment guide

## Requirements

- Python 3.13 for local development, or a container runtime.
- A Mist API token with access to the organizations to compare.

## Run locally

```bash
git clone https://github.com/jmorrison-juniper/MistOrgLicensingComparison.git
cd MistOrgLicensingComparison
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
cp .env.example .env
# Edit .env and set MIST_API_TOKEN.
python app.py
```

Open `http://127.0.0.1:5000`. The application listens on `127.0.0.1` by default. Set `FLASK_RUN_HOST=0.0.0.0` if it must listen on all interfaces, and restrict network access appropriately.

## Run in a container

Build the image:

```bash
podman build -t mist-licensing .
```

Create a local `.env` from `.env.example`, set the token, then start the app:

```bash
podman compose up -d
```

Docker can also be used with the included Dockerfile and Compose configuration. For a direct run, pass the token through the container environment rather than placing it in an image:

```bash
podman run --rm -p 5000:5000 --env-file .env mist-licensing
```

The image is built for `linux/amd64` and `linux/arm64`, including Apple Silicon and ARM-based cloud hosts. The container runs as a non-root user. The build workflow delegates to the shared [misthelper-devtools](https://github.com/jmorrison-juniper/misthelper-devtools) container workflow.

## Configuration

Set values in `.env` for local runs or in the container environment for deployments.

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `MIST_API_TOKEN` | Yes | — | Mist API token; use comma-separated tokens to combine access from multiple accounts. |
| `MIST_ORG_ID` | No | Auto-detected | Default organization ID. |
| `MIST_HOST` | No | `api.mist.com` | Mist API host/region. |
| `PORT` | No | `5000` | Flask development server port. |
| `FLASK_RUN_HOST` | No | `127.0.0.1` | Address used by `python app.py`. |
| `LOG_LEVEL` | No | `INFO` | Python logging level. |

For multiple Mist accounts, set `MIST_API_TOKEN=token1,token2`. Accessible organizations are aggregated and deduplicated. Keep tokens out of source control and container image layers.

## Health check

`GET /health` returns HTTP 200 and `{"status":"healthy"}` when the Flask process is responding.
