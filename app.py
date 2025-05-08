import os
import io
import zipfile
import tempfile

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import SimpleITK as sitk
import plotly.graph_objects as go  # Para vista 3D interactiva

# Configuración de página y estilo
st.set_page_config(layout="wide", page_title="Brachyanalysis")

# CSS personalizado
st.markdown("""
<style>
    .main-header { color: #28aec5; text-align: center; font-size: 42px; margin-bottom: 20px; font-weight: bold; }
    .giant-title { color: #28aec5; text-align: center; font-size: 72px; margin: 30px 0; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; text-shadow: 2px 2px 4px rgba(0,0,0,0.1); }
    .sub-header { color: #c0d711; font-size: 24px; margin-bottom: 15px; font-weight: bold; }
    .stButton>button { background-color: #28aec5; color: white; border: none; border-radius: 4px; padding: 8px 16px; }
    .stButton>button:hover { background-color: #1c94aa; }
    .info-box { background-color: rgba(40, 174, 197, 0.1); border-left: 3px solid #28aec5; padding: 10px; margin: 10px 0; }
    .success-box { background-color: rgba(192, 215, 17, 0.1); border-left: 3px solid #c0d711; padding: 10px; margin: 10px 0; }
    .plot-container { border: 2px solid #c0d711; border-radius: 5px; padding: 10px; margin-top: 20px; }
    div[data-baseweb="select"] { border-radius: 4px; border-color: #28aec5; }
    div[data-baseweb="slider"] > div { background-color: #c0d711 !important; }
    div.stRadio > div[role="radiogroup"] > label { background-color: rgba(40, 174, 197, 0.1); margin-right: 10px; padding: 5px 15px; border-radius: 4px; }
    div.stRadio > div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child { background-color: #28aec5; }
    .upload-section { background-color: rgba(40, 174, 197, 0.05); padding: 20px; border-radius: 8px; margin-bottom: 20px; }
    .stUploadButton>button { background-color: #c0d711; color: #1e1e1e; font-weight: bold; }
    .sidebar-title { color: #28aec5; font-size: 28px; font-weight: bold; margin-bottom: 15px; }
    .control-section { background-color: rgba(40, 174, 197, 0.05); padding: 15px; border-radius: 8px; margin-top: 15px; }
    .input-row { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# Barra lateral
st.sidebar.markdown('<p class="sidebar-title">Brachyanalysis</p>', unsafe_allow_html=True)
st.sidebar.markdown('<p class="sub-header">Visualizador de imágenes DICOM</p>', unsafe_allow_html=True)
st.sidebar.markdown('<p class="sub-header">Configuración</p>', unsafe_allow_html=True)

# Carga de archivo ZIP
uploaded_file = st.sidebar.file_uploader("Sube un archivo ZIP con tus archivos DICOM", type="zip")

# Funciones auxiliares
def find_dicom_series(directory):
    series = []
    for root, dirs, files in os.walk(directory):
        try:
            ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(root)
            for sid in ids:
                flist = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(root, sid)
                if flist:
                    series.append((sid, flist))
        except Exception:
            pass
    return series


def apply_window_level(image, window_width, window_center):
    imgf = image.astype(float)
    mn = window_center - window_width/2.0
    mx = window_center + window_width/2.0
    win = np.clip(imgf, mn, mx)
    if mx != mn:
        return (win - mn) / (mx - mn)
    return np.zeros_like(imgf)

# Procesamiento inicial
dirname = None
if uploaded_file:
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(io.BytesIO(uploaded_file.read()), 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    dirname = temp_dir
    st.sidebar.markdown('<div class="success-box">Archivos extraídos correctamente.</div>', unsafe_allow_html=True)

# Leer DICOM
dicom_series = []
img = None
if dirname:
    with st.spinner('Buscando series DICOM...'):
        dicom_series = find_dicom_series(dirname)
    if dicom_series:
        options = [f"Serie {i+1}: {sid[:10]}... ({len(flist)} archivos)"
                   for i, (sid, flist) in enumerate(dicom_series)]
        choice = st.sidebar.selectbox("Seleccionar serie DICOM:", options)
        idx = options.index(choice)
        sid, flist = dicom_series[idx]
        reader = sitk.ImageSeriesReader()
        reader.SetFileNames(flist)
        img = sitk.GetArrayViewFromImage(reader.Execute())
    else:
        st.sidebar.error("No se encontraron DICOM válidos en el ZIP cargado.")

# Visualización y controles
if img is not None:
    # Dimensiones
    n_ax, n_cor, n_sag = img.shape

    # Sliders para cada vista
    st.sidebar.subheader("Selección de cortes")
    slice_axial   = st.sidebar.slider('Corte Axial',   0, n_ax-1, n_ax//2)
    slice_coronal = st.sidebar.slider('Corte Coronal', 0, n_cor-1, n_cor//2)
    slice_sagital = st.sidebar.slider('Corte Sagital', 0, n_sag-1, n_sag//2)

    # Presets de ventana
    mn, mx = float(img.min()), float(img.max())
    default_ww = mx - mn
    default_wc = mn + default_ww/2
    presets = {"Default": (default_ww, default_wc), "CT Abdomen": (350, 50), "CT Bone": (2000, 350), "Custom": None}
    sel = st.sidebar.selectbox("Presets ventana", list(presets.keys()))
    if presets[sel] is not None:
        ww, wc = presets[sel]
    else:
        ww = st.sidebar.number_input("Ancho de ventana (WW)", 1.0, mw if (mw:=mx-mn)>0 else 1.0, default_ww)
        wc = st.sidebar.number_input("Centro de ventana (WL)", mn-default_ww, mx+default_ww, default_wc)

    # Checkbox 3D\    show_3d = st.sidebar.checkbox("Mostrar vista 3D interactiva")

    # Función render 2D\    def render2d(slice2d):
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.axis('off')
        ax.imshow(apply_window_level(slice2d, ww, wc), cmap='gray', origin='lower')
        return fig

    # Construir grid 2x2
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.subheader("Axial")
        st.pyplot(render2d(img[slice_axial, :, :]))
    with row1_col2:
        st.subheader("Coronal")
        st.pyplot(render2d(img[:, slice_coronal, :]))

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        st.subheader("Sagital")
        st.pyplot(render2d(img[:, :, slice_sagital]))
    with row2_col2:
        st.subheader("Vista 3D")
        if show_3d:
            x, y, z = np.mgrid[0:n_ax, 0:n_cor, 0:n_sag]
            fig3d = go.Figure(data=go.Volume(
                x=x.flatten(), y=y.flatten(), z=z.flatten(),
                value=img.flatten(), opacity=0.05, surface_count=20
            ))
            st.plotly_chart(fig3d, use_container_width=True)
        else:
            st.info("Marca 'Mostrar vista 3D interactiva' en la barra lateral para visualizar.")

# Encabezado y pie de página
st.markdown('<p class="giant-title">Brachyanalysis</p>', unsafe_allow_html=True)
st.markdown("""
<hr>
<div style="text-align:center;color:#28aec5;font-size:14px;">
    Brachyanalysis - Visualizador de imágenes DICOM
</div>
""", unsafe_allow_html=True)
