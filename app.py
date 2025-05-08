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
    .giant-title { color: #28aec5; text-align: center; font-size: 48px; margin-bottom: 10px; font-weight: bold; }
    .sub-header { color: #28aec5; font-size: 20px; margin-bottom: 5px; font-weight: bold; }
    .sidebar-title { color: #28aec5; font-size: 24px; font-weight: bold; margin-bottom: 10px; }
    .plot-container { padding: 5px; }
</style>
""", unsafe_allow_html=True)

# Encabezado principal
st.markdown('<p class="giant-title">Brachyanalysis</p>', unsafe_allow_html=True)

# Configuración de la barra lateral
st.sidebar.markdown('<p class="sidebar-title">Brachyanalysis</p>', unsafe_allow_html=True)
st.sidebar.markdown('**Carga de DICOM (.zip)**')
uploaded_file = st.sidebar.file_uploader("Selecciona ZIP con archivos DICOM", type="zip")

# Funciones auxiliares
def find_dicom_series(directory):
    """Busca series DICOM en un directorio dado"""
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


def apply_window_level(image, ww, wl):
    """Aplica ventana y nivel a una imagen"""
    arr = image.astype(float)
    mn = wl - ww/2.0
    mx = wl + ww/2.0
    clipped = np.clip(arr, mn, mx)
    if mx != mn:
        return (clipped - mn) / (mx - mn)
    return np.zeros_like(arr)


def render_slice(slice2d, ww, wl):
    fig, ax = plt.subplots(figsize=(4,4))
    ax.imshow(apply_window_level(slice2d, ww, wl), cmap='gray', origin='lower')
    ax.axis('off')
    return fig

# Extracción de archivos
dirname = None
if uploaded_file:
    tmpdir = tempfile.mkdtemp()
    with zipfile.ZipFile(io.BytesIO(uploaded_file.read()), 'r') as zf:
        zf.extractall(tmpdir)
    dirname = tmpdir
    st.sidebar.success("ZIP extraído correctamente")

# Carga de la primera serie encontrada
def load_first_series(path):
    series = find_dicom_series(path)
    if not series:
        return None
    sid, files = series[0]
    reader = sitk.ImageSeriesReader()
    reader.SetFileNames(files)
    img3d = reader.Execute()
    return sitk.GetArrayViewFromImage(img3d)

img = None
if dirname:
    with st.spinner('Cargando serie DICOM...'):
        img = load_first_series(dirname)
    if img is None:
        st.sidebar.error("No se encontró ninguna serie DICOM válida.")

# Visualización en cuadrícula de tres vistas
if img is not None:
    # Dimensiones de la imagen 3D
    n_ax, n_cor, n_sag = img.shape

    # Sliders de cortes
    st.sidebar.subheader("Ajuste de cortes")
    idx_ax = st.sidebar.slider('Corte Axial', 0, n_ax-1, n_ax//2)
    idx_cor = st.sidebar.slider('Corte Coronal', 0, n_cor-1, n_cor//2)
    idx_sag = st.sidebar.slider('Corte Sagital', 0, n_sag-1, n_sag//2)

    # Controles de ventana
    st.sidebar.subheader("Ventana / Nivel (WW/WL)")
    min_val, max_val = float(img.min()), float(img.max())
    default_ww = max_val - min_val
    default_wl = min_val + default_ww/2
    ww = st.sidebar.number_input('WW', min_value=1.0, value=default_ww)
    wl = st.sidebar.number_input('WL', value=default_wl)

    # Mostrar las tres vistas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader('Axial')
        st.pyplot(render_slice(img[idx_ax, :, :], ww, wl))
    with col2:
        st.subheader('Coronal')
        st.pyplot(render_slice(img[:, idx_cor, :], ww, wl))
    with col3:
        st.subheader('Sagital')
        st.pyplot(render_slice(img[:, :, idx_sag], ww, wl))

    # Pie de página
    st.markdown("""
    <hr>
    <div style='text-align:center;color:#28aec5;font-size:14px;'>
        Brachyanalysis - 2D Quadrants Viewer
    </div>
    """, unsafe_allow_html=True)

