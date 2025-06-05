import streamlit as st
import pandas as pd

st.title("✅ Verificador de temperatura del pollo")

uploaded_file = st.file_uploader("📤 Sube tu archivo CSV con la temperatura", type=["csv"])

temperatura_objetivo = st.number_input("🌡️ Temperatura mínima (°C)", min_value=0.0, value=83.0)
tiempo_objetivo_minutos = st.number_input("⏱️ Tiempo mínimo por encima de esa temperatura (minutos)", min_value=0.0, value=129.0)

def formato_tiempo(segundos):
    minutos = segundos / 60
    if minutos < 60:
        return f"{minutos:.2f} minutos"
    else:
        horas = minutos / 60
        return f"{horas:.2f} horas"

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

        df['tiempo_delta'] = df['marca de tiempo'].diff().dt.total_seconds().fillna(0)
        df['en_rango'] = df['temperatura real del nucleo'] >= temperatura_objetivo
        df['grupo'] = (df['en_rango'] != df['en_rango'].shift()).cumsum()

        grupos_en_rango = df[df['en_rango']].groupby('grupo')

        # Crear un dataframe con info de cada intervalo continuo arriba del umbral
        intervalos = grupos_en_rango.agg(
            inicio=('marca de tiempo', 'first'),
            fin=('marca de tiempo', 'last'),
            duracion_segundos=('tiempo_delta', 'sum')
        ).reset_index(drop=True)

        # Mostrar la tabla de intervalos con duración formateada
        intervalos['duracion'] = intervalos['duracion_segundos'].apply(formato_tiempo)

        tiempo_total_en_rango = intervalos['duracion_segundos'].sum()
        max_tiempo_continuo = intervalos['duracion_segundos'].max() if not intervalos.empty else 0

        st.write(f"Tiempo total acumulado por encima de {temperatura_objetivo}°C: **{formato_tiempo(tiempo_total_en_rango)}**")
        st.write(f"Máximo tiempo continuo por encima de {temperatura_objetivo}°C: **{formato_tiempo(max_tiempo_continuo)}**")

        # Convertir tiempo objetivo a segundos para la comparación
        tiempo_objetivo_segundos = tiempo_objetivo_minutos * 60

        if max_tiempo_continuo >= tiempo_objetivo_segundos:
            st.success("✅ El pollo cumplió con el tiempo mínimo requerido de forma continua.")
        else:
            st.error("❌ El pollo NO cumplió con el tiempo mínimo requerido de forma continua.")

        # Mostrar tabla con intervalos para verificación
        st.subheader("📅 Intervalos continuos donde la temperatura estuvo por encima del objetivo")
        st.dataframe(intervalos[['inicio', 'fin', 'duracion']])
