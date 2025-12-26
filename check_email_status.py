#!/usr/bin/env python3
"""
Email Status Checker
Checks the current email configuration and provides troubleshooting info
"""

import os
import sys
from dotenv import load_dotenv

def check_email_status():
    """Check current email configuration status"""
    print("📧 NICL Email System Status Check")
    print("=" * 50)
    
    # Check .env file
    print("1. 📁 Checking .env file...")
    if os.path.exists('.env'):
        print("   ✅ .env file found")
        load_dotenv()
    else:
        print("   ❌ .env file not found")
        print("   🔧 Create a .env file with BREVO_API_KEY")
        return False
    
    # Check Brevo API key
    print("\n2. 🔑 Checking Brevo API key...")
    brevo_key = os.getenv('BREVO_API_KEY')
    if brevo_key:
        print(f"   ✅ BREVO_API_KEY found: {brevo_key[:20]}...")
    else:
        print("   ❌ BREVO_API_KEY not found in .env")
        print("   🔧 Add BREVO_API_KEY=your_key_here to .env file")
        return False
    
    # Check completion email service
    print("\n3. 📄 Checking completion_email_service.py...")
    if os.path.exists('completion_email_service.py'):
        print("   ✅ completion_email_service.py found")
    else:
        print("   ❌ completion_email_service.py not found")
        return False
    
    # Check environment variables (set by server)
    print("\n4. 👤 Checking user email configuration...")
    user_email = os.getenv('USER_EMAIL')
    user_name = os.getenv('USER_NAME')
    
    if user_email:
        print(f"   ✅ User email configured: {user_email}")
        print(f"   ✅ User name: {user_name or 'NICL User'}")
    else:
        print("   ⚠️ User email not configured")
        print("   💡 Configure in the 'Email Notifications' tab in the web interface")
    
    # Test Brevo connection
    print("\n5. 🌐 Testing Brevo API connection...")
    try:
        import sib_api_v3_sdk
        from sib_api_v3_sdk.rest import ApiException
        
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = brevo_key
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
        
        # Try to get account info (this tests the API key)
        account_api = sib_api_v3_sdk.AccountApi(sib_api_v3_sdk.ApiClient(configuration))
        account_info = account_api.get_account()
        
        print(f"   ✅ Brevo API connection successful")
        print(f"   📊 Account: {account_info.company_name if hasattr(account_info, 'company_name') else 'Connected'}")
        
    except ImportError:
        print("   ❌ sib_api_v3_sdk not installed")
        print("   🔧 Run: pip install sib-api-v3-sdk")
        return False
    except ApiException as e:
        print(f"   ❌ Brevo API error: {e.status} - {e.reason}")
        print("   🔧 Check your BREVO_API_KEY in .env file")
        return False
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("📊 OVERALL STATUS")
    print("=" * 50)
    print("✅ Email system is properly configured!")
    print("\n💡 How to use:")
    print("1. Configure your email in the 'Email Notifications' tab")
    print("2. Generate PDFs or SMS links")
    print("3. Check your email for completion notifications")
    
    if not user_email:
        print("\n⚠️ NEXT STEP: Configure your email address in the web interface")
    
    return True

def show_troubleshooting():
    """Show troubleshooting information"""
    print("\n🔧 TROUBLESHOOTING GUIDE")
    print("=" * 50)
    print("If emails are not being sent, check:")
    print()
    print("1. 📁 .env file exists with BREVO_API_KEY")
    print("2. 🔑 Brevo API key is valid and active")
    print("3. 👤 User email is configured in the web interface")
    print("4. 📧 Check spam/junk folder in your email")
    print("5. 🌐 Internet connection is working")
    print("6. 📄 completion_email_service.py file exists")
    print()
    print("📞 For Brevo account issues:")
    print("   - Login to https://app.brevo.com")
    print("   - Check API key in Settings > API Keys")
    print("   - Verify account is active and not suspended")
    print()
    print("🧪 To test email system:")
    print("   python test_email_system.py your-email@example.com")

if __name__ == "__main__":
    success = check_email_status()
    
    if not success:
        show_troubleshooting()
        sys.exit(1)
    
    # Ask if user wants to run a test
    if len(sys.argv) == 1:  # No email provided
        test_email = input("\n🧪 Want to send a test email? Enter your email (or press Enter to skip): ").strip()
        if test_email and '@' in test_email:
            print(f"\n🚀 Running test email to: {test_email}")
            os.system(f'python test_email_system.py "{test_email}"')
    
    print("\n✅ Email status check complete!")