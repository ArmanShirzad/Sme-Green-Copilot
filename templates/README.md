# Form Templates Directory

Place PDF form templates here for ingestion into the system.

## Expected Templates

1. **VSME Snapshot** (`vsme_snapshot.pdf`)
   - CSRD VSME standard form
   - Download from: https://www.efrag.org/sites/default/files/sites/webpublishing/SiteAssets/VSME%20Standard.pdf

2. **GDPR Art.30 Record** (`gdpr_art30_record.pdf`)
   - No official form exists; create template with fields:
     - Controller details
     - Processing purposes
     - Data categories
     - Recipients
     - Retention periods
     - Security measures

3. **EU AI Act Risk Worksheet** (`ai_act_risk_worksheet.pdf`)
   - Risk assessment template
   - Reference: https://artificialintelligenceact.eu

4. **German Energy Audit** (`energy_audit_de.pdf`)
   - BAFA guidelines structure
   - Download from: https://www.bafa.de/SharedDocs/Downloads/EN/Energy/ea_guidelines.pdf

## Ingestion

To ingest a template:

```bash
python ingest.py templates/your_form.pdf form_id form_name form_type
```

Example:
```bash
python ingest.py templates/vsme_snapshot.pdf vsme_snapshot "CSRD VSME Snapshot" csrd
```
