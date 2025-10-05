# API Configuration Usage Guide

This guide shows how to use the `api_config.py` file for Brevo Email API and ZwennPay QR Code API in any project.

## Installation Requirements

```bash
pip install requests segno
```

## Quick Start

### 1. Import the APIs

```python
from api_config import BrevoAPI, ZwennPayAPI
```

### 2. Generate QR Code

```python
# Generate QR code for payment
result = ZwennPayAPI.generate_qr_code(
    amount=1500.00,
    policy_no="00407/0095764", 
    mobile_no="59892555",
    customer_name="John Doe",
    nic="A091289380036E"
)

if result["success"]:
    qr_data = result["qr_data"]
    
    # Create QR image
    import segno
    qr = segno.make(qr_data, error='L')
    qr.save("payment_qr.png", scale=8, border=2)
else:
    print(f"Error: {result['error']}")
```

### 3. Send Email via Brevo

```python
# Your Brevo API key
api_key = "your-brevo-api-key-here"

# Create email payload
payload = BrevoAPI.create_email_payload(
    sender_email="noreply@nic.mu",
    sender_name="NIC Insurance", 
    recipient_email="customer@example.com",
    recipient_name="John Doe",
    subject="Policy Arrears Notice",
    html_content="<h1>Dear John Doe,</h1><p>Your policy has arrears of MUR 1,500.00</p>"
)

# Send email
result = BrevoAPI.send_email(api_key, payload)

if result["success"]:
    print(f"Email sent! Message ID: {result['message_id']}")
else:
    print(f"Failed: {result['error']}")
```

### 4. Send Email with PDF Attachment

```python
# Read PDF file
with open("policy_letter.pdf", "rb") as f:
    pdf_content = f.read()

# Create email with attachment
payload = BrevoAPI.create_email_payload(
    sender_email="noreply@nic.mu",
    sender_name="NIC Insurance",
    recipient_email="customer@example.com", 
    recipient_name="John Doe",
    subject="Your Policy Letter",
    html_content="<p>Please find your policy letter attached.</p>",
    attachment_content=pdf_content,
    attachment_name="policy_letter.pdf"
)

result = BrevoAPI.send_email(api_key, payload)
```

## Configuration Options

### ZwennPay API

- **Merchant ID**: Default is 151, can be customized
- **Timeout**: Default is 20 seconds
- **Customer Name**: Automatically truncated to 24 characters

### Brevo API

- **Base URL**: https://api.brevo.com/v3
- **Timeout**: 30 seconds for email sending
- **Attachments**: Supports PDF and other file types

## Error Handling

Both APIs return standardized response formats:

```python
{
    "success": True/False,
    "error": "Error message if failed",
    "status_code": HTTP_status_code,
    # Additional fields specific to each API
}
```

## Integration Examples

### In PDF Generation Script

```python
from api_config import ZwennPayAPI
import segno

# Generate QR for each policy
for index, row in df.iterrows():
    amount = row['Arrears Amount']
    policy_no = row['Policy No']
    mobile_no = row['MOBILE_NO']
    customer_name = f"{row['Owner 1 First Name']} {row['Owner 1 Surname']}"
    nic = row['NIC']
    
    # Generate QR code
    qr_result = ZwennPayAPI.generate_qr_code(
        amount=amount,
        policy_no=policy_no,
        mobile_no=mobile_no, 
        customer_name=customer_name,
        nic=nic
    )
    
    if qr_result["success"]:
        # Create QR image
        qr = segno.make(qr_result["qr_data"], error='L')
        qr_filename = f"qr_{policy_no.replace('/', '_')}.png"
        qr.save(qr_filename, scale=8, border=2)
        
        # Use qr_filename in PDF generation...
    else:
        print(f"QR failed for {policy_no}: {qr_result['error']}")
```

### In Email Service

```python
from api_config import BrevoAPI
import os

def send_policy_emails(email_data, pdf_folder, api_key):
    """Send emails with PDF attachments"""
    
    for item in email_data:
        # Find PDF file
        pdf_path = os.path.join(pdf_folder, item['pdf_filename'])
        
        if os.path.exists(pdf_path):
            # Read PDF
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Create email
            payload = BrevoAPI.create_email_payload(
                sender_email="noreply@nic.mu",
                sender_name="NIC Insurance",
                recipient_email=item['email'],
                recipient_name=item['name'],
                subject=f"Policy Arrears - {item['policy_no']}",
                html_content=f"<p>Dear {item['name']},</p><p>Please find your policy letter attached.</p>",
                attachment_content=pdf_content,
                attachment_name=item['pdf_filename']
            )
            
            # Send email
            result = BrevoAPI.send_email(api_key, payload)
            
            if result["success"]:
                print(f"✅ Email sent to {item['email']}")
            else:
                print(f"❌ Email failed for {item['email']}: {result['error']}")
```

## Benefits of Using This Configuration

1. **Reusable**: Use across multiple projects without copying code
2. **Standardized**: Consistent API response formats
3. **Error Handling**: Built-in error handling and validation
4. **Documented**: Clear parameter descriptions and examples
5. **Maintainable**: Single place to update API endpoints or configurations
6. **Type Safe**: Clear parameter types and return values

## File Structure for New Projects

```
your_project/
├── api_config.py          # Copy this file
├── your_main_script.py    # Your project code
└── requirements.txt       # Add: requests, segno
```

Simply copy `api_config.py` to your new project and start using the APIs immediately!