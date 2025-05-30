from supabase import create_client, Client

# Supabase setup
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ask for confirmation
confirm = input("⚠️ This will DELETE ALL rows in 'mcc_meta_data'. Type YES to confirm: ")
if confirm.strip().upper() == "YES":
    response = supabase.table('mcc_meta_data').delete().not_.is_('id', None).execute()
    print("✅ All rows deleted successfully.")
else:
    print("❌ Deletion cancelled.")

