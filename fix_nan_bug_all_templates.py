#!/usr/bin/env python3
"""
Fix NaN Bug in All PDF Templates
This script fixes the TypeError: object of type 'float' has no len() issue
that occurs when owner1_first_name contains 'nan' values.
"""

import os
import re

# List of Python files to fix
template_files = [
    'SPH_Fresh_working.py',
    'SPH_Fresh_old.py', 
    'MED_SPH_Fresh_Signature.py',
    'MED_SPH_Fresh.py',
    'MED_JPH_Fresh_Signature07oct25.py',
    'MED_JPH_Fresh_Signature.py',
    'MED_JPH_Fresh.py',
    'JPH_Fresh_old2oct.py',
    'JPH_Fresh05oct.py',
    'JPH_Fresh02oct.py',
    'JPH_Fresh.py',
    'JPH_Fresh - Copy.py',
    'Company_Fresh05oct.py',
    'Company_Fresh.py'
]

# The problematic pattern to find
old_pattern = r"first_initial = owner1_first_name\[0\]\.upper\(\) if owner1_first_name and len\(owner1_first_name\) > 0 else ''"

# The safe replacement
new_pattern = """first_initial = ''
    if owner1_first_name and isinstance(owner1_first_name, str) and len(owner1_first_name) > 0 and owner1_first_name.lower() != 'nan':
        first_initial = owner1_first_name[0].upper()"""

# The surname pattern to find
surname_old_pattern = r"surname_part = owner1_surname\.strip\(\) if owner1_surname else ''"

# The safe surname replacement
surname_new_pattern = """# Handle surname safely (check for NaN and non-string values)
    surname_part = ''
    if owner1_surname and isinstance(owner1_surname, str) and owner1_surname.lower() != 'nan':
        surname_part = owner1_surname.strip()"""

def fix_file(filename):
    """Fix NaN handling in a single file"""
    if not os.path.exists(filename):
        print(f"⚠️  File not found: {filename}")
        return False
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file needs fixing
        if 'owner1_first_name[0].upper()' not in content:
            print(f"✅ {filename}: Already fixed or no issue found")
            return True
        
        # Fix first name handling
        content = re.sub(old_pattern, new_pattern, content)
        
        # Fix surname handling
        content = re.sub(surname_old_pattern, surname_new_pattern, content)
        
        # Write back the fixed content
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"🔧 {filename}: Fixed NaN handling")
        return True
        
    except Exception as e:
        print(f"❌ {filename}: Error - {str(e)}")
        return False

def main():
    print("🔧 Fixing NaN Bug in All PDF Templates")
    print("=====================================")
    print()
    
    fixed_count = 0
    total_count = 0
    
    for filename in template_files:
        total_count += 1
        if fix_file(filename):
            fixed_count += 1
    
    print()
    print(f"📊 Summary: {fixed_count}/{total_count} files processed successfully")
    print()
    print("🎯 What was fixed:")
    print("- Added isinstance(owner1_first_name, str) check")
    print("- Added owner1_first_name.lower() != 'nan' check") 
    print("- Added safe surname handling")
    print("- Prevents TypeError when Excel contains 'nan' values")
    print()
    print("✅ All templates should now handle NaN values safely!")

if __name__ == "__main__":
    main()