#!/usr/bin/env python3
"""
Completion Email Notification Service
Sends email notifications when PDF generation or SMS link generation is completed
"""

import sys
import os
import json
import argparse
from datetime import datetime
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Brevo Configuration
BREVO_API_KEY = os.getenv('BREVO_API_KEY')
SENDER_EMAIL = "system@niclmauritius.site"
SENDER_NAME = "NICL System Notifications"
REPLY_TO_EMAIL = "support@niclmauritius.site"
REPLY_TO_NAME = "NICL Support"

def setup_brevo_client():
    """Setup Brevo API client"""
    try:
        if not BREVO_API_KEY:
            print("[ERROR] BREVO_API_KEY not found in environment variables")
            return None
            
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = BREVO_API_KEY
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
        return api_instance
    except Exception as e:
        print(f"[ERROR] Failed to initialize Brevo client: {str(e)}")
        return None

def send_pdf_completion_email(user_email, user_name, folder_name, pdf_count, processing_time, template_type):
    """Send email notification when PDF generation is completed"""
    try:
        api_instance = setup_brevo_client()
        if not api_instance:
            return False, "Failed to initialize email client"

        subject = f"✅ PDF Generation Completed - {folder_name}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
                    <h2 style="margin: 0; font-size: 24px;">✅ PDF Generation Completed</h2>
                </div>
                
                <p>Dear {user_name},</p>
                
                <p>Your PDF generation task has been completed successfully!</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #28a745; margin-top: 0;">Generation Summary</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">📁 Output Folder:</td>
                            <td style="padding: 8px 0;">{folder_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">📄 PDFs Generated:</td>
                            <td style="padding: 8px 0; color: #28a745; font-weight: bold;">{pdf_count} files</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">🏷️ Template Used:</td>
                            <td style="padding: 8px 0;">{template_type}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">⏱️ Processing Time:</td>
                            <td style="padding: 8px 0;">{processing_time}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">📅 Completed At:</td>
                            <td style="padding: 8px 0;">{datetime.now().strftime('%d %B %Y at %H:%M')}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #e7f3ff; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Next Steps:</strong></p>
                    <ul style="margin: 10px 0;">
                        <li>Your PDFs are ready for download in the system</li>
                        <li>You can now generate SMS links for customer notifications</li>
                        <li>Use the "Combine PDFs" feature if needed</li>
                    </ul>
                </div>
                
                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://niclmauritius.site/" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        🔗 Access System
                    </a>
                </p>
                
                <p>Best regards,<br>
                <strong>NICL System</strong></p>
                
                <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    This is an automated notification. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[sib_api_v3_sdk.SendSmtpEmailTo(email=user_email, name=user_name)],
            sender=sib_api_v3_sdk.SendSmtpEmailSender(email=SENDER_EMAIL, name=SENDER_NAME),
            reply_to=sib_api_v3_sdk.SendSmtpEmailReplyTo(email=REPLY_TO_EMAIL, name=REPLY_TO_NAME),
            subject=subject,
            html_content=html_content
        )
        
        api_response = api_instance.send_transac_email(send_smtp_email)
        message_id = api_response.message_id if hasattr(api_response, 'message_id') else 'unknown'
        
        print(f"[SUCCESS] PDF completion email sent to {user_email} - Message ID: {message_id}")
        return True, message_id
        
    except Exception as e:
        error_msg = f"Failed to send PDF completion email: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return False, error_msg

def send_sms_completion_email(user_email, user_name, folder_name, sms_count, processing_time, template_type):
    """Send email notification when SMS link generation is completed"""
    try:
        api_instance = setup_brevo_client()
        if not api_instance:
            return False, "Failed to initialize email client"

        subject = f"📱 SMS Links Generated - {folder_name}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #6f42c1, #e83e8c); color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
                    <h2 style="margin: 0; font-size: 24px;">📱 SMS Links Generated</h2>
                </div>
                
                <p>Dear {user_name},</p>
                
                <p>Your SMS link generation task has been completed successfully!</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #6f42c1; margin-top: 0;">Generation Summary</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">📁 Source Folder:</td>
                            <td style="padding: 8px 0;">{folder_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">📱 SMS Links Created:</td>
                            <td style="padding: 8px 0; color: #6f42c1; font-weight: bold;">{sms_count} links</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">🏷️ Template Type:</td>
                            <td style="padding: 8px 0;">{template_type}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">⏱️ Processing Time:</td>
                            <td style="padding: 8px 0;">{processing_time}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; font-weight: bold;">📅 Completed At:</td>
                            <td style="padding: 8px 0;">{datetime.now().strftime('%d %B %Y at %H:%M')}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <p style="margin: 0;"><strong>📋 Next Steps:</strong></p>
                    <ul style="margin: 10px 0;">
                        <li>Download the SMS batch file from the system</li>
                        <li>Import the CSV file into your SMS platform</li>
                        <li>SMS links expire in 30 days for security</li>
                        <li>Each link can be accessed up to 10 times</li>
                    </ul>
                </div>
                
                <div style="background-color: #d1ecf1; padding: 15px; border-left: 4px solid #17a2b8; margin: 20px 0;">
                    <p style="margin: 0;"><strong>🔗 SMS Link Features:</strong></p>
                    <ul style="margin: 10px 0;">
                        <li>Mobile-optimized letter viewer</li>
                        <li>QR codes for instant payments</li>
                        <li>PDF download capability</li>
                        <li>Secure, time-limited access</li>
                    </ul>
                </div>
                
                <p style="text-align: center; margin: 30px 0;">
                    <a href="https://niclmauritius.site/" style="background-color: #6f42c1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        📱 Download SMS File
                    </a>
                </p>
                
                <p>Best regards,<br>
                <strong>NICL System</strong></p>
                
                <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    This is an automated notification. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[sib_api_v3_sdk.SendSmtpEmailTo(email=user_email, name=user_name)],
            sender=sib_api_v3_sdk.SendSmtpEmailSender(email=SENDER_EMAIL, name=SENDER_NAME),
            reply_to=sib_api_v3_sdk.SendSmtpEmailReplyTo(email=REPLY_TO_EMAIL, name=REPLY_TO_NAME),
            subject=subject,
            html_content=html_content
        )
        
        api_response = api_instance.send_transac_email(send_smtp_email)
        message_id = api_response.message_id if hasattr(api_response, 'message_id') else 'unknown'
        
        print(f"[SUCCESS] SMS completion email sent to {user_email} - Message ID: {message_id}")
        return True, message_id
        
    except Exception as e:
        error_msg = f"Failed to send SMS completion email: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return False, error_msg

def main():
    parser = argparse.ArgumentParser(description='Send completion notification emails')
    parser.add_argument('--type', required=True, choices=['pdf', 'sms'], help='Notification type')
    parser.add_argument('--email', required=True, help='User email address')
    parser.add_argument('--name', required=True, help='User name')
    parser.add_argument('--folder', required=True, help='Folder name')
    parser.add_argument('--count', required=True, type=int, help='Number of items processed')
    parser.add_argument('--time', required=True, help='Processing time')
    parser.add_argument('--template', required=True, help='Template type')
    
    args = parser.parse_args()
    
    if args.type == 'pdf':
        success, result = send_pdf_completion_email(
            args.email, args.name, args.folder, args.count, args.time, args.template
        )
    elif args.type == 'sms':
        success, result = send_sms_completion_email(
            args.email, args.name, args.folder, args.count, args.time, args.template
        )
    
    if success:
        print(f"[SUCCESS] Completion email sent successfully")
        sys.exit(0)
    else:
        print(f"[ERROR] Failed to send completion email: {result}")
        sys.exit(1)

if __name__ == "__main__":
    main()