#!/usr/bin/env python3
"""
Brevo Email Service
Handles email sending with PDF attachments using Brevo API
"""

import sys
import os
import json
import argparse
import base64
from pathlib import Path
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Brevo Configuration
BREVO_API_KEY = os.getenv('BREVO_API_KEY')
SENDER_EMAIL = "arrears@niclmauritius.site"
SENDER_NAME = "NIC Life Insurance Mauritius"
REPLY_TO_EMAIL = "nicarlife@nicl.mu"
REPLY_TO_NAME = "NIC Life Insurance"

# Validate that API key is loaded
if not BREVO_API_KEY:
    print("[ERROR] BREVO_API_KEY not found in environment variables. Please check your .env file.")
    sys.exit(1)

def setup_brevo_client():
    """Setup Brevo API client"""
    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = BREVO_API_KEY
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
        print("[INFO] Brevo client initialized successfully")
        return api_instance
    except Exception as e:
        print(f"[ERROR] Failed to initialize Brevo client: {str(e)}", file=sys.stderr)
        return None

def encode_pdf_attachment(pdf_path):
    """Encode PDF file as base64 for email attachment"""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
            encoded_content = base64.b64encode(pdf_content).decode('utf-8')
            return encoded_content
    except Exception as e:
        print(f"[ERROR] Failed to encode PDF {pdf_path}: {str(e)}", file=sys.stderr)
        return None

def send_email_with_pdf(api_instance, recipient_email, recipient_name, policy_no, pdf_path):
    """Send email with PDF attachment using Brevo"""
    try:
        # Encode PDF attachment
        pdf_content = encode_pdf_attachment(pdf_path)
        if not pdf_content:
            return False, "Failed to encode PDF attachment"

        # Get PDF filename
        pdf_filename = os.path.basename(pdf_path)
        
        # Create email content
        subject = f"Arrears Notice - Policy {policy_no}"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0;">NIC Mauritius - Policy Arrears Notice</h2>
                
                <p>Dear {recipient_name},</p>
                
                <p>We hope this email finds you well.</p>
                
                <p>Please find attached the arrears notice for your insurance policy <strong>{policy_no}</strong>.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #2c5aa0; margin: 20px 0;">
                    <p><strong>Important:</strong> Please review the attached document and take the necessary action to settle any outstanding amounts.</p>
                </div>
                
                <p>For any queries or assistance, please contact our Customer Service Team:</p>
                <ul>
                    <li>📞 Phone: +230 602-3315</li>
                    <li>📧 Email: nicarlife@nicl.mu</li>
                </ul>
                
                <p>Thank you for your attention to this matter.</p>
                
                <p>Best regards,<br>
                <strong>NIC Mauritius Team</strong></p>
                
                <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    This is an automated email. Please do not reply to this email address.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Create attachment
        attachment = sib_api_v3_sdk.SendSmtpEmailAttachment(
            content=pdf_content,
            name=pdf_filename
        )
        
        # Create email object
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[sib_api_v3_sdk.SendSmtpEmailTo(email=recipient_email, name=recipient_name)],
            sender=sib_api_v3_sdk.SendSmtpEmailSender(email=SENDER_EMAIL, name=SENDER_NAME),
            reply_to=sib_api_v3_sdk.SendSmtpEmailReplyTo(email=REPLY_TO_EMAIL, name=REPLY_TO_NAME),
            subject=subject,
            html_content=html_content,
            attachment=[attachment]
        )
        
        # Send email
        api_response = api_instance.send_transac_email(send_smtp_email)
        message_id = api_response.message_id if hasattr(api_response, 'message_id') else 'unknown'
        
        print(f"[SUCCESS] Email sent to {recipient_email} - Message ID: {message_id}")
        return True, message_id
        
    except ApiException as e:
        error_msg = f"Brevo API error: {e.status} - {e.reason}"
        print(f"[ERROR] {error_msg}", file=sys.stderr)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"[ERROR] {error_msg}", file=sys.stderr)
        return False, error_msg

def find_pdf_file(pdf_folder, expected_filename):
    """Find PDF file with fuzzy matching for Unicode issues - ONLY uses protected PDFs for email security"""
    
    # Define search locations - PROTECTED FOLDER FIRST for email security
    search_locations = [
        os.path.join(pdf_folder, 'protected'),    # Protected subfolder (PREFERRED for emails)
        pdf_folder,  # Main folder (legacy structure - fallback only)
    ]
    
    # Note: Unprotected folder is intentionally excluded for email security
    
    # Try exact match in all locations
    for location in search_locations:
        if os.path.exists(location):
            exact_path = os.path.join(location, expected_filename)
            if os.path.exists(exact_path):
                print(f"[INFO] Found PDF (exact match): {exact_path}")
                return exact_path
    
    # If exact match fails, try fuzzy matching in all locations
    try:
        import re
        policy_match = re.match(r'^([^_]+_[^_]+)', expected_filename)
        if policy_match:
            policy_prefix = policy_match.group(1)
            
            for location in search_locations:
                if not os.path.exists(location):
                    continue
                    
                try:
                    # Get all PDF files in this location
                    pdf_files = [f for f in os.listdir(location) if f.endswith('.pdf')]
                    
                    # Find files that start with the same policy number
                    matching_files = [f for f in pdf_files if f.startswith(policy_prefix)]
                    
                    if len(matching_files) == 1:
                        found_path = os.path.join(location, matching_files[0])
                        print(f"[INFO] Found PDF via fuzzy match: {found_path} (expected: {expected_filename})")
                        return found_path
                    elif len(matching_files) > 1:
                        print(f"[WARNING] Multiple PDFs match policy {policy_prefix} in {location}: {matching_files}")
                        # Return the first match
                        found_path = os.path.join(location, matching_files[0])
                        print(f"[INFO] Using first match: {found_path}")
                        return found_path
                        
                except Exception as e:
                    print(f"[WARNING] Error searching in {location}: {str(e)}")
                    continue
    
    except Exception as e:
        print(f"[WARNING] Error during fuzzy PDF search: {str(e)}")
    
    return None

def process_email_batch(email_data_file, pdf_folder):
    """Process batch of emails from JSON data"""
    try:
        # Setup Brevo client
        api_instance = setup_brevo_client()
        if not api_instance:
            return False, "Failed to initialize Brevo client"
        
        # Load email data with proper UTF-8 encoding
        with open(email_data_file, 'r', encoding='utf-8') as f:
            email_data = json.load(f)
        
        results = []
        success_count = 0
        failed_count = 0
        
        print(f"[INFO] Processing {len(email_data)} emails...")
        
        for i, record in enumerate(email_data, 1):
            try:
                recipient_email = record.get('email', '')
                recipient_name = record.get('name', '')
                policy_no = record.get('policy_no', '')
                pdf_filename = record.get('pdf_filename', '')
                
                if not all([recipient_email, recipient_name, policy_no, pdf_filename]):
                    print(f"[WARNING] Skipping record {i}: Missing required fields")
                    failed_count += 1
                    continue
                
                # Use fuzzy matching to find the PDF file
                pdf_path = find_pdf_file(pdf_folder, pdf_filename)
                if not pdf_path:
                    print(f"[WARNING] PDF not found: {pdf_filename} in {pdf_folder}")
                    # List available PDFs for debugging
                    try:
                        available_pdfs = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
                        print(f"[DEBUG] Available PDFs: {available_pdfs[:5]}...")  # Show first 5
                    except:
                        pass
                    failed_count += 1
                    continue
                
                print(f"[PROCESSING] {i}/{len(email_data)}: {recipient_email}")
                
                success, message_id = send_email_with_pdf(
                    api_instance, recipient_email, recipient_name, policy_no, pdf_path
                )
                
                if success:
                    success_count += 1
                    results.append({
                        'email': recipient_email,
                        'status': 'sent',
                        'message_id': message_id
                    })
                else:
                    failed_count += 1
                    results.append({
                        'email': recipient_email,
                        'status': 'failed',
                        'error': message_id
                    })
                
                # Small delay to avoid rate limiting
                if i % 10 == 0:
                    print(f"[INFO] Processed {i} emails, pausing briefly...")
                    import time
                    time.sleep(1)
                    
            except Exception as e:
                print(f"[ERROR] Failed to process record {i}: {str(e)}", file=sys.stderr)
                failed_count += 1
        
        print(f"[SUMMARY] Completed: {success_count} sent, {failed_count} failed")
        return True, {
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results
        }
        
    except Exception as e:
        error_msg = f"Batch processing failed: {str(e)}"
        print(f"[ERROR] {error_msg}", file=sys.stderr)
        return False, error_msg

def main():
    parser = argparse.ArgumentParser(description='Send emails with PDF attachments via Brevo')
    parser.add_argument('--data', required=True, help='JSON file with email data')
    parser.add_argument('--folder', required=True, help='Folder containing PDF files')
    parser.add_argument('--output', help='Output file for results (optional)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data):
        print(f"[ERROR] Email data file not found: {args.data}", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.exists(args.folder):
        print(f"[ERROR] PDF folder not found: {args.folder}", file=sys.stderr)
        sys.exit(1)
    
    success, result = process_email_batch(args.data, args.folder)
    
    if success:
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"[INFO] Results saved to: {args.output}")
        sys.exit(0)
    else:
        print(f"[ERROR] {result}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()