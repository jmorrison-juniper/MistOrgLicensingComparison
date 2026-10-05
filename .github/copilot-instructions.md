# MistOrgLicensingComparison agent instructions

This file holds the rules that apply to MistOrgLicensingComparison only. The rules that apply to each
repository of this owner are in `AGENTS.md` at the repository root. Read `AGENTS.md` first. This
file adds to it, and it does not hold a copy of a rule from it. Where the two files disagree, obey
`AGENTS.md` for a writing rule, a safety rule, or a security rule.

## What this repository is

This repository is a Flask web app for Juniper Mist administrators. It compares how organizations
use licenses, their device counts, and purchased license balances. The app reads Mist data through
its API and shows the results in a browser. The app runs with Python 3.13 or in a container for
Linux on amd64 or arm64.

## Language and environment

Use Python 3.13 for the app and Python tests. Use Node.js 24 for the frontend tests. The container
image uses Python 3.13. Follow the setup steps in `docs/DEVELOPMENT.md`. Install the packages from
`requirements-dev.lock.txt` for development. The runtime and development requirements have their
own lock files.

| Variable | Required | Default or use |
| - | - | - |
| `MIST_API_TOKEN` | Yes | One or more tokens, separated by commas. `MIST_APITOKEN` is a legacy fallback. |
| `MIST_ORG_ID` | No | The app uses the first organization from the token when this value is empty. |
| `MIST_HOST` | No | `api.mist.com` |
| `PORT` | No | `5000` |
| `FLASK_RUN_HOST` | No | `127.0.0.1` |
| `FLASK_DEBUG` | No | `false` |
| `LOG_LEVEL` | No | `INFO` |

## Local gates

Run each command from the repository root. The Python tests run without credentials. They use mock
responses and make no Mist API calls.

| Gate | Command | Expected result |
| - | - | - |
| Compile | `python -m compileall -q app.py mist_connection.py` | Exit code 0. |
| Lint | `ruff check app.py mist_connection.py tests` | No findings. |
| Format | `black --check app.py mist_connection.py tests` | No files need changes. |
| Types | `mypy app.py mist_connection.py` | No type findings. |
| Python tests | `python -m unittest discover -s tests -v` | All tests pass. |
| Frontend tests | `node --test tests/frontend.test.cjs` | All tests pass. |
| Security | `bandit -r app.py mist_connection.py -ll` | No findings. |
| Dependencies | `pip-audit --disable-pip --no-deps -r requirements.lock.txt` | No known vulnerabilities. |
| Complexity | `radon cc app.py mist_connection.py -j \| complexity-gate --max 15` | Each function is within the limit. |
| Dead code | `vulture app.py mist_connection.py --min-confidence 90 --ignore-decorators @app.route` | No findings. |
| STE with dictionary | `ste-linter --config .ste-linter.toml --min-score 80 README.md AGENTS.md .github/copilot-instructions.md` | Each file scores 80 or more. Confirm `dictionary: used`. |
| STE without dictionary | `ste-linter --config .ste-linter.toml --min-score 80 --dictionary /nonexistent README.md AGENTS.md .github/copilot-instructions.md` | Each file scores 80 or more. Confirm `dictionary: skipped`. |

## Architecture and conventions

`app.py` creates the module-level Flask app and its HTTP routes. `mist_connection.py` holds the
`MistConnection` class and calls the `mistapi` SDK.
`templates/index.html` holds the browser interface and its inline JavaScript. The page uses
Bootstrap 5.3.8, Bootstrap Icons 1.13.1, a dark theme, and the accent color `#E20074`.

| Route | Purpose |
| - | - |
| `GET /` | Show the comparison page. |
| `GET /health` | Return the process health status. |
| `GET /api/organizations` | List organizations for the configured tokens. |
| `GET /api/organization/<org_id>` | Return one organization's details. |
| `GET /api/licenses/<org_id>` | Return one organization's license summary. |
| `GET /api/license-usage/<org_id>` | Return site license data. |
| `GET /api/inventory/<org_id>` | Return physical device counts. |
| `POST /api/compare` | Compare the requested organizations. |

| SDK method | Purpose |
| - | - |
| `getSelf` | Check the configured token. |
| `getOrg` | Read organization data. |
| `getOrgLicensesSummary` | Read license data. |
| `getOrgLicensesBySite` | Read license use by site. |
| `countOrgInventory` | Read device counts. |

Each SDK response has `status_code` and `data`. The app reads `data` only when the status is 200.

`tests/test_app.py` and `tests/test_mist_connection.py` use mocked Mist responses.

`tests/frontend.test.cjs` runs the page script with a stub DOM. It blocks live API access.

The primary code files are `app.py`, `mist_connection.py`, and `templates/index.html`. The runtime
requirements and lock file are `requirements.txt` and `requirements.lock.txt`. The development
requirements and lock files are `requirements-dev.txt` and `requirements-dev.lock.txt`. The shared
quality workflow installs `requirements-dev.txt`.

## Safety in this repository

Keep Mist tokens in environment variables. For a local run, copy `.env.example` to `.env`. Git ignores
`.env`. Do not put a token in the source or container image.

Warning: anyone who can connect to port 5000 can use the app. Limit network access, because the app has
no sign-in page.

The page keeps manual organization and purchase values in browser memory. Export the table as a
CSV file to keep those values if you reload the page. The app does not write these values to a
database.

## Containers and ports

See `docs/DEPLOYMENT.md` for local Podman and Docker commands.
`docker-compose.yml` defines `web` and names its container `mist-licensing`.
It publishes host port 5000 to container port 5000. The image runs as `appuser`, not root.
The image supports `linux/amd64` and `linux/arm64`, including Apple Silicon hosts.
Offline tests do not start containers. This repository reserves no port range for container tests.

## Git and GitHub in this repository

Tags use the `YY.MM.DD.HH.MM` format. Create an annotated tag with release notes.
Push the tag with `git push origin <tag>` to start a release build.
The build workflow publishes images to
`ghcr.io/jmorrison-juniper/mistorglicensingcomparison`. It builds images for pushes to `main` and
version tags. A pull request build does not publish an image.
The repository has offline test, Python quality gate, container build, and stranded branch report
workflows. The stranded branch report runs each Monday at 07:00 UTC.

The repository has `documentation`, `python`, and `in-progress` labels. It has no scope labels, no
`auto-merge` label, no CodeQL workflow, no changelog, and no pull request template.

## Known pitfalls

- Pull request #16 fixed a Gunicorn 26 startup error. The container runs without root access. Keep
  `--no-control-socket` in the Dockerfile command.
- Pull request #16 fixed inventory errors that looked like zero devices. Keep the failed-request
  test in `tests/test_mist_connection.py`.

## Key files

| File | Purpose |
| - | - |
| `app.py` | Flask app and HTTP routes. |
| `mist_connection.py` | Mist API sessions and data retrieval. |
| `templates/index.html` | Browser interface, calculations, and CSV export. |
| `Dockerfile` | Container image and runtime command. |
| `docker-compose.yml` | Local container service and port mapping. |
| `docs/API.md` | App routes and Mist API operations. |
| `docs/DEVELOPMENT.md` | Development setup, tests, and quality checks. |
| `LICENSE` | Project license terms. |
| `tests/` | Offline Python and frontend tests. |

## External resources

The app calls the Juniper Mist API through the `mistapi` package. See `docs/API.md` for the
operations that the app uses. The `mistapi` package lists `python-dotenv>=1.1.0` as a dependency.
This repository has no context file for Spec Kit.
