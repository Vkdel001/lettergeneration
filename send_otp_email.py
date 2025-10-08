#!/usr/bin/env python3
"""
OTP Email Sender
Uses existing Brevo setup to send OTP emails for authentication
"""

import sys
import os
import argparse
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Brevo Configuration (reusing existing setup)
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
    """Setup Brevo API client (reusing existing function)"""
    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = BREVO_API_KEY
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
        print("[INFO] Brevo client initialized successfully")
        return api_instance
    except Exception as e:
        print(f"[ERROR] Failed to initialize Brevo client: {str(e)}", file=sys.stderr)
        return None

def send_otp_email(api_instance, recipient_email, otp):
    """Send OTP email using existing Brevo setup"""
    try:
        # Create OTP email content
        subject = "NIC PDF Generator - Access Code"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #667eea; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0;">NIC PDF Generator</h1>
                    <p style="margin: 10px 0 0 0;">One-Time Password (OTP)</p>
                </div>
                
                <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px;">
                    <h2 style="color: #333; margin-top: 0;">Hello,</h2>
                    
                    <p>You have requested access to the NIC PDF Generator system. Please use the following OTP to complete your authentication:</p>
                    
                    <div style="background: white; padding: 20px; margin: 20px 0; text-align: center; border-radius: 8px; border: 2px solid #667eea;">
                        <div style="font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 5px; margin-bottom: 10px;">{otp}</div>
                        <p style="margin: 0;"><strong>This OTP is valid for 10 minutes only</strong></p>
                    </div>

                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="margin: 0 0 10px 0;"><strong>Security Notice:</strong></p>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>This OTP is for single use only</li>
                            <li>Do not share this code with anyone</li>
                            <li>If you didn't request this OTP, please ignore this email</li>
                            <li>The system is restricted to authorized NIC personnel only</li>
                        </ul>
                    </div>

                    <p>If you have any issues accessing the system, please contact your system administrator.</p>
                    
                    <p>Best regards,<br>
                    <strong>NIC Insurance IT Team</strong></p>
                </div>
                
                <div style="text-align: center; margin-top: 30px; color: #666; font-size: 12px;">
                    <p>© 2025 NIC Insurance - Secure PDF Generation System</p>
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create email object (reusing existing structure)
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[sib_api_v3_sdk.SendSmtpEmailTo(email=recipient_email, name="NIC User")],
            sender=sib_api_v3_sdk.SendSmtpEmailSender(email=SENDER_EMAIL, name=SENDER_NAME),
            reply_to=sib_api_v3_sdk.SendSmtpEmailReplyTo(email=REPLY_TO_EMAIL, name=REPLY_TO_NAME),
            subject=subject,
            html_content=html_content
        )
        
        # Send email
        api_response = api_instance.send_transac_email(send_smtp_email)
        message_id = api_response.message_id if hasattr(api_response, 'message_id') else 'unknown'
        
        print(f"[SUCCESS] OTP email sent to {recipient_email} - Message ID: {message_id}")
        return True, message_id
        
    except ApiException as e:
        error_msg = f"Brevo API error: {e.status} - {e.reason}"
        print(f"[ERROR] {error_msg}", file=sys.stderr)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"[ERROR] {error_msg}", file=sys.stderr)
        return False, error_msg

def main():
    parser = argparse.ArgumentParser(description='Send OTP email via existing Brevo setup')
    parser.add_argument('--email', required=True, help='Recipient email address')
    parser.add_argument('--otp', required=True, help='OTP code to send')
    
    args = parser.parse_args()
    
    # Setup Brevo client
    api_instance = setup_brevo_client()
    if not api_instance:
        print("[ERROR] Failed to initialize Brevo client", file=sys.stderr)
        sys.exit(1)
    
    # Send OTP email
    success, result = send_otp_email(api_instance, args.email, args.otp)
    
    if success:
        print(f"[INFO] OTP email sent successfully")
        sys.exit(0)
    else:
        print(f"[ERROR] Failed to send OTP email: {result}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()