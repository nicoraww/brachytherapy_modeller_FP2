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
    .plot-container { border: 2px solid #c0d711; border-radius: 5px; padding: 10px; margin-top: 20px; }
    .sidebar-title { color: #28aec5; font-size: 28px; font-weight: bold; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# Barra lateral
st.sidebar.markdown('<p class="sidebar-title">Brachyanalysis</p>', unsafe_allow_html=True)
st.sidebar.markdown('<p class="sub-header">Visualizador de imágenes DICOM</p>', unsafe_allow_html=True)
st.sidebar.markdown('<p class="sub-header">Configuración</p>', unsafe_allow_html=True)

# Carga de archivo ZIP
uploaded_file = st.sidebar.file_uploader("Sube un archivo ZIP con tus DICOM", type="zip")

# Función para buscar series DICOM
def find_dicom_series(directory):
    series_list = []
    for root, _, _ in os.walk(directory):
        try:
            ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(root)
            for sid in ids:
                files = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(root, sid)
                if files:
                    series_list.append((sid, files))
        except Exception:
            pass
    return series_list

# Función para aplicar ventana/nivel
def apply_window_level(image, ww, wc):
    imgf = image.astype(float)
    mn = wc - ww/2.0
    mx = wc + ww/2.0
    win = np.clip(imgf, mn, mx)
    return (win - mn)/(mx - mn) if mx != mn else np.zeros_like(imgf)

# Función para renderizar un slice
def render2d(slice2d, ww, wc):
    fig, ax = plt.subplots(figsize=(5,5))
    ax.axis('off')
    ax.imshow(apply_window_level(slice2d, ww, wc), cmap='gray', origin='lower')
    return fig

# Procesamiento inicial
img = None
dirname = None
if uploaded_file:
    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(io.BytesIO(uploaded_file.read()), 'r') as z:
        z.extractall(tmp)
    dirname = tmp
    st.sidebar.success("Archivos extraídos correctamente.")

# Leer serie DICOM
def load_series():
    if not dirname:
        return None
    with st.spinner('Buscando series DICOM...'):
        lst = find_dicom_series(dirname)
    if not lst:
        st.sidebar.error("No se encontraron series DICOM.")
        return None
    opts = [f"Serie {i+1}: {sid[:10]}... ({len(files)} ficheros)" for i,(sid,files) in enumerate(lst)]
    sel = st.sidebar.selectbox("Selecciona serie:", opts)
    idx = opts.index(sel)
    _, files = lst[idx]
    rdr = sitk.ImageSeriesReader()
    rdr.SetFileNames(files)
    img_arr = sitk.GetArrayViewFromImage(rdr.Execute())
    return img_arr

img = load_series()

# Mostrar vistas 2D en cuadrícula 1x3
if img is not None:
    n_ax, n_cor, n_sag = img.shape
    st.sidebar.subheader("Cortes")
    ax_ix = st.sidebar.slider('Axial', 0, n_ax-1, n_ax//2)
    cr_ix = st.sidebar.slider('Coronal', 0, n_cor-1, n_cor//2)
    sa_ix = st.sidebar.slider('Sagital', 0, n_sag-1, n_sag//2)
    
    st.sidebar.subheader("Ventana (WW/WL)")
    mn, mx = float(img.min()), float(img.max())
    default_ww = mx - mn
    default_wc = mn + default_ww/2
    ww = st.sidebar.number_input('WW', min_value=1.0, value=default_ww)
    wc = st.sidebar.number_input('WL', value=default_wc)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Axial")
        st.pyplot(render2d(img[ax_ix,:,:], ww, wc))
    with col2:
        st.subheader("Coronal")
        st.pyplot(render2d(img[:,cr_ix,:], ww, wc))
    with col3:
        st.subheader("Sagital")
        st.pyplot(render2d(img[:,:,sa_ix], ww, wc))

# Título y pie\st.markdown('<p class="giant-title">Brachyanalysis</p>', unsafe_allow_html=True)
st.markdown("""
<hr>
<div style="text-align:center;color:#28aec5;font-size:14px;">
    Brachyanalysis - Visualizador de DICOM
</div>
""", unsafe_allow_html=True)
