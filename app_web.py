import streamlit as st
import fitz
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Auditor Forense de PDFs", layout="wide")

# --- FECHA DE ACTUALIZACIÓN AUTOMÁTICA ---
try:
    fecha_update = datetime.fromtimestamp(os.path.getmtime(__file__)).strftime('%d/%m/%Y %H:%M')
except:
    fecha_update = "28/04/2026"

st.title("🔍 Analizador Forense de Documentos")
st.info(f"🚀 **Motor de análisis v2.1** | Última actualización: {fecha_update}")

# --- LÓGICA PARA BORRAR CONSULTAS ---
if 'historico' not in st.session_state:
    st.session_state.historico = []

col1, col2 = st.columns([8, 1])
with col2:
    if st.button("🗑️ Borrar"):
        st.session_state.historico = []
        st.rerun()

st.write("Sube tus archivos para verificar metadatos, cronología y parches estructurales.")

# El cargador de archivos
archivos_subidos = st.file_uploader("Arrastra tus PDFs aquí", type="pdf", accept_multiple_files=True, key="uploader")

if archivos_subidos:
    resultados = []
    editores_web = ['ilovepdf', 'smallpdf', 'sodapdf', 'pdf2go', 'nitro', 'foxit', 'canva', 'fpdf', 'quartz']
    
    for archivo in archivos_subidos:
        bytes_data = archivo.read()
        doc = fitz.open(stream=bytes_data, filetype="pdf")
        
        # 1. Metadatos
        metadatos = doc.metadata
        productor = metadatos.get('producer', 'Desconocido')
        creador = metadatos.get('creator', 'Desconocido')
        f_crea = metadatos.get('creationDate', '')
        f_mod = metadatos.get('modDate', '')
        
        fecha_c = f_crea[2:10] if (f_crea and len(f_crea) > 10) else "Desconocida"
        fecha_m = f_mod[2:10] if (f_mod and len(f_mod) > 10) else "Original"
        
        # 2. Estructura
        versiones = bytes_data.count(b'%%EOF')
        tiene_anotaciones = False
        
        for pagina in doc:
            if len(list(pagina.annots())) > 0 or len(list(pagina.widgets())) > 0:
                tiene_anotaciones = True
                break

        # 3. Riesgo
        nivel = "Bajo"
        detalles = []
        
        if any(h in productor.lower() for h in editores_web) or any(h in creador.lower() for h in editores_web):
            nivel = "Crítico"
            detalles.append(f"Software de edición detectado: {productor}")

        if f_mod and f_crea and f_mod != f_crea:
            nivel = "Alto"
            detalles.append("⚠️ Archivo re-guardado (discrepancia de fechas)")

        if versiones > 1:
            nivel = "Crítico"
            detalles.append(f"Se detectaron {versiones} capas de guardado")

        if tiene_anotaciones:
            nivel = "Crítico"
            detalles.append("🕵️ Parche detectado: Elementos superpuestos encontrados")

        resultados.append({
            "Archivo": archivo.name,
            "Productor": productor,
            "Creación": fecha_c,
            "Modificación": fecha_m,
            "Riesgo": nivel,
            "Análisis": " | ".join(detalles) if detalles else "Integridad aparente"
        })

    # Guardamos en el estado de la sesión
    st.session_state.historico = resultados

# Mostrar la tabla si hay datos
if st.session_state.historico:
    df = pd.DataFrame(st.session_state.historico)
    
    def style_riesgo(val):
        color = '#ff4b4b' if val == 'Crítico' else ('#ffa500' if val == 'Alto' else '#28a745')
        return f'background-color: {color}; color: white; font-weight: bold'

    st.dataframe(df.style.map(style_riesgo, subset=['Riesgo']), use_container_width=True)
