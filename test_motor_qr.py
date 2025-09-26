#!/usr/bin/env python3
"""
Test Motor Insurance Renewal QR Code - Single Record
"""

import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
import pandas as pd
import requests
import segno

# Register Cambria fonts
cambria_regular_path = os.path.join(os.path.dirname(__file__), 'fonts', 'cambria.ttf')
cambria_bold_path = os.path.join(os.path.dirname(__file__), 'fonts', 'cambriab.ttf')

if os.path.isfile(cambria_regular_path) and os.path.isfile(cambria_bold_path):
    try:
        pdfmetrics.registerFont(TTFont('Cambria', cambria_regular_path))
        pdfmetrics.registerFont(TTFont('Cambria-Bold', cambria_bold_path))
        print("[OK] Cambria fonts registered successfully")
    except Exception as e:
        print(f"[ERROR] Failed to register Cambria fonts: {str(e)}")
        sys.exit(1)
else:
    print("[ERROR] Font files not found")
    sys.exit(1)

# PDF Configuration
width, height = A4
margin = 50

def test_qr_generation():
    """Test QR code generation with sample data"""
    
    # Read Excel file - just first row
    try:
        df = pd.read_excel('output_motor_renewal.xlsx')
        print(f"📊 Loaded {len(df)} records from Excel")
        
        # Take only first row for testing
        row = df.iloc[0]
        print(f"🧪 Testing with first record: {row.get('Title', '')} {row.get('Firstname', '')} {row.get('Surname', '')}")
        
    except FileNotFoundError:
        print("❌ Error: output_motor_renewal.xlsx not found!")
        return
    except Exception as e:
        print(f"❌ Error reading Excel file: {str(e)}")
        return
    
    # Helper function to safely get and clean data
    def safe_get(column_name, default=''):
        value = row.get(column_name, default)
        if pd.isna(value) or value is None:
            return default
        return str(value).strip()
    
    # Map Excel columns to policy data
    policy_data = {
        'date': datetime.now().strftime('%d %B %Y'),
        'title': safe_get('Title'),
        'firstname': safe_get('Firstname'),
        'surname': safe_get('Surname'),
        'name': f"{safe_get('Title')} {safe_get('Firstname')} {safe_get('Surname')}".strip(),
        'policy_no': safe_get('Policy No'),
        'new_net_premium': safe_get('New Net Premium'),
        'mobile_no': safe_get('Mobile No'),
        'nic': safe_get('NIC Number')
    }
    
    print(f"\n🔍 Debug Info:")
    print(f"Policy No: '{policy_data['policy_no']}'")
    print(f"Premium: '{policy_data['new_net_premium']}'")
    print(f"Mobile: '{policy_data['mobile_no']}'")
    print(f"NIC: '{policy_data['nic']}'")
    
    # Generate QR Code for payment using API
    qr_filename = None
    try:
        # Create full_name for API (first letter of first name + surname, max 24 chars)
        first_initial = policy_data['firstname'][0].upper() if policy_data['firstname'] and len(policy_data['firstname']) > 0 else ''
        surname_part = policy_data['surname'].strip() if policy_data['surname'] else ''
        
        if first_initial and surname_part:
            full_name_temp = f"{first_initial} {surname_part}"
            full_name = full_name_temp[:24] if len(full_name_temp) > 24 else full_name_temp
        elif surname_part:
            full_name = surname_part[:24] if len(surname_part) > 24 else surname_part
        else:
            full_name = ''
        
        print(f"Full name for API: '{full_name}'")
        
        # Get data for QR code
        amount = policy_data['new_net_premium']
        mobile_no = policy_data['mobile_no']
        policy_no_api = policy_data['policy_no'].replace('/', '.') if policy_data['policy_no'] else ''
        
        print(f"\n🌐 API Request Data:")
        print(f"Amount: '{amount}'")
        print(f"Policy No API: '{policy_no_api}'")
        print(f"Mobile: '{mobile_no}'")
        print(f"Full Name: '{full_name}'")
        print(f"NIC: '{policy_data['nic']}'")
        
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
            "AdditionalPurposeTransaction": str(policy_data['nic'])
        }
        
        print(f"\n📡 Making API call...")
        response = requests.post(
            "https://api.zwennpay.com:9425/api/v1.0/Common/GetMerchantQR",
            headers={"accept": "text/plain", "Content-Type": "application/json"},
            json=payload,
            timeout=20
        )
        
        print(f"API Response Status: {response.status_code}")
        print(f"API Response Text: '{response.text}'")
        
        if response.status_code == 200:
            qr_data = str(response.text).strip()
            if not qr_data or qr_data.lower() in ('null', 'none', 'nan'):
                print(f"⚠️ No valid QR data received")
                qr_filename = None
            else:
                print(f"✅ Valid QR data received: {qr_data[:50]}...")
                qr = segno.make(qr_data, error='L')
                qr_filename = f"test_qr.png"
                qr.save(qr_filename, scale=8, border=2, dark='#000000')
                print(f"✅ QR code saved as: {qr_filename}")
        else:
            print(f"❌ API request failed: {response.status_code} - {response.text}")
            qr_filename = None
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Network error while generating QR: {str(e)}")
        qr_filename = None
    except Exception as e:
        print(f"⚠️ Error generating QR: {str(e)}")
        qr_filename = None
    
    # Create test PDF
    pdf_filename = "test_motor_renewal.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=A4)
    
    # Simple test content
    y_pos = height - 100
    c.setFont("Cambria", 12)
    c.drawString(margin, y_pos, "TEST MOTOR INSURANCE RENEWAL")
    y_pos -= 30
    
    c.setFont("Cambria", 10)
    c.drawString(margin, y_pos, f"Policy: {policy_data['policy_no']}")
    y_pos -= 20
    c.drawString(margin, y_pos, f"Name: {policy_data['name']}")
    y_pos -= 20
    c.drawString(margin, y_pos, f"Premium: {policy_data['new_net_premium']}")
    y_pos -= 40
    
    # Test QR code display
    if qr_filename and os.path.exists(qr_filename):
        print(f"📄 Adding QR code to PDF...")
        qr_size = 100
        qr_x = (width - qr_size) / 2
        qr_y = y_pos - qr_size
        c.drawImage(qr_filename, qr_x, qr_y, qr_size, qr_size)
        
        # Add label
        c.setFont("Cambria", 8)
        label_text = "Scan and Pay with your favourite payment app"
        label_width = c.stringWidth(label_text, "Cambria", 8)
        label_x = (width - label_width) / 2
        c.drawString(label_x, qr_y - 15, label_text)
        
        print(f"✅ QR code added to PDF")
    else:
        print(f"❌ No QR code to add to PDF")
        c.drawString(margin, y_pos, "❌ QR CODE NOT GENERATED")
    
    c.save()
    
    # Clean up
    if qr_filename and os.path.exists(qr_filename):
        os.remove(qr_filename)
    
    print(f"\n✅ Test PDF generated: {pdf_filename}")
    print(f"🔍 Check the PDF to see if QR code appears")

if __name__ == "__main__":
    print("🧪 Testing Motor Insurance QR Code Generation...")
    test_qr_generation()