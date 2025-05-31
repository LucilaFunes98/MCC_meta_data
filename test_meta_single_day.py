from datetime import datetime
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights

# Meta API credentials
access_token = os.getenv('ACCESS_TOKEN')
app_id = os.getenv('APP_ID')
app_secret = os.getenv('APP_SECRET')

FacebookAdsApi.init(app_id, app_secret, access_token)

# Query for a **single day**
params = {
    'level': 'ad',
    'time_range': {'since': '2024-01-01', 'until': '2024-01-07'},
    # REMOVE time_increment
    'fields': [
        'ad_name',
        'campaign_name',
        'impressions',
        'spend',
        'date_start',
        'date_stop',
        'actions'
    ]
}


print("🚀 Sending request...")

try:
    insights = AdAccount(ad_account_id).get_insights(params=params)
    for ad in insights:
        print("✅ Got ad:", ad['ad_name'], ad['date_start'], ad['spend'])
except Exception as e:
    print("❌ Error:", e)
