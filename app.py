import os
import io
import zipfile
import tempfile

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import SimpleITK as sitk

# Configuración de página y estilo
st.set_page_config(layout="wide", page_title="Brachyanalysis")
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
    .sidebar-title { color: #28aec5; font-size: 28px; font-weight: bold; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# Barra lateral
st.sidebar.markdown('<p class="sidebar-title">Brachyanalysis</p>', unsafe_allow_html=True)
st.sidebar.markdown('<p class="sub-header">Visualizador de imágenes DICOM</p>', unsafe_allow_html=True)
st.sidebar.markdown('<p class="sub-header">Configuración</p>', unsafe_allow_html=True)

# Carga de archivo ZIP
uploaded_file = st.sidebar.file_uploader("Sube un archivo ZIP con tus archivos DICOM", type="zip")

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
            continue
    return series


def apply_window_level(image, window_width, window_center):
    img_float = image.astype(float)
    mn = window_center - window_width/2.0
    mx = window_center + window_width/2.0
    win = np.clip(img_float, mn, mx)
    return (win - mn)/(mx - mn) if mx != mn else np.zeros_like(img_float)


def render2d(slice2d, ww, wc):
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.axis('off')
    ax.imshow(apply_window_level(slice2d, ww, wc), cmap='gray', origin='lower')
    return fig

# Procesamiento inicial
dirname = None
if uploaded_file:
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(io.BytesIO(uploaded_file.read()), 'r') as z:
        z.extractall(temp_dir)
    dirname = temp_dir
    st.sidebar.markdown('<div class="success-box">Archivos extraídos correctamente.</div>', unsafe_allow_html=True)

# Lectura de la serie DICOM
img = None
if dirname:
    with st.spinner('Buscando series DICOM...'):
        series = find_dicom_series(dirname)
    if series:
        options = [f"Serie {i+1}: {sid[:10]} ({len(flist)} archivos)" for i,(sid, flist) in enumerate(series)]
        choice = st.sidebar.selectbox("Seleccionar serie DICOM:", options)
        idx = options.index(choice)
        sid, flist = series[idx]
        reader = sitk.ImageSeriesReader()
        reader.SetFileNames(flist)
        img = sitk.GetArrayViewFromImage(reader.Execute())
    else:
        st.sidebar.error("No se encontraron series DICOM válidas.")

# Visualización de las tres vistas en cuadrícula
if img is not None:
    # Dimensiones
    n_ax, n_cor, n_sag = img.shape
    
    # Sliders para cortes
    st.sidebar.subheader("Selección de cortes")
    axial_ix    = st.sidebar.slider('Corte Axial',   0, n_ax-1, n_ax//2)
    coronal_ix  = st.sidebar.slider('Corte Coronal', 0, n_cor-1, n_cor//2)
    sagittal_ix = st.sidebar.slider('Corte Sagital', 0, n_sag-1, n_sag//2)
    
    # Ajuste de ventana
    mn, mx = float(img.min()), float(img.max())
    ww_default = mx - mn
    wc_default = mn + ww_default/2
    st.sidebar.subheader("Ajuste de ventana")
    ww = st.sidebar.number_input("WW (Ancho)", min_value=1.0, value=ww_default)
    wc = st.sidebar.number_input("WL (Centro)", value=wc_default)
    
    # Mostrar las tres vistas juntas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Axial")
        st.pyplot(render2d(img[axial_ix, :, :], ww, wc))
    with col2:
        st.subheader("Coronal")
        st.pyplot(render2d(img[:, coronal_ix, :], ww, wc))
    with col3:
        st.subheader("Sagital")
        st.pyplot(render2d(img[:, :, sagittal_ix], ww, wc))

# Título y pie de página
st.markdown('<p class="giant-title">Brachyanalysis</p>', unsafe_allow_html=True)
st.markdown("""
<hr>
<div style="text-align:center;color:#28aec5;font-size:14px;">
    Brachyanalysis - Visualizador de imágenes DICOM
</div>
""", unsafe_allow_html=True)
