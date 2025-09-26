# -*- coding: utf-8 -*-
# Import necessary libraries for data handling, HTTP requests, QR code generation, and PDF creation
import pandas as pd
import sys
import io

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
try:
    df = pd.read_excel("Generic_Template.xlsx", engine='openpyxl')
    print(f"[OK] Excel file loaded successfully with {len(df)} rows")
    print(f"[INFO] Available columns: {list(df.columns)}")
    
    # Check if DataFrame is empty
    if len(df) == 0:
        print("[WARNING] Excel file is empty")
        sys.exit(1)
        
except FileNotFoundError:
    print("[ERROR] Excel file 'Generic_Template.xlsx' not found in the current directory")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error reading Excel file: {str(e)}")
    sys.exit(1)

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
    assignee_surname = row.get('Assignee Surname Corrected', '')
    owner1_address1 = row.get('Owner 1 Policy Address 1', '')
    owner1_address2 = row.get('Owner 1 Policy Address 2', '')
    owner1_address3 = row.get('Owner 1 Policy Address 3', '')
    owner1_address4 = row.get('Owner 1 Policy Address 4', '')
    policy_no = row.get('Policy No', '')
    print(f"[DEBUG] policy_no value = '{policy_no}' (type: {type(policy_no)})")
    frequency = row.get('Frequency', '')
    gross_premium = row.get('Computed Gross Premium', 0)
    no_installments = row.get('No of Instalments in Arrears', 0)
    arrears_amount = row.get('Arrears Amount', 0)
    agent_no = row.get('Agent No', '')
    
    # Extract additional columns for later use
    mobile_no = row.get('MOBILE_NO', '')
    nic = row.get('NIC', '')
    
    # Debug output for the extracted variables
    print(f"[DEBUG] Owner 1 First Name: '{owner1_first_name}'")
    print(f"[DEBUG] Owner 1 Surname: '{owner1_surname}'")
    print(f"[DEBUG] Mobile No: '{mobile_no}'")
    print(f"[DEBUG] NIC: '{nic}'")
    
    # Console log NIC value for each record
    print(f"[NIC] Record {index + 1}: NIC = '{nic}' (type: {type(nic)})")
    
    # Create full_name variable (first letter of first name + surname, max 24 chars)
    first_initial = owner1_first_name[0].upper() if owner1_first_name and len(owner1_first_name) > 0 else ''
    surname_part = owner1_surname.strip() if owner1_surname else ''
    
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
            "MerchantId": 80,
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
            "AdditionalBillNumber": str(policy_no),
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

    # Create a PDF for the current policyholder
    pdf_filename = f"output_letters/{safe_policy}_{safe_name}.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=A4)
    width, height = A4
    margin = 50
    bottom_margin = 20
    y_pos = height - margin - 80

    # Store the top position of the date
    date_top_y = y_pos

    # Add current date
    current_date = datetime.now().strftime("%d-%B-%Y")
    date_para = Paragraph(f"{current_date}", styles['SalutationText'])
    date_para.wrapOn(c, width - margin, height)
    date_para.drawOn(c, margin, y_pos - date_para.height)
    y_pos -= date_para.height + 12

    # Add recipient address
    address_lines = [name]
    if pd.notna(owner1_address1):
        address_lines.append(str(owner1_address1))
    if pd.notna(owner1_address2):
        address_lines.append(str(owner1_address2))
    if pd.notna(owner1_address3):
        address_lines.append(str(owner1_address3))
    if pd.notna(owner1_address4):
        address_lines.append(str(owner1_address4))
    
    for line in address_lines:
        addr_para = Paragraph(line.upper(), styles['SalutationText'])
        addr_para.wrapOn(c, width - 2 * margin, height)
        addr_para.drawOn(c, margin, y_pos - addr_para.height)
        y_pos -= addr_para.height + 6
    y_pos -= 2

    # Add salutation
    salutation_text = f"Dear {owner1_title} {owner1_surname},"
    salutation = Paragraph(salutation_text, styles['BodyText'])
    salutation.wrapOn(c, width - 2 * margin, height)
    salutation.drawOn(c, margin, y_pos - salutation.height)
    y_pos -= salutation.height +8

    

    # Add subject line
    subject = Paragraph("RE: ARREARS ON YOUR LIFE INSURANCE POLICY", styles['BoldText'])
    subject.wrapOn(c, width - 2 * margin, height)
    subject.drawOn(c, margin, y_pos - subject.height)
    y_pos -= subject.height + 8

    # Add introductory paragraph
    intro_text = f"We write to inform you that, as of <font name='Cambria-Bold'>29 August 2025</font>, an amount of <font name='Cambria-Bold'>MUR {amount:,.2f}</font> remains outstanding on your life insurance policy, as detailed below:"
    intro = Paragraph(intro_text, styles['BodyText'])
    intro.wrapOn(c, width - 2 * margin, height)
    intro.drawOn(c, margin, y_pos - intro.height)
    y_pos -= intro.height + 8

    # Create and draw policy details table
    table_headers = [
        Paragraph('Policy No.', styles['TableTextBold']),
        Paragraph('Payment Frequency', styles['TableTextBold']),
        Paragraph('Premium Amount (MUR)', styles['TableTextBold']),
        Paragraph('No. of Instalments in Arrears', styles['TableTextBold']),
        Paragraph('Total Premium Amount in Arrears (MUR)', styles['TableTextBold'])
    ]
    table_data = [
        [
            Paragraph(str(policy_no), styles['TableText']),
            Paragraph(str(frequency), styles['TableText']),
            Paragraph(f"{gross_premium:,.2f}", styles['TableText']),
            Paragraph(str(no_installments), styles['TableText']),
            Paragraph(f"{amount:,.2f}", styles['TableText'])
        ]
    ]
    data = [table_headers] + table_data
    table = Table(data, colWidths=[80, 70, 70, 90, 100])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Cambria'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWHEIGHT', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TEXTWRAP', (0, 0), (-1, -1), 'CJK'),
    ]))
    table_width, table_height = table.wrap(width - 2 * margin, 0)
    table.drawOn(c, margin, y_pos - table_height)
    y_pos -= table_height + 12

    # Add body text
    text1 = "We kindly urge you to settle this outstanding amount as soon as possible to ensure that your insurance cover remains active and fully effective."
    para1 = Paragraph(text1, styles['BodyText'])
    para1.wrapOn(c, width - 2 * margin, height)
    para1.drawOn(c, margin, y_pos - para1.height)
    y_pos -= para1.height + 8

    text2 = "As your insurer, we wish to remind you of the following:"
    para2 = Paragraph(text2, styles['BodyText'])
    para2.wrapOn(c, width - 2 * margin, height)
    para2.drawOn(c, margin, y_pos - para2.height)
    y_pos -= para2.height + 6

    text3 = "1.	Your life insurance policy provides essential protection and financial security for you and your loved ones against unforeseen circumstances."
    para3 = Paragraph(text3, styles['BodyText'])
    para3.wrapOn(c, width - 2 * margin - 10, height)
    para3.drawOn(c, margin + 10, y_pos - para3.height)
    y_pos -= para3.height + 6

    text4 = "2.	Regular premium payments help your policy fund grow over time."
    para4 = Paragraph(text4, styles['BodyText'])
    para4.wrapOn(c, width - 2 * margin - 10, height)
    para4.drawOn(c, margin + 10, y_pos - para4.height)
    y_pos -= para4.height + 6

    text5 = "3.	Failure to settle outstanding arrears may impact the payment of future benefits and claims."
    para5 = Paragraph(text5, styles['BodyText'])
    para5.wrapOn(c, width - 2 * margin - 10, height)
    para5.drawOn(c, margin + 10, y_pos - para5.height)
    y_pos -= para5.height + 6

    text6 = "4.	If you are facing financial difficulties or would like to arrange a payment plan, please contact us on 602 3315 or email nicarlife@nicl.mu at your earliest convenience."
    para6 = Paragraph(text6, styles['BodyText'])
    para6.wrapOn(c, width - 2 * margin - 10, height)
    para6.drawOn(c, margin + 10, y_pos - para6.height)
    y_pos -= para6.height + 8

   

    text8 = "For your convenience, you may now settle payments via the QR code below using apps such as Juice or MyT Money."
    para8 = Paragraph(text8, styles['BoldText'])
    para8.wrapOn(c, width - 2 * margin, height)
    para8.drawOn(c, margin, y_pos - para8.height)
    y_pos -= para8.height + 15

    # Add logo and QR code vertically stacked and center aligned
    logo_qr_y_position = y_pos - 10  # Starting position for logo and QR code (reduced spacing)
    
    # Calculate center position for horizontal alignment
    page_center_x = width / 2
    
    # Add logo image (centered horizontally)
    if os.path.exists("maucas.jpeg"):
        img = ImageReader("maucas.jpeg")
        img_width = 120
        img_height = img_width * (img.getSize()[1] / img.getSize()[0])
        # Center the logo horizontally
        logo_x = page_center_x - (img_width / 2)
        c.drawImage(img, logo_x, logo_qr_y_position - img_height, width=img_width, height=img_height)
        logo_qr_y_position -= img_height + 10  # Move down for QR code with spacing

    # Add QR code below logo (centered horizontally)
    if os.path.exists(qr_filename):
        qr_size = 100
        # Center the QR code horizontally
        qr_x = page_center_x - (qr_size / 2)
        c.drawImage(qr_filename, qr_x, logo_qr_y_position - qr_size, width=qr_size, height=qr_size)
        logo_qr_y_position -= qr_size + 10  # Update position after QR code
    
    y_pos = logo_qr_y_position - 10  # Update y_pos to continue below logo/QR stack

    # Add footer text
    remaining_height = max(bottom_margin + 30, y_pos - 30)
    footer1 = Paragraph(
        "If you have already cleared this amount, kindly disregard this letter.",
        styles['BodyText']
    )
    footer1.wrapOn(c, width - 2 * margin, height)
    footer1.drawOn(c, margin, remaining_height - footer1.height)

    # Add agent number
    remaining_height -= footer1.height + 10
    agent_text_height = 0
    if pd.notna(assignee_surname) and str(assignee_surname).strip() not in ['', 'nan', 'NaN']:
        agent_text = Paragraph(f"{assignee_surname}", styles['BodyText'])
        agent_text.wrapOn(c, width - 2 * margin, height)
        agent_text.drawOn(c, margin, remaining_height - agent_text.height)
        agent_text_height = agent_text.height
    remaining_height -= agent_text_height

    # Add absolute footer
    footer2 = Paragraph(
        "This is a computer-generated letter and does not require any signature.",
        styles['disclaimerText']
    )
    footer2.wrapOn(c, width - 2 * margin, height)
    footer2.drawOn(c, margin, bottom_margin)

    # Save the PDF
    c.save()

    # Clean up QR code file
    if os.path.exists(qr_filename):
        os.remove(qr_filename)

    print(f"✅ PDF generated successfully for {name}")

print(f"🎉 Script completed. Processed {len(df)} rows total.")