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
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
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
    print("[OK] Cambria fonts registered successfully")
except Exception as e:
    raise Exception(f"Failed to register fonts: {str(e)}")

# Read the Excel file containing renewal data
try:
    df = pd.read_excel("RENEWAL_LISTING.xlsx", engine='openpyxl')
    print(f"[OK] Excel file loaded successfully with {len(df)} rows")
    print(f"[INFO] Available columns: {list(df.columns)}")
    
    if len(df) == 0:
        print("[WARNING] Excel file is empty")
        sys.exit(1)
        
except FileNotFoundError:
    print("[ERROR] Excel file 'RENEWAL_LISTING.xlsx' not found in the current directory")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error reading Excel file: {str(e)}")
    sys.exit(1)

# Create output folder
output_folder = "output_renewals"
if len(sys.argv) > 1:
    for i, arg in enumerate(sys.argv):
        if arg == '--output' and i + 1 < len(sys.argv):
            output_folder = sys.argv[i + 1]
            break

os.makedirs(output_folder, exist_ok=True)
print(f"[INFO] Using output folder: {output_folder}")# Define custom paragraph styles
styles = {}

styles['BodyText'] = ParagraphStyle(
    name='BodyText',
    fontName='Cambria',
    fontSize=10.5,
    leading=12,
    spaceAfter=6,
    alignment=TA_JUSTIFY
)

styles['BoldText'] = ParagraphStyle(
    name='BoldText',
    fontName='Cambria-Bold',
    fontSize=11,
    leading=13,
    spaceAfter=6
)

styles['SalutationText'] = ParagraphStyle(
    name='SalutationText',
    fontName='Cambria-Bold',
    fontSize=10.5,
    leading=6,
    spaceAfter=5
)

styles['FooterText'] = ParagraphStyle(
    name='FooterText',
    fontName='Cambria',
    fontSize=10.5,
    leading=13,
    spaceAfter=0,
    alignment=TA_CENTER
)

styles['TableText'] = ParagraphStyle(
    name='TableText',
    fontName='Cambria',
    fontSize=9,
    leading=11,
    spaceAfter=6,
    alignment=TA_CENTER
)

styles['TableTextBold'] = ParagraphStyle(
    name='TableTextBold',
    fontName='Cambria-Bold',
    fontSize=10,
    leading=11,
    spaceAfter=6,
    alignment=TA_CENTER
)

styles['BlueHeading'] = ParagraphStyle(
    name='BlueHeading',
    fontName='Cambria-Bold',
    fontSize=11,
    leading=13,
    spaceAfter=8,
    textColor=colors.blue
)

styles['SmallText'] = ParagraphStyle(
    name='SmallText',
    fontName='Cambria',
    fontSize=9,
    leading=11,
    spaceAfter=4,
    alignment=TA_JUSTIFY
)

# Function to format dates
def format_date(date_value):
    if pd.isna(date_value):
        return ""
    try:
        if isinstance(date_value, (int, float)):
            date_obj = pd.to_datetime(date_value, origin='1899-12-30', unit='D')
        else:
            date_obj = pd.to_datetime(date_value)
        return date_obj.strftime('%d %B %Y')
    except:
        return str(date_value)

# Function to format currency
def format_currency(amount):
    try:
        return f"MUR {float(amount):,.2f}"
    except:
        return "MUR 0.00"# Process each row in the DataFrame
for index, row in df.iterrows():
    print(f"[PROCESSING] Row {index + 1} of {len(df)}")
    
    # Extract data from Excel columns
    pol_no = str(row.get('POL_NO', '')) if pd.notna(row.get('POL_NO', '')) else ''
    name = str(row.get('NAME', '')) if pd.notna(row.get('NAME', '')) else ''
    surname = str(row.get('SURNAME', '')) if pd.notna(row.get('SURNAME', '')) else ''
    title = str(row.get('TITLE', '')) if pd.notna(row.get('TITLE', '')) else ''
    address1 = str(row.get('ADDRESS1', '')) if pd.notna(row.get('ADDRESS1', '')) else ''
    address2 = str(row.get('ADDRESS2', '')) if pd.notna(row.get('ADDRESS2', '')) else ''
    address3 = str(row.get('ADDRESS3', '')) if pd.notna(row.get('ADDRESS3', '')) else ''
    
    # Policy dates
    expiry_from = row.get('EXPIRY_POL_FROM_DT', '')
    expiry_to = row.get('EXPIRY_POL_TO_DT', '')
    renewal_start = row.get('REN_POL_START_DT', '')
    renewal_end = row.get('REN_POL_TO_DT', '')
    
    # Policy details
    plan = str(row.get('PLAN', '')) if pd.notna(row.get('PLAN', '')) else ''
    cat_plan = str(row.get('CAT_PLAN', '')) if pd.notna(row.get('CAT_PLAN', '')) else ''
    inpatient_limit = row.get('INPATIENT_LIMIT', 0)
    outpatient_limit = row.get('OUTPATIENT_LIMIT', 0)
    cat_limit = row.get('CAT_LIMIT', 0)
    
    # Premium information
    total_premium = row.get('TOTAL_PREMIUM', 0)
    fsc_levy = row.get('FSC_LEVY', 0)
    
    # Additional fields for QR generation
    mobile_no = str(row.get('MOB_NO', '')) if pd.notna(row.get('MOB_NO', '')) else ''
    
    # Skip if essential data is missing
    if not pol_no or not name:
        print(f"⚠️ Skipping row {index + 1}: Missing essential data")
        continue
    
    # Create full customer name
    full_customer_name = f"{title} {name} {surname}".strip()
    
    # Create filename-safe names
    try:
        from filename_utils import sanitize_filename
        safe_name = sanitize_filename(full_customer_name)
        safe_policy = sanitize_filename(pol_no)
    except ImportError:
        safe_name = re.sub(r'[^\w\s-]', '', full_customer_name).strip().replace(' ', '_')
        safe_policy = re.sub(r'[^\w\s-]', '_', pol_no).strip()
    
    print(f"[DEBUG] Processing: {full_customer_name} - Policy: {pol_no}")
    
    # Format dates
    expiry_from_formatted = format_date(expiry_from)
    expiry_to_formatted = format_date(expiry_to)
    renewal_start_formatted = format_date(renewal_start)
    renewal_end_formatted = format_date(renewal_end)
    
    # Create cover period string
    cover_period = f"{expiry_from_formatted} to {expiry_to_formatted}"  
  # Generate QR Code for payment
    qr_filename = None
    try:
        # Create first initial + surname for customer label (max 24 chars)
        first_initial = name[0].upper() if name and len(name) > 0 else ''
        surname_part = surname.strip() if surname else ''
        
        if first_initial and surname_part:
            customer_label_temp = f"{first_initial} {surname_part}"
            customer_label = customer_label_temp[:24] if len(customer_label_temp) > 24 else customer_label_temp
        elif surname_part:
            customer_label = surname_part[:24] if len(surname_part) > 24 else surname_part
        else:
            customer_label = ''
        
        # API payload for QR generation
        payload = {
            "MerchantId": 153,
            "SetTransactionAmount": True,
            "TransactionAmount": str(total_premium),
            "SetConvenienceIndicatorTip": False,
            "ConvenienceIndicatorTip": 0,
            "SetConvenienceFeeFixed": False,
            "ConvenienceFeeFixed": 0,
            "SetConvenienceFeePercentage": False,
            "ConvenienceFeePercentage": 0,
            "SetAdditionalBillNumber": True,
            "AdditionalRequiredBillNumber": False,
            "AdditionalBillNumber": str(pol_no).replace('/', '.'),
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
            "AdditionalCustomerLabel": str(customer_label),
            "SetAdditionalTerminalLabel": False,
            "AdditionalRequiredTerminalLabel": False,
            "AdditionalTerminalLabel": "",
            "SetAdditionalPurposeTransaction": True,
            "AdditionalRequiredPurposeTransaction": False,
            "AdditionalPurposeTransaction": "Healthcare Renewal"
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
                qr = segno.make(qr_data, error='L')
                qr_filename = f"qr_{safe_policy}.png"
                qr.save(qr_filename, scale=8, border=2, dark='#000000')
                print(f"✅ QR code generated for {full_customer_name}")
            else:
                print(f"⚠️ No valid QR data received for {full_customer_name}")
        else:
            print(f"❌ API request failed for {full_customer_name}: {response.status_code}")

    except Exception as e:
        print(f"⚠️ Error generating QR for {full_customer_name}: {str(e)}")    # Create PDF
    pdf_filename = f"{output_folder}/{safe_policy}_{safe_name}.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=A4)
    width, height = A4
    margin = 50
    bottom_margin = 20
    
    # Start from top
    y_pos = height - margin
    
    # Add NIC I.sphere app QR codes (top right)
    app_qr_y = height - 120
    app_qr_x = width - 220
    
    # Add the NIC I.sphere logo with QR codes
    if os.path.exists("isphere_logo.jpeg"):
        isphere_img = ImageReader("isphere_logo.jpeg")
        isphere_width = 200
        isphere_height = isphere_width * (isphere_img.getSize()[1] / isphere_img.getSize()[0])
        c.drawImage(isphere_img, app_qr_x, app_qr_y - isphere_height, width=isphere_width, height=isphere_height)
    else:
        # Fallback text if image not found
        c.setFont("Cambria-Bold", 12)
        c.drawString(app_qr_x, app_qr_y, "NIC I.sphere App Download")
    
    y_pos = height - 150  # Move below app QRs
    
    # Add current date (top left)
    current_date = datetime.now().strftime("%d %B %Y")
    date_para = Paragraph(current_date, styles['SalutationText'])
    date_para.wrapOn(c, width - margin, height)
    date_para.drawOn(c, margin, y_pos)
    y_pos -= date_para.height + 15
    
    # Add customer address
    address_lines = [full_customer_name.upper()]
    if address1: address_lines.append(address1.upper())
    if address2: address_lines.append(address2.upper())
    if address3: address_lines.append(address3.upper())
    
    for line in address_lines:
        addr_para = Paragraph(line, styles['SalutationText'])
        addr_para.wrapOn(c, width - 2 * margin, height)
        addr_para.drawOn(c, margin, y_pos)
        y_pos -= addr_para.height + 4
    
    y_pos -= 10
    
    # Add salutation
    salutation = Paragraph("Dear Sir/ Madam", styles['BodyText'])
    salutation.wrapOn(c, width - 2 * margin, height)
    salutation.drawOn(c, margin, y_pos)
    y_pos -= salutation.height + 8    # Add subject line
    subject_text = f"<font name='Cambria-Bold' color='blue'>RE: RENEWAL OF YOUR HEALTHCARE INSURANCE - POLICY ID {pol_no}</font>"
    subject = Paragraph(subject_text, styles['BodyText'])
    subject.wrapOn(c, width - 2 * margin, height)
    subject.drawOn(c, margin, y_pos)
    y_pos -= subject.height + 12
    
    # Add policy expiry notice
    expiry_text = f"We wish to inform you that your Healthcare Insurance Policy, as detailed hereunder, will expire on <font name='Cambria-Bold'>{expiry_to_formatted}</font> and is due for renewal."
    expiry_para = Paragraph(expiry_text, styles['BodyText'])
    expiry_para.wrapOn(c, width - 2 * margin, height)
    expiry_para.drawOn(c, margin, y_pos)
    y_pos -= expiry_para.height + 12
    
    # Create policy details table
    table_headers = [
        Paragraph('<font name="Cambria-Bold">Cover Period</font>', styles['TableText']),
        Paragraph('<font name="Cambria-Bold">Insured Name</font>', styles['TableText']),
        Paragraph('<font name="Cambria-Bold">Plan(s)*</font>', styles['TableText']),
        Paragraph('<font name="Cambria-Bold">Inpatient (MUR)</font>', styles['TableText']),
        Paragraph('<font name="Cambria-Bold">Outpatient (MUR)</font>', styles['TableText']),
        Paragraph('<font name="Cambria-Bold">Catastrophe (MUR)</font>', styles['TableText'])
    ]
    
    table_data = [
        [
            Paragraph(cover_period, styles['TableText']),
            Paragraph(f"{name} {surname}", styles['TableText']),
            Paragraph(f"{plan}<br/>{cat_plan}", styles['TableText']),
            Paragraph(f"{inpatient_limit:,.0f}", styles['TableText']),
            Paragraph(f"{outpatient_limit:,.0f}", styles['TableText']),
            Paragraph(f"{cat_limit:,.0f}", styles['TableText'])
        ]
    ]
    
    data = [table_headers] + table_data
    table = Table(data, colWidths=[80, 80, 80, 60, 60, 60])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Cambria'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWHEIGHT', (0, 0), (-1, -1), 20),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    table_width, table_height = table.wrap(width - 2 * margin, 0)
    table.drawOn(c, margin, y_pos - table_height)
    y_pos -= table_height + 15
    
    # Add note about policy details
    note_text = "* Please refer to your Healthcare Insurance Policy for benefit details"
    note_para = Paragraph(note_text, styles['BodyText'])
    note_para.wrapOn(c, width - 2 * margin, height)
    note_para.drawOn(c, margin, y_pos)
    y_pos -= note_para.height + 15 
   # Add Renewal Premium section
    renewal_heading = Paragraph('<font name="Cambria-Bold" color="blue">RENEWAL PREMIUM</font>', styles['BodyText'])
    renewal_heading.wrapOn(c, width - 2 * margin, height)
    renewal_heading.drawOn(c, margin, y_pos)
    y_pos -= renewal_heading.height + 8
    
    # Premium text
    premium_text = f"Considering a number of factors including, inter-alia, your claims history, medical inflation and prevailing market conditions, the renewal premium for the period <font name='Cambria-Bold'>{renewal_start_formatted} to {renewal_end_formatted}</font> will be <font name='Cambria-Bold'>{format_currency(total_premium)}</font> inclusive of FSC fee and other applicable fees. Should there be any major change in your claim ratio at expiry, the renewal premium may be subject to review."
    premium_para = Paragraph(premium_text, styles['BodyText'])
    premium_para.wrapOn(c, width - 2 * margin, height)
    premium_para.drawOn(c, margin, y_pos)
    y_pos -= premium_para.height + 15
    
    # Add QR code and logo after the premium text
    if qr_filename and os.path.exists(qr_filename):
        # Add payment instruction
        qr_instruction = Paragraph("For your convenience, you may settle payments via the QR code below using apps such as Juice or MyT Money.", styles['BoldText'])
        qr_instruction.wrapOn(c, width - 2 * margin, height)
        qr_instruction.drawOn(c, margin, y_pos)
        y_pos -= qr_instruction.height + 10
        
        # Calculate center position
        page_center_x = width / 2
        
        # Add maucas logo (centered)
        if os.path.exists("maucas2.jpeg"):
            img = ImageReader("maucas2.jpeg")
            img_width = 120
            img_height = img_width * (img.getSize()[1] / img.getSize()[0])
            logo_x = page_center_x - (img_width / 2)
            c.drawImage(img, logo_x, y_pos - img_height, width=img_width, height=img_height)
            y_pos -= img_height + 10
        
        # Add QR code (centered)
        qr_size = 100
        qr_x = page_center_x - (qr_size / 2)
        c.drawImage(qr_filename, qr_x, y_pos - qr_size, width=qr_size, height=qr_size)
        y_pos -= qr_size + 15
    
    # Add Special Terms section
    special_terms_heading = Paragraph('<font name="Cambria-Bold" color="blue">SPECIAL TERMS</font>', styles['BodyText'])
    special_terms_heading.wrapOn(c, width - 2 * margin, height)
    special_terms_heading.drawOn(c, margin, y_pos)
    y_pos -= special_terms_heading.height + 8
    
    special_terms_text = "The following special terms shall apply to the renewed Policy:"
    special_terms_para = Paragraph(special_terms_text, styles['BodyText'])
    special_terms_para.wrapOn(c, width - 2 * margin, height)
    special_terms_para.drawOn(c, margin, y_pos)
    y_pos -= special_terms_para.height + 6
    
    # Special terms list
    term1 = "1. Premium is payable upfront unless a Credit Facility Arrangement is entered into."
    term1_para = Paragraph(term1, styles['BodyText'])
    term1_para.wrapOn(c, width - 2 * margin - 10, height)
    term1_para.drawOn(c, margin + 10, y_pos)
    y_pos -= term1_para.height + 4
    
    term2 = "2. Capping or exclusion, if any, on the expiring cover period will be maintained on the renewal policy."
    term2_para = Paragraph(term2, styles['BodyText'])
    term2_para.wrapOn(c, width - 2 * margin - 10, height)
    term2_para.drawOn(c, margin + 10, y_pos)
    y_pos -= term2_para.height + 12    # Add Possibility to Upgrade section
    upgrade_heading = Paragraph('<font name="Cambria-Bold" color="blue">POSSIBILITY TO UPGRADE YOUR BENEFITS</font>', styles['BodyText'])
    upgrade_heading.wrapOn(c, width - 2 * margin, height)
    upgrade_heading.drawOn(c, margin, y_pos)
    y_pos -= upgrade_heading.height + 8
    
    upgrade_text = "Subject to underwriting and applicable waiting periods, you are eligible to upgrade your present benefits. This will allow for a more comprehensive cover. Please refer to the attached options, detailed herewith. We invite you to advise on any upgrade you may wish to effect for timely implementation."
    upgrade_para = Paragraph(upgrade_text, styles['BodyText'])
    upgrade_para.wrapOn(c, width - 2 * margin, height)
    upgrade_para.drawOn(c, margin, y_pos)
    y_pos -= upgrade_para.height + 15
    
    # Add Renewal Procedure section
    procedure_heading = Paragraph('<font name="Cambria-Bold" color="blue">RENEWAL PROCEDURE</font>', styles['BodyText'])
    procedure_heading.wrapOn(c, width - 2 * margin, height)
    procedure_heading.drawOn(c, margin, y_pos)
    y_pos -= procedure_heading.height + 8
    
    procedure_text = "In order to avoid any interruption in cover, we would invite you to kindly complete the attached Renewal Acceptance Form and settle your renewal premium through your insurance advisor or by visiting one of our offices or through our digital facility put at your disposal."
    procedure_para = Paragraph(procedure_text, styles['BodyText'])
    procedure_para.wrapOn(c, width - 2 * margin, height)
    procedure_para.drawOn(c, margin, y_pos)
    y_pos -= procedure_para.height + 15
    
    # Add Arrears section
    arrears_heading = Paragraph('<font name="Cambria-Bold" color="blue">ARREARS</font>', styles['BodyText'])
    arrears_heading.wrapOn(c, width - 2 * margin, height)
    arrears_heading.drawOn(c, margin, y_pos)
    y_pos -= arrears_heading.height + 8
    
    arrears_text1 = "The renewal of the Policy is subject to the settlement of any premium due on your previous healthcare Insurance Policies. Accordingly, should any outstanding premium, please ensure same is settled not later than <font name='Cambria-Bold'>EXPIRY_POL_TO_DT_MM</font>. Failing to do so may result in interruption or cancellation of your insurance cover."
    arrears_para1 = Paragraph(arrears_text1, styles['BodyText'])
    arrears_para1.wrapOn(c, width - 2 * margin, height)
    arrears_para1.drawOn(c, margin, y_pos)
    y_pos -= arrears_para1.height + 8
    
    arrears_text2 = "We trust this proposal is appropriate to your healthcare insurance needs and we look forward to discussing same in more detail with you as may be applicable."
    arrears_para2 = Paragraph(arrears_text2, styles['BodyText'])
    arrears_para2.wrapOn(c, width - 2 * margin, height)
    arrears_para2.drawOn(c, margin, y_pos)
    y_pos -= arrears_para2.height + 8
    
    # Additional services text
    services_text = "In addition to your current coverage, we offer a wide range of tailored insurance solutions in Motor, Travel, Property, Liability, Life & Pension, and Loan to ensure more complete protection for you and your assets."
    services_para = Paragraph(services_text, styles['BodyText'])
    services_para.wrapOn(c, width - 2 * margin, height)
    services_para.drawOn(c, margin, y_pos)
    y_pos -= services_para.height + 8
    
    # Contact information
    contact_text = "Should you require any further information, our Customer Service team will gladly assist you on 602 3000, <font color='blue'>customerservice@nicl.mu</font> or any of our offices or our insurance advisors across the island."
    contact_para = Paragraph(contact_text, styles['BodyText'])
    contact_para.wrapOn(c, width - 2 * margin, height)
    contact_para.drawOn(c, margin, y_pos)
    y_pos -= contact_para.height + 8
    
    # Closing
    closing_text = "Assuring you of our best services at all times."
    closing_para = Paragraph(closing_text, styles['BodyText'])
    closing_para.wrapOn(c, width - 2 * margin, height)
    closing_para.drawOn(c, margin, y_pos)
    y_pos -= closing_para.height + 15
    
    # Signature
    signature_text = "Yours sincerely"
    signature_para = Paragraph(signature_text, styles['BodyText'])
    signature_para.wrapOn(c, width - 2 * margin, height)
    signature_para.drawOn(c, margin, y_pos)
    y_pos -= signature_para.height + 8
    
    dept_text = "Healthcare Insurance (Underwriting)"
    dept_para = Paragraph(dept_text, styles['BodyText'])
    dept_para.wrapOn(c, width - 2 * margin, height)
    dept_para.drawOn(c, margin, y_pos)
    y_pos -= dept_para.height + 20
    
    # Enclosure
    enclosure_text = "Encl.: Renewal Acceptance Form"
    enclosure_para = Paragraph(enclosure_text, styles['BodyText'])
    enclosure_para.wrapOn(c, width - 2 * margin, height)
    enclosure_para.drawOn(c, margin, y_pos)
    
    # Save PDF
    c.save()
    
    # Clean up QR file
    if qr_filename and os.path.exists(qr_filename):
        os.remove(qr_filename)
    
    print(f"✅ Healthcare renewal PDF generated for {full_customer_name}")

print(f"🎉 Healthcare renewal script completed. Processed {len(df)} rows total.")