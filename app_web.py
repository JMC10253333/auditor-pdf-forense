import streamlit as st
import fitz
import pandas as pd
from collections import Counter

st.set_page_config(page_title="Auditor Forense de PDFs", layout="wide")

st.title("🔍 Analizador Forense de Documentos")
st.write("Especializado en detección de parches en montos ($) y manipulación de metadatos.")

archivos_subidos = st.file_uploader("Arrastra tus PDFs aquí", type="pdf", accept_multiple_files=True)

if archivos_subidos:
    resultados = []
    editores_web = ['ilovepdf', 'smallpdf', 'sodapdf', 'pdf2go', 'nitro', 'foxit', 'canva']
    
    for archivo in archivos_subidos:
        bytes_data = archivo.read()
        doc = fitz.open(stream=bytes_data, filetype="pdf")
        
        # 1. Metadatos y Fechas
        metadatos = doc.metadata
        productor = metadatos.get('producer', 'Desconocido')
        creador = metadatos.get('creator', 'Desconocido')
        f_crea = metadatos.get('creationDate', '')
        f_mod = metadatos.get('modDate', '')
        
        fecha_c = f_crea[2:10] if (f_crea and len(f_crea) > 10) else "Desconocida"
        fecha_m = f_mod[2:10] if (f_mod and len(f_mod) > 10) else "Original"
        
        # 2. Análisis de Texto y Cifras ($)
        tamanos_fuentes = []
        anomalias_dinero = []
        
        for pagina in doc:
            dict_texto = pagina.get_text("dict")
            for bloque in dict_texto["blocks"]:
                if "lines" in bloque:
                    for linea in bloque["lines"]:
                        for span in linea["spans"]:
                            texto = span["text"].strip()
                            tamano = round(span["size"], 1)
                            tamanos_fuentes.append(tamano)
                            
                            # Filtro: Solo nos interesan textos con "$" o números con formato de miles (ej: 250.000)
                            es_cifra = "$" in texto or (any(char.isdigit() for char in texto) and "." in texto)
                            if es_cifra:
                                anomalias_dinero.append(tamano)

        # 3. Lógica de Riesgo
        nivel = "Bajo"
        detalles = []
        
        # Alerta: Herramientas Web
        if any(h in productor.lower() for h in editores_web):
            nivel = "Crítico"
            detalles.append(f"Software de edición detectado: {productor}")

        # Alerta: Manipulación Temporal
        if f_mod and f_crea and f_mod != f_crea:
            nivel = "Alto"
            detalles.append("⚠️ El archivo fue re-guardado (discrepancia de fechas)")

        # Alerta: Capas (Incremental Updates)
        versiones = bytes_data.count(b'%%EOF')
        if versiones > 1:
            nivel = "Crítico"
            detalles.append(f"Se detectaron {versiones} capas de cambios estructurales")

        # Alerta: Anomalía en Cifras Monetarias
        if tamanos_fuentes and anomalias_dinero:
            tamano_dominante = Counter(tamanos_fuentes).most_common(1)[0][0]
            # Si el monto ($) es un 15% más grande que la letra común del documento
            for tam_cifra in anomalias_dinero:
                if tam_cifra > tamano_dominante * 1.15:
                    nivel = "Crítico"
                    msg = f"🔍 MONTO SOSPECHOSO: Cifra detectada con tamaño {tam_cifra}pt (superior al {tamano_dominante}pt base)"
                    if msg not in detalles:
                        detalles.append(msg)

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
    # ########################################
    # python -m streamlit run "C:\Users\marcelo.castro\OneDrive\Personal\Python\app_web.py"
    # ######################################## 