import os
import io
import zipfile
import tempfile

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import SimpleITK as sitk

# Configuración de página
st.set_page_config(layout="wide", page_title="Brachyanalysis")

# Título principal
st.title("Brachyanalysis")

# Carga de archivo ZIP con DICOM en la barra lateral
uploaded = st.sidebar.file_uploader("Carga ZIP con tus archivos DICOM", type="zip")

# Función para encontrar y leer la primera serie DICOM
@st.cache_data
def load_first_series_from_zip(uploaded_zip):
    tmpdir = tempfile.mkdtemp()
    with zipfile.ZipFile(io.BytesIO(uploaded_zip.read()), 'r') as zf:
        zf.extractall(tmpdir)
    # Buscar series
    series = []
    for root, _, _ in os.walk(tmpdir):
        ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(root)
        if ids:
            # Tomar la primera serie encontrada
            files = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(root, ids[0])
            if files:
                series.append(files)
    if not series:
        return None
    files = series[0]
    reader = sitk.ImageSeriesReader()
    reader.SetFileNames(files)
    image3d = reader.Execute()
    return sitk.GetArrayViewFromImage(image3d)  # Devuelve array Z,Y,X

img = None
if uploaded:
    with st.spinner('Extrayendo y cargando DICOM...'):
        img = load_first_series_from_zip(uploaded)
    if img is None:
        st.sidebar.error("No se encontró ninguna serie DICOM válida en el ZIP.")

# Mostrar cuadrícula de tres vistas si exist
if img is not None:
    # Dimensiones
    nz, ny, nx = img.shape
    # Sliders de cortes
    st.sidebar.subheader("Cortes")
    z_ix = st.sidebar.slider("Axial", 0, nz-1, nz//2)
    y_ix = st.sidebar.slider("Coronal", 0, ny-1, ny//2)
    x_ix = st.sidebar.slider("Sagital", 0, nx-1, nx//2)

    # Ventana y nivel
    st.sidebar.subheader("Ventana y Nivel (WW/WL)")
    mn, mx = float(img.min()), float(img.max())
    default_ww = mx - mn
    default_wl = (mx + mn)/2
    ww = st.sidebar.number_input("WW", min_value=1.0, value=default_ww)
    wl = st.sidebar.number_input("WL", value=default_wl)

    # Función de ventana
    def window_img(slice2d):
        arr = slice2d.astype(float)
        mnv = wl - ww/2
        mxv = wl + ww/2
        clipped = np.clip(arr, mnv, mxv)
        return (clipped - mnv)/(mxv - mnv) if mxv!=mnv else np.zeros_like(arr)

    # Crear cuadrícula 1x3
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Axial")
        fig, ax = plt.subplots(figsize=(4,4))
        ax.imshow(window_img(img[z_ix,:,:]), cmap='gray')
        ax.axis('off')
        st.pyplot(fig)
    with col2:
        st.subheader("Coronal")
        fig, ax = plt.subplots(figsize=(4,4))
        ax.imshow(window_img(img[:,y_ix,:]), cmap='gray')
        ax.axis('off')
        st.pyplot(fig)
    with col3:
        st.subheader("Sagital")
        fig, ax = plt.subplots(figsize=(4,4))
        ax.imshow(window_img(img[:,:,x_ix]), cmap='gray')
        ax.axis('off')
        st.pyplot(fig)

    # Pie de página
    st.markdown("---")
    st.markdown('<div style="text-align:center;color:#28aec5;font-size:14px;">Brachyanalysis - Quadrants Viewer</div>', unsafe_allow_html=True)
