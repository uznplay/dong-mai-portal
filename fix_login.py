
import os
from supabase import create_client, Client

# Service Key provided by user
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhud294Zmdta21vbndyd3V0ZW1wIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTU4NTc5OCwiZXhwIjoyMDg1MTYxNzk4fQ.z-k-6vYCgP4gcLuZzCYrgvU0cSefWoDScLhNJ0OIRT8"
URL = "https://hnwoxfgmkmonwrwutemp.supabase.co"

print(f"Connecting to {URL}...")
supabase: Client = create_client(URL, SERVICE_KEY)

EMAIL = "admin@dongmai.gov.vn"
PASSWORD = "admin123"

def fix_auth():
    print(f"1. Creating Auth User '{EMAIL}'...")
    try:
        # Create user in Supabase Auth
        # Note: supabase-py admin auth usage might differ slightly depending on version, 
        # but usually it's supabase.auth.admin.create_user
        
        # Check if user exists first to get ID
        # Listing users is one way, or just try create and catch error
        
        auth_user = None
        try:
             # Try creating
            res = supabase.auth.admin.create_user({
                "email": EMAIL,
                "password": PASSWORD,
                "email_confirm": True
            })
            auth_user = res
            print("   -> Auth User Created.")
        except Exception as e:
            print(f"   -> User might already exist or error: {e}")
            # Try to list users to find him
            # This is a bit hacky if create fails, but let's assume valid key allows listing
            try:
                users = supabase.auth.admin.list_users()
                for u in users:
                    if u.email == EMAIL:
                        auth_user = u
                        break
            except:
                pass

        if not auth_user:
            print("CRITICAL: Could not create or find Auth User.")
            return

        user_id = auth_user.id if hasattr(auth_user, 'id') else auth_user.user.id
        print(f"   -> Auth User ID: {user_id}")

        print("2. Syncing 'admin_users' table...")
        # Check existing admin in public table
        res = supabase.table("admin_users").select("*").eq("email", EMAIL).execute()
        
        if len(res.data) > 0:
            current_row = res.data[0]
            if current_row['id'] == user_id:
                print("   -> ID already matches. All good.")
                return
            
            print(f"   -> Mismatch! Table ID: {current_row['id']} != Auth ID: {user_id}")
            print("   -> Deleting old row...")
            supabase.table("admin_users").delete().eq("email", EMAIL).execute()
        
        print("   -> Inserting correct row...")
        new_admin = {
            "id": user_id, # IMPORTANCE: Force this ID
            "email": EMAIL,
            "password_hash": "$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZRGdjGj/nMskyBPMa6KCdXjQGpQla", # admin123 hash
            "full_name": "Quản trị viên hệ thống",
            "role": "super_admin",
            "is_active": True,
            "permissions": {"manage_users": True, "manage_news": True, "manage_settings": True, "view_stats": True}
        }
        supabase.table("admin_users").insert(new_admin).execute()
        print("SUCCESS: Admin user synced!")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_auth()
