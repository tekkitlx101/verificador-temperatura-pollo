import streamlit as st
import pandas as pd

st.title("✅ Verificador de temperatura del pollo")

uploaded_file = st.file_uploader("📤 Sube tu archivo CSV con la temperatura", type=["csv"])

temperatura_objetivo = st.number_input("🌡️ Temperatura mínima (°C)", min_value=0.0, value=72.0)
tiempo_objetivo = st.number_input("⏱️ Tiempo mínimo por encima de esa temperatura (segundos)", min_value=0.0, value=90.0)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, encoding='utf-8', engine='python')

    df.columns = [c.strip().lower().replace('á', 'a').replace('é', 'e').replace('í', 'i')
                  .replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n').replace('ã', 'a')
                  .replace('ü', 'u').replace('à', 'a').replace('ç', 'c').replace('ã', 'a')
                  for c in df.columns]

    if 'marca de tiempo' not in df.columns or 'temperatura real del nucleo' not in df.columns:
        st.error("El CSV debe tener las columnas 'marca de tiempo' y 'temperatura real del nucleo'")
    else:
        df['marca de tiempo'] = pd.to_datetime(df['marca de tiempo'], errors='coerce')
        df = df.dropna(subset=['marca de tiempo'])
        df = df.sort_values('marca de tiempo').reset_index(drop=True)

        df['temperatura real del nucleo'] = pd.to_numeric(df['temperatura real del nucleo'], errors='coerce')
        df = df.dropna(subset=['temperatura real del nucleo'])

        # Diferencia de tiempo entre lecturas
        df['tiempo_delta'] = df['marca de tiempo'].diff().dt.total_seconds().fillna(0)

        # Crear columna booleana para si temperatura está por encima del objetivo
        df['en_rango'] = df['temperatura real del nucleo'] >= temperatura_objetivo

        # Agrupar para encontrar intervalos continuos donde 'en_rango' es True o False
        df['grupo'] = (df['en_rango'] != df['en_rango'].shift()).cumsum()

        # Filtrar solo grupos donde 'en_rango' es True (por encima del umbral)
        grupos_en_rango = df[df['en_rango']].groupby('grupo')

        # Calcular duración de cada grupo como suma de tiempo_delta
        duraciones = grupos_en_rango['tiempo_delta'].sum()

        # Tiempo total acumulado (como antes)
        tiempo_total_en_rango = duraciones.sum()

        # Máximo tiempo continuo por encima de temperatura objetivo
        max_tiempo_continuo = duraciones.max() if not duraciones.empty else 0

        st.write(f"Tiempo total acumulado por encima de {temperatura_objetivo}°C: **{tiempo_total_en_rango:.2f} segundos**")
        st.write(f"Máximo tiempo continuo por encima de {temperatura_objetivo}°C: **{max_tiempo_continuo:.2f} segundos**")

        if max_tiempo_continuo >= tiempo_objetivo:
            st.success("✅ El pollo cumplió con el tiempo mínimo requerido de forma continua.")
        else:
            st.error("❌ El pollo NO cumplió con el tiempo mínimo requerido de forma continua.")
