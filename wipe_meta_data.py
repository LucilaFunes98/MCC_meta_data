from supabase import create_client, Client

# Supabase setup
SUPABASE_URL = 'https://zcwxocyebcmlzuoqxhhe.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpjd3hvY3llYmNtbHp1b3F4aGhlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MjYzMjMyNywiZXhwIjoyMDU4MjA4MzI3fQ.3uygE9Pr9Zxe3-cva1RRhB8KyxHgm5QbdWA419Nv7tY'
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ask for confirmation
confirm = input("⚠️ This will DELETE ALL rows in 'mcc_meta_data'. Type YES to confirm: ")
if confirm.strip().upper() == "YES":
    response = supabase.table('mcc_meta_data').delete().not_.is_('id', None).execute()
    print("✅ All rows deleted successfully.")
else:
    print("❌ Deletion cancelled.")

