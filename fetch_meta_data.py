from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from supabase import create_client
from datetime import datetime, timedelta

# --- Configuración ---
ACCESS_TOKEN = 'EACG4WGYXqIcBO043eX4gUfeTAmeoeiGEvh8PzhxTC4RCCNaGXWZC3bs7H3TocRwUf6KqWwvdveDSPqSVybZAZBwBJwzi0Fp9zLRtmFvqcNTl0X2fWWfsQQ8Y856N1wwcrBwuZAritZCp75v5TsSyTxXO5ecPIDIBGOrfZAUxs3sZAoNYe6PoICNMt0dRZBwZD'
AD_ACCOUNT_ID = 'act_1442495952786268'
APP_ID = '9491364040910983'
APP_SECRET = 'cfcb34ec40d36a7eb352d061362be5c7'
SUPABASE_URL = 'https://zcwxocyebcmlzuoqxhhe.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpjd3hvY3llYmNtbHp1b3F4aGhlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MjYzMjMyNywiZXhwIjoyMDU4MjA4MzI3fQ.3uygE9Pr9Zxe3-cva1RRhB8KyxHgm5QbdWA419Nv7tY'
TABLE_NAME = 'mcc_meta_data'

# Inicializar Facebook API
FacebookAdsApi.init(APP_ID, APP_SECRET, ACCESS_TOKEN)
account = AdAccount(AD_ACCOUNT_ID)

# Inicializar Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Limpiar tabla antes de cargar nuevos datos
print(f"🧹 Limpiando tabla '{TABLE_NAME}'...")
supabase.table(TABLE_NAME).delete().neq('id', 0).execute()
print("✅ Tabla limpiada.")

# --- Parámetros de fechas ---
since_date = datetime(2024, 1, 1)
until_date = datetime.today()
chunk_size = 7  # Días por chunk

fields = [
    AdsInsights.Field.campaign_name,
    AdsInsights.Field.adset_name,
    AdsInsights.Field.ad_name,
    AdsInsights.Field.date_start,
    AdsInsights.Field.date_stop,
    AdsInsights.Field.spend,
    AdsInsights.Field.impressions,
    AdsInsights.Field.reach,
    AdsInsights.Field.actions,
    AdsInsights.Field.objective,
]

print(f"📅 Obteniendo datos del {since_date.date()} al {until_date.date()}...")
current_date = since_date
data_to_insert = []

while current_date < until_date:
    chunk_end = min(current_date + timedelta(days=chunk_size - 1), until_date)
    params = {
        'level': 'ad',
        'time_range': {'since': current_date.strftime('%Y-%m-%d'), 'until': chunk_end.strftime('%Y-%m-%d')},
        'time_increment': 1,
        'limit': 1000,
    }
    print(f"📆 Fetching {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}")

    try:
        insights = account.get_insights(fields=fields, params=params)
        for ad in insights:
            actions = ad.get('actions', [])
            post_engagement_value = 0
            video_views_3s_value = 0

            for action in actions:
                if action['action_type'] == 'post_engagement':
                    post_engagement_value = int(action.get('value', 0))
                elif action['action_type'] in ['video_view', 'video_view_3s']:
                    video_views_3s_value += int(action.get('value', 0))

            true_engagements = post_engagement_value - video_views_3s_value
            if true_engagements < 0:
                true_engagements = 0  # Seguridad

            impressions = int(ad.get('impressions', 0))
            spend = float(ad.get('spend', 0))
            engagement_rate = (true_engagements / impressions * 100) if impressions > 0 else 0
            cpe = (spend / true_engagements) if true_engagements > 0 else 0
            cpm = (spend / impressions * 1000) if impressions > 0 else 0

            adset_name = ad.get ('adset_name', '').lower()
            if 'instagram' in adset_name:
                platform = 'instagram'
            elif 'facebook' in adset_name:
                platform = 'facebook'
            else:
                platform = 'unknown'

            data_to_insert.append({
                'campaign_name': ad.get('campaign_name', ''),
                'adset_name': ad.get('adset_name', ''),
                'ad_name': ad.get('ad_name', ''),
                'date_start': ad.get('date_start', ''),
                'date_stop': ad.get('date_stop', ''),
                'spend': spend,
                'impressions': impressions,
                'reach': int(ad.get('reach', 0)),
                'actions': actions,
                'objective': ad.get('objective', ''),
                'total_engagements': true_engagements,
                'engagement_rate': engagement_rate,
                'cpe': spend / true_engagements if true_engagements > 0 else 0,
                'cpm': cpm,
                'platform': platform,
            })

    except Exception as e:
        print(f"❌ Error fetching: {e}")

    current_date += timedelta(days=chunk_size)

if data_to_insert:
    supabase.table(TABLE_NAME).insert(data_to_insert).execute()
    print(f"✅ {len(data_to_insert)} registros insertados.")
else:
    print("⚠️ No se obtuvieron datos.")
