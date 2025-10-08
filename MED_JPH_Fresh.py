# -*- coding: utf-8 -*-
# Import necessary libraries for data handling, HTTP requests, QR code generation, and PDF creation
import pandas as pd
import sys
import io
from datetime import datetime

# Set UTF-8 encoding for stdout to handle Unicode characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
import segno
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.colors import gray

import os
import re
from datetime import datetime
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfFileReader, PdfFileWriter

# Verify font files exist
cambria_regular_path = os.path.join(os.path.dirname(__file__), 'fonts', 'cambria.ttf')
cambria_bold_path = os.path.join(os.path.dirname(__file__), 'fonts', 'cambriab.ttf')

if not os.path.isfile(cambria_regular_path):
    raise FileNotFoundError(f"Font file not found: {cambria_regular_path}")
if not os.path.isfile(cambria_bold_path):
    raise FileNotFoundError(f"Font file not found: {cambria_bold_path}")

# Register Cambria fonts
try:
    pdfmetrics.registerFont(TTFont('Cambria', cambria_regular_path))
    pdfmetrics.registerFont(TTFont('Cambria-Bold', cambria_bold_path))
    print("[OK] Cambria (from cambria.ttf) and Cambria-Bold (from cambriab.ttf) fonts registered successfully")
except Exception as e:
    raise Exception(f"Failed to register fonts: {str(e)}")

# Read the Excel file containing policyholder data
# Robust Excel file loading with multiple fallback locations
def load_excel_file():
    """Load Excel file from multiple possible locations with error handling"""
    possible_files = [
        "Generic_Template.xlsx",  # Primary location (root)
        "temp_uploads/Generic_Template.xlsx",  # Server upload location
        "Generic_template.xlsx",  # Case variation
        "temp_uploads/Generic_template.xlsx",  # Case variation in temp
    ]
    
    # Also check for any .xlsx files in current directory as fallback
    import glob
    xlsx_files = glob.glob("*.xlsx")
    possible_files.extend(xlsx_files)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for f in possible_files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)
    
    print(f"[DEBUG] Looking for Excel file in these locations: {unique_files}")
    
    for file_path in unique_files:
        if os.path.exists(file_path):
            try:
                print(f"[INFO] Attempting to load: {file_path}")
                df = pd.read_excel(file_path, engine='openpyxl')
                
                # Validate the file has required columns
                required_cols = ['Policy No', 'Arrears Amount']
                available_cols = list(df.columns)
                missing_cols = [col for col in required_cols if col not in available_cols]
                
                if missing_cols:
                    print(f"[WARNING] File {file_path} missing required columns: {missing_cols}")
                    continue
                
                if len(df) == 0:
                    print(f"[WARNING] File {file_path} is empty")
                    continue
                
                print(f"[OK] Excel file loaded successfully from: {file_path}")
                print(f"[OK] Loaded {len(df)} rows with columns: {available_cols}")
                return df
                
            except Exception as e:
                print(f"[WARNING] Failed to load {file_path}: {str(e)}")
                continue
    
    # If we get here, no valid file was found
    print("[ERROR] No valid Excel file found!")
    print("[ERROR] Searched locations:")
    for f in unique_files:
        exists = "✓" if os.path.exists(f) else "✗"
        print(f"[ERROR]   {exists} {f}")
    
    print("[ERROR] Please ensure your Excel file is uploaded correctly")
    sys.exit(1)

# Load the Excel file using robust method
df = load_excel_file()

# Create a folder named 'output_letters' to store generated PDFs, if it doesn't already exist
os.makedirs("output_letters", exist_ok=True)

# Define custom paragraph styles explicitly
styles = {}

# Define custom 'BodyText' style for body paragraphs
styles['BodyText'] = ParagraphStyle(
    name='BodyText',
    fontName='Cambria',
    fontSize=10.5,
    leading=12,
    spaceAfter=6,
    alignment=TA_JUSTIFY
)

styles['disclaimerText'] = ParagraphStyle(
    name='disclaimerText',
    fontName='Cambria',
    fontSize=10.5,
    leading=10,
    spaceAfter=6,
    alignment=1,
    textColor=gray

)

# Define custom 'BoldText' style for headings
styles['BoldText'] = ParagraphStyle(
    name='BoldText',
    fontName='Cambria-Bold',
    fontSize=11,
    leading=13,
    spaceAfter=6
)

# Define custom 'SalutationText' style for the "Dear..." line and address
styles['SalutationText'] = ParagraphStyle(
    name='SalutationText',
    fontName='Cambria-Bold',
    fontSize=10.5,
    leading=6,
    spaceAfter=5
)

# Define custom 'FooterText' style for the absolute footer at the bottom
styles['FooterText'] = ParagraphStyle(
    name='FooterText',
    fontName='Cambria',
    fontSize=10.5,
    leading=13,
    spaceAfter=0,
    alignment=1  # Center alignment for footer text
)

# Define custom 'BodyFooterText' style for the "Kindly disregard..." text
styles['BodyFooterText'] = ParagraphStyle(
    name='BodyFooterText',
    fontName='Cambria',
    fontSize=10.5,
    leading=13,
    spaceAfter=6,
    alignment=0  # Left alignment
)

# Define custom 'TableText' style for table data to enforce center alignment
styles['TableText'] = ParagraphStyle(
    name='TableText',
    fontName='Cambria',
    fontSize=9,
    leading=11,
    spaceAfter=6,
    alignment=1
)

# Define custom 'TableTextBold' style for table headers
styles['TableTextBold'] = ParagraphStyle(
    name='TableTextBold',
    fontName='Cambria-Bold',
    fontSize=10,
    leading=11,
    spaceAfter=6,
    alignment=1
)

# Iterate through each row in the DataFrame to process individual policyholder data
for index, row in df.iterrows():
    print(f"[PROCESSING] Row {index + 1} of {len(df)}")
    
    # Extract relevant data from the current row
    owner1_title = row.get('Owner 1 Title', '')
    owner1_first_name = row.get('Owner 1 First Name', '')
    owner1_surname = row.get('Owner 1 Surname', '')
    owner2_title = row.get('Owner 2 Title', '')
    owner2_first_name = row.get('Owner 2 First Name', '')
    owner2_surname = row.get('Owner 2 Surname', '')
    assignee_surname = row.get('Assignee Surname Corrected', '')
    owner1_address1 = row.get('Owner 1 Policy Address 1', '')
    owner1_address2 = row.get('Owner 1 Policy Address 2', '')
    owner1_address3 = row.get('Owner 1 Policy Address 3', '')
    owner1_address4 = row.get('Owner 1 Policy Address 4', '')
    policy_no = str(row.get('Policy No', '')) if pd.notna(row.get('Policy No', '')) else ''
    policy_no_api = policy_no.replace('/', '.') if policy_no else ''
    print(f"[DEBUG] policy_no value = '{policy_no}' (type: {type(policy_no)})")
    print(f"[DEBUG] policy_no_api value = '{policy_no_api}' (type: {type(policy_no_api)})")
    frequency = row.get('Frequency', '')
    gross_premium = row.get('Computed Gross Premium', 0)
    no_installments = row.get('No of Instalments in Arrears', 0)
    arrears_amount = row.get('Arrears Amount', 0)
    agent_no = row.get('Agent No', '')
    
    # Extract additional columns for later use
    mobile_no = row.get('MOBILE_NO', '')
    nic = row.get('NIC', '')
    arrears_processing_date_raw = row.get('Arrears Processing Date', '')
    
    # Debug output for the extracted variables
    print(f"[DEBUG] Owner 1 First Name: '{owner1_first_name}'")
    print(f"[DEBUG] Owner 1 Surname: '{owner1_surname}'")
    print(f"[DEBUG] Mobile No: '{mobile_no}'")
    print(f"[DEBUG] NIC: '{nic}'")
    
    # Process arrears processing date
    if arrears_processing_date_raw and pd.notna(arrears_processing_date_raw):
        try:
            # Handle Excel serial date number (e.g., 45900.0901388889)
            if isinstance(arrears_processing_date_raw, (int, float)):
                # Convert Excel serial number to datetime
                date_obj = pd.to_datetime(arrears_processing_date_raw, origin='1899-12-30', unit='D')
                arrears_date_formatted = date_obj.strftime('%d-%B-%Y')  # "31-August-2025"
            else:
                # Handle string format "31/08/2025  02:09:48" (fallback)
                date_part = str(arrears_processing_date_raw).split()[0]
                date_obj = datetime.strptime(date_part, '%d/%m/%Y')
                arrears_date_formatted = date_obj.strftime('%d-%B-%Y')
        except:
            arrears_date_formatted = "29 August 2025"  # fallback
    else:
        arrears_date_formatted = "29 August 2025"  # fallback
    
    print(f"[DEBUG] Arrears Processing Date: '{arrears_processing_date_raw}' -> '{arrears_date_formatted}'")
    
    # Console log NIC value for each record
    print(f"[NIC] Record {index + 1}: NIC = '{nic}' (type: {type(nic)})")
    
    # Create full_name variable (first letter of first name + surname, max 24 chars)
    first_initial = ''
    if owner1_first_name and isinstance(owner1_first_name, str) and len(owner1_first_name) > 0 and owner1_first_name.lower() != 'nan':
        first_initial = owner1_first_name[0].upper()
    # Handle surname safely (check for NaN and non-string values)
    surname_part = ''
    if owner1_surname and isinstance(owner1_surname, str) and owner1_surname.lower() != 'nan':
        surname_part = owner1_surname.strip()
    
    # Combine and ensure max 24 characters
    if first_initial and surname_part:
        full_name_temp = f"{first_initial} {surname_part}"
        full_name = full_name_temp[:24] if len(full_name_temp) > 24 else full_name_temp
    elif surname_part:
        full_name = surname_part[:24] if len(surname_part) > 24 else surname_part
    else:
        full_name = ''
    
    print(f"[DEBUG] Full Name (max 24 chars): '{full_name}' (length: {len(full_name)})")
    
    # Validate required fields
    if pd.isna(policy_no) or str(policy_no).strip() == '':
        print(f"⚠️ Skipping row {index + 1}: Missing policy number")
        continue

    # Format values for use in the PDF
    name = f"{owner1_title} {owner1_first_name} {owner1_surname}"
    amount = float(arrears_amount) if pd.notna(arrears_amount) else 0.0
    no_installments = no_installments if pd.notna(no_installments) else 0
    gross_premium = float(gross_premium) if pd.notna(gross_premium) else 0.0

    # Sanitize name and policy number for safe filename creation
    safe_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
    safe_policy = re.sub(r'[^\w\s-]', '_', str(policy_no)).strip()

    # Generate QR Code for payment
    try:
        payload = {
            "MerchantId": 151,
            "SetTransactionAmount": True,
            "TransactionAmount": str(amount),
            "SetConvenienceIndicatorTip": False,
            "ConvenienceIndicatorTip": 0,
            "SetConvenienceFeeFixed": False,
            "ConvenienceFeeFixed": 0,
            "SetConvenienceFeePercentage": False,
            "ConvenienceFeePercentage": 0,
            "SetAdditionalBillNumber": True,
            "AdditionalRequiredBillNumber": False,
            "AdditionalBillNumber": str(policy_no_api),
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
            "AdditionalCustomerLabel": str(full_name),
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
            if not qr_data or qr_data.lower() in ('null', 'none', 'nan'):
                print(f"⚠️ No valid QR data received for {name}")
                continue
                
            qr = segno.make(qr_data, error='L')
            qr_filename = f"qr_{safe_policy}.png"
            qr.save(qr_filename, scale=8, border=2, dark='#000000')
        else:
            print(f"❌ API request failed for {name}: {response.status_code} - {response.text}")
            continue

    except requests.exceptions.RequestException as e:
        print(f"⚠️ Network error while generating QR for {name}: {str(e)}")
        continue
    except Exception as e:
        print(f"⚠️ Error generating QR for {name}: {str(e)}")
        continue

    # Create a PDF for the current policyholder - NEW FORMAT
    pdf_filename = f"output_letters/{safe_policy}_{safe_name}.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=A4)
    width, height = A4
    margin = 50
    bottom_margin = 20
    y_pos = height - margin - 40

    # Add current date (top left, above name)
    current_date = datetime.now().strftime("%d-%B-%Y")  # System date in dd-month-yyyy format
    c.setFont("Cambria", 10)
    c.drawString(margin, y_pos, current_date)
    y_pos -= 25

    # Add recipient address block
    address_lines = []
    address_lines.append(f"{owner1_title} {owner1_first_name} {owner1_surname}")
    
    # Add Owner 2 information if available
    if (pd.notna(owner2_title) and str(owner2_title).strip()) or \
       (pd.notna(owner2_first_name) and str(owner2_first_name).strip()) or \
       (pd.notna(owner2_surname) and str(owner2_surname).strip()):
        owner2_line = f"{owner2_title} {owner2_first_name} {owner2_surname}".strip()
        if owner2_line:
            address_lines.append(owner2_line)
    
    if pd.notna(owner1_address1) and str(owner1_address1).strip():
        address_lines.append(str(owner1_address1))
    if pd.notna(owner1_address2) and str(owner1_address2).strip():
        address_lines.append(str(owner1_address2))
    if pd.notna(owner1_address3) and str(owner1_address3).strip():
        address_lines.append(str(owner1_address3))
    if pd.notna(owner1_address4) and str(owner1_address4).strip():
        address_lines.append(str(owner1_address4))
    
    c.setFont("Cambria", 10)
    for line in address_lines:
        c.drawString(margin, y_pos, line)
        y_pos -= 14
    y_pos -= 10

    # Add NOTICE header (centered and underlined)
    notice_text = "NOTICE: MISE EN DEMEURE"
    article_text = "Article 1983-21, 3382-4(Code Civil)"
    
    c.setFont("Cambria-Bold", 12)
    notice_width = c.stringWidth(notice_text, "Cambria-Bold", 12)
    notice_x = (width - notice_width) / 2
    c.drawString(notice_x, y_pos, notice_text)
    # Underline the notice
    c.line(notice_x, y_pos - 2, notice_x + notice_width, y_pos - 2)
    y_pos -= 16
    
    c.setFont("Cambria", 10)
    article_width = c.stringWidth(article_text, "Cambria", 10)
    article_x = (width - article_width) / 2
    c.drawString(article_x, y_pos, article_text)
    y_pos -= 20

    # Add salutation
    salutation_text = f"Dear Valued Customers,"
    c.setFont("Cambria", 10)
    c.drawString(margin, y_pos, salutation_text)
    y_pos -= 16

    # Add policy details table
    table_data = [
        ["POLICY NO.", "", f"{policy_no}"],
        ["PREMIUM", "", f"MUR {gross_premium:,.2f}"],
        ["PAYMENT FREQUENCY", "", f"{frequency}"]
    ]
    
    # Draw table with lines
    table_start_y = y_pos
    row_height = 16
    col_widths = [120, 20, 200]  # Adjust column widths
    
    for i, row in enumerate(table_data):
        current_y = table_start_y - (i * row_height)
        c.setFont("Cambria", 10)
        
        # Draw the row data
        x_pos = margin
        for j, cell in enumerate(row):
            if j == 0:  # First column (labels)
                c.setFont("Cambria-Bold", 10)
            else:
                c.setFont("Cambria", 10)
            c.drawString(x_pos, current_y, cell)
            x_pos += col_widths[j]
        
        # Lines removed for cleaner look
    
    y_pos = table_start_y - (len(table_data) * row_height) - 10

    # Add main body text
    body_text1 = f"You are hereby notified that the premiums due by you under the above Policy as on {arrears_date_formatted} amounts to MUR {amount:,.2f}."
    para1 = Paragraph(body_text1, styles['BodyText'])
    para1.wrapOn(c, width - 2 * margin, height)
    para1.drawOn(c, margin, y_pos - para1.height)
    y_pos -= para1.height + 12

    body_text2 = "You may wish to verify payments effected one month before and one month after the periods mentioned above given that premiums received will not set off against the oldest installment(s) due."
    para2 = Paragraph(body_text2, styles['BodyText'])
    para2.wrapOn(c, width - 2 * margin, height)
    para2.drawOn(c, margin, y_pos - para2.height)
    y_pos -= para2.height + 12

    body_text3 = "You are hereby further notified that, as provided by law and as set out in your contract, should you not pay the <font name='Cambria-Bold'>total</font> premium amount due within <font name='Cambria-Bold'>20 days</font> of the date of receipt of the present Mise en Demeure, the Policy cover shall be suspended as from the 21st day until noon the day on which you pay the total premiums in arrears."
    para3 = Paragraph(body_text3, styles['BodyText'])
    para3.wrapOn(c, width - 2 * margin, height)
    para3.drawOn(c, margin, y_pos - para3.height)
    y_pos -= para3.height + 12

    body_text4 = "Should the premiums remain unpaid for a further 10 days after the expiry of the above-mentioned delay of 20 days, we hereby inform you that we shall consider the above Policy as cancelled as per the article 1983-84 al.2 which states that 'Le défaut de paiement d'une prime dû pour sanction, après accomplissement des formalités prescrites par l'article 1983-81, que la résiliation pure et simple de l'assurance ou la réduction de ses effets' with effect from the expiry of the aforesaid period of 10 days."
    para4 = Paragraph(body_text4, styles['BodyText'])
    para4.wrapOn(c, width - 2 * margin, height)
    para4.drawOn(c, margin, y_pos - para4.height)
    y_pos -= para4.height + 12

    body_text5 = "For your convenience, you may now settle payments via the QR code below using apps such as Juice or MyT Money."
    para5 = Paragraph(body_text5, styles['BodyText'])
    para5.wrapOn(c, width - 2 * margin, height)
    para5.drawOn(c, margin, y_pos - para5.height)
    y_pos -= para5.height + 10

    # Add MauCAS logo and QR code (centered)
    page_center_x = width / 2
    
    # Add logo image (centered horizontally)
    if os.path.exists("maucas.jpeg"):
        img = ImageReader("maucas.jpeg")
        img_width = 120
        img_height = img_width * (img.getSize()[1] / img.getSize()[0])
        logo_x = page_center_x - (img_width / 2)
        c.drawImage(img, logo_x, y_pos - img_height, width=img_width, height=img_height)
        y_pos -= img_height + 5

    # Add QR code below logo (centered horizontally)
    if os.path.exists(qr_filename):
        qr_size = 80
        qr_x = page_center_x - (qr_size / 2)
        c.drawImage(qr_filename, qr_x, y_pos - qr_size, width=qr_size, height=qr_size)
        y_pos -= qr_size + 10

    # Add footer text
    footer_text1 = "Please accept our apologies and kindly disregard this notice if payment has already been made by the time it reaches you."
    para_footer1 = Paragraph(footer_text1, styles['BodyText'])
    para_footer1.wrapOn(c, width - 2 * margin, height)
    para_footer1.drawOn(c, margin, y_pos - para_footer1.height)
    y_pos -= para_footer1.height + 12

    footer_text2 = "Should you require any additional information, please do not hesitate to email us on nicarlife@nicl.mu or call our Recovery Department on 602-3315."
    para_footer2 = Paragraph(footer_text2, styles['BodyText'])
    para_footer2.wrapOn(c, width - 2 * margin, height)
    para_footer2.drawOn(c, margin, y_pos - para_footer2.height)
    y_pos -= para_footer2.height + 20

    # Add assignee surname
    if pd.notna(assignee_surname) and str(assignee_surname).strip() not in ['', 'nan', 'NaN']:
        c.setFont("Cambria", 10)
        c.drawString(margin, y_pos, f"{assignee_surname}")
        y_pos -= 20

    # Add disclaimer at bottom
    disclaimer_text = "This is a computer-generated letter and does not require authentication."
    para_disclaimer = Paragraph(disclaimer_text, styles['disclaimerText'])
    para_disclaimer.wrapOn(c, width - 2 * margin, height)
    para_disclaimer.drawOn(c, margin, bottom_margin)

    # Save the PDF
    c.save()

    # Add password protection using customer's NIC
    try:
        if nic and str(nic).strip():
            password = str(nic).strip()
            
            # Create password-protected version
            temp_filename = pdf_filename.replace('.pdf', '_temp.pdf')
            os.rename(pdf_filename, temp_filename)
            
            # Read the unprotected PDF
            with open(temp_filename, 'rb') as input_file:
                reader = PdfFileReader(input_file)
                writer = PdfFileWriter()
                
                # Copy all pages
                for page_num in range(reader.getNumPages()):
                    writer.addPage(reader.getPage(page_num))
                
                # Encrypt with NIC as password
                writer.encrypt(password)
                
                # Write password-protected PDF
                with open(pdf_filename, 'wb') as output_file:
                    writer.write(output_file)
            
            # Remove temporary file
            os.remove(temp_filename)
            print(f"🔒 PDF password-protected with NIC: {password}")
        else:
            print(f"⚠️ No NIC found for {name}, PDF saved without password protection")
    except Exception as e:
        print(f"⚠️ Failed to add password protection: {str(e)}")
        # If password protection fails, ensure we still have the original PDF
        temp_filename = pdf_filename.replace('.pdf', '_temp.pdf')
        if os.path.exists(temp_filename):
            os.rename(temp_filename, pdf_filename)

    # Clean up QR code file
    if os.path.exists(qr_filename):
        os.remove(qr_filename)

    print(f"✅ PDF generated successfully for {name}")

print(f"🎉 Script completed. Processed {len(df)} rows total.")