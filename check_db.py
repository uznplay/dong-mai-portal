
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: Missing SUPABASE_URL or SUPABASE_KEY in .env")
    exit(1)

print(f"Connecting to {url}...")
try:
    supabase: Client = create_client(url, key)
    # Try to select from admin_users
    response = supabase.table("admin_users").select("count", count="exact").execute()
    print("Connection Successful!")
    print(f"Admin Users Count: {response.count}")
    
    # Check featured_news
    response_news = supabase.table("featured_news").select("count", count="exact").execute()
    print(f"Featured News Count: {response_news.count}")
    
except Exception as e:
    print(f"Connection Failed or Tables Missing: {e}")
    # Check if specifics
    if "relation" in str(e) and "does not exist" in str(e):
         print("CRITICAL: Tables do not exist. Please run the SQL scripts.")
    exit(1)
