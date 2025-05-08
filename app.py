import os
import io
import zipfile
import tempfile

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import SimpleITK as sitk
from skimage.transform import resize  # Asegúrate de que scikit-image esté instalado

# Para vista 3D interactiva
import plotly.graph_objects as go

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
</style>
""", unsafe_allow_html=True)

# Barra lateral
st.sidebar.markdown('<p class="sidebar-title">Brachyanalysis</p>', unsafe_allow_html=True)
st.sidebar.markdown('<p class="sub-header">Visualizador de imágenes DICOM</p>', unsafe_allow_html=True)

# Carga de archivo ZIP
uploaded_file = st.sidebar.file_uploader("Sube un archivo ZIP con tus archivos DICOM", type="zip")

# Función para buscar series DICOM
def find_dicom_series(directory):
    series_found = []
    for root, dirs, files in os.walk(directory):
        try:
            series_ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(root)
            for sid in series_ids:
                file_list = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(root, sid)
                if file_list:
                    series_found.append((sid, root, file_list))
        except Exception:
            continue
    return series_found

# Función para aplicar ventana/nivel
def apply_window_level(image, window_width, window_center):
    img_float = image.astype(float)
    min_v = window_center - window_width/2.0
    max_v = window_center + window_width/2.0
    windowed = np.clip(img_float, min_v, max_v)
    if max_v != min_v:
        return (windowed - min_v) / (max_v - min_v)
    return np.zeros_like(img_float)

# Procesamiento inicial
dirname = None
if uploaded_file:
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(io.BytesIO(uploaded_file.read()), 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    dirname = temp_dir
    st.sidebar.markdown('<div class="success-box">Archivos extraídos correctamente.</div>', unsafe_allow_html=True)

# Lectura y selección de la serie DICOM
dicom_series = None
img = None
original_image = None
if dirname:
    with st.spinner('Buscando series DICOM...'):
        dicom_series = find_dicom_series(dirname)
    if dicom_series:
        options = [f"Serie {i+1}: {series[0][:10]}... ({len(series[2])} archivos)" \
                   for i, series in enumerate(dicom_series)]
        selection = st.sidebar.selectbox("Seleccionar serie DICOM:", options)
        selected_idx = options.index(selection)
        sid, dirpath, files = dicom_series[selected_idx]
        reader = sitk.ImageSeriesReader()
        reader.SetFileNames(files)
        data = reader.Execute()
        img = sitk.GetArrayViewFromImage(data)  # NumPy array (Z, Y, X)
        original_image = img  # Guardamos para visualización 3D
    else:
        st.sidebar.error("No se encontraron DICOM válidos en el ZIP cargado.")

# Visualización 2D
if img is not None:
    n_ax, n_cor, n_sag = img.shape
    st.sidebar.subheader("Opciones de visualización 2D")
    view2d = st.sidebar.selectbox("Vista 2D", ["Axial", "Coronal", "Sagital"])
    max_idx = {'Axial': n_ax-1, 'Coronal': n_cor-1, 'Sagital': n_sag-1}[view2d]
    slice_ix = st.sidebar.slider('Corte', 0, max_idx, max_idx//2)

    # Presets de ventana
    min_val, max_val = float(img.min()), float(img.max())
    default_ww = max_val - min_val
    default_wc = min_val + default_ww/2
    presets = {"Default": (default_ww, default_wc), "CT Abdomen": (350, 50), "CT Bone": (2000, 350), "Custom": None}
    preset_choice = st.sidebar.selectbox("Presets ventana", list(presets.keys()))
    if preset_choice != "Custom":
        ww, wc = presets[preset_choice]
    else:
        ww = st.sidebar.number_input("Ancho de ventana (WW)", 1.0, default_ww*2, default_ww)
        wc = st.sidebar.number_input("Centro ventana (WL)", min_val-default_ww, max_val+default_ww, default_wc)

    def render2d(slice2d):
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.axis('off')
        ax.imshow(apply_window_level(slice2d, ww, wc), cmap='gray', origin='lower')
        return fig

    if view2d == "Axial":
        fig2d = render2d(img[slice_ix, :, :])
    elif view2d == "Coronal":
        fig2d = render2d(img[:, slice_ix, :])
    else:
        fig2d = render2d(img[:, :, slice_ix])
    st.pyplot(fig2d)

    # Vista 3D interactiva
    if st.sidebar.checkbox("Mostrar vista 3D interactiva"):
        st.sidebar.info("Reducción de resolución para mejorar el rendimiento")

        # Reducimos resolución para performance
        target_shape = (64, 64, 64)
        img_resized = resize(original_image, target_shape, anti_aliasing=True)

        # Crear grid de coordenadas
        x, y, z = np.mgrid[0:target_shape[0], 0:target_shape[1], 0:target_shape[2]]
        fig3d = go.Figure(data=go.Volume(
            x=x.flatten(), y=y.flatten(), z=z.flatten(),
            value=img_resized.flatten(),
            opacity=0.1,
            surface_count=15,
            colorscale="Gray",
        ))
        fig3d.update_layout(margin=dict(l=0, r=0, b=0, t=0))
        st.plotly_chart(fig3d, use_container_width=True)

# Encabezado y pie de página
st.markdown('<p class="giant-title">Brachyanalysis</p>', unsafe_allow_html=True)
st.markdown("""
<hr>
<div style="text-align:center;color:#28aec5;font-size:14px;">
    Brachyanalysis - Visualizador de imágenes DICOM
</div>
""", unsafe_allow_html=True)
