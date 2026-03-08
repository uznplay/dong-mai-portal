
import os
from supabase import create_client, Client

# User provided Service Key
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhud294Zmdta21vbndyd3V0ZW1wIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTU4NTc5OCwiZXhwIjoyMDg1MTYxNzk4fQ.z-k-6vYCgP4gcLuZzCYrgvU0cSefWoDScLhNJ0OIRT8"
URL = "https://hnwoxfgmkmonwrwutemp.supabase.co"

print(f"Connecting to {URL} with Service Key...")

try:
    supabase: Client = create_client(URL, SERVICE_KEY)
    
    # Check if 'admin_users' table exists by selecting 0 rows, ignoring error?
    # Supabase-py throws error if table doesn't exist.
    print("Checking 'admin_users' table...")
    try:
        response = supabase.table("admin_users").select("id").limit(1).execute()
        print("Table 'admin_users' EXISTS.")
        
        # Check if admin exists
        print("Checking for admin account...")
        response = supabase.table("admin_users").select("*").eq("email", "admin@dongmai.gov.vn").execute()
        
        if len(response.data) == 0:
            print("Admin not found. Creating default admin...")
            # Insert admin
            new_admin = {
                "email": "admin@dongmai.gov.vn",
                "password_hash": "$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZRGdjGj/nMskyBPMa6KCdXjQGpQla",
                "full_name": "Quản trị viên hệ thống",
                "role": "super_admin",
                "is_active": True,
                "permissions": {"manage_users": True, "manage_news": True, "manage_settings": True, "view_stats": True}
            }
            res = supabase.table("admin_users").insert(new_admin).execute()
            print("Admin created successfully!")
        else:
            print("Admin account already exists.")
            
    except Exception as table_err:
        print(f"Error accessing table: {table_err}")
        if "relation" in str(table_err) and "does not exist" in str(table_err):
            print("CONCLUSION: Tables do not exist.")
        else:
            print("CONCLUSION: Unknown error accessing tables.")

except Exception as e:
    print(f"Connection Failed: {e}")
