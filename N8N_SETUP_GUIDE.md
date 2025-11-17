# n8n Workflow Setup Guide

## Overview

This guide helps you set up n8n workflows for the Green SME Compliance Co-Pilot to handle:
1. **Email Delivery** - Send compliance PDFs via email
2. **File Storage** - Store files to MinIO (optional)
3. **Audit Logging** - Log submissions to database (optional)

## Prerequisites

1. n8n installed and running
   ```bash
   npm install -g n8n
   n8n start
   ```
2. Access n8n at: http://localhost:5678
3. SMTP email credentials (Gmail, SendGrid, etc.)

## Workflow 1: Email Compliance Documents

### Purpose
Send filled PDF forms and compliance packs via email with attachments.

### Step-by-Step Setup

#### Step 1: Create New Workflow
1. Open n8n at http://localhost:5678
2. Click **"Add workflow"**
3. Name it: **"Compliance Email Sender"**

#### Step 2: Add Webhook Trigger
1. Click **"+"** to add node
2. Search for **"Webhook"**
3. Select **"Webhook"** node
4. Configure:
   - **HTTP Method**: `POST`
   - **Path**: `compliance-email`
   - **Response Mode**: `Last Node`
   - **Authentication**: None (or add if needed)
5. Click **"Listen for Test Event"** to activate
6. **Copy the webhook URL** (e.g., `http://localhost:5678/webhook/compliance-email`)
7. Add this URL to your `.env` file:
   ```
   N8N_WEBHOOK_URL=http://localhost:5678/webhook/compliance-email
   ```

#### Step 3: Add Read Binary File Node
1. Add new node: **"Read Binary File"**
2. Connect Webhook → Read Binary File
3. Configure:
   - **File Path**: `{{ $json.filePath }}`
   - This reads the file from the path sent by FastAPI

#### Step 4: Add Email Node (SMTP)
1. Add new node: **"Email Send (SMTP)"**
2. Connect Read Binary File → Email Send
3. Configure SMTP:
   - **Host**: Your SMTP server
     - Gmail: `smtp.gmail.com`
     - SendGrid: `smtp.sendgrid.net`
     - Outlook: `smtp-mail.outlook.com`
   - **Port**: 
     - Gmail: `587` (TLS) or `465` (SSL)
     - SendGrid: `587`
   - **User**: Your email address
   - **Password**: Your email password or app password
   - **Secure**: `TLS` or `SSL` (depending on port)
4. Configure Email:
   - **From Email**: `{{ $json.recipient }}` or your sender email
   - **To Email**: `{{ $json.recipient }}`
   - **Subject**: `{{ $json.subject }}` or `Compliance Document - {{ $now.toFormat('yyyy-MM-dd') }}`
   - **Email Type**: `HTML`
   - **Message**: 
     ```html
     <p>{{ $json.body }}</p>
     <p>Generated on: {{ $now.toFormat('yyyy-MM-dd HH:mm:ss') }}</p>
     ```
   - **Attachments**: 
     - **Name**: `{{ $json.filePath.split('/').pop() }}`
     - **Data**: `{{ $binary.data }}`
     - **Type**: `application/pdf`

#### Step 5: Add Respond to Webhook Node
1. Add new node: **"Respond to Webhook"**
2. Connect Email Send → Respond to Webhook
3. Configure:
   - **Response Code**: `200`
   - **Response Body**: 
     ```json
     {
       "status": "sent",
       "recipient": "{{ $json.recipient }}",
       "timestamp": "{{ $now.toISO() }}"
     }
     ```

#### Step 6: Save and Activate
1. Click **"Save"** (top right)
2. Toggle **"Active"** switch (top right)
3. Workflow is now live!

### Testing the Workflow

Test from your FastAPI:
```bash
curl -X POST http://localhost:8000/tools/emailFile \
  -H "Content-Type: application/json" \
  -d '{
    "filePath": "outputs/compliance_pack_1.pdf",
    "recipient": "your-email@example.com"
  }'
```

---

## Workflow 2: File Storage to MinIO (Optional)

### Purpose
Store compliance documents to MinIO object storage for backup/archival.

### Setup

#### Step 1: Create New Workflow
- Name: **"Compliance File Storage"**

#### Step 2: Add Webhook
- Path: `compliance-store`
- Method: `POST`

#### Step 3: Add HTTP Request Node
1. Add **"HTTP Request"** node
2. Configure:
   - **Method**: `PUT`
   - **URL**: `{{ $env.MINIO_URL }}/compliance/{{ $json.filePath.split('/').pop() }}`
   - **Authentication**: `Generic Credential Type`
   - **User**: `{{ $env.MINIO_ACCESS_KEY }}`
   - **Password**: `{{ $env.MINIO_SECRET_KEY }}`
   - **Body**: Read file binary data
   - **Headers**:
     - `Content-Type`: `application/pdf`

#### Step 4: Add Response Node
- Return success status

---

## Workflow 3: Audit Logging (Optional)

### Purpose
Log all compliance submissions to database for audit trail.

### Setup

#### Step 1: Create New Workflow
- Name: **"Compliance Audit Log"**

#### Step 2: Add Webhook
- Path: `compliance-audit`
- Method: `POST`

#### Step 3: Add Code Node
1. Add **"Code"** node
2. Write SQLite insert:
   ```javascript
   const sqlite3 = require('sqlite3').verbose();
   const db = new sqlite3.Database(process.env.DB_PATH || 'db.sqlite');
   
   const submission = $input.item.json;
   
   db.run(
     `INSERT INTO Submission (userId, intent, selected_forms, answers, files, status, audit_trail)
      VALUES (?, ?, ?, ?, ?, ?, ?)`,
     [
       1, // userId
       submission.intent || 'unknown',
       JSON.stringify(submission.forms || []),
       JSON.stringify(submission.answers || {}),
       submission.filePath,
       'completed',
       JSON.stringify({ timestamp: new Date().toISOString(), action: 'email_sent' })
     ],
     function(err) {
       if (err) {
         console.error(err);
         return { error: err.message };
       }
       return { success: true, id: this.lastID };
     }
   );
   ```

#### Step 4: Add Response Node
- Return audit log confirmation

---

## Complete Workflow: Email + Storage + Audit

### Combined Workflow Structure

```
Webhook (POST /compliance-email)
  ↓
Read Binary File (from filePath)
  ↓
Split into 3 parallel branches:
  ├─→ Email Send (SMTP)
  ├─→ HTTP Request (MinIO storage) [optional]
  └─→ Code (Audit log) [optional]
  ↓
Merge results
  ↓
Respond to Webhook (200 OK)
```

### Setup Steps

1. **Webhook Node** (as above)
2. **Read Binary File** (as above)
3. **Split Node** - Add **"Split In Batches"** or use **"IF"** nodes
4. **Three parallel branches**:
   - Email (required)
   - MinIO storage (optional)
   - Audit log (optional)
5. **Merge Node** - Add **"Merge"** node to combine results
6. **Respond to Webhook** - Return combined status

---

## Quick Setup: Simple Email Workflow

### Minimal Configuration (5 minutes)

1. **Webhook**:
   - Path: `compliance-email`
   - Method: `POST`

2. **Read Binary File**:
   - File Path: `{{ $json.filePath }}`

3. **Email Send (SMTP)**:
   - **Gmail Example**:
     - Host: `smtp.gmail.com`
     - Port: `587`
     - User: `your-email@gmail.com`
     - Password: `your-app-password` (not regular password!)
     - Secure: `TLS`
   - To: `{{ $json.recipient }}`
   - Subject: `{{ $json.subject || 'Compliance Document' }}`
   - Message: `{{ $json.body || 'Please find attached your compliance document.' }}`
   - Attachments: Use binary data from Read Binary File node

4. **Respond to Webhook**:
   - Response Code: `200`
   - Response Body: `{ "status": "sent" }`

5. **Save & Activate**

---

## Gmail App Password Setup

If using Gmail, you need an App Password:

1. Go to Google Account: https://myaccount.google.com/
2. Security → 2-Step Verification (enable if not enabled)
3. App Passwords → Generate
4. Select "Mail" and "Other (Custom name)"
5. Name it: "n8n Compliance"
6. Copy the 16-character password
7. Use this in n8n Email node (not your regular password)

---

## Testing

### Test from Terminal:
```bash
# Test email workflow
curl -X POST http://localhost:5678/webhook/compliance-email \
  -H "Content-Type: application/json" \
  -d '{
    "filePath": "outputs/test.pdf",
    "recipient": "test@example.com",
    "subject": "Test Compliance Document",
    "body": "This is a test email with compliance document."
  }'
```

### Test from FastAPI:
```bash
curl -X POST http://localhost:8000/tools/emailFile \
  -H "Content-Type: application/json" \
  -d '{
    "filePath": "outputs/compliance_pack_1.pdf",
    "recipient": "your-email@example.com"
  }'
```

---

## Troubleshooting

### Issue: Webhook not receiving requests
- **Solution**: Make sure workflow is **Active** (toggle switch)
- Check webhook URL matches `.env` file
- Verify n8n is running on port 5678

### Issue: File not found
- **Solution**: Ensure `filePath` is absolute or relative to n8n working directory
- Check file exists at the specified path
- Use absolute paths: `/full/path/to/outputs/file.pdf`

### Issue: Email not sending
- **Solution**: 
  - Verify SMTP credentials
  - Check firewall allows port 587/465
  - For Gmail, use App Password (not regular password)
  - Check spam folder

### Issue: Attachment not working
- **Solution**: 
  - Ensure Read Binary File node is connected before Email node
  - Use `{{ $binary.data }}` in Email attachments
  - Set attachment type to `application/pdf`

---

## Environment Variables for n8n

Add to n8n environment (Settings → Environment Variables):

```
MINIO_URL=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
DB_PATH=/path/to/db.sqlite
```

---

## Next Steps

1. Set up the simple email workflow first
2. Test with a real PDF file
3. Add MinIO storage if needed
4. Add audit logging for compliance tracking
5. Customize email templates for different document types

---

## Workflow Export (JSON)

Once configured, you can export your workflow as JSON for backup or sharing:
1. Click workflow menu (three dots)
2. Select "Download"
3. Save the JSON file

To import later:
1. Click "+" → "Import from File"
2. Select your JSON file

