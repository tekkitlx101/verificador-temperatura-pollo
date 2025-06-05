import streamlit as st
import pandas as pd

st.title("✅ Verificador de temperatura del pollo")

uploaded_file = st.file_uploader("📤 Sube tu archivo CSV con la temperatura", type=["csv"])

temperatura_objetivo = st.number_input("🌡️ Temperatura mínima (°C)", min_value=0.0, value=72.0)
tiempo_objetivo = st.number_input("⏱️ Tiempo mínimo por encima de esa temperatura (segundos)", min_value=0.0, value=90.0)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Asegurar columnas
    df.columns = [c.strip().lower() for c in df.columns]
    if 'timestamp' not in df.columns or 'temperature' not in df.columns:
        st.error("El CSV debe tener columnas 'timestamp' y 'temperature'")
    else:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        df['tiempo_delta'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
        tiempo_en_rango = df[df['temperature'] >= temperatura_objetivo]['tiempo_delta'].sum()

        st.write(f"Tiempo total por encima de {temperatura_objetivo}°C: **{tiempo_en_rango:.2f} segundos**")
        
        if tiempo_en_rango >= tiempo_objetivo:
            st.success("✅ El pollo cumplió con el tiempo mínimo requerido.")
        else:
            st.error("❌ El pollo NO cumplió con el tiempo mínimo requerido.")
