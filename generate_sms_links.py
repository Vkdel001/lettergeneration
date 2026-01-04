#!/usr/bin/env python3
"""
SMS Link Generation Script
Generates unique web links for customer letters and creates SMS bulk files.
This is an additional feature that works alongside existing PDF generation.
"""

import pandas as pd
import json
import os
import sys
import argparse
import hashlib
import requests
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

def generate_unique_id(policy_no, index, timestamp=None):
    """Generate a unique, non-guessable identifier for the letter"""
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    # Combine policy number, index, timestamp, and random component for uniqueness
    data = f"{policy_no}-{index}-{timestamp}-{os.urandom(8).hex()}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]

def create_short_url(long_url):
    """Create custom short URL using nicl.ink domain"""
    import json
    import random
    import string
    from datetime import datetime, timedelta
    
    # Generate unique 6-character short ID (lowercase + digits)
    chars = string.ascii_lowercase + string.digits
    short_id = ''.join(random.choice(chars) for _ in range(6))
    
    # Load existing mappings
    try:
        with open('url_mappings.json', 'r') as f:
            mappings = json.load(f)
    except FileNotFoundError:
        mappings = {}
    
    # Ensure unique ID (retry if collision)
    attempts = 0
    while short_id in mappings and attempts < 10:
        short_id = ''.join(random.choice(chars) for _ in range(6))
        attempts += 1
    
    if attempts >= 10:
        print(f"[WARNING] Could not generate unique short ID after 10 attempts")
        # Fallback to longer ID
        short_id = ''.join(random.choice(chars) for _ in range(8))
    
    # Store mapping
    mappings[short_id] = {
        "url": long_url,
        "created": datetime.now().isoformat(),
        "expires": (datetime.now() + timedelta(days=30)).isoformat(),
        "clicks": 0,
        "active": True
    }
    
    # Save mappings
    try:
        with open('url_mappings.json', 'w') as f:
            json.dump(mappings, f, indent=2)
        print(f"[SMS] Created short URL: https://nicl.ink/{short_id} -> {long_url}")
    except Exception as e:
        print(f"[SMS] Error saving URL mapping: {e}")
        # Fallback to original URL if storage fails
        return long_url
    
    return f"https://nicl.ink/{short_id}"

def generate_qr_code_for_customer(policy_no, mobile_no, customer_name, nic):
    """Generate QR code for customer payment"""
    try:
        # Validate required fields
        if not policy_no or str(policy_no).strip().lower() in ['nan', 'none', '']:
            print(f"[SMS] QR generation skipped: Missing policy number")
            return None
            
        if not mobile_no or str(mobile_no).strip().lower() in ['nan', 'none', '']:
            print(f"[SMS] QR generation skipped for {policy_no}: Missing mobile number")
            return None
            
        if not customer_name or str(customer_name).strip().lower() in ['nan', 'none', 'name_missing']:
            print(f"[SMS] QR generation skipped for {policy_no}: Missing customer name")
            return None
            
        if not nic or str(nic).strip().lower() in ['nan', 'none', '']:
            print(f"[SMS] QR generation skipped for {policy_no}: Missing NIC")
            return None
        
        print(f"[SMS] Generating QR code for {policy_no} - Mobile: {mobile_no}, NIC: {nic}, Name: {customer_name}")
        
        # Use same API as PDF generation
        payload = {
            "MerchantId": 151,
            "SetTransactionAmount": False,
            "TransactionAmount": 0,
            "SetConvenienceIndicatorTip": False,
            "ConvenienceIndicatorTip": 0,
            "SetConvenienceFeeFixed": False,
            "ConvenienceFeeFixed": 0,
            "SetConvenienceFeePercentage": False,
            "ConvenienceFeePercentage": 0,
            "SetAdditionalBillNumber": True,
            "AdditionalRequiredBillNumber": False,
            "AdditionalBillNumber": str(policy_no.replace('/', '.')),
            "SetAdditionalMobileNo": True,
            "AdditionalRequiredMobileNo": False,
            "AdditionalMobileNo": str(mobile_no),
            "SetAdditionalStoreLabel": False,
            "AdditionalRequiredStoreLabel": False,
            "AdditionalStoreLabel": "",
            "SetAdditionalLoyaltyNumber": False,
            "AdditionalRequiredLoyaltyNumber": False,
            "AdditionalLoyaltyNumber": "",
            "SetAdditionalReferenceLabel": False,
            "AdditionalRequiredReferenceLabel": False,
            "AdditionalReferenceLabel": "",
            "SetAdditionalCustomerLabel": True,
            "AdditionalRequiredCustomerLabel": False,
            "AdditionalCustomerLabel": str(customer_name),
            "SetAdditionalTerminalLabel": False,
            "AdditionalRequiredTerminalLabel": False,
            "AdditionalTerminalLabel": "",
            "SetAdditionalPurposeTransaction": True,
            "AdditionalRequiredPurposeTransaction": False,
            "AdditionalPurposeTransaction": str(nic)
        }
        
        response = requests.post(
            "https://api.zwennpay.com:9425/api/v1.0/Common/GetMerchantQR",
            headers={"accept": "text/plain", "Content-Type": "application/json"},
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            qr_data = str(response.text).strip()
            if qr_data and qr_data.lower() not in ('null', 'none', 'nan'):
                print(f"[SMS] QR code generated successfully for policy {policy_no}")
                return qr_data
            else:
                print(f"[SMS] QR API returned invalid data for {policy_no}: '{qr_data}'")
                return None
        else:
            print(f"[SMS] QR API failed for {policy_no}: HTTP {response.status_code} - {response.text}")
            return None
        
    except Exception as e:
        print(f"[SMS] QR generation failed for {policy_no}: {e}")
        return None

def extract_letter_data(row, index, template_type):
    """Extract letter content data from Excel row"""
    
    # Build customer name safely
    name_parts = []
    if pd.notna(row.get('Owner 1 Title', '')) and str(row.get('Owner 1 Title', '')).strip().lower() not in ['nan', '']:
        name_parts.append(str(row.get('Owner 1 Title', '')).strip())
    if pd.notna(row.get('Owner 1 First Name', '')) and str(row.get('Owner 1 First Name', '')).strip().lower() not in ['nan', '']:
        name_parts.append(str(row.get('Owner 1 First Name', '')).strip())
    if pd.notna(row.get('Owner 1 Surname', '')) and str(row.get('Owner 1 Surname', '')).strip().lower() not in ['nan', '']:
        name_parts.append(str(row.get('Owner 1 Surname', '')).strip())
    
    customer_name = ' '.join(name_parts) if name_parts else 'Name_Missing'
    
    # Build address
    address_lines = []
    for addr_field in ['Owner 1 Policy Address 1', 'Owner 1 Policy Address 2', 'Owner 1 Policy Address 3', 'Owner 1 Policy Address 4']:
        if pd.notna(row.get(addr_field, '')) and str(row.get(addr_field, '')).strip():
            address_lines.append(str(row.get(addr_field, '')).strip())
    
    # Process date
    arrears_date_raw = row.get('Arrears Processing Date', '')
    if arrears_date_raw and pd.notna(arrears_date_raw):
        try:
            if isinstance(arrears_date_raw, (int, float)):
                date_obj = pd.to_datetime(arrears_date_raw, origin='1899-12-30', unit='D')
            else:
                date_obj = pd.to_datetime(arrears_date_raw, dayfirst=True)
            arrears_date_formatted = date_obj.strftime('%d-%B-%Y')
        except:
            today = datetime.now()
            first_day_current_month = today.replace(day=1)
            last_day_previous_month = first_day_current_month - timedelta(days=1)
            arrears_date_formatted = last_day_previous_month.strftime('%d %B %Y')
    else:
        today = datetime.now()
        first_day_current_month = today.replace(day=1)
        last_day_previous_month = first_day_current_month - timedelta(days=1)
        arrears_date_formatted = last_day_previous_month.strftime('%d %B %Y')
    
    # Extract policy details
    policy_no = str(row.get('Policy No', '')) if pd.notna(row.get('Policy No', '')) else ''
    arrears_amount = float(row.get('Arrears Amount', 0)) if pd.notna(row.get('Arrears Amount', 0)) else 0.0
    frequency = str(row.get('Frequency', '')) if pd.notna(row.get('Frequency', '')) else ''
    gross_premium = float(row.get('Computed Gross Premium', 0)) if pd.notna(row.get('Computed Gross Premium', 0)) else 0.0
    mobile_no = str(row.get('MOBILE_NO', '')) if pd.notna(row.get('MOBILE_NO', '')) else ''
    nic = str(row.get('NIC', '')) if pd.notna(row.get('NIC', '')) else ''
    
    # Generate QR code for payment
    qr_code_data = generate_qr_code_for_customer(policy_no, mobile_no, customer_name, nic)
    
    # If QR generation failed, try with minimal data (like PDF generation does)
    if not qr_code_data and policy_no:
        print(f"[SMS] Retrying QR generation with minimal data for {policy_no}")
        # Try with just policy number and a default mobile if available
        fallback_mobile = mobile_no if mobile_no and str(mobile_no).strip().lower() not in ['nan', 'none', ''] else "57000000"
        fallback_nic = nic if nic and str(nic).strip().lower() not in ['nan', 'none', ''] else "A0000000000000"
        fallback_name = customer_name if customer_name != 'Name_Missing' else "Customer"
        
        qr_code_data = generate_qr_code_for_customer(policy_no, fallback_mobile, fallback_name, fallback_nic)
    
    # Template-specific content
    if template_type == 'SPH':
        subject = "RE: ARREARS ON YOUR LIFE INSURANCE POLICY"
        letter_type = "Life Insurance"
        body_intro = "At NIC, we value the trust you have placed in us to protect what matters most— your financial future & that of your loved ones. We are writing to remind you that your life insurance policy shows a premium amount in arrears as shown below:"
    elif template_type in ['MED_SPH', 'MED_JPH']:
        subject = "RE: FIRST NOTICE ARREARS ON HEALTH INSURANCE POLICY"
        letter_type = "Health Insurance"
        body_intro = "We are writing to you with regards to the aforementioned Insurance Policy and we have noticed that there remains an outstanding amount due."
    elif template_type == 'JPH':
        subject = "RE: ARREARS ON YOUR LIFE INSURANCE POLICY"
        letter_type = "Life Insurance"
        body_intro = "At NIC, we value the trust you have placed in us to protect what matters most— your financial future & that of your loved ones. We are writing to remind you that your life insurance policy shows a premium amount in arrears as shown below:"
    elif template_type == 'Company':
        subject = "RE: ARREARS ON YOUR COMPANY INSURANCE POLICY"
        letter_type = "Company Insurance"
        body_intro = "We are writing to inform you about the outstanding premium on your company insurance policy."
    else:
        subject = "RE: ARREARS ON YOUR INSURANCE POLICY"
        letter_type = "Insurance"
        body_intro = "We are writing to remind you about the outstanding premium on your insurance policy."
    
    return {
        "customerName": customer_name,
        "policyNo": policy_no,
        "mobileNo": mobile_no,
        "nic": nic,
        "date": arrears_date_formatted,
        "address": address_lines,
        "salutation": f"Dear {customer_name},",
        "subject": subject,
        "letterType": letter_type,
        "bodyIntro": body_intro,
        "policyDetails": {
            "policyNo": policy_no,
            "premium": f"MUR {gross_premium:,.2f}",
            "frequency": frequency,
            "arrearsAmount": f"MUR {arrears_amount:,.2f}"
        },
        "templateType": template_type,
        "qrCodeData": qr_code_data,
        "rowIndex": index
    }

def save_letter_json(unique_id, letter_data, output_folder):
    """Save individual letter data as JSON file"""
    letter_links_dir = os.path.join("letter_links", output_folder)
    os.makedirs(letter_links_dir, exist_ok=True)
    
    # Add metadata
    letter_data.update({
        "id": unique_id,
        "createdAt": datetime.now().isoformat(),
        "expiresAt": (datetime.now() + timedelta(days=30)).isoformat(),
        "accessCount": 0,
        "maxAccess": 10,
        "isActive": True
    })
    
    json_file = os.path.join(letter_links_dir, f"{unique_id}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(letter_data, f, indent=2, ensure_ascii=False)
    
    return json_file

def save_sms_csv(sms_data, output_folder):
    """Save SMS bulk file as CSV"""
    letter_links_dir = os.path.join("letter_links", output_folder)
    os.makedirs(letter_links_dir, exist_ok=True)
    
    csv_file = os.path.join(letter_links_dir, "sms_batch.csv")
    
    # Create DataFrame and save as CSV
    df = pd.DataFrame(sms_data)
    df.to_csv(csv_file, index=False, encoding='utf-8')
    
    return csv_file

def generate_sms_links_for_folder(output_folder, template_type, base_url="https://your-domain.com"):
    """Generate SMS links for all customers in an output folder"""
    
    print(f"[SMS] Starting SMS link generation for folder: {output_folder}")
    print(f"[SMS] Template type: {template_type}")
    
    # IMPORTANT: Clear existing SMS links before generating new ones
    letter_links_dir = os.path.join("letter_links", output_folder)
    if os.path.exists(letter_links_dir):
        print(f"[SMS] Clearing existing SMS links in {letter_links_dir}")
        try:
            import shutil
            shutil.rmtree(letter_links_dir)
            print(f"[SMS] Successfully cleared existing SMS links")
        except Exception as e:
            print(f"[SMS] Warning: Could not clear existing SMS links: {e}")
    
    # Recreate the directory
    os.makedirs(letter_links_dir, exist_ok=True)
    
    # Load Excel file (enhanced logic to find folder-specific files first)
    possible_files = [
        f"{output_folder}_source.xlsx",             # Folder-specific source file
        f"{output_folder}.xlsx",                    # Folder-named file
        "Generic_Template.xlsx",                    # Current file
        "temp_uploads/Generic_Template.xlsx",       # Upload location
        "Generic_template.xlsx",                    # Case variation
        "temp_uploads/Generic_template.xlsx",       # Case variation in temp
        "Generic_Template_processed.xlsx",          # Processed file
        "temp_uploads/Generic_Template_processed.xlsx",  # Processed in temp
    ]
    
    # Also look for backup files (created during PDF generation)
    import glob
    backup_files = glob.glob("Generic_Template_backup_*.xlsx")
    debug_files = glob.glob("Generic_Template_debug_*.xlsx")
    
    # Add backup and debug files to search list
    possible_files.extend(backup_files)
    possible_files.extend(debug_files)
    
    # IMPORTANT: Also check if there's a folder-specific Excel file in the output folder itself
    folder_excel_files = []
    if os.path.exists(output_folder):
        try:
            folder_files = os.listdir(output_folder)
            folder_excel_files = [os.path.join(output_folder, f) for f in folder_files if f.endswith('.xlsx')]
            possible_files = folder_excel_files + possible_files  # Prioritize folder-specific files
        except Exception as e:
            print(f"[SMS] Could not scan folder {output_folder} for Excel files: {e}")
    
    print(f"[SMS] Searching for Excel file in {len(possible_files)} locations...")
    if folder_excel_files:
        print(f"[SMS] Found {len(folder_excel_files)} Excel files in output folder: {folder_excel_files}")
    
    df = None
    used_file = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            try:
                print(f"[SMS] Attempting to load: {file_path}")
                df = pd.read_excel(file_path, engine='openpyxl')
                
                # Validate the file has required columns
                required_cols = ['Policy No', 'Arrears Amount']
                available_cols = list(df.columns)
                missing_cols = [col for col in required_cols if col not in available_cols]
                
                if missing_cols:
                    print(f"[SMS] File {file_path} missing required columns: {missing_cols}")
                    continue
                
                if len(df) == 0:
                    print(f"[SMS] File {file_path} is empty")
                    continue
                
                used_file = file_path
                print(f"[SMS] Successfully loaded Excel file: {file_path} ({len(df)} rows)")
                print(f"[SMS] Available columns: {available_cols}")
                break
                
            except Exception as e:
                print(f"[SMS] Failed to load {file_path}: {e}")
                continue
    
    if df is None:
        print("[SMS] ERROR: No valid Excel file found!")
        print("[SMS] Searched locations:")
        for f in possible_files:
            exists = "✓" if os.path.exists(f) else "✗"
            print(f"[SMS]   {exists} {f}")
        print("[SMS] Please ensure the Excel file is available or regenerate PDFs")
        return 0
    
    # Check if PDFs exist in the output folder
    protected_folder = os.path.join(output_folder, "protected")
    unprotected_folder = os.path.join(output_folder, "unprotected")
    
    if not os.path.exists(protected_folder) and not os.path.exists(unprotected_folder):
        print(f"[SMS] ERROR: No PDF folders found in {output_folder}")
        print(f"[SMS] Please generate PDFs first before creating SMS links")
        return 0
    
    letter_links = []
    sms_data = []
    
    print(f"[SMS] Processing {len(df)} records...")
    
    for index, row in df.iterrows():
        try:
            # Extract customer data
            mobile = str(row.get('MOBILE_NO', '')).strip() if pd.notna(row.get('MOBILE_NO', '')) else ''
            policy_no = str(row.get('Policy No', '')) if pd.notna(row.get('Policy No', '')) else ''
            
            # Skip if no mobile number
            if not mobile or mobile.lower() in ['nan', 'none', '']:
                print(f"[SMS] Skipping row {index + 1}: No mobile number")
                continue
            
            # Skip if no policy number
            if not policy_no or policy_no.lower() in ['nan', 'none', '']:
                print(f"[SMS] Skipping row {index + 1}: No policy number")
                continue
            
            # Generate unique ID
            unique_id = generate_unique_id(policy_no, index)
            
            # Extract letter data
            letter_data = extract_letter_data(row, index, template_type)
            
            # Add PDF path information
            safe_policy = policy_no.replace('/', '_').replace('\\', '_')
            safe_name = letter_data['customerName'].replace(' ', '_').replace('/', '_').replace('\\', '_')
            
            # Use sequence number for PDF filename (matching PDF generation logic)
            pdf_filename = f"{index+1:03d}_{safe_policy}_{safe_name}.pdf"
            letter_data["pdfPath"] = f"/{output_folder}/protected/{pdf_filename}"
            
            # Save letter data as JSON
            json_file = save_letter_json(unique_id, letter_data, output_folder)
            
            # Generate URLs
            long_url = f"{base_url}/letter/{unique_id}"
            short_url = create_short_url(long_url)
            
            # Create SMS message
            customer_title = row.get('Owner 1 Title', '')
            customer_surname = row.get('Owner 1 Surname', '')
            name_for_sms = f"{customer_title} {customer_surname}".strip() if customer_surname else letter_data['customerName']
            
            sms_text = f"Dear {name_for_sms}, your NICL arrears notice is ready. View online: {short_url} Valid for 30 days."
            
            # Prepare SMS data
            sms_data.append({
                'Mobile': mobile,
                'Message': sms_text,
                'ShortURL': short_url,
                'Policy': policy_no,
                'CustomerName': letter_data['customerName'],
                'Status': 'Ready'
            })
            
            letter_links.append({
                'unique_id': unique_id,
                'policy_no': policy_no,
                'customer_name': letter_data['customerName'],
                'mobile': mobile,
                'long_url': long_url,
                'short_url': short_url
            })
            
            if (index + 1) % 50 == 0:
                print(f"[SMS] Processed {index + 1}/{len(df)} records...")
        
        except Exception as e:
            print(f"[SMS] Error processing row {index + 1}: {e}")
            continue
    
    # Save SMS bulk file
    if sms_data:
        csv_file = save_sms_csv(sms_data, output_folder)
        print(f"[SMS] SMS bulk file saved: {csv_file}")
        print(f"[SMS] Generated {len(sms_data)} SMS links successfully")
        
        # Print summary
        print(f"\n[SMS] SUMMARY:")
        print(f"[SMS] - Total records processed: {len(df)}")
        print(f"[SMS] - SMS links generated: {len(sms_data)}")
        print(f"[SMS] - JSON files created: {len(letter_links)}")
        print(f"[SMS] - SMS bulk file: {csv_file}")
        
        return len(sms_data)
    else:
        print("[SMS] No valid SMS data generated")
        return 0

def main():
    start_time = time.time()  # Track processing time for email notification
    
    parser = argparse.ArgumentParser(description='Generate SMS links for PDF letters')
    parser.add_argument('--folder', required=True, help='Output folder containing PDFs')
    parser.add_argument('--template', required=True, help='Template type (e.g., SPH_Fresh.py)')
    parser.add_argument('--base-url', default='https://your-domain.com', help='Base URL for letter viewer')
    
    args = parser.parse_args()
    
    # Extract template type from filename
    template_type = args.template.replace('.py', '').replace('_Fresh', '').replace('_Signature', '')
    
    try:
        links_generated = generate_sms_links_for_folder(args.folder, template_type, args.base_url)
        
        if links_generated > 0:
            print(f"\n[SMS] SUCCESS: Generated {links_generated} SMS links")
            
            # Send completion email notification
            try:
                # Get user email from environment or use a default
                user_email = os.getenv('USER_EMAIL', 'admin@niclmauritius.site')
                user_name = os.getenv('USER_NAME', 'NICL User')
                
                # Calculate processing time
                end_time = time.time()
                processing_time_seconds = int(end_time - start_time)
                processing_time = f"{processing_time_seconds // 60}m {processing_time_seconds % 60}s"
                
                # Send completion email
                email_cmd = [
                    'python', 'completion_email_service.py',
                    '--type', 'sms',
                    '--email', user_email,
                    '--name', user_name,
                    '--folder', args.folder,
                    '--count', str(links_generated),
                    '--time', processing_time,
                    '--template', template_type
                ]
                
                print(f"[EMAIL] Sending SMS completion notification to {user_email}...")
                email_result = subprocess.run(email_cmd, capture_output=True, text=True, timeout=30)
                
                if email_result.returncode == 0:
                    print(f"[EMAIL] ✅ SMS completion notification sent successfully")
                else:
                    print(f"[EMAIL] ⚠️ Failed to send SMS completion notification: {email_result.stderr}")
                    
            except Exception as e:
                print(f"[EMAIL] Warning: Could not send SMS completion notification: {e}")
            
            sys.exit(0)
        else:
            print(f"\n[SMS] ERROR: No SMS links generated")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[SMS] FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()