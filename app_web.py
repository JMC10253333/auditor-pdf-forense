import streamlit as st
import fitz
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Auditor Forense de PDFs", layout="wide")

# --- NUEVA SECCIÓN: FECHA DE ACTUALIZACIÓN ---
# Obtiene la fecha en que se modificó este archivo de código
try:
    fecha_update = datetime.fromtimestamp(os.path.getmtime(__file__)).strftime('%d/%m/%Y %H:%M')
except:
    fecha_update = "28/04/2026" # Fecha manual de respaldo

st.title("🔍 Analizador Forense de Documentos")
st.info(f"🚀 **Última actualización del motor de análisis:** {fecha_update}")
st.write("Análisis de integridad basado en metadatos, cronología y estructura de capas.")

# --- EL RESTO DEL CÓDIGO SIGUE IGUAL ---
archivos_subidos = st.file_uploader("Arrastra tus PDFs aquí", type="pdf", accept_multiple_files=True)

if archivos_subidos:
    resultados = []
    editores_web = ['ilovepdf', 'smallpdf', 'sodapdf', 'pdf2go', 'nitro', 'foxit', 'canva', 'fpdf', 'quartz']
    
    for archivo in archivos_subidos:
        bytes_data = archivo.read()
        doc = fitz.open(stream=bytes_data, filetype="pdf")
        
        metadatos = doc.metadata
        productor = metadatos.get('producer', 'Desconocido')
        creador = metadatos.get('creator', 'Desconocido')
        f_crea = metadatos.get('creationDate', '')
        f_mod = metadatos.get('modDate', '')
        
        fecha_c = f_crea[2:10] if (f_crea and len(f_crea) > 10) else "Desconocida"
        fecha_m = f_mod[2:10] if (f_mod and len(f_mod) > 10) else "Original"
        
        versiones = bytes_data.count(b'%%EOF')
        tiene_anotaciones = False
        
        for pagina in doc:
            if len(list(pagina.annots())) > 0:
                tiene_anotaciones = True
                break
            if len(list(pagina.widgets())) > 0:
                tiene_anotaciones = True
                break

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
            detalles.append("🕵️ Parche detectado: Se encontraron elementos superpuestos")

        resultados.append({
            "Archivo": archivo.name,
            "Productor": productor,
            "Creación": fecha_c,
            "Modificación": fecha_m,
            "Riesgo": nivel,
            "Análisis": " | ".join(detalles) if detalles else "Integridad aparente"
        })

    df = pd.DataFrame(resultados)
    
    def style_riesgo(val):
        color = '#ff4b4b' if val == 'Crítico' else ('#ffa500' if val == 'Alto' else '#28a745')
        return f'background-color: {color}; color: white; font-weight: bold'

    st.dataframe(df.style.map(style_riesgo, subset=['Riesgo']), use_container_width=True)
