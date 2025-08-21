import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime

st.set_page_config(page_title="Simulador de Examen", layout="centered")

# Inicialización de variables
if "preguntas" not in st.session_state:
    st.session_state.preguntas = None
    st.session_state.examen = None
    st.session_state.respuestas_usuario = {}
    st.session_state.preguntas_seleccionadas = []
    st.session_state.in_test = False
    st.session_state.indice_pregunta = 0
    st.session_state.config = {}
    st.session_state.mostrar_resultados = False
    st.session_state.resultados = None
    st.session_state.tiempo_inicio = None
    st.session_state.tiempo_total = None

def cargar_excel(file):
    examen_df = pd.read_excel(file, sheet_name="Examen", header=None)
    preguntas_df = pd.read_excel(file, sheet_name="Preguntas")
    examen_info = {
        "nombre": examen_df.iloc[0, 1],
        "descripcion": examen_df.iloc[1, 1]
    }
    return examen_info, preguntas_df

def evaluar():
    resumen = []
    correctas = 0
    for _, row in st.session_state.preguntas_seleccionadas.iterrows():
        resp_correcta = [r.strip() for r in row['Respuesta'].split(",")]
        resp_usuario = st.session_state.respuestas_usuario.get(row['ID'], [])
        es_correcta = sorted(resp_correcta) == sorted(resp_usuario)
        if es_correcta:
            correctas += 1
        resumen.append({
            "ID": row['ID'],
            "Pregunta": row['Pregunta'],
            "Respuesta Usuario": ", ".join(resp_usuario),
            "Respuesta Correcta": ", ".join(resp_correcta),
            "Correcta": es_correcta
        })
    porcentaje = (correctas / len(st.session_state.preguntas_seleccionadas)) * 100
    return correctas, porcentaje, pd.DataFrame(resumen)

def guardar_historial(nombre_examen, correctas, porcentaje, tiempo_total):
    archivo = "historial_resultados.csv"
    nuevo_registro = pd.DataFrame([{
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Examen": nombre_examen,
        "Correctas": correctas,
        "Total": len(st.session_state.preguntas_seleccionadas),
        "Porcentaje": round(porcentaje, 2),
        "Tiempo (segundos)": int(tiempo_total)
    }])
    try:
        historial = pd.read_csv(archivo)
        historial = pd.concat([historial, nuevo_registro], ignore_index=True)
    except FileNotFoundError:
        historial = nuevo_registro
    historial.to_csv(archivo, index=False)

st.title("📘 Simulador de Examen con Cronómetro e Histórico")

if not st.session_state.in_test and not st.session_state.mostrar_resultados:
    archivo_excel = st.file_uploader("📂 Cargar archivo Excel", type=["xlsx"])
    if archivo_excel:
        st.session_state.examen, st.session_state.preguntas = cargar_excel(archivo_excel)
        st.success("Archivo cargado correctamente ✅")
        st.write(f"**Nombre del examen:** {st.session_state.examen['nombre']}")
        st.write(f"**Descripción:** {st.session_state.examen['descripcion']}")
        total_pregs = len(st.session_state.preguntas)
        st.write(f"**Total de preguntas cargadas:** {total_pregs}")

        num_pregs = st.number_input("Número de preguntas a responder", min_value=1, max_value=total_pregs, value=total_pregs)
        orden = st.radio("Orden de las preguntas", ["Secuencial", "Aleatorio"])
        porcentaje_min = st.slider("Porcentaje mínimo para aprobar", 0, 100, 80)

        if st.button("🚀 Iniciar examen"):
            if orden == "Aleatorio":
                st.session_state.preguntas_seleccionadas = st.session_state.preguntas.sample(num_pregs).reset_index(drop=True)
            else:
                st.session_state.preguntas_seleccionadas = st.session_state.preguntas.head(num_pregs).reset_index(drop=True)
            st.session_state.config = {"porcentaje_min": porcentaje_min}
            st.session_state.in_test = True
            st.session_state.indice_pregunta = 0
            st.session_state.respuestas_usuario = {}
            st.session_state.tiempo_inicio = time.time()

elif st.session_state.in_test:
    # Cronómetro en vivo
    tiempo_transcurrido = int(time.time() - st.session_state.tiempo_inicio)
    st.write(f"⏱ Tiempo transcurrido: **{tiempo_transcurrido} segundos**")

    pregunta_actual = st.session_state.preguntas_seleccionadas.iloc[st.session_state.indice_pregunta]
    st.header(st.session_state.examen['nombre'])
    st.subheader(f"Pregunta {st.session_state.indice_pregunta+1} de {len(st.session_state.preguntas_seleccionadas)}")
    st.write(pregunta_actual['Pregunta'])

    opciones = [pregunta_actual[f"Opción {chr(65+i)}"] for i in range(6) if pd.notna(pregunta_actual.get(f"Opción {chr(65+i)}"))]
    respuestas_correctas = pregunta_actual['Respuesta'].split(",")
    multiple = len(respuestas_correctas) > 1

    if multiple:
        seleccion = st.multiselect("Selecciona tus respuestas", [chr(65+i) for i in range(len(opciones))],
                                    default=st.session_state.respuestas_usuario.get(pregunta_actual['ID'], []))
    else:
        seleccion = st.radio("Selecciona tu respuesta", [chr(65+i) for i in range(len(opciones))],
                             index=None if pregunta_actual['ID'] not in st.session_state.respuestas_usuario else
                             [chr(65+i) for i in range(len(opciones))].index(st.session_state.respuestas_usuario[pregunta_actual['ID']][0]))

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬅ Anterior", disabled=st.session_state.indice_pregunta == 0):
            st.session_state.respuestas_usuario[pregunta_actual['ID']] = seleccion if isinstance(seleccion, list) else [seleccion]
            st.session_state.indice_pregunta -= 1
            st.experimental_rerun()
    with col2:
        if st.button("➡ Siguiente", disabled=st.session_state.indice_pregunta == len(st.session_state.preguntas_seleccionadas)-1):
            if not seleccion:
                st.warning("Debes seleccionar al menos una respuesta")
            else:
                st.session_state.respuestas_usuario[pregunta_actual['ID']] = seleccion if isinstance(seleccion, list) else [seleccion]
                st.session_state.indice_pregunta += 1
                st.experimental_rerun()
    with col3:
        if st.button("✅ Finalizar", disabled=st.session_state.indice_pregunta != len(st.session_state.preguntas_seleccionadas)-1):
            if not seleccion:
                st.warning("Debes seleccionar al menos una respuesta")
            else:
                st.session_state.respuestas_usuario[pregunta_actual['ID']] = seleccion if isinstance(seleccion, list) else [seleccion]
                correctas, porcentaje, df_resumen = evaluar()
                st.session_state.tiempo_total = time.time() - st.session_state.tiempo_inicio
                guardar_historial(st.session_state.examen['nombre'], correctas, porcentaje, st.session_state.tiempo_total)
                st.session_state.resultados = {
                    "correctas": correctas,
                    "porcentaje": porcentaje,
                    "df": df_resumen
                }
                st.session_state.in_test = False
                st.session_state.mostrar_resultados = True
                st.experimental_rerun()

elif st.session_state.mostrar_resultados:
    correctas = st.session_state.resultados["correctas"]
    porcentaje = st.session_state.resultados["porcentaje"]
    df_resumen = st.session_state.resultados["df"]
    color = "green" if porcentaje >= st.session_state.config['porcentaje_min'] else "red"
    st.markdown(f"<h2 style='color:{color}'> {'APROBADO' if color=='green' else 'REPROBADO'} </h2>", unsafe_allow_html=True)
    st.write(f"**Correctas:** {correctas} de {len(st.session_state.preguntas_seleccionadas)} ({porcentaje:.2f}%)")
    st.write(f"⏱ Tiempo total: {int(st.session_state.tiempo_total)} segundos")

    filtro = st.radio("Filtrar preguntas:", ["Todas", "Correctas", "Incorrectas"])
    if filtro == "Correctas":
        df_filtrado = df_resumen[df_resumen["Correcta"] == True]
    elif filtro == "Incorrectas":
