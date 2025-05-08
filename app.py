import os
import io
import zipfile
import tempfile

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import SimpleITK as sitk
from skimage.transform import resize  # Asegúrate de que scikit-image esté instalado
import plotly.graph_objects as go

# Configuración de página y estilo
st.set_page_config(layout="wide", page_title="Brachyanalysis")
st.markdown("""
<style>
    .giant-title { color: #28aec5; text-align: center; font-size: 48px; margin-bottom: 10px; font-weight: bold; }
    .sub-header { color: #28aec5; font-size: 20px; margin-bottom: 5px; font-weight: bold; }
    .sidebar-title { color: #28aec5; font-size: 24px; font-weight: bold; margin-bottom: 10px; }
    .plot-container { padding: 5px; }
</style>
""", unsafe_allow_html=True)

# Barra lateral
st.sidebar.markdown('<p class="sidebar-title">Brachyanalysis</p>', unsafe_allow_html=True)
st.sidebar.markdown('**Carga DICOM**')
uploaded_file = st.sidebar.file_uploader(".zip con DICOM", type="zip")

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
        except:
            pass
    return series


def apply_window_level(img, ww, wc):
    f = img.astype(float)
    mn = wc - ww/2.0
    mx = wc + ww/2.0
    w = np.clip(f, mn, mx)
    return (w - mn)/(mx - mn) if mx!=mn else np.zeros_like(f)


def render2d(slice2d, ww, wc):
    fig, ax = plt.subplots(figsize=(4,4))
    ax.imshow(apply_window_level(slice2d, ww, wc), cmap='gray', origin='lower')
    ax.axis('off')
    return fig

# Cargar y extraer DICOM
dirname=None
if uploaded_file:
    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(io.BytesIO(uploaded_file.read()), 'r') as z:
        z.extractall(tmp)
    dirname=tmp
    st.sidebar.success("ZIP extraído")

# Leer primera serie DICOM
def load_series(dirpath):
    lst = find_dicom_series(dirpath)
    if not lst:
        return None
    sid, files = lst[0]
    reader = sitk.ImageSeriesReader()
    reader.SetFileNames(files)
    return sitk.GetArrayViewFromImage(reader.Execute())

img=None
if dirname:
    with st.spinner('Cargando DICOM...'):
        img = load_series(dirname)
    if img is None:
        st.sidebar.error("No se encontró serie DICOM")

# Mostrar cuadrícula 2x2
if img is not None:
    n_ax,n_cor,n_sag = img.shape
    # Sliders laterales\    st.sidebar.markdown('**Ajustes Cortes**')
    ax_ix = st.sidebar.slider('Axial', 0, n_ax-1, n_ax//2)
    cr_ix = st.sidebar.slider('Coronal', 0, n_cor-1, n_cor//2)
    sa_ix = st.sidebar.slider('Sagital', 0, n_sag-1, n_sag//2)
    
    # Ventana básica\    st.sidebar.markdown('**WW / WL**')
    mn, mx = float(img.min()), float(img.max())
    ww = st.sidebar.number_input('WW', 1.0, mx-mn, mx-mn)
    wc = st.sidebar.number_input('WL', mn, mx, mn+(mx-mn)/2)

    # Generar grid\    st.markdown('<p class="giant-title">Brachyanalysis</p>', unsafe_allow_html=True)
    r1c1, r1c2 = st.columns(2)
    r2c1, r2c2 = st.columns(2)
    
    with r1c1:
        st.subheader('Axial')
        st.pyplot(render2d(img[ax_ix,:,:], ww, wc))
    with r1c2:
        st.subheader('Coronal')
        st.pyplot(render2d(img[:,cr_ix,:], ww, wc))

    with r2c1:
        st.subheader('Sagital')
        st.pyplot(render2d(img[:,:,sa_ix], ww, wc))
    with r2c2:
        st.subheader('3D Preview')
        st.info('Vista 3D deshabilitada')

    st.markdown("""
    <hr>
    <div style='text-align:center;color:#28aec5;font-size:14px;'>
        Brachyanalysis - 2D Quadrants
    </div>
    """, unsafe_allow_html=True)
