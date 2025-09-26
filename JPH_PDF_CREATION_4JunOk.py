# Import necessary libraries for data handling, HTTP requests, QR code generation, and PDF creation
import pandas as pd
import requests
import segno
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os
import re
from datetime import datetime
from reportlab.lib.utils import ImageReader

# Read the Excel file containing policyholder data
df = pd.read_excel("Generic_Template.xlsx")

# Create a folder named 'output_letters' to store generated PDFs, if it doesn't already exist
os.makedirs("output_letters_JPH", exist_ok=True)

# Initialize stylesheet for formatting text in the PDF
styles = getSampleStyleSheet()

# Define custom 'BodyText' style for body paragraphs if not already present
if 'BodyText' not in styles:
    styles.add(ParagraphStyle(
        name='BodyText',
        fontSize=8,
        leading=10,
        spaceAfter=6,
        fontName='Helvetica'
    ))

# Define custom 'BoldText' style for headings if not already present
if 'BoldText' not in styles:
    styles.add(ParagraphStyle(
        name='BoldText',
        fontSize=11,
        leading=12,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    ))

# Define custom 'SalutationText' style for the "Dear..." line if not already present
if 'SalutationText' not in styles:
    styles.add(ParagraphStyle(
        name='SalutationText',
        fontSize=9,
        leading=10,
        spaceAfter=6,
        fontName='Helvetica'
    ))

# Define custom 'FooterText' style for the absolute footer at the bottom of the page
if 'FooterText' not in styles:
    styles.add(ParagraphStyle(
        name='FooterText',
        fontSize=8,
        leading=10,
        spaceAfter=0,
        fontName='Helvetica',
        alignment=1  # Center alignment for footer text
    ))

# Define custom 'BodyFooterText' style for the "Kindly disregard..." text to match body text
if 'BodyFooterText' not in styles:
    styles.add(ParagraphStyle(
        name='BodyFooterText',
        fontSize=8,  # Matches BodyText size
        leading=10,
        spaceAfter=6,
        fontName='Helvetica',
        alignment=0  # Left alignment
    ))

# Define custom 'TableText' style for table data to enforce center alignment
if 'TableText' not in styles:
    styles.add(ParagraphStyle(
        name='TableText',
        parent=styles['BodyText'],  # Inherit from BodyText (fontSize=8, Helvetica, leading=10)
        alignment=1,  # Center alignment (0=Left, 1=Center, 2=Right)
        spaceAfter=6
    ))

# Define custom 'TableTextBold' style for table headers to enforce center alignment and bold text
if 'TableTextBold' not in styles:
    styles.add(ParagraphStyle(
        name='TableTextBold',
        parent=styles['TableText'],  # Inherit from TableText (center alignment, fontSize=8, leading=10)
        fontName='Helvetica-Bold',  # Use bold font for headers
        spaceAfter=6
    ))

# Iterate through each row in the DataFrame to process individual policyholder data
for index, row in df.iterrows():
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
    policy_no = row.get('Policy No', '')
    frequency = row.get('Frequency', '')
    gross_premium = row.get('Computed Gross Premium', 0)
    no_installments = row.get('No of Instalments in Arrears', 0)
    arrears_amount = row.get('Arrears Amount', 0)
    agent_no = row.get('Agent No', '')

    # Format values for use in the PDF
    name = f"{owner1_title} {owner1_first_name} {owner1_surname}"
    name2 = f"{owner2_title} {owner2_first_name} {owner2_surname}"
    amount = float(arrears_amount) if pd.notna(arrears_amount) else 0.0  # Convert arrears amount to float, default to 0.0 if missing
    no_installments = no_installments if pd.notna(no_installments) else 0  # Use number of installments, default to 0 if missing
    gross_premium = float(gross_premium) if pd.notna(gross_premium) else 0.0  # Convert gross premium to float, default to 0.0 if missing

    # Sanitize name and policy number for safe filename creation
    safe_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')  # Remove invalid characters and replace spaces with underscores
    safe_policy = re.sub(r'[^\w\s-]', '_', str(policy_no)).strip()  # Replace invalid characters in policy number with underscores

    # Generate QR Code for payment
    try:
        # Define payload for the API request to generate a QR code
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
        
        # Send POST request to the QR code generation API
        response = requests.post(
            "https://apiuat.zwennpay.com:9425/api/v1.0/Common/GetMerchantQR",
            headers={"accept": "text/plain", "Content-Type": "application/json"},
            json=payload,
            timeout=20
        )
        
        # Check if the API request was successful
        if response.status_code == 200:
            qr_data = str(response.text).strip()  # Get the QR code data from the response
            if not qr_data or qr_data.lower() in ('null', 'none', 'nan'):
                print(f"⚠️ No valid QR data received for {name}")
                continue  # Skip to the next iteration if QR data is invalid
                
            # Create and save the QR code as a PNG file
            qr = segno.make(qr_data, error='L')  # Generate QR code with low error correction
            qr_filename = f"qr_{safe_policy}.png"
            qr.save(qr_filename, scale=8, border=2, dark='#000000')  # Save QR code with specified scale and color
        else:
            print(f"❌ API request failed for {name}: {response.status_code} - {response.text}")
            continue  # Skip to the next iteration if the API request failed

    except requests.exceptions.RequestException as e:
        print(f"⚠️ Network error while generating QR for {name}: {str(e)}")
        continue  # Skip to the next iteration on network error
    except Exception as e:
        print(f"⚠️ Error generating QR for {name}: {str(e)}")
        continue  # Skip to the next iteration on general error

    # Create a PDF for the current policyholder
    pdf_filename = f"output_letters_JPH/{safe_policy}_{safe_name}.pdf"  # Define the PDF filename
    c = canvas.Canvas(pdf_filename, pagesize=A4)  # Initialize a PDF canvas with A4 size
    width, height = A4  # Get A4 page dimensions
    margin = 50  # Set standard margin
    bottom_margin = 20  # Set bottom margin for footer
    y_pos = height - margin - 10  # Initialize vertical position with extra 10 units of space at the top

    # Store the top position of the date for aligning images and QR code
    date_top_y = y_pos

    # Add current date to the PDF
    current_date = datetime.now().strftime("%d/%m/%Y")  # Format current date as DD/MM/YYYY
    date_para = Paragraph(f"{current_date}", styles['SalutationText'])
    date_para.wrapOn(c, width - margin, height)  # Wrap text to fit page width
    date_para.drawOn(c, margin, y_pos - date_para.height)  # Draw date on the canvas
    y_pos -= date_para.height + 12  # Update y-position

    # Add recipient address to the PDF
    address_lines = [name]  # Start with the policyholder's name
    if pd.notna(name2):
        address_lines.append(str(name2))  # Add address line 1 if not null
    if pd.notna(owner1_address1):
        address_lines.append(str(owner1_address1))  # Add address line 1 if not null
    if pd.notna(owner1_address2):
        address_lines.append(str(owner1_address2))  # Add address line 2 if not null
    if pd.notna(owner1_address3):
        address_lines.append(str(owner1_address3))  # Add address line 3 if not null
    if pd.notna(owner1_address4):
        address_lines.append(str(owner1_address4))  # Add address line 4 if not null
    
    # Draw each address line on the PDF
    for line in address_lines:
        addr_para = Paragraph(line, styles['SalutationText'])
        addr_para.wrapOn(c, width - 2 * margin, height)
        addr_para.drawOn(c, margin, y_pos - addr_para.height)
        y_pos -= addr_para.height + 6  # Update y-position with reduced gap
    y_pos -= 2  # Add small extra space after address

    # Add salutation based on surname comparison
    if pd.notna(owner2_surname) and owner1_surname == owner2_surname:
        salutation_text = f"Dear {owner1_title} & {owner2_title} {owner1_surname},"
    else:
        salutation_text = f"Dear {owner1_title} {owner1_surname} & {owner2_title} {owner2_surname},"
    salutation = Paragraph(salutation_text, styles['BodyText'])
    salutation.wrapOn(c, width - 2 * margin, height)
    salutation.drawOn(c, margin, y_pos - salutation.height)
    y_pos -= salutation.height + 8

    # Add subject line to the PDF
    subject = Paragraph("RE: ARREARS ON YOUR LIFE INSURANCE POLICY", styles['BoldText'])
    subject.wrapOn(c, width - 2 * margin, height)
    subject.drawOn(c, margin, y_pos - subject.height)
    y_pos -= subject.height + 8

    # Add introductory paragraph about arrears
    intro_text = f"Our records indicate that, as at 29 March 2025, an amount of MUR {amount:.2f} is due under your referred policy as follows:"
    intro = Paragraph(intro_text, styles['BodyText'])
    intro.wrapOn(c, width - 2 * margin, height)
    intro.drawOn(c, margin, y_pos - intro.height)
    y_pos -= intro.height + 8

    # Create and draw a table with policy details
    # Use TableTextBold for headers to ensure center alignment and bold text
    table_headers = [
        Paragraph('Policy No.', styles['TableTextBold']),
        Paragraph('Payment Frequency', styles['TableTextBold']),
        Paragraph('Premium Amount (MUR)', styles['TableTextBold']),
        Paragraph('No. of Instalments in Arrears', styles['TableTextBold']),
        Paragraph('Total Premium Amount in Arrears (MUR)', styles['TableTextBold'])
    ]
    # Use TableText for data values to ensure center alignment without bold
    table_data = [
        [
            Paragraph(str(policy_no), styles['TableText']),
            Paragraph(str(frequency), styles['TableText']),
            Paragraph(f"{gross_premium:.2f}", styles['TableText']),
            Paragraph(str(no_installments), styles['TableText']),
            Paragraph(f"{amount:.2f}", styles['TableText'])
        ]
    ]
    # Combine headers and data
    data = [table_headers] + table_data
    # Adjust column widths to accommodate long headers
    table = Table(data, colWidths=[80, 70, 70, 90, 100])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center-align all cells
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),  # Default to Helvetica (overridden by TableTextBold for headers)
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Font size for all cells
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # Add grid lines
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertically align to middle
        ('ROWHEIGHT', (0, 0), (-1, -1), 15),  # Set row height
        ('LEFTPADDING', (0, 0), (-1, -1), 2),  # Add left padding
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),  # Add right padding
        ('TEXTWRAP', (0, 0), (-1, -1), 'CJK'),  # Enable word wrapping for long headers
    ]))
    # Calculate table dimensions
    table_width, table_height = table.wrap(width - 2 * margin, 0)
    # Draw table on the canvas
    table.drawOn(c, margin, y_pos - table_height)
    # Update y-position
    y_pos -= table_height + 12

    # Add body text explaining the importance of settling arrears
    text1 = "It is important that you settle the premium in arrears at the earliest possible to ensure your insurance covers are properly maintained and stay in force."
    para1 = Paragraph(text1, styles['BodyText'])
    para1.wrapOn(c, width - 2 * margin, height)
    para1.drawOn(c, margin, y_pos - para1.height)
    y_pos -= para1.height + 8

    # Add additional body text with reminders
    text2 = "As a caring insurer, it is our duty to remind you that:"
    para2 = Paragraph(text2, styles['BodyText'])
    para2.wrapOn(c, width - 2 * margin, height)
    para2.drawOn(c, margin, y_pos - para2.height)
    y_pos -= para2.height + 6

    # Add numbered list items with indentation
    text3 = "1. Your life insurance cover provides for protection and financial security for you and your family members against unforeseen and unexpected events."
    para3 = Paragraph(text3, styles['BodyText'])
    para3.wrapOn(c, width - 2 * margin - 10, height)
    para3.drawOn(c, margin + 10, y_pos - para3.height)
    y_pos -= para3.height + 6

    text4 = "2. Maintaining premium payments up to date enables your policy fund to grow over time constantly."
    para4 = Paragraph(text4, styles['BodyText'])
    para4.wrapOn(c, width - 2 * margin - 10, height)
    para4.drawOn(c, margin + 10, y_pos - para4.height)
    y_pos -= para4.height + 6

    text5 = "3. In event of non-payment of total outstanding arrears, it may affect the payment of any future benefits and claims when these fall due."
    para5 = Paragraph(text5, styles['BodyText'])
    para5.wrapOn(c, width - 2 * margin - 10, height)
    para5.drawOn(c, margin + 10, y_pos - para5.height)
    y_pos -= para5.height + 6

    text6 = "4. If you are experiencing financial difficulties or require payment facilities to settle the arrears, please contact our office on 602 3315 immediately or email us to discuss for any payment arrangements."
    para6 = Paragraph(text6, styles['BodyText'])
    para6.wrapOn(c, width - 2 * margin - 10, height)
    para6.drawOn(c, margin + 10, y_pos - para6.height)
    y_pos -= para6.height + 8

    # Add instructions for settling arrears
    text7 = "We would advise that you promptly arrange to settle the said arrears at the earliest by either a bank transfer (e.g. MCB Juice Transfer, other mobile apps, internet banking), to any of the following bank accounts or by direct payment at any NIC Branch office."
    para7 = Paragraph(text7, styles['BodyText'])
    para7.wrapOn(c, width - 2 * margin, height)
    para7.drawOn(c, margin, y_pos - para7.height)
    y_pos -= para7.height + 8

    # Add banking details and contact information
    text8 = "Please ensure you correctly include the aforementioned Policy No. in the description / remarks section when conducting the transfer: For any further information, please contact our Recovery Department on 602-3315 or email us on nicarlife@nicl.mu"
    para8 = Paragraph(text8, styles['BodyText'])
    para8.wrapOn(c, width - 2 * margin, height)
    para8.drawOn(c, margin, y_pos - para8.height)
    y_pos -= para8.height + 8

    # Create and draw a table with banking details
    banking_data = [
        ['No.', 'Banking Institutions', 'Account Numbers'],
        ['1.', 'The Mauritius Commercial Bank Ltd (MCB)', '000-444-031-917'],
        ['2.', 'SBM Bank (Mauritius) Ltd', '61-0301-0005-6068'],
        ['3.', 'MauBank Ltd', '1431-0000-7061'],
        ['4.', 'Absa Bank (Mauritius) Limited', '0142-000-342']
    ]
    banking_table = Table(banking_data, colWidths=[30, 200, 100])  # Define column widths
    banking_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),  # Set font
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Set font size
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),  # Add grid lines
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertically align to middle
        ('ROWHEIGHT', (0, 0), (-1, -1), 15),  # Set row height
        ('LEFTPADDING', (0, 0), (-1, -1), 2),  # Add left padding
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),  # Add right padding
    ]))
    banking_table_width, banking_table_height = banking_table.wrap(width - 2 * margin, 0)
    banking_table.drawOn(c, margin, y_pos - banking_table_height)
    y_pos -= banking_table_height + 8

    # Add footer text instructing to disregard the letter if payment was made
    remaining_height = max(bottom_margin + 30, y_pos - 30)  # Ensure space for two lines
    footer1 = Paragraph(
        "Kindly disregard this letter if you have already settled the arrears on your Life Insurance Policy.",
        styles['BodyText']
    )
    footer1.wrapOn(c, width - 2 * margin, height)
    footer1.drawOn(c, margin, remaining_height - footer1.height)

    # Add agent number below the disregard notice with some vertical space
    remaining_height -= footer1.height + 10  # Add 10 units of vertical space
    agent_text_height = 0
    if pd.notna(assignee_surname) and str(assignee_surname).strip() not in ['', 'nan', 'NaN']:
        agent_text = Paragraph(
            f"{assignee_surname}",
            styles['BodyText']
        )
        agent_text.wrapOn(c, width - 2 * margin, height)
        agent_text.drawOn(c, margin, remaining_height - agent_text.height)
        agent_text_height = agent_text.height
    remaining_height -= agent_text_height

    # Add absolute footer at the bottom of the page
    footer2 = Paragraph(
        "This is a computer-generated letter and does not require any signature.",
        styles['FooterText']
    )
    footer2.wrapOn(c, width - 2 * margin, height)
    footer2.drawOn(c, margin, bottom_margin)

    # Add logo image (maucas.jpeg) at the top-right of the page
    img_height = 0  # Default height in case image doesn't exist
    if os.path.exists("maucas.jpeg"):
        img = ImageReader("maucas.jpeg")
        img_width = 80  # Set fixed width to match QR code
        img_height = img_width * (img.getSize()[1] / img.getSize()[0])  # Calculate height to maintain aspect ratio
        c.drawImage(img, width - 100, date_top_y - img_height, width=img_width, height=img_height)

    # Add QR code below the logo image
    if os.path.exists(qr_filename):
        qr_y = date_top_y - img_height - 80  # Position QR code below the image
        c.drawImage(qr_filename, width - 100, qr_y, width=80, height=80)

    # Save the PDF
    c.save()

    # Clean up the temporary QR code file
    if os.path.exists(qr_filename):
        os.remove(qr_filename)

    # Print success message for each PDF created
    print(f"✅ PDF created successfully for {name}")