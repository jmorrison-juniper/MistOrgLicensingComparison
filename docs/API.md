# API reference

The Flask application provides the following routes. JSON endpoints return a `success` flag and either `data` or an error message. Mist-backed endpoints require `MIST_API_TOKEN`.

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Render the comparison dashboard. |
| `GET` | `/health` | Return application health. |
| `GET` | `/api/organizations` | List organizations accessible to configured tokens. |
| `GET` | `/api/organization/<org_id>` | Get organization details. |
| `GET` | `/api/licenses/<org_id>` | Get the organization license summary. |
| `GET` | `/api/license-usage/<org_id>` | Get license usage by site. |
| `GET` | `/api/inventory/<org_id>` | Get organization inventory counts. |
| `POST` | `/api/compare` | Compare organizations and return license and inventory data. |

The compare request body is a JSON object containing a non-empty list of organization IDs:

```json
{
  "org_ids": ["organization-id-1", "organization-id-2"]
}
```

The response data contains one result per requested organization. A per-organization retrieval failure is represented in that result's `error` field; the request can still return other organizations' results.

The application uses these Mist API operations:

| Mist endpoint | Purpose |
| --- | --- |
| `GET /api/v1/self` | Validate the token and retrieve user information. |
| `GET /api/v1/orgs/{org_id}` | Retrieve organization details. |
| `GET /api/v1/orgs/{org_id}/licenses` | Retrieve license summary, entitlements, and amendments. |
| `GET /api/v1/orgs/{org_id}/licenses/usages` | Retrieve license usage by site. |
| `GET /api/v1/orgs/{org_id}/inventory` | Retrieve organization inventory. |
| `GET /api/v1/orgs/{org_id}/inventory/count` | Retrieve inventory counts by device type. |
