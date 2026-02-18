# SMS CSV File Generation - How It Works

## 📋 Overview

The SMS link generation system reads the **same Excel file** used for PDF generation and creates a CSV file with SMS messages containing custom short URLs (nicl.ink).

## 🔄 Data Flow Process

```
Excel File (Generic_Template.xlsx)
    ↓
Read by generate_sms_links.py
    ↓
Process each row (customer)
    ↓
Generate unique ID + short URL
    ↓
Create SMS message text
    ↓
Collect all SMS data
    ↓
Save as CSV file (sms_batch.csv)
```

## 📊 Step-by-Step Explanation

### Step 1: Excel File Location
The script searches for the Excel file in this priority order:

1. **Folder-specific file** (PRIORITY): `{output_folder}_source.xlsx`
   - Example: `output_sph_December2025_source.xlsx`
   
2. **Legacy location**: `{output_folder}.xlsx`

3. **Current file**: `Generic_Template.xlsx`

4. **Temp uploads**: `temp_uploads/Generic_Template.xlsx`

5. **Backup files**: `Generic_Template_backup_*.xlsx`

### Step 2: Read Excel Data
```python
df = pd.read_excel(file_path, engine='openpyxl')
```

The script reads ALL rows from the Excel file, same data used for PDF generation.

### Step 3: Process Each Row
For each row in the Excel file:

```python
for index, row in df.iterrows():
    # Extract data from Excel columns
    mobile = row.get('MOBILE_NO', '')
    policy_no = row.get('Policy No', '')
    customer_title = row.get('Owner 1 Title', '')
    customer_surname = row.get('Owner 1 Surname', '')
    customer_name = build_full_name(row)  # Combines Title + First + Surname
```

### Step 4: Generate Unique ID
```python
unique_id = generate_unique_id(policy_no, index)
# Creates: 16-character hash like "7e89984128160d9b"
```

This ID is used to:
- Create the letter viewer URL
- Store letter data as JSON file

### Step 5: Create Short URL
```python
long_url = f"{base_url}/letter/{unique_id}"
# Example: https://arrears.niclmauritius.site/letter/7e89984128160d9b

short_url = create_short_url(long_url)
# Creates: https://nicl.ink/abc123 (6-character ID)
```

### Step 6: Build SMS Message
```python
name_for_sms = f"{customer_title} {customer_surname}".strip()
# Example: "Mr Ramricha"

sms_text = f"Dear {name_for_sms}, your NICL arrears notice is ready. View online: {short_url} Valid for 30 days."
# Example: "Dear Mr Ramricha, your NICL arrears notice is ready. View online: https://nicl.ink/abc123 Valid for 30 days."
```

### Step 7: Collect SMS Data
For each valid row (has mobile number and policy number), the script creates a dictionary:

```python
sms_data.append({
    'Mobile': mobile,              # From Excel: MOBILE_NO column
    'Message': sms_text,           # Generated SMS message
    'ShortURL': short_url,         # Custom nicl.ink short URL
    'Policy': policy_no,           # From Excel: Policy No column
    'CustomerName': customer_name, # Built from Title + First + Surname
    'Status': 'Ready'              # Always "Ready"
})
```

### Step 8: Save as CSV
```python
df = pd.DataFrame(sms_data)
df.to_csv(csv_file, index=False, encoding='utf-8')
```

Creates CSV file at: `letter_links/{output_folder}/sms_batch.csv`

## 📄 CSV File Structure

The generated CSV file has these columns:

| Column | Source | Example |
|--------|--------|---------|
| **Mobile** | Excel: `MOBILE_NO` | 57123456 |
| **Message** | Generated | "Dear Mr Ramricha, your NICL arrears notice is ready..." |
| **ShortURL** | Generated | https://nicl.ink/abc123 |
| **Policy** | Excel: `Policy No` | 00920/0000893 |
| **CustomerName** | Excel: `Owner 1 Title` + `First Name` + `Surname` | MR BHOOSAN RAMRICHA |
| **Status** | Fixed value | Ready |

## 🔍 Excel Columns Used

The script reads these columns from your Excel file:

### Required Columns:
- `MOBILE_NO` - Customer mobile number (MUST have value)
- `Policy No` - Policy number (MUST have value)

### Name Columns:
- `Owner 1 Title` - Mr, Mrs, Ms, etc.
- `Owner 1 First Name` - First name
- `Owner 1 Surname` - Last name

### Address Columns (for letter viewer):
- `Owner 1 Policy Address 1`
- `Owner 1 Policy Address 2`
- `Owner 1 Policy Address 3`
- `Owner 1 Policy Address 4`

### Policy Details (for letter viewer):
- `Arrears Amount` - Amount owed
- `Frequency` - Payment frequency
- `Computed Gross Premium` - Premium amount
- `Arrears Processing Date` - Date for letter
- `NIC` - National ID (for QR code)

## ⚠️ Skipped Rows

Rows are skipped if:
1. **No mobile number**: `MOBILE_NO` is empty or "nan"
2. **No policy number**: `Policy No` is empty or "nan"

Example output:
```
[SMS] Skipping row 45: No mobile number
[SMS] Skipping row 127: No policy number
```

## 📁 Output Files Created

For each SMS generation, these files are created:

### 1. CSV File (Main Output)
```
letter_links/output_sph_December2025/sms_batch.csv
```
Contains all SMS messages ready to send

### 2. JSON Files (One per customer)
```
letter_links/output_sph_December2025/7e89984128160d9b.json
letter_links/output_sph_December2025/a3f8c2d1e5b9f4a7.json
...
```
Contains full letter data for web viewer

### 3. Status File
```
letter_links/output_sph_December2025/status.json
```
Contains generation metadata (timestamp, counts, etc.)

## 🔗 URL Mapping Storage

Short URLs are stored in:
```
url_mappings.json
```

Example content:
```json
{
  "abc123": {
    "url": "https://arrears.niclmauritius.site/letter/7e89984128160d9b",
    "created": "2026-01-04T13:07:10.458Z",
    "expires": "2026-02-03T13:07:10.470Z",
    "clicks": 0,
    "active": true
  }
}
```

## 📊 Example Data Flow

### Input (Excel Row):
```
Policy No: 00920/0000893
Owner 1 Title: MR
Owner 1 First Name: BHOOSAN
Owner 1 Surname: RAMRICHA
MOBILE_NO: 57123456
Arrears Amount: 439.17
```

### Processing:
1. Generate unique ID: `7e89984128160d9b`
2. Create long URL: `https://arrears.niclmauritius.site/letter/7e89984128160d9b`
3. Create short URL: `https://nicl.ink/abc123`
4. Build SMS: "Dear MR RAMRICHA, your NICL arrears notice is ready. View online: https://nicl.ink/abc123 Valid for 30 days."

### Output (CSV Row):
```csv
Mobile,Message,ShortURL,Policy,CustomerName,Status
57123456,"Dear MR RAMRICHA, your NICL arrears notice is ready. View online: https://nicl.ink/abc123 Valid for 30 days.",https://nicl.ink/abc123,00920/0000893,MR BHOOSAN RAMRICHA,Ready
```

## 🎯 Key Points

1. **Same Excel file**: Uses the exact same file as PDF generation
2. **One row = One SMS**: Each Excel row generates one SMS message
3. **Automatic skipping**: Rows without mobile/policy are skipped automatically
4. **Custom URLs**: Each customer gets a unique nicl.ink short URL
5. **30-day validity**: Links expire after 30 days
6. **CSV format**: Ready to import into SMS gateway systems

## 📱 SMS Message Format

The SMS message follows this template:
```
Dear {Title} {Surname}, your NICL arrears notice is ready. View online: {short_url} Valid for 30 days.
```

**Character count**: Approximately 100-120 characters (fits in single SMS)

## 🔄 Regeneration Behavior

When you regenerate SMS links for the same folder:
1. **Clears old links**: Deletes existing `letter_links/{folder}` directory
2. **Creates fresh links**: Generates new unique IDs and short URLs
3. **Overwrites CSV**: Creates new `sms_batch.csv` file
4. **Updates mappings**: Adds new short URLs to `url_mappings.json`

---

**Summary**: The SMS CSV file is generated by reading your Excel file, processing each row to create a unique short URL, and saving all SMS messages in a CSV format ready for bulk SMS sending.