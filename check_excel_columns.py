#!/usr/bin/env python3
"""
Check Excel columns for Motor Insurance Renewal
"""

import pandas as pd

try:
    df = pd.read_excel('output_motor_renewal.xlsx')
    print(f"📊 Excel file loaded: {len(df)} rows")
    print(f"\n📋 Available columns:")
    for i, col in enumerate(df.columns, 1):
        print(f"{i:2d}. {col}")
    
    print(f"\n🔍 First row sample data:")
    first_row = df.iloc[0]
    for col in df.columns:
        value = first_row[col]
        if pd.isna(value):
            value = "NaN"
        print(f"{col}: '{value}'")
        
    # Check for mobile-related columns
    mobile_cols = [col for col in df.columns if 'mobile' in col.lower() or 'phone' in col.lower() or 'tel' in col.lower()]
    if mobile_cols:
        print(f"\n📱 Mobile-related columns found: {mobile_cols}")
    else:
        print(f"\n❌ No mobile-related columns found")
        
except Exception as e:
    print(f"❌ Error: {e}")