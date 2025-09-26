#!/usr/bin/env python3
"""
Brevo Email Sender Script
Sends emails with PDF attachments using Brevo API
"""

import pandas as pd
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import base64
import os
import sys
import json
import argparse
from pathlib import Path
import time

def setup_brevo_client(api_key):
    """Setup Brevo API client"""
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key
    return sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

def send_single_email(api_