# Troubleshooting Guide

This guide covers common issues and their solutions. If you don't find your issue here, please [open a GitHub issue](https://github.com/dstmrk/kanso/issues).

---

## Installation Issues

### Docker Won't Start

**Symptom**: `docker compose up` fails or container keeps restarting.

**Solutions**:

1. **Check Docker is running**:
   ```bash
   docker info
   ```
   If this fails, start Docker Desktop (macOS/Windows) or the Docker service (Linux).

2. **Check port availability**:
   ```bash
   # Check if port 9525 is in use
   lsof -i :9525  # macOS/Linux
   netstat -an | findstr 9525  # Windows
   ```
   If in use, change the port in `docker-compose.yml`:
   ```yaml
   ports:
     - "8080:9525"  # Use port 8080 instead
   ```

3. **View container logs**:
   ```bash
   docker compose logs -f kanso
   ```

4. **Rebuild from scratch**:
   ```bash
   docker compose down -v
   docker compose pull
   docker compose up -d
   ```

---

### Application Won't Load in Browser

**Symptom**: Browser shows "connection refused" or blank page at `localhost:9525`.

**Solutions**:

1. **Verify container is running**:
   ```bash
   docker ps
   ```
   Look for `kanso` in the output.

2. **Check correct URL**: Make sure you're using `http://` not `https://`:
   ```
   http://localhost:9525  ✅
   https://localhost:9525 ❌
   ```

3. **Try different browser**: Clear cache or use incognito mode.

4. **Wait for startup**: The app needs a few seconds to start. Check logs:
   ```bash
   docker compose logs -f kanso
   ```
   Look for "NiceGUI is running on http://0.0.0.0:9525".

---

## Google Sheets Connection Issues

### "Invalid Credentials" Error

**Symptom**: Connection test fails with "Invalid credentials" message.

**Solutions**:

1. **Verify JSON structure**:
   - Must contain `"type": "service_account"`
   - Must have `client_email`, `private_key`, `project_id`

2. **Check JSON formatting**:
   - No trailing commas
   - No extra whitespace in keys
   - Copy the entire JSON file content

3. **Regenerate credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts)
   - Select your service account
   - Keys → Add Key → Create new key → JSON
   - Use the new JSON file

---

### "Spreadsheet Not Found" Error

**Symptom**: Credentials work but Kanso can't find your sheet.

**Solutions**:

1. **Share the spreadsheet**:
   - Open your Google Sheet
   - Click "Share" button
   - Add your service account email (from JSON: `client_email`)
   - Give "Viewer" or "Editor" permission

2. **Use correct URL format**:
   ```
   ✅ https://docs.google.com/spreadsheets/d/SHEET_ID/edit
   ✅ https://docs.google.com/spreadsheets/d/SHEET_ID/
   ❌ https://sheets.google.com/...  (wrong domain)
   ```

3. **Check sheet ID**:
   The ID is the long string in the URL between `/d/` and `/edit`.

---

### "API Error" or Rate Limiting

**Symptom**: Dashboard shows API errors or data doesn't load.

**Solutions**:

1. **Wait and retry**: Google API has rate limits. Wait a few minutes.

2. **Check API quotas**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - APIs & Services → Google Sheets API → Quotas
   - Verify you haven't exceeded limits

3. **Enable the Sheets API**:
   - APIs & Services → Library
   - Search "Google Sheets API"
   - Click "Enable"

---

## Data Display Issues

### Dashboard Shows No Data

**Symptom**: Dashboard loads but shows empty charts or "No data".

**Solutions**:

1. **Check sheet names**: Kanso expects these exact worksheet names:
   - `Assets`
   - `Liabilities`
   - `Expenses`
   - `Incomes`

2. **Verify data format**:
   - First row must be headers
   - Date column format: `YYYY-MM` (e.g., `2024-01`)
   - Amount format: Currency symbol + number (e.g., `€ 1.000,50`)

3. **Refresh data manually**:
   - Go to Settings → Data tab
   - Click "Refresh Data"

4. **Clear cache**:
   - Go to Settings → Data tab
   - Update configuration to force cache refresh

---

### Charts Not Rendering

**Symptom**: Charts show loading spinners indefinitely or are blank.

**Solutions**:

1. **Check browser console**:
   - Press F12 (Developer Tools)
   - Look for JavaScript errors in Console tab

2. **Try different browser**: Some older browsers may have compatibility issues.

3. **Verify data types**: Ensure amounts are numbers (not text).

4. **Check date range**: Make sure you have data for multiple months.

---

### Wrong Currency Display

**Symptom**: Numbers show wrong currency symbol or format.

**Solutions**:

1. **Set currency in Settings**:
   - Go to Settings → Account tab
   - Select your preferred currency

2. **Check data format in Google Sheets**:
   - Amounts should include currency symbol (e.g., `€ 500`)
   - Or be plain numbers if currency is set in Kanso

---

## Performance Issues

### Slow Loading Times

**Symptom**: Dashboard takes a long time to load.

**Solutions**:

1. **Check network connection**: Slow internet affects Google Sheets API calls.

2. **Reduce data volume**: Very large spreadsheets (thousands of rows) may be slow.

3. **Use refresh wisely**: Don't refresh data unnecessarily. Kanso caches data for 24 hours.

4. **Check Docker resources**:
   ```bash
   docker stats kanso
   ```
   If memory/CPU is maxed, allocate more resources to Docker.

---

### Browser Freezing

**Symptom**: Browser becomes unresponsive when using Kanso.

**Solutions**:

1. **Reduce data range**: If you have many years of data, consider archiving old data.

2. **Close other tabs**: Free up browser memory.

3. **Update browser**: Use latest version of Chrome, Firefox, Safari, or Edge.

---

## Settings Issues

### Changes Not Saving

**Symptom**: Settings revert after page refresh.

**Solutions**:

1. **Check browser storage**:
   - Ensure cookies/localStorage are enabled
   - Try incognito mode to rule out extensions

2. **Clear browser data**:
   - Clear cookies and site data for `localhost:9525`
   - Refresh and reconfigure

3. **Check volume permissions** (Docker):
   ```bash
   ls -la ./kanso-data
   ```
   Ensure the directory is writable.

---

### Theme Not Switching

**Symptom**: Dark/light mode toggle doesn't work.

**Solutions**:

1. **Hard refresh**: Press Ctrl+Shift+R (Cmd+Shift+R on Mac).

2. **Clear localStorage**:
   - Open Developer Tools (F12)
   - Application tab → Local Storage
   - Clear all entries for `localhost:9525`

---

## Quick Add Issues

### Expense Not Saving

**Symptom**: Quick Add form shows error when saving.

**Solutions**:

1. **Check all required fields**:
   - Merchant: Cannot be empty
   - Amount: Must be a positive number
   - Category: Must be selected
   - Type: Must be selected

2. **Verify Google Sheets permissions**:
   - Service account needs "Editor" access to save data
   - "Viewer" access is read-only

3. **Check sheet structure**:
   - Expenses sheet must exist with correct headers:
     `Date | Merchant | Amount | Category | Type`

---

## Getting Help

If you've tried these solutions and still have issues:

1. **Check existing issues**: [GitHub Issues](https://github.com/dstmrk/kanso/issues)

2. **Open a new issue** with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Browser and OS version
   - Docker logs if applicable (`docker compose logs kanso`)

3. **Ask in discussions**: [GitHub Discussions](https://github.com/dstmrk/kanso/discussions)

---

## Common Error Messages

| Error Message | Likely Cause | Solution |
|--------------|--------------|----------|
| "Please add your Google credentials in Settings" | No credentials configured | Go to Settings → Data → Add credentials |
| "Invalid JSON" | Malformed credentials JSON | Copy entire JSON file, check for typos |
| "Invalid Google Sheets URL" | Wrong URL format | Use full spreadsheet URL with `/d/SHEET_ID/` |
| "Could not connect to Google Sheets" | Network or API issue | Check internet, verify API is enabled |
| "Worksheet not found" | Wrong sheet name | Rename sheets to: Assets, Liabilities, Expenses, Incomes |
| "Could not read data" | Wrong data format | Check date and amount formats |

---

**Still stuck?** Don't hesitate to [open an issue](https://github.com/dstmrk/kanso/issues). We're here to help!
