import streamlit as st
import pandas as pd
import altair as alt

st.title("✅ Verificador de temperatura del pollo y abatidor")

st.header("🍗 Verificación del horno")

uploaded_file_horno = st.file_uploader("📤 Sube el CSV del horno", type=["csv"], key="horno")

temperatura_objetivo_horno = st.number_input(
    "🌡️ Temperatura mínima del horno (°C)", 
    min_value=0, 
    value=83, 
    step=1,
    key="temp_horno"
)

tiempo_objetivo_minutos_horno = st.number_input(
    "⏱️ Tiempo mínimo por encima de esa temperatura (minutos)", 
    min_value=0, 
    value=129, 
    step=1,
    key="tiempo_horno"
)

st.divider()

st.header("❄️ Verificación del abatidor")

uploaded_file_abatidor = st.file_uploader("📤 Sube el CSV del abatidor", type=["csv"], key="abatidor")

temperatura_maxima_abatidor = st.number_input(
    "❄️ Temperatura máxima del abatidor (°C)", 
    min_value=-30, 
    value=4, 
    step=1,
    key="temp_abatidor"
)

tiempo_objetivo_minutos_abatidor = st.number_input(
    "🕒 Tiempo mínimo por debajo de esa temperatura (minutos)", 
    min_value=0, 
    value=40, 
    step=1,
    key="tiempo_abatidor"
)

def formato_tiempo(segundos):
    minutos_totales = int(round(segundos / 60))
    if minutos_totales < 60:
        return f"{minutos_totales} minutos"
    else:
        horas = minutos_totales // 60
        minutos = minutos_totales % 60
        return f"{horas} horas {minutos} minutos"

def procesar_csv(df, columna_tiempo, columna_temp, umbral, mayor_que, tiempo_min_requerido):
    df = df[[columna_tiempo, columna_temp]].dropna()
    df[columna_tiempo] = pd.to_datetime(df[columna_tiempo], errors='coerce')
    df[columna_temp] = pd.to_numeric(df[columna_temp], errors='coerce')
    df = df.dropna()
    df = df.sort_values(columna_tiempo).reset_index(drop=True)
    df['tiempo_delta'] = df[columna_tiempo].diff().dt.total_seconds().fillna(0)

    if mayor_que:
        df['en_rango'] = df[columna_temp] >= umbral
    else:
        df['en_rango'] = df[columna_temp] <= umbral

    df['grupo'] = (df['en_rango'] != df['en_rango'].shift()).cumsum()
    grupos = df[df['en_rango']].groupby('grupo')

    intervalos = grupos.agg(
        inicio=(columna_tiempo, 'first'),
        fin=(columna_tiempo, 'last'),
        duracion_segundos=('tiempo_delta', 'sum')
    ).reset_index(drop=True)

    intervalos['inicio'] = intervalos['inicio'].dt.time
    intervalos['fin'] = intervalos['fin'].dt.time
    intervalos['duracion'] = intervalos['duracion_segundos'].apply(formato_tiempo)

    tiempo_total = intervalos['duracion_segundos'].sum()
    max_continuo = intervalos['duracion_segundos'].max() if not intervalos.empty else 0
    cumple = max_continuo >= (tiempo_min_requerido * 60)

    return df, intervalos, tiempo_total, max_continuo, cumple

cumple_horno = False
cumple_abatidor = False

# Procesar horno
if uploaded_file_horno is not None:
    df_horno = pd.read_csv(uploaded_file_horno, encoding='utf-8', engine='python')
    df_horno.columns = [c.strip().lower() for c in df_horno.columns]

    if 'marca de tiempo' in df_horno.columns and 'temperatura real del nucleo' in df_horno.columns:
        df_proc, intervalos, total, max_cont, cumple_horno = procesar_csv(
            df_horno, 'marca de tiempo', 'temperatura real del nucleo',
            temperatura_objetivo_horno, mayor_que=True,
            tiempo_min_requerido=tiempo_objetivo_minutos_horno
        )

        st.subheader("📈 Horno: intervalos válidos")
        st.dataframe(intervalos)

        st.write(f"Tiempo total por encima de {temperatura_objetivo_horno}°C: **{formato_tiempo(total)}**")
        st.write(f"Máximo tiempo continuo por encima: **{formato_tiempo(max_cont)}**")

        if cumple_horno:
            st.success("✅ El horno cumple con el requisito.")
        else:
            st.error("❌ El horno NO cumple con el requisito.")

        # Añadir columna para línea verde discontinua
        df_proc['temp_visible'] = df_proc.apply(
            lambda row: row['temperatura real del nucleo'] if row['temperatura real del nucleo'] >= temperatura_objetivo_horno else None,
            axis=1
        )

        base = alt.Chart(df_proc).encode(x='marca de tiempo:T')
        linea_roja = base.mark_line(color='red').encode(y='temperatura real del nucleo:Q')
        linea_verde = base.mark_line(color='green').encode(y='temp_visible:Q')
        threshold_line = alt.Chart(pd.DataFrame({'threshold': [temperatura_objetivo_horno]})).mark_rule(color='black', strokeDash=[4, 4]).encode(y='threshold:Q')

        st.altair_chart((linea_roja + linea_verde + threshold_line).properties(
            width=700, height=400, title="Temperatura del horno"
        ).interactive(), use_container_width=True)

    else:
        st.error("El CSV del horno debe tener columnas 'marca de tiempo' y 'temperatura real del nucleo'.")

# Procesar abatidor
if uploaded_file_abatidor is not None:
    df_abatidor = pd.read_csv(uploaded_file_abatidor, encoding='utf-8', engine='python')
    df_abatidor.columns = [c.strip().lower() for c in df_abatidor.columns]

    if 'marca de tiempo' in df_abatidor.columns and 'temperatura real del nucleo' in df_abatidor.columns:
        df_proc, intervalos, total, max_cont, cumple_abatidor = procesar_csv(
            df_abatidor, 'marca de tiempo', 'temperatura real del nucleo',
            temperatura_maxima_abatidor, mayor_que=False,
            tiempo_min_requerido=tiempo_objetivo_minutos_abatidor
        )

        st.subheader("📉 Abatidor: intervalos válidos")
        st.dataframe(intervalos)

        st.write(f"Tiempo total por debajo de {temperatura_maxima_abatidor}°C: **{formato_tiempo(total)}**")
        st.write(f"Máximo tiempo continuo por debajo: **{formato_tiempo(max_cont)}**")

        if cumple_abatidor:
            st.success("✅ El abatidor cumple con el requisito.")
        else:
            st.error("❌ El abatidor NO cumple con el requisito.")
    else:
        st.error("El CSV del abatidor debe tener columnas 'marca de tiempo' y 'temperatura real del nucleo'.")

# Veredicto final
if uploaded_file_horno and uploaded_file_abatidor:
    st.divider()
    st.subheader("📊 Resultado Final")
    if cumple_horno and cumple_abatidor:
        st.success("✅ El proceso completo ha sido correcto: horno y abatidor cumplen.")
    else:
        st.error("❌ El proceso NO cumple: alguno de los dispositivos no pasó la verificación.")
