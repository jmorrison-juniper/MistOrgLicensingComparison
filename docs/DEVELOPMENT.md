# Development guide

## Project layout

```text
app.py                 Flask application and JSON endpoints
mist_connection.py     Mist API integration
templates/index.html   Single-page comparison interface
tests/                 Offline Python and frontend tests
.github/workflows/     Build, test, and quality workflows
```

## Install development dependencies

Use Python 3.13 and Node.js 24. Install the pinned development tools:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.lock.txt
```

## Tests and quality checks

```bash
python -m unittest discover -s tests -v
node --test tests/frontend.test.cjs
ruff check app.py mist_connection.py tests
black --check app.py mist_connection.py tests
mypy app.py mist_connection.py
bandit -r app.py mist_connection.py -ll
pip-audit --disable-pip --no-deps -r requirements.lock.txt
```

The Python tests mock the Mist SDK and HTTP transport. Frontend tests execute the inline application script against a stub DOM. These tests require no Mist credentials and make no live Mist API calls. Coverage includes HTTP errors, malformed comparison requests, partial results, multi-token organization selection, device counts, SDK compatibility, SUB-AI bundles, manual counts, and CSV export.

## Dependency refresh

The runtime and development manifests pin direct dependencies; their lock files pin resolved dependencies. After changing a manifest, refresh the corresponding lock in a clean Python 3.13 environment:

```bash
python -m pip install -r requirements.txt
python -m pip freeze > requirements.lock.txt
python -m pip install -r requirements-dev.txt
python -m pip freeze > requirements-dev.lock.txt
```

Compare resolved dependencies on Linux and macOS. Keep Linux-only keyring dependencies in both locks with `sys_platform == "linux"` markers. Run the offline tests and quality checks before merging a refresh.

The container and offline test workflow use the runtime lock; shared quality gates install the development manifest. Bootstrap 5.3.8 and Bootstrap Icons 1.13.1 are loaded from jsDelivr. The shared workflows are pinned to the `misthelper-devtools` v0.6.2 release. Gunicorn's unused management socket is disabled because the non-root container user has no writable home directory.

## CI and releases

GitHub Actions runs offline tests, shared quality gates, and the CodeQL analysis, and it builds/publishes multi-architecture images to `ghcr.io/jmorrison-juniper/mistorglicensingcomparison`. The build workflow calls the pinned shared container workflow. Dependabot tracks action and shared workflow pins.

Release tags use `YY.MM.DD.HH.MM` format. Create an annotated tag with release notes to trigger the release build.

## Contributing

1. Fork the repository and create a feature branch.
2. Make a focused change and add or update offline tests.
3. Run the relevant tests and quality checks.
4. Submit a pull request.

## License and related projects

This project is licensed under [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](../LICENSE).

- [MistCircuitStats](https://github.com/jmorrison-juniper/MistCircuitStats): Mist Gateway WAN port statistics.
- [MistCircuitStats-Redis](https://github.com/jmorrison-juniper/MistCircuitStats-Redis): Redis-cached version.
