import streamlit as st
import pandas as pd
import altair as alt

st.title("✅ Verificador de temperatura del pollo")

uploaded_file = st.file_uploader("📤 Sube tu archivo CSV con la temperatura", type=["csv"])

temperatura_objetivo = st.number_input(
    "🌡️ Temperatura mínima (°C)", 
    min_value=0, 
    value=83, 
    step=1
)

tiempo_objetivo_minutos = st.number_input(
    "⏱️ Tiempo mínimo por encima de esa temperatura (minutos)", 
    min_value=0, 
    value=129, 
    step=1
)

def formato_tiempo(segundos):
    minutos_totales = int(round(segundos / 60))
    if minutos_totales < 60:
        return f"{minutos_totales} minutos"
    else:
        horas = minutos_totales // 60
        minutos = minutos_totales % 60
        return f"{horas} horas {minutos} minutos"

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

        intervalos = grupos_en_rango.agg(
            inicio=('marca de tiempo', 'first'),
            fin=('marca de tiempo', 'last'),
            duracion_segundos=('tiempo_delta', 'sum')
        ).reset_index(drop=True)

        # Mostrar solo la hora en inicio y fin
        intervalos['inicio'] = intervalos['inicio'].dt.time
        intervalos['fin'] = intervalos['fin'].dt.time

        intervalos['duracion'] = intervalos['duracion_segundos'].apply(formato_tiempo)

        tiempo_total_en_rango = intervalos['duracion_segundos'].sum()
        max_tiempo_continuo = intervalos['duracion_segundos'].max() if not intervalos.empty else 0

        st.write(f"Tiempo total acumulado por encima de {temperatura_objetivo}°C: **{formato_tiempo(tiempo_total_en_rango)}**")
        st.write(f"Máximo tiempo continuo por encima de {temperatura_objetivo}°C: **{formato_tiempo(max_tiempo_continuo)}**")

        tiempo_objetivo_segundos = tiempo_objetivo_minutos * 60

        if max_tiempo_continuo >= tiempo_objetivo_segundos:
            st.success("✅ El pollo cumplió con el tiempo mínimo requerido de forma continua.")
        else:
            st.error("❌ El pollo NO cumplió con el tiempo mínimo requerido de forma continua.")

        st.subheader("📅 Intervalos continuos donde la temperatura estuvo por encima del objetivo")
        st.dataframe(intervalos[['inicio', 'fin', 'duracion']])

        # Gráfica: una roja general y una verde encima donde está por encima del umbral
        base = alt.Chart(df).encode(x='marca de tiempo:T')

        # Línea roja general
        linea_roja = base.mark_line(color='red').encode(
            y='temperatura real del nucleo:Q'
        )

        # Línea verde solo en puntos por encima del umbral
        linea_verde = base.transform_filter(
            alt.datum['temperatura real del nucleo'] >= temperatura_objetivo
        ).mark_line(color='green').encode(
            y='temperatura real del nucleo:Q'
        )

        # Línea de umbral
        threshold_line = alt.Chart(
            pd.DataFrame({'threshold': [temperatura_objetivo]})
        ).mark_rule(color='black', strokeDash=[4, 4]).encode(
            y='threshold:Q'
        )

        grafica = (linea_roja + linea_verde + threshold_line).properties(
            width=700,
            height=400,
            title='Temperatura del núcleo del pollo a lo largo del tiempo'
        ).interactive()

        st.altair_chart(grafica, use_container_width=True)
