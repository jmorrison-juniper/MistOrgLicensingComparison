# User guide

## Overview

The dashboard loads the organizations accessible to the configured Mist API token or tokens. Select one or more organizations and choose **Compare Selected** to load license and device inventory data. The comparison includes totals and summary cards.

### Compare organizations

1. Select the organizations to compare, or choose **Select All**.
2. Choose **Compare Selected**.
3. Review device counts and license usage/entitlement values. License column tooltips describe supported license types.
4. Choose **Export CSV** to download the displayed comparison.

Organization and license data are requested when a comparison is run. A failed inventory request is reported as an error rather than being represented as zero devices.

### Add a manual organization

Choose **Add Manual Org** to add a row for an organization that is not available through the Mist API token. Enter its name, device counts, and license values. License values accept `usage/entitled` (for example, `8/10`) or a single number. Manual values are included in the totals and CSV export.

### Calculate remaining licenses

After comparing organizations, enter the purchased count for each license type in **Purchased Licenses (Optional)** and choose **Calculate Remaining**. The remaining value is purchased licenses minus the total entitled licenses in the displayed comparison. A negative value indicates that entitlements exceed the purchased amount entered.

The **SUB-AI** bundle contributes one each to SUB-MAN, SUB-VNA, SUB-AST, SUB-ENG, and SUB-PMA. Enter the purchased SUB-AI count separately; it is included in the calculations for those five component types.

### Supported license types

License types documented in the Juniper Mist Management Guide:

- Wireless: `SUB-MAN`, `SUB-VNA`, `SUB-AST`, `SUB-ENG`, `SUB-PMA`, and the `SUB-AI` bundle.
- Wired: `SUB-EX12`, `SUB-EX24`, `SUB-EX48`, `SUB-EX-VNA`, and `SUB-SVNA`.
- WAN: `SUB-WAN` and `SUB-WVNA`.
- Mist Edge: `SUB-ME`.
- Access Assurance: `S-CLIENT-S` and `S-CLIENT-A`.

The application may also encounter `SUB-SSR`, `SUB-SPRM2`, and `SUB-WAN1` through `SUB-WAN5` in API responses. These are marked as undocumented/inferred in the UI; confirm their meaning with Juniper before relying on them.

## Example screens

These screenshots are from the application template and JavaScript running locally with synthetic responses substituted for the API. They contain no real organization or account data.

![Organization selection and license comparison](screenshots/license-comparison.png)

![Manual organization entry](screenshots/manual-organization.png)

![Purchased and remaining license totals](screenshots/remaining-licenses.png)
