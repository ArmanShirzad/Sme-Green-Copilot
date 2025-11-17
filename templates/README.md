# Templates Directory

This directory contains PDF templates for compliance forms.

## Downloaded Templates

1. **vsme_standard.pdf** - VSME Standard for CSRD (EFRAG)
   - Source: https://www.efrag.org/sites/default/files/sites/webpublishing/SiteAssets/VSME%20Standard.pdf
   - Status: ✅ Downloaded (1.6MB, 66 pages)

2. **vsme_explanatory_note_may2025.pdf** - VSME Explanatory Note (May 2025)
   - Source: https://xbrl.efrag.org/downloads/vsme/VSME-Digital-Template-and-XBRL-Taxonomy-Explanatory-Note-May-2025.pdf
   - Status: ✅ Downloaded (847KB, 23 pages)

3. **bafa_energy_audit_guidelines.pdf** - German Energie Audit Guidelines (BAFA)
   - Source: https://www.bafa.de/SharedDocs/Downloads/EN/Energy/ea_guidelines.pdf
   - Status: ✅ Downloaded (748KB, 23 pages)

## Templates to Create

The following templates need to be created using the `create_templates.py` script when the virtual environment is activated:

1. **gdpr_art30_record.pdf** - GDPR Article 30 Record of Processing Activities
2. **gdpr_dpia_template.pdf** - DPIA Template (GDPR Article 35)
3. **ai_act_risk_worksheet.pdf** - EU AI Act Risk Classification Worksheet
4. **vsme_snapshot.pdf** - VSME CSRD Snapshot (simplified template)

## Creating Templates

After setting up the virtual environment and installing dependencies:

```bash
# Activate virtual environment
source green-agent-env/bin/activate

# Run template creation script
python create_templates.py
```

This will generate the PDF templates using ReportLab.

## Template Usage

These templates are used by the ingestion pipeline (`ingest.py`) for semantic field mapping. After creating the templates, ingest them:

```bash
python ingest.py templates/gdpr_art30_record.pdf gdpr_art30 "GDPR Article 30 Record"
python ingest.py templates/gdpr_dpia_template.pdf gdpr_dpia "GDPR DPIA Template"
python ingest.py templates/ai_act_risk_worksheet.pdf ai_act_risk "EU AI Act Risk Worksheet"
python ingest.py templates/vsme_snapshot.pdf vsme_snapshot "VSME CSRD Snapshot"
```

