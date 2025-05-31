# --- dashboard_v2 refinado y corregido ---
import streamlit as st
st.set_page_config(page_title="McCain Campaign Dashboard", layout="wide")

import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client
import numpy as np

load_dotenv()

# Configuración
SUPABASE_URL = st.secrets["general"]["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["general"]["SUPABASE_KEY"]
TABLE_NAME = st.secrets["general"]["TABLE_NAME"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Sidebar para seleccionar la página
st.sidebar.title("Navegación")
page = st.sidebar.radio("Selecciona una página", ["Dashboard General", "Análisis de Audiencia"])

# Cargar datos
response = supabase.table(TABLE_NAME).select("*").execute()
df = pd.DataFrame(response.data)

if df.empty:
    st.warning("⚠️ No hay datos disponibles.")
else:
    df['date_start'] = pd.to_datetime(df['date_start'])
    df['spend'] = pd.to_numeric(df['spend'], errors='coerce').fillna(0)
    df['impressions'] = pd.to_numeric(df['impressions'], errors='coerce').fillna(0)
    df['reach'] = pd.to_numeric(df['reach'], errors='coerce').fillna(0)
    df['total_engagements'] = pd.to_numeric(df['total_engagements'], errors='coerce').fillna(0)
    df['cpe'] = df['spend'] / df['total_engagements'].replace(0, np.nan)
    df['cpm'] = (df['spend'] / df['impressions'].replace(0, np.nan)) * 1000
    df['engagement_rate'] = df['total_engagements'] / df['impressions'].replace(0, np.nan)
    df['objective'] = df['objective'].astype(str).str.strip().str.lower()
    if 'platform' not in df.columns:
        df['platform'] = 'unknown'

if page == "Dashboard General":
    st.title("📊 Dashboard General McCain")

    date_min = pd.to_datetime("2024-01-01")
    date_max = df['date_start'].max()
    date_range = st.slider("Seleccionar rango de fechas", min_value=date_min.date(), max_value=date_max.date(), value=(date_min.date(), date_max.date()))
    filtered = df[(df['date_start'] >= pd.to_datetime(date_range[0])) & (df['date_start'] <= pd.to_datetime(date_range[1]))]
    objective_filter = st.selectbox("Filtrar por objetivo", ["Todos", "engagement", "awareness"])
    if objective_filter != "Todos":
        filtered = filtered[filtered['objective'].str.contains(objective_filter)]
    
    st.title("Vista combinada")
    
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    col1.metric("Total Reach", f"{filtered['reach'].sum():,.0f}")
    col2.metric("Total Impressions", f"{filtered['impressions'].sum():,.0f}")
    col3.metric("Post Engagements", f"{filtered['total_engagements'].sum():,.0f}")
    col4.metric("CPE (€)", f"{(filtered['spend'].sum() / filtered['total_engagements'].replace(0, np.nan).sum()):.2f}")
    col5.metric("CPM (€)", f"{(filtered['spend'].sum() / filtered['impressions'].replace(0, np.nan).sum())*1000:.2f}")
    col6.metric("Engagement Rate", f"{(filtered['engagement_rate'].mean() * 100):.2f}%")
    col7.metric("Amount Spent (€)", f"{filtered['spend'].sum():.2f}")

    # 🔥 Gráfico principal - limpio y legible 🔥
    selected_metrics = st.multiselect("Seleccionar métricas para el gráfico", ['reach', 'impressions', 'total_engagements', 'cpe', 'cpm', 'spend'], default=['reach', 'total_engagements'])

    # Limpiar datos (sin NaN, inf)
    clean_filtered = filtered.copy()
    for metric in ['cpe', 'cpm', 'engagement_rate']:
        clean_filtered[metric] = clean_filtered[metric].replace([np.inf, -np.inf], np.nan)

    grouped = clean_filtered.groupby('date_start').agg({
        'reach': 'sum',
        'impressions': 'sum',
        'total_engagements': 'sum',
        'spend': 'sum',
        'cpe': 'mean',
        'cpm': 'mean',
        'engagement_rate': 'mean'
    }).reset_index()

    fig = go.Figure()
    colors = {'reach': 'blue', 'impressions': 'green', 'total_engagements': 'orange', 'cpe': 'red', 'cpm': 'purple', 'spend': 'brown'}
    for metric in selected_metrics:
        yaxis_type = "y2" if metric in ['cpe', 'cpm', 'engagement_rate'] else "y"
        fig.add_trace(go.Scatter(
            x=grouped['date_start'],
            y=grouped[metric],
            mode='lines+markers',
            name=metric,
            yaxis=yaxis_type,
            line=dict(color=colors.get(metric, 'black'))
        ))
    fig.update_layout(yaxis=dict(title="Reach/Impressions/Engagements/Spend"), yaxis2=dict(title="CPE/CPM/Engagement Rate", overlaying="y", side="right"), title="Métricas globales por fecha")
    st.plotly_chart(fig, use_container_width=True)

    # Gráfico Amount Spent limpio
    total_spend = grouped.set_index('date_start')['spend']
    engagement_spend = filtered[filtered['objective'].str.contains('engagement', case=False, na=False)].groupby('date_start')['spend'].sum()
    awareness_spend = filtered[filtered['objective'].str.contains('awareness', case=False, na=False)].groupby('date_start')['spend'].sum()

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=total_spend.index, y=total_spend, mode='lines+markers', name="Total Spent"))
    fig2.add_trace(go.Scatter(x=engagement_spend.index, y=engagement_spend, mode='lines+markers', name="Engagement Spent"))
    fig2.add_trace(go.Scatter(x=awareness_spend.index, y=awareness_spend, mode='lines+markers', name="Awareness Spent"))
    fig2.update_layout(title="Evolución de gasto por día")
    st.plotly_chart(fig2, use_container_width=True)

    # Comparativa Facebook vs Instagram (filtro robusto)
    fb_df = filtered[filtered['platform'].str.lower().str.contains("facebook", na=False)]
    ig_df = filtered[filtered['platform'].str.lower().str.contains("instagram", na=False)]

    for metric, title in [("total_engagements", "Post Engagements Facebook vs Instagram"), ("reach", "Reach Facebook vs Instagram")]:
        fb_group = fb_df.groupby('date_start')[fb_df.select_dtypes(include='number').columns].mean().reset_index()
        ig_group = ig_df.groupby('date_start')[ig_df.select_dtypes(include='number').columns].mean().reset_index()
        
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=fb_group['date_start'], y=fb_group[metric], mode='lines+markers', name="Facebook"))
        fig3.add_trace(go.Scatter(x=ig_group['date_start'], y=ig_group[metric], mode='lines+markers', name="Instagram"))
        fig3.update_layout(title=title)
        st.plotly_chart(fig3, use_container_width=True)

    # Top 10 Ads por plataforma
    for platform_df, platform_name in [(fb_df, "Facebook"), (ig_df, "Instagram")]:
        if not platform_df.empty:
            top_ads = platform_df.groupby('ad_name').agg({'total_engagements':'sum','reach':'sum'}).reset_index().sort_values(by='total_engagements' if objective_filter=="engagement" else 'reach', ascending=False).head(10)
            st.subheader(f"Top 10 Ads en {platform_name}")
            st.dataframe(top_ads)
        else:
            st.warning(f"No hay datos para {platform_name}.")

            # 📈 Sección Predictiva Mejorada 📈
    st.header("🔮 Predicción de resultados")
    st.markdown("Introduce un presupuesto, duración, objetivo y mes para estimar el rendimiento esperado basado en datos históricos del mismo mes.")

    # Inputs del usuario
    budget = st.number_input("Introduce el presupuesto (€)", min_value=1, value=100)
    days = st.number_input("Introduce la duración (días)", min_value=1, value=5)
    campaign_type = st.selectbox("Selecciona tipo de campaña", ["engagement", "awareness"])
    month_selected = st.selectbox("Selecciona el mes para la predicción", [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ])

    # Mapear mes en español a número
    month_map = {
        'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6,
        'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
    }
    month_number = month_map.get(month_selected, None)

    # Filtrar datos históricos por tipo de campaña y mes
    hist_filtered = filtered[
        (filtered['objective'].str.contains(campaign_type, case=False, na=False)) &
        (filtered['date_start'].dt.month == month_number)
    ]

    # Calcular promedios históricos
    avg_cpm = hist_filtered['cpm'].mean()
    avg_cpe = hist_filtered['cpe'].mean()
    avg_engagement_rate = hist_filtered['engagement_rate'].mean()

    if pd.notna(avg_cpm) and pd.notna(avg_cpe) and not hist_filtered.empty:
        # Estimaciones
        total_spend = budget
        estimated_impressions = total_spend / (avg_cpm / 1000)
        estimated_engagements = total_spend / avg_cpe
        estimated_reach = estimated_impressions  # Estimación similar (ajustable)

        # Mostrar resultados
        st.subheader(f"Resultados estimados para {month_selected}:")
        col1, col2, col3 = st.columns(3)
        col1.metric("Reach estimado", f"{estimated_reach:,.0f}")
        col2.metric("Impresiones estimadas", f"{estimated_impressions:,.0f}")
        col3.metric("Engagements estimados", f"{estimated_engagements:,.0f}")

        st.write(f"CPM medio histórico ({month_selected}): €{avg_cpm:.2f}")
        st.write(f"CPE medio histórico ({month_selected}): €{avg_cpe:.2f}")
        st.write(f"Engagement Rate medio histórico ({month_selected}): {avg_engagement_rate * 100:.2f}%")
    else:
        st.warning(f"⚠️ No hay suficientes datos históricos para estimar el rendimiento en {month_selected} con el objetivo '{campaign_type}'.")

# Análisis de Audiencia 

elif page == "Análisis de Audiencia":
    st.title("👥 Análisis de Audiencia McCain")
    
    # Filtrar por plataforma
    platform_filter = st.selectbox("Seleccionar plataforma", ["Todas", "Facebook", "Instagram"])
    if platform_filter != "Todas":
        filtered = df[df['platform'].str.lower() == platform_filter.lower()]
    
    # Gráfico de distribución de objetivos
    objective_counts = filtered['objective'].value_counts()
    fig_objective = go.Figure(data=[go.Pie(labels=objective_counts.index, values=objective_counts.values)])
    fig_objective.update_layout(title="Distribución de Objetivos")
    st.plotly_chart(fig_objective, use_container_width=True)

    # Gráfico de distribución de plataformas
    platform_counts = filtered['platform'].value_counts()
    fig_platform = go.Figure(data=[go.Bar(x=platform_counts.index, y=platform_counts.values)])
    fig_platform.update_layout(title="Distribución de Plataformas")
    st.plotly_chart(fig_platform, use_container_width=True)

    # Gráfico de engagement por objetivo
    engagement_by_objective = filtered.groupby('objective')['total_engagements'].sum().reset_index()
    fig_engagement = go.Figure(data=[go.Bar(x=engagement_by_objective['objective'], y=engagement_by_objective['total_engagements'])])
    fig_engagement.update_layout(title="Engagement por Objetivo")
    st.plotly_chart(fig_engagement, use_container_width=True)
repr("")