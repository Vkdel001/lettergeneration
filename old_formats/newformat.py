# Import necessary libraries for data handling, HTTP requests, QR code generation, and PDF creation
import pandas as pd
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
    print("✅ Cambria (from cambria.ttf) and Cambria-Bold (from cambriab.ttf) fonts registered successfully")
except Exception as e:
    raise Exception(f"Failed to register fonts: {str(e)}")

# Read the Excel file containing policyholder data
try:
    df = pd.read_excel("Generic_Template.xlsx")
    print(f"✅ Excel file loaded successfully with {len(df)} rows")
    print(f"Available columns: {list(df.columns)}")
except FileNotFoundError:
    raise FileNotFoundError("Excel file 'Generic_Template.xlsx' not found in the current directory")

# Create a folder named 'output_letters' to store generated PDFs, if it doesn't already exist
os.makedirs("output_letters", exist_ok=True)

# Define custom paragraph styles explicitly
styles = {}

styles['BodyText'] = ParagraphStyle(
    name='BodyText',
    fontName='Cambria',
    fontSize=9,
    leading=12,
    spaceAfter=6,
    alignment=TA_JUSTIFY
)

styles['disclaimerText'] = ParagraphStyle(
    name='disclaimerText',
    fontName='Cambria',
    fontSize=9,
    leading=10,
    spaceAfter=6,
    alignment=1,
    textColor=gray
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
    fontSize=8,
    leading=6,
    spaceAfter=5
)

styles['FooterText'] = ParagraphStyle(
    name='FooterText',
    fontName='Cambria',
    fontSize=9,
    leading=13,
    spaceAfter=0,
    alignment=1
)

styles['BodyFooterText'] = ParagraphStyle(
    name='BodyFooterText',
    fontName='Cambria',
    fontSize=9,
    leading=13,
    spaceAfter=6,
    alignment=0
)

styles['TableText'] = ParagraphStyle(
    name='TableText',
    fontName='Cambria',
    fontSize=9,
    leading=11,
    spaceAfter=6,
    alignment=1
)

styles['TableTextBold'] = ParagraphStyle(
    name='TableTextBold',
    fontName='Cambria-Bold',
    fontSize=9,
    leading=11,
    spaceAfter=6,
    alignment=1
)

# Iterate through each row in the DataFrame to process individual policyholder data
for index, row in df.iterrows():
    owner1_title = row.get('Owner 1 Title', '')
    owner1_first_name = row.get('Owner 1 First Name', '')
    owner1_surname = row.get('Owner 1 Surname', '')
    assignee_surname = row.get('Assignee Surname Corrected', '')
    owner1_address1 = row.get('Owner 1 Policy Address 1', '')
    owner1_address2 = row.get('Owner 1 Policy Address 2', '')
    owner1_address3 = row.get('Owner 1 Policy Address 3', '')
    owner1_address4 = row.get('Owner 1 Policy Address 4', '')
    policy_no = row.get('Policy No', '')
    frequency = row.get('Frequency', '')
    gross_premium = row.get('Computed Gross Premium', 0)
    no_installments = row.get('No of Instalments in Arrears', 0)
    arrears_amount = row.get('Arrears Amount', 0)
    agent_no = row.get('Agent No', '')

    name = f"{owner1_title} {owner1_first_name} {owner1_surname}"
    amount = float(arrears_amount) if pd.notna(arrears_amount) else 0.0
    no_installments = no_installments if pd.notna(no_installments) else 0
    gross_premium = float(gross_premium) if pd.notna(gross_premium) else 0.0

    safe_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
    safe_policy = re.sub(r'[^\w\s-]', '_', str(policy_no)).strip()

    # Generate QR Code for payment
    try:
        payload = {
            "MerchantId": 57,
            "SetTransactionAmount": True,
            "TransactionAmount": str(amount),
            "SetConvenienceIndicatorTip": False,
            "ConvenienceIndicatorTip": 0,
            "SetConvenienceFeeFixed": False,
            "ConvenienceFeeFixed": 0,
            "SetConvenienceFeePercentage": False,
            "ConvenienceFeePercentage": 0,
        }
        response = requests.post(
            "https://apiuat.zwennpay.com:9425/api/v1.0/Common/GetMerchantQR",
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

    pdf_filename = f"output_letters/{safe_policy}_{safe_name}.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=A4)
    width, height = A4
    margin = 50
    bottom_margin = 20
    y_pos = height - margin - 80

    date_top_y = y_pos
    current_date = datetime.now().strftime("%d/%m/%Y")
    date_para = Paragraph(f"{current_date}", styles['SalutationText'])
    date_para.wrapOn(c, width - margin, height)
    date_para.drawOn(c, margin, y_pos - date_para.height)
    y_pos -= date_para.height + 12

    address_lines = [name]
    if pd.notna(owner1_address1) and str(owner1_address1).strip(): 
        address_lines.append(str(owner1_address1))
    if pd.notna(owner1_address2) and str(owner1_address2).strip(): 
        address_lines.append(str(owner1_address2))
    if pd.notna(owner1_address3) and str(owner1_address3).strip(): 
        address_lines.append(str(owner1_address3))
    if pd.notna(owner1_address4) and str(owner1_address4).strip(): 
        address_lines.append(str(owner1_address4))

    for line in address_lines:
        addr_para = Paragraph(line.upper(), styles['SalutationText'])
        addr_para.wrapOn(c, width - 2 * margin, height)
        addr_para.drawOn(c, margin, y_pos - addr_para.height)
        y_pos -= addr_para.height + 6
    y_pos -= 2

    salutation_text = f"Dear {owner1_title} {owner1_surname},"
    salutation = Paragraph(salutation_text, styles['BodyText'])
    salutation.wrapOn(c, width - 2 * margin, height)
    salutation.drawOn(c, margin, y_pos - salutation.height)
    y_pos -= salutation.height + 8

    subject = Paragraph("RE: ARREARS ON YOUR LIFE INSURANCE POLICY", styles['BoldText'])
    subject.wrapOn(c, width - 2 * margin, height)
    subject.drawOn(c, margin, y_pos - subject.height)
    y_pos -= subject.height + 8

    intro_text = f"Our records indicate that, as at 29 March 2025, an amount of MUR {amount:.2f} is due under your referred policy as follows:"
    intro = Paragraph(intro_text, styles['BodyText'])
    intro.wrapOn(c, width - 2 * margin, height)
    intro.drawOn(c, margin, y_pos - intro.height)
    y_pos -= intro.height + 8

    # --- policy table and explanatory paragraphs remain unchanged ---

    # Insert NEW paragraph before QR/Logo
    text7 = "We strongly advise you to settle the arrears promptly using one of our accepted payment methods. For your convenience, you may scan the QR code below to access the payment portal directly:"
    para7 = Paragraph(text7, styles['BodyText'])
    para7.wrapOn(c, width - 2 * margin, height)
    para7.drawOn(c, margin, y_pos - para7.height)
    y_pos -= para7.height + 12

    # Add logo image at the top-right of the page
    if os.path.exists("maucas.jpeg"):
        img = ImageReader("maucas.jpeg")
        img_width = 120  # Made bigger (was 80)
        img_height = img_width * (img.getSize()[1] / img.getSize()[0])  # Maintain aspect ratio
        c.drawImage(img, width - 140, date_top_y - img_height, width=img_width, height=img_height)

    # Add QR code below the logo at top-right
    if os.path.exists(qr_filename):
        qr_size = 100  # Made bigger (was 80)
        qr_y = date_top_y - img_height - qr_size - 10  # Position below logo
        c.drawImage(qr_filename, width - 140, qr_y, width=qr_size, height=qr_size)

    # --- Continue with the rest of your letter (banking table, disclaimers, footer, etc.) ---

    footer1 = Paragraph(
        "Kindly disregard this letter if you have already settled the arrears on your Life Insurance Policy.",
        styles['BodyText']
    )
    footer1.wrapOn(c, width - 2 * margin, height)
    footer1.drawOn(c, margin, y_pos - footer1.height)
    y_pos -= footer1.height + 10

    if pd.notna(assignee_surname) and str(assignee_surname).strip() not in ['', 'nan', 'NaN']:
        agent_text = Paragraph(f"{assignee_surname}", styles['BodyText'])
        agent_text.wrapOn(c, width - 2 * margin, height)
        agent_text.drawOn(c, margin, y_pos - agent_text.height)
        y_pos -= agent_text.height + 10

    footer2 = Paragraph(
        "This is a computer-generated letter and does not require any signature.",
        styles['disclaimerText']
    )
    footer2.wrapOn(c, width - 2 * margin, height)
    footer2.drawOn(c, margin, bottom_margin)

    c.save()

    if os.path.exists(qr_filename):
        os.remove(qr_filename)

    print(f"✅ PDF generated successfully for {name}")
