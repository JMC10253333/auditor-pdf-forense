import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import os
import hashlib
from datetime import datetime
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
import io

st.set_page_config(page_title="Auditor Forense Pro", layout="wide")

st.title("🔍 Analizador Forense de Documentos")
st.write("Suite avanzada: Metadatos, Estructura, Huella Digital y Análisis de Integridad.")

# --- LÓGICA DE ESTADO Y LIMPIEZA ---
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0
if 'historico' not in st.session_state:
    st.session_state.historico = []

if st.button("🗑️ Borrar consultas y archivos"):
    st.session_state.historico = []
    st.session_state.uploader_key += 1
    st.rerun()

archivos_subidos = st.file_uploader(
    "Arrastra tus PDFs aquí", 
    type="pdf", 
    accept_multiple_files=True, 
    key=f"uploader_{st.session_state.uploader_key}"
)

if archivos_subidos:
    resultados = []
    # Lista de editores web que disparan alerta crítica inmediata
    editores_web = ['ilovepdf', 'smallpdf', 'sodapdf', 'pdf2go', 'nitro', 'foxit', 'canva', 'fpdf', 'quartz']
    
    for archivo in archivos_subidos:
        bytes_data = archivo.read()
        
        # 1. Huella Digital (SHA-256)
        sha256_hash = hashlib.sha256(bytes_data).hexdigest()
        
        doc = fitz.open(stream=bytes_data, filetype="pdf")
        
        # 2. Metadatos
        metadatos = doc.metadata
        productor = metadatos.get('producer', 'Desconocido')
        f_crea = metadatos.get('creationDate', '')
        f_mod = metadatos.get('modDate', '')
        
        fecha_c = f_crea[2:10] if (f_crea and len(f_crea) > 10) else "Desconocida"
        fecha_m = f_mod[2:10] if (f_mod and len(f_mod) > 10) else "Original"
        
        # 3. Análisis de Capas y Parches
        versiones = bytes_data.count(b'%%EOF')
        tiene_anotaciones = False
        for pagina in doc:
            if len(list(pagina.annots())) > 0 or len(list(pagina.widgets())) > 0:
                tiene_anotaciones = True
                break

        # 4. Análisis Estructural (Fragmentación)
        orden_caotico = False
        try:
            for page_layout in extract_pages(io.BytesIO(bytes_data)):
                text_elements = [element for element in page_layout if isinstance(element, LTTextContainer)]
                if len(text_elements) > 120: # Umbral ajustado para evitar falsos positivos
                    orden_caotico = True
        except:
            pass

        # --- LÓGICA DE RIESGO RECALIBRADA (v3.1) ---
        nivel = "Bajo"
        detalles = []
        es_modificado = f_mod and f_crea and f_mod != f_crea

        # Regla A: Editores Web conocidos (Riesgo Crítico siempre)
        if any(h in productor.lower() for h in editores_web):
            nivel = "Crítico"
            detalles.append(f"Software de edición detectado: {productor}")

        # Regla B: Parches Detectados
        if tiene_anotaciones:
            if es_modificado:
                # Si el archivo fue re-guardado, el parche es altamente sospechoso
                nivel = "Crítico"
                detalles.append("🕵️ Parche Malicioso: Elementos superpuestos en archivo modificado")
            else:
                # Si la fecha es original, es probable que sea un parche de sistema (QR, sellos, etc.)
                detalles.append("ℹ️ Parche Estructural: Elementos técnicos de origen detectados")

        # Regla C: Discrepancia temporal
        if es_modificado and nivel != "Crítico":
            nivel = "Alto"
            detalles.append("⚠️ Archivo re-guardado (discrepancia de fechas)")

        # Regla D: Capas incrementales
        if versiones > 1 and nivel == "Bajo":
            nivel = "Alto"
            detalles.append(f"Edición incremental: {versiones} capas detectadas")
            
        if orden_caotico and nivel == "Bajo":
            nivel = "Medio"
            detalles.append("🧩 Fragmentación inusual en la estructura del texto")

        resultados.append({
            "Archivo": archivo.name,
            "Riesgo": nivel,
            "SHA-256 (Huella)": sha256_hash[:12] + "...",
            "Productor": productor,
            "Modificación": fecha_m,
            "Análisis": " | ".join(detalles) if detalles else "Integridad aparente"
        })
    st.session_state.historico = resultados

# Mostrar resultados
if st.session_state.historico:
    df = pd.DataFrame(st.session_state.historico)
    def style_riesgo(val):
        color = '#ff4b4b' if val == 'Crítico' else ('#ffa500' if val == 'Alto' else ('#28a745' if val == 'Bajo' else '#1f77b4'))
        return f'background-color: {color}; color: white; font-weight: bold'
    st.dataframe(df.style.map(style_riesgo, subset=['Riesgo']), use_container_width=True)

# --- PIE DE PÁGINA ---
try:
    fecha_update = datetime.fromtimestamp(os.path.getmtime(__file__)).strftime('%d/%m/%Y %H:%M')
except:
    fecha_update = "29/04/2026"

st.divider()
st.caption(f"🚀 **Motor Forense Avanzado v3.1** | Lógica de discriminación de origen activada | Última actualización: {fecha_update}")
