# -*- coding: utf-8 -*-
"""
API Configuration File
Contains all API endpoints, payloads, and configuration for reuse across projects
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# BREVO EMAIL API CONFIGURATION
# =============================================================================

class BrevoAPI:
    """Brevo Email API Configuration and Helper Functions"""
    
    # API Configuration
    BASE_URL = "https://api.brevo.com/v3"
    SEND_EMAIL_ENDPOINT = f"{BASE_URL}/smtp/email"
    
    # Default headers (API key should be set when using)
    DEFAULT_HEADERS = {
        "accept": "application/json",
        "content-type": "application/json"
    }
    
    # Get API key from environment variable
    @staticmethod
    def get_api_key():
        """Get Brevo API key from environment variable"""
        api_key = os.getenv('BREVO_API_KEY')
        if not api_key:
            raise ValueError("BREVO_API_KEY not found in environment variables. Please set it in .env file")
        return api_key
    
    @staticmethod
    def get_headers(api_key):
        """Get headers with API key"""
        headers = BrevoAPI.DEFAULT_HEADERS.copy()
        headers["api-key"] = api_key
        return headers
    
    @staticmethod
    def create_email_payload(sender_email, sender_name, recipient_email, recipient_name, 
                           subject, html_content, attachment_content=None, attachment_name=None):
        """
        Create email payload for Brevo API
        
        Args:
            sender_email (str): Sender's email address
            sender_name (str): Sender's name
            recipient_email (str): Recipient's email address
            recipient_name (str): Recipient's name
            subject (str): Email subject
            html_content (str): HTML content of the email
            attachment_content (bytes, optional): PDF attachment content
            attachment_name (str, optional): Name of the attachment file
        
        Returns:
            dict: Brevo API payload
        """
        payload = {
            "sender": {
                "name": sender_name,
                "email": sender_email
            },
            "to": [
                {
                    "email": recipient_email,
                    "name": recipient_name
                }
            ],
            "subject": subject,
            "htmlContent": html_content
        }
        
        # Add attachment if provided
        if attachment_content and attachment_name:
            import base64
            attachment_base64 = base64.b64encode(attachment_content).decode('utf-8')
            payload["attachment"] = [
                {
                    "content": attachment_base64,
                    "name": attachment_name
                }
            ]
        
        return payload
    
    @staticmethod
    def send_email(payload, api_key=None):
        """
        Send email via Brevo API
        
        Args:
            payload (dict): Email payload
            api_key (str, optional): Brevo API key (if not provided, uses environment variable)
        
        Returns:
            dict: API response
        """
        if api_key is None:
            api_key = BrevoAPI.get_api_key()
        try:
            headers = BrevoAPI.get_headers(api_key)
            response = requests.post(
                BrevoAPI.SEND_EMAIL_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            return {
                "success": response.status_code == 201,
                "status_code": response.status_code,
                "response": response.json() if response.content else {},
                "message_id": response.json().get("messageId") if response.content else None
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": None,
                "response": {},
                "message_id": None
            }
    
    @staticmethod
    def send_simple_email(recipient_email, recipient_name, subject, html_content, 
                         attachment_content=None, attachment_name=None,
                         sender_email=None, sender_name=None, api_key=None):
        """
        Send email with default sender configuration
        
        Args:
            recipient_email (str): Recipient's email
            recipient_name (str): Recipient's name
            subject (str): Email subject
            html_content (str): HTML content
            attachment_content (bytes, optional): PDF attachment
            attachment_name (str, optional): Attachment filename
            sender_email (str, optional): Sender email (uses env var if not provided)
            sender_name (str, optional): Sender name (uses env var if not provided)
            api_key (str, optional): API key (uses env var if not provided)
        
        Returns:
            dict: API response
        """
        # Use environment variables for defaults
        if sender_email is None:
            sender_email = os.getenv('DEFAULT_SENDER_EMAIL', 'noreply@nic.mu')
        if sender_name is None:
            sender_name = os.getenv('DEFAULT_SENDER_NAME', 'NIC Insurance')
        
        payload = BrevoAPI.create_email_payload(
            sender_email=sender_email,
            sender_name=sender_name,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=subject,
            html_content=html_content,
            attachment_content=attachment_content,
            attachment_name=attachment_name
        )
        
        return BrevoAPI.send_email(payload, api_key)

# =============================================================================
# ZWENNPAY QR CODE API CONFIGURATION
# =============================================================================

class ZwennPayAPI:
    """ZwennPay QR Code API Configuration and Helper Functions"""
    
    # API Configuration
    BASE_URL = "https://api.zwennpay.com:9425"
    QR_ENDPOINT = f"{BASE_URL}/api/v1.0/Common/GetMerchantQR"
    
    # Default headers
    DEFAULT_HEADERS = {
        "accept": "text/plain",
        "Content-Type": "application/json"
    }
    
    # Default merchant configuration
    DEFAULT_MERCHANT_ID = 151
    
    @staticmethod
    def create_qr_payload(amount, policy_no, mobile_no, customer_name, nic, 
                         merchant_id=None):
        """
        Create QR code payload for ZwennPay API
        
        Args:
            amount (float): Transaction amount
            policy_no (str): Policy number (bill number)
            mobile_no (str): Customer mobile number
            customer_name (str): Customer name (max 24 chars)
            nic (str): Customer NIC number
            merchant_id (int, optional): Merchant ID (defaults to 151)
        
        Returns:
            dict: ZwennPay API payload
        """
        if merchant_id is None:
            merchant_id = ZwennPayAPI.DEFAULT_MERCHANT_ID
        
        # Ensure customer name is max 24 characters
        if len(customer_name) > 24:
            customer_name = customer_name[:24]
        
        payload = {
            "MerchantId": merchant_id,
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
            "AdditionalCustomerLabel": str(customer_name),
            "SetAdditionalTerminalLabel": False,
            "AdditionalRequiredTerminalLabel": False,
            "AdditionalTerminalLabel": "",
            "SetAdditionalPurposeTransaction": True,
            "AdditionalRequiredPurposeTransaction": False,
            "AdditionalPurposeTransaction": str(nic)
        }
        
        return payload
    
    @staticmethod
    def generate_qr_code(amount, policy_no, mobile_no, customer_name, nic, 
                        merchant_id=None, timeout=20):
        """
        Generate QR code via ZwennPay API
        
        Args:
            amount (float): Transaction amount
            policy_no (str): Policy number
            mobile_no (str): Customer mobile number
            customer_name (str): Customer name
            nic (str): Customer NIC
            merchant_id (int, optional): Merchant ID
            timeout (int, optional): Request timeout in seconds
        
        Returns:
            dict: API response with QR data
        """
        try:
            payload = ZwennPayAPI.create_qr_payload(
                amount, policy_no, mobile_no, customer_name, nic, merchant_id
            )
            
            response = requests.post(
                ZwennPayAPI.QR_ENDPOINT,
                headers=ZwennPayAPI.DEFAULT_HEADERS,
                json=payload,
                timeout=timeout
            )
            
            if response.status_code == 200:
                qr_data = str(response.text).strip()
                if qr_data and qr_data.lower() not in ('null', 'none', 'nan'):
                    return {
                        "success": True,
                        "qr_data": qr_data,
                        "status_code": response.status_code,
                        "error": None
                    }
                else:
                    return {
                        "success": False,
                        "qr_data": None,
                        "status_code": response.status_code,
                        "error": "No valid QR data received"
                    }
            else:
                return {
                    "success": False,
                    "qr_data": None,
                    "status_code": response.status_code,
                    "error": f"API request failed: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "qr_data": None,
                "status_code": None,
                "error": f"Network error: {str(e)}"
            }

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

def example_brevo_usage():
    """Example of how to use Brevo API"""
    
    # Method 1: Simple email (uses environment variables)
    result = BrevoAPI.send_simple_email(
        recipient_email="customer@example.com",
        recipient_name="John Doe",
        subject="Your Insurance Policy Arrears",
        html_content="<h1>Dear John Doe,</h1><p>Your policy has arrears...</p>"
    )
    
    if result["success"]:
        print(f"Email sent successfully! Message ID: {result['message_id']}")
    else:
        print(f"Email failed: {result['error']}")
    
    # Method 2: Manual configuration
    payload = BrevoAPI.create_email_payload(
        sender_email="noreply@nic.mu",
        sender_name="NIC Insurance",
        recipient_email="customer@example.com",
        recipient_name="John Doe",
        subject="Your Insurance Policy Arrears",
        html_content="<h1>Dear John Doe,</h1><p>Your policy has arrears...</p>",
        attachment_content=None,  # PDF bytes would go here
        attachment_name="policy_letter.pdf"
    )
    
    # Send email (API key from environment)
    result = BrevoAPI.send_email(payload)
    
    if result["success"]:
        print(f"Email sent successfully! Message ID: {result['message_id']}")
    else:
        print(f"Email failed: {result['error']}")

def example_zwennpay_usage():
    """Example of how to use ZwennPay API"""
    
    # Generate QR code
    result = ZwennPayAPI.generate_qr_code(
        amount=1500.00,
        policy_no="00407/0095764",
        mobile_no="59892555",
        customer_name="John Doe",
        nic="A091289380036E"
    )
    
    if result["success"]:
        print(f"QR code generated successfully!")
        print(f"QR Data: {result['qr_data']}")
        
        # You can now use the QR data with segno to create the actual QR image
        import segno
        qr = segno.make(result['qr_data'], error='L')
        qr.save("payment_qr.png", scale=8, border=2, dark='#000000')
        
    else:
        print(f"QR generation failed: {result['error']}")

if __name__ == "__main__":
    print("API Configuration loaded successfully!")
    print("Available classes: BrevoAPI, ZwennPayAPI")
    print("Run example_brevo_usage() or example_zwennpay_usage() to see examples")