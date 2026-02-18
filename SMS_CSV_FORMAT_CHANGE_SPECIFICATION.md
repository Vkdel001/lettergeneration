# SMS CSV Format Change - Specification Document

**Document Version:** 1.0  
**Date:** February 18, 2026  
**Status:** Pending Approval  
**Author:** Kiro AI Assistant

---

## 📋 Executive Summary

This document specifies the changes required to modify the SMS CSV file format from the current generic format to a new format that includes detailed customer information with a more professional SMS message template.

**IMPORTANT:** No code changes will be made without explicit approval.

---

## 🎯 Objective

Change the SMS CSV file format to provide:
1. Sequential numbering (SN)
2. Separate surname and first name columns
3. National ID (NID) column
4. More detailed and professional SMS message text
5. Dynamic arrears amount and date in the message

---

## 📊 Format Comparison

### **Current Format (6 columns):**

| Column | Example Value |
|--------|---------------|
| Mobile | 57942004 |
| Message | Dear Mr Haulkhory, your NICL arrears notice is ready. View: https://nicl.ink/d68vcw Password: Your National ID (no spaces) Valid 30 days \| Help: 602-3315 |
| ShortURL | https://nicl.ink/d68vcw |
| Policy | 00840/0000511 |
| CustomerName | Mr Sheik Waajeeb Noorani Haulkhory |
| Status | Ready |

### **New Format (6 columns):**

| Column | Example Value |
|--------|---------------|
| SN | 1 |
| Surname | Haulkhory |
| First Name | Sheik Waajeeb Noorani |
| NID | 1 |
| Mobile No | 57942004 |
| Message Text | Valued Client, your Life Policy 00840/0000511 is in arrears for an amount of MUR 1,025.00 as at January 2026. View Details : https://nicl.ink/d68vcw Password: Your National ID. Thank you - NIC Team Tel 602 3315 for info. |

---

## 🔍 Detailed Column Specifications

### **Column 1: SN (Serial Number)**
- **Type:** Integer
- **Format:** Sequential numbering starting from 1
- **Source:** Row index + 1
- **Example:** 1, 2, 3, 4, ...

### **Column 2: Surname**
- **Type:** Text
- **Format:** Last name only
- **Source:** Excel column `Owner 1 Surname`
- **Example:** "Haulkhory", "Abacousnac", "Smith"
- **Handling:** 
  - If empty: Use "Unknown"
  - Trim whitespace
  - Preserve original case

### **Column 3: First Name**
- **Type:** Text
- **Format:** Title + First Name + Middle Names (if any)
- **Source:** Excel columns `Owner 1 Title` + `Owner 1 First Name`
- **Example:** "Mr Sheik Waajeeb Noorani", "Mrs Jane Marie"
- **Handling:**
  - Combine Title and First Name with space
  - If Title is empty, use First Name only
  - If both empty: Use "Valued Client"
  - Trim whitespace

### **Column 4: NID**
- **Type:** Text (Numeric)
- **Format:** Hardcoded value "1"
- **Source:** Hardcoded constant (NOT from Excel)
- **Example:** "1" (always)
- **Handling:**
  - Always use the value "1" for all records
  - This is a fixed value, not extracted from Excel
  - **IMPORTANT:** Do NOT use the actual National ID from Excel column `NIC`

### **Column 5: Mobile No**
- **Type:** Text (Numeric)
- **Format:** Mobile number without country code
- **Source:** Excel column `MOBILE_NO`
- **Example:** "57942004", "57123456"
- **Handling:**
  - Remove any spaces or special characters
  - Keep only digits
  - If empty: Skip this record (don't include in CSV)

### **Column 6: Message Text**
- **Type:** Text
- **Format:** Professional SMS message with dynamic data
- **Template:** See Message Template section below
- **Max Length:** ~160 characters (single SMS) or up to 459 characters (3 SMS segments)

---

## 📱 Message Template Specification

### **Template Structure:**

```
Valued Client, your {PolicyType} Policy {PolicyNo} is in arrears for an amount of MUR {ArrearsAmount} as at {Month} {Year}. View Details : {ShortURL} Password: Your National ID. Thank you - NIC Team Tel 602 3315 for info.
```

### **Dynamic Fields:**

#### **1. PolicyType**
- **Source:** Template type from folder name or template parameter
- **Mapping:**
  - `SPH` → "Life"
  - `JPH` → "Life"
  - `MED_SPH` → "Health"
  - `MED_JPH` → "Health"
  - `Company` → "Company"
- **Example:** "Life", "Health", "Company"

#### **2. PolicyNo**
- **Source:** Excel column `Policy No`
- **Format:** As-is from Excel (e.g., "00840/0000511")
- **Example:** "00208/0001662", "00840/0000511"

#### **3. ArrearsAmount**
- **Source:** Excel column `Arrears Amount`
- **Format:** "MUR X,XXX.XX" (with thousand separators and 2 decimal places)
- **Example:** "MUR 1,025.00", "MUR 2,774.80"
- **Handling:**
  - Format with comma as thousand separator
  - Always show 2 decimal places
  - If empty or 0: Use "MUR 0.00"

#### **4. Month**
- **Source:** Excel column `Arrears Processing Date`
- **Format:** Full month name (e.g., "January", "February")
- **Example:** "January", "December"
- **Handling:**
  - Extract month from date
  - If date is empty: Use current month

#### **5. Year**
- **Source:** Excel column `Arrears Processing Date`
- **Format:** 4-digit year (e.g., "2026")
- **Example:** "2026", "2025"
- **Handling:**
  - Extract year from date
  - If date is empty: Use current year

#### **6. ShortURL**
- **Source:** Generated short URL (nicl.ink)
- **Format:** "https://nicl.ink/xxxxxx"
- **Example:** "https://nicl.ink/d68vcw"

---

## 📝 Message Examples

### **Example 1: Life Insurance (SPH)**
```
Valued Client, your Life Policy 00208/0001662 is in arrears for an amount of MUR 1,025.00 as at January 2026. View Details : https://nicl.ink/d68vcw Password: Your National ID. Thank you - NIC Team Tel 602 3315 for info.
```

**Character count:** ~210 characters (2 SMS segments)

### **Example 2: Health Insurance (MED_SPH)**
```
Valued Client, your Health Policy 00840/0000511 is in arrears for an amount of MUR 2,774.80 as at February 2026. View Details : https://nicl.ink/abc123 Password: Your National ID. Thank you - NIC Team Tel 602 3315 for info.
```

**Character count:** ~212 characters (2 SMS segments)

### **Example 3: Company Insurance**
```
Valued Client, your Company Policy 00920/0001234 is in arrears for an amount of MUR 5,500.00 as at January 2026. View Details : https://nicl.ink/xyz789 Password: Your National ID. Thank you - NIC Team Tel 602 3315 for info.
```

**Character count:** ~213 characters (2 SMS segments)

---

## 🔧 Technical Implementation

### **File to Modify:**

**Primary File:** `generate_sms_links.py`

**Function to Modify:** `save_sms_csv()` and SMS data preparation section

---

### **Current Code (Lines ~456-467):**

```python
# Create SMS message
customer_title = row.get('Owner 1 Title', '')
customer_surname = row.get('Owner 1 Surname', '')
name_for_sms = f"{customer_title} {customer_surname}".strip() if customer_surname else letter_data['customerName']

sms_text = f"Dear {name_for_sms}, your NICL arrears notice is ready. View: {short_url} Password: Your National ID (no spaces) Valid 30 days | Help: 602-3315"

# Prepare SMS data
sms_data.append({
    'Mobile': mobile,
    'Message': sms_text,
    'ShortURL': short_url,
    'Policy': policy_no,
    'CustomerName': letter_data['customerName'],
    'Status': 'Ready'
})
```

---

### **Proposed New Code:**

```python
# Extract customer details for new CSV format
customer_title = str(row.get('Owner 1 Title', '')).strip() if pd.notna(row.get('Owner 1 Title', '')) else ''
customer_first_name = str(row.get('Owner 1 First Name', '')).strip() if pd.notna(row.get('Owner 1 First Name', '')) else ''
customer_surname = str(row.get('Owner 1 Surname', '')).strip() if pd.notna(row.get('Owner 1 Surname', '')) else 'Unknown'

# Build first name (Title + First Name)
first_name_combined = f"{customer_title} {customer_first_name}".strip() if customer_first_name else customer_title
if not first_name_combined:
    first_name_combined = "Valued Client"

# Extract NIC - HARDCODED VALUE
nic = "1"  # Always use "1" as per requirement (not from Excel)

# Extract arrears amount
arrears_amount = float(row.get('Arrears Amount', 0)) if pd.notna(row.get('Arrears Amount', 0)) else 0.0
arrears_formatted = f"MUR {arrears_amount:,.2f}"

# Extract and format date
arrears_date_raw = row.get('Arrears Processing Date', '')
if arrears_date_raw and pd.notna(arrears_date_raw):
    try:
        if isinstance(arrears_date_raw, (int, float)):
            date_obj = pd.to_datetime(arrears_date_raw, origin='1899-12-30', unit='D')
        else:
            date_obj = pd.to_datetime(arrears_date_raw, dayfirst=True)
        month_name = date_obj.strftime('%B')  # Full month name
        year = date_obj.strftime('%Y')        # 4-digit year
    except:
        month_name = datetime.now().strftime('%B')
        year = datetime.now().strftime('%Y')
else:
    month_name = datetime.now().strftime('%B')
    year = datetime.now().strftime('%Y')

# Determine policy type from template
policy_type_map = {
    'SPH': 'Life',
    'JPH': 'Life',
    'MED_SPH': 'Health',
    'MED_JPH': 'Health',
    'Company': 'Company'
}
policy_type = policy_type_map.get(template_type, 'Life')

# Create new SMS message format
sms_text = f"Valued Client, your {policy_type} Policy {policy_no} is in arrears for an amount of {arrears_formatted} as at {month_name} {year}. View Details : {short_url} Password: Your National ID. Thank you - NIC Team Tel 602 3315 for info."

# Prepare SMS data with new format
sms_data.append({
    'SN': index + 1,                    # Sequential number
    'Surname': customer_surname,        # Last name only
    'First Name': first_name_combined,  # Title + First Name
    'NID': nic,                         # National ID
    'Mobile No': mobile,                # Mobile number
    'Message Text': sms_text            # New message format
})
```

---

### **Function: `save_sms_csv()` - No Changes Required**

The `save_sms_csv()` function automatically uses the dictionary keys as column headers, so it will work with the new format without modification:

```python
def save_sms_csv(sms_data, output_folder):
    """Save SMS bulk file as CSV"""
    letter_links_dir = os.path.join("letter_links", output_folder)
    os.makedirs(letter_links_dir, exist_ok=True)
    
    csv_file = os.path.join(letter_links_dir, "sms_batch.csv")
    
    # Create DataFrame and save as CSV
    df = pd.DataFrame(sms_data)
    df.to_csv(csv_file, index=False, encoding='utf-8')
    
    return csv_file
```

This function will automatically create columns based on the dictionary keys in `sms_data`.

---

## 📂 Files to Modify

| File | Lines to Change | Change Type | Estimated Lines |
|------|-----------------|-------------|-----------------|
| `generate_sms_links.py` | ~456-467 | Replace SMS data preparation | ~50 lines |

**Total Files:** 1 file  
**Total Lines Changed:** ~50 lines

---

## 🧪 Testing Requirements

### **Test Cases:**

#### **1. Basic Functionality Test**
- Generate SMS links for a small dataset (10 records)
- Verify CSV has correct columns: SN, Surname, First Name, NID, Mobile No, Message Text
- Verify sequential numbering (1, 2, 3, ...)
- Verify all data is populated correctly

#### **2. Data Extraction Test**
- Test with records having all fields populated
- Test with records missing optional fields (Title, First Name)
- Test with records missing NIC
- Verify fallback values work correctly

#### **3. Message Format Test**
- Verify policy type is correct (Life/Health/Company)
- Verify arrears amount formatting (comma separator, 2 decimals)
- Verify date extraction (month name and year)
- Verify short URL is included
- Verify message length is reasonable (< 300 characters)

#### **4. Template Type Test**
- Test with SPH template → "Life Policy"
- Test with JPH template → "Life Policy"
- Test with MED_SPH template → "Health Policy"
- Test with MED_JPH template → "Health Policy"
- Test with Company template → "Company Policy"

#### **4. Edge Cases Test**
- Empty surname → Should use "Unknown"
- Empty first name and title → Should use "Valued Client"
- NID → Should always be "1" (hardcoded)
- Empty arrears amount → Should use "MUR 0.00"
- Invalid date → Should use current month/year

---

## 📊 Sample Output Comparison

### **Before (Current Format):**

```csv
Mobile,Message,ShortURL,Policy,CustomerName,Status
57942004,"Dear Mr Haulkhory, your NICL arrears notice is ready. View: https://nicl.ink/d68vcw Password: Your National ID (no spaces) Valid 30 days | Help: 602-3315",https://nicl.ink/d68vcw,00840/0000511,Mr Sheik Waajeeb Noorani Haulkhory,Ready
```

### **After (New Format):**

```csv
SN,Surname,First Name,NID,Mobile No,Message Text
1,Haulkhory,Mr Sheik Waajeeb Noorani,1,57942004,"Valued Client, your Life Policy 00840/0000511 is in arrears for an amount of MUR 1,025.00 as at January 2026. View Details : https://nicl.ink/d68vcw Password: Your National ID. Thank you - NIC Team Tel 602 3315 for info."
```

---

## 🔍 Data Mapping Reference

### **Excel Columns Used:**

| Excel Column | CSV Column | Processing |
|--------------|------------|------------|
| Row Index | SN | index + 1 |
| Owner 1 Surname | Surname | Direct, fallback "Unknown" |
| Owner 1 Title + Owner 1 First Name | First Name | Combined, fallback "Valued Client" |
| (Hardcoded) | NID | Always "1" |
| MOBILE_NO | Mobile No | Direct |
| Policy No | Message Text (embedded) | Direct |
| Arrears Amount | Message Text (embedded) | Format: "MUR X,XXX.XX" |
| Arrears Processing Date | Message Text (embedded) | Extract month name and year |
| Template Type | Message Text (embedded) | Map to policy type |
| Generated Short URL | Message Text (embedded) | Direct |

---

## ⚠️ Important Considerations

### **1. Message Length**
- Current message: ~210-220 characters
- SMS cost: 2 SMS segments per message
- Consider if message needs to be shorter for cost savings

### **2. Character Encoding**
- CSV should use UTF-8 encoding to support special characters
- Test with names containing accents (é, è, ê, etc.)

### **3. Backward Compatibility**
- Old SMS CSV files will have different format
- Systems reading the CSV may need updates
- Consider keeping old format as backup option

### **4. Excel Column Dependencies**
- Requires `Owner 1 Surname` column
- Requires `Owner 1 First Name` column
- Requires `Arrears Amount` column
- Requires `Arrears Processing Date` column
- **Note:** NID column is hardcoded as "1" (not from Excel)

If any of these columns are missing, the script should handle gracefully with fallback values.

---

## 📋 Implementation Checklist

Before implementation:

- [ ] Review and approve the new CSV format
- [ ] Review and approve the new SMS message template
- [ ] Confirm column names are correct
- [ ] Confirm message template wording is correct
- [ ] Confirm policy type mapping is correct
- [ ] Confirm fallback values are acceptable
- [ ] Confirm character encoding (UTF-8) is acceptable
- [ ] Test with sample data
- [ ] Verify SMS gateway accepts new format
- [ ] Update any downstream systems that read the CSV

---

## 🚀 Deployment Plan

### **Phase 1: Development & Testing**
1. Implement changes in `generate_sms_links.py`
2. Test locally with sample data
3. Verify CSV format matches specification
4. Verify message text is correct
5. Test with different templates (SPH, JPH, MED, Company)

### **Phase 2: Staging Deployment**
1. Deploy to staging environment
2. Generate SMS links for test folder
3. Verify CSV format
4. Test with SMS gateway (if applicable)
5. Get user acceptance

### **Phase 3: Production Deployment**
1. Backup current `generate_sms_links.py`
2. Deploy new version
3. Test with one real folder
4. Monitor for issues
5. Full rollout if successful

---

## 🔄 Rollback Plan

If issues arise:

```bash
# Restore previous version
git checkout HEAD~1 generate_sms_links.py

# Or restore from backup
cp generate_sms_links.py.backup generate_sms_links.py

# Restart server if needed
pm2 restart all
```

---

## ✅ Approval Required

**This specification requires approval before implementation.**

Please review:
1. New CSV column structure
2. New SMS message template
3. Data mapping and fallback values
4. Message length and SMS cost implications

**Once approved, implementation will proceed with the exact specifications outlined in this document.**

---

**Document Status:** Awaiting Approval  
**Next Step:** Review and approve specification before code changes
