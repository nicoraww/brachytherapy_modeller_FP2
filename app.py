import os
import io
import zipfile
import tempfile
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import SimpleITK as sitk

# Configuración de página y estilo
st.set_page_config(layout="wide", page_title="DieSitCom")

# CSS personalizado para aplicar los colores solicitados
st.markdown("""
<style>
    .main-header {
        color: #28aec5;
        text-align: center;
        font-size: 42px;
        margin-bottom: 20px;
        font-weight: bold;
    }
    .sub-header {
        color: #c0d711;
        font-size: 24px;
        margin-bottom: 15px;
        font-weight: bold;
    }
    .stButton>button {
        background-color: #28aec5;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
    }
    .stButton>button:hover {
        background-color: #1c94aa;
    }
    .info-box {
        background-color: rgba(40, 174, 197, 0.1);
        border-left: 3px solid #28aec5;
        padding: 10px;
        margin: 10px 0;
    }
    .success-box {
        background-color: rgba(192, 215, 17, 0.1);
        border-left: 3px solid #c0d711;
        padding: 10px;
        margin: 10px 0;
    }
    .plot-container {
        border: 2px solid #c0d711;
        border-radius: 5px;
        padding: 10px;
        margin-top: 20px;
    }
    div[data-baseweb="select"] {
        border-radius: 4px;
        border-color: #28aec5;
    }
    div[data-baseweb="slider"] > div {
        background-color: #c0d711 !important;
    }
    /* Estilos para radio buttons */
    div.stRadio > div[role="radiogroup"] > label {
        background-color: rgba(40, 174, 197, 0.1);
        margin-right: 10px;
        padding: 5px 15px;
        border-radius: 4px;
    }
    div.stRadio > div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child {
        background-color: #28aec5;
    }
</style>
""", unsafe_allow_html=True)

# Encabezado principal
st.markdown('<p class="main-header">DieSitCom</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Visualizador de imágenes DICOM</p>', unsafe_allow_html=True)

# Layout de dos columnas para controles y visualización
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<p class="sub-header">Configuración</p>', unsafe_allow_html=True)
    
    # Opción para seleccionar entre directorios existentes o subir archivos
    option = st.radio("Seleccionar método de entrada:", ["Seleccionar directorio", "Subir archivos DICOM (ZIP)"])

# Función para buscar recursivamente archivos DICOM en un directorio
def find_dicom_series(directory):
    """Busca recursivamente series DICOM en el directorio y sus subdirectorios"""
    series_found = []
    # Explorar cada subdirectorio
    for root, dirs, files in os.walk(directory):
        try:
            # Intentar leer series DICOM en este directorio
            series_ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(root)
            for series_id in series_ids:
                series_files = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(root, series_id)
                if series_files:
                    series_found.append((series_id, root, series_files))
        except Exception as e:
            with col1:
                st.warning(f"Advertencia al buscar en {root}: {str(e)}")
            continue
    
    return series_found

with col1:
    if option == "Seleccionar directorio":
        # Función para seleccionar directorios
        def dir_selector(folder_path='.'):
            dirnames = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
            if not dirnames:
                st.info("No se encontraron directorios en la ruta actual.")
                return None
            selected_folder = st.selectbox('Seleccionar carpeta', dirnames)
            if selected_folder is None:
                return None
            return os.path.join(folder_path, selected_folder)
        
        dirname = dir_selector()
        temp_dir = None  # No hay directorio temporal para este caso
    else:
        # Opción para subir archivos como ZIP
        uploaded_file = st.file_uploader("Sube un archivo ZIP con tus archivos DICOM", type="zip")
        dirname = None
        temp_dir = None
        
        if uploaded_file is not None:
            # Crear un directorio temporal para extraer los archivos
            temp_dir = tempfile.mkdtemp()
            try:
                # Leer el contenido del ZIP
                with zipfile.ZipFile(io.BytesIO(uploaded_file.read()), 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Establecer dirname al directorio temporal
                dirname = temp_dir
                st.markdown('<div class="success-box">Archivos extraídos correctamente.</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error al extraer el archivo ZIP: {str(e)}")

def plot_slice(vol, slice_ix):
    fig, ax = plt.subplots()
    plt.axis('off')
    selected_slice = vol[slice_ix, :, :]
    ax.imshow(selected_slice, origin='lower', cmap='gray')
    return fig

if dirname is not None:
    # Buscar todas las series DICOM recursivamente
    with col1:
        with st.spinner('Buscando series DICOM...'):
            dicom_series = find_dicom_series(dirname)
    
    if not dicom_series:
        with col1:
            st.error("No se encontraron archivos DICOM válidos en el directorio seleccionado/subido.")
            # Mostrar el contenido del directorio para depuración
            st.markdown('<p class="sub-header">Contenido del directorio:</p>', unsafe_allow_html=True)
            files_found = []
            for root, dirs, files in os.walk(dirname):
                for file in files:
                    files_found.append(os.path.join(root, file))
            if files_found:
                st.code("\n".join(files_found[:20]))  # Mostrar hasta 20 archivos
                if len(files_found) > 20:
                    st.write(f"... y {len(files_found) - 20} archivos más")
            else:
                st.write("No se encontraron archivos en el directorio")
    else:
        # Mostrar las series encontradas
        with col1:
            st.markdown(f'<div class="info-box">Se encontraron {len(dicom_series)} series DICOM</div>', unsafe_allow_html=True)
            
            # Si hay múltiples series, permitir seleccionar una
            selected_series_idx = 0
            if len(dicom_series) > 1:
                series_options = [f"Serie {i+1}: {series_id[:10]}... ({len(files)} archivos)" 
                                for i, (series_id, _, files) in enumerate(dicom_series)]
                selected_series_option = st.selectbox("Seleccionar serie DICOM:", series_options)
                selected_series_idx = series_options.index(selected_series_option)
            
            try:
                # Obtener la serie seleccionada
                series_id, series_dir, dicom_names = dicom_series[selected_series_idx]
                
                reader = sitk.ImageSeriesReader()
                reader.SetFileNames(dicom_names)
                reader.LoadPrivateTagsOn()
                reader.MetaDataDictionaryArrayUpdateOn()
                data = reader.Execute()
                img = sitk.GetArrayViewFromImage(data)
            
                n_slices = img.shape[0]
                slice_ix = st.slider('Seleccionar corte', 0, n_slices - 1, int(n_slices/2))
                output = st.radio('Tipo de visualización', ['Imagen', 'Metadatos'], index=0)
            except Exception as e:
                st.error(f"Error al procesar los archivos DICOM: {str(e)}")
                st.write("Detalles del error:", str(e))
        
        with col2:
            if 'output' in locals() and output == 'Imagen':
                st.markdown('<p class="sub-header">Visualización DICOM</p>', unsafe_allow_html=True)
                st.markdown('<div class="plot-container">', unsafe_allow_html=True)
                fig = plot_slice(img, slice_ix)
                plot = st.pyplot(fig)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Información adicional sobre la imagen
                st.markdown('<p class="sub-header">Información de la imagen</p>', unsafe_allow_html=True)
                img_info = {
                    "Dimensiones": f"{img.shape[1]} x {img.shape[2]} píxeles",
                    "Número total de cortes": n_slices,
                    "Corte actual": slice_ix + 1,
                    "Valores mín/máx": f"{img[slice_ix].min()} / {img[slice_ix].max()}"
                }
                
                info_cols = st.columns(2)
                for i, (key, value) in enumerate(img_info.items()):
                    with info_cols[i % 2]:
                        st.markdown(f"**{key}:** {value}")
                
            elif 'output' in locals() and output == 'Metadatos':
                st.markdown('<p class="sub-header">Metadatos DICOM</p>', unsafe_allow_html=True)
                try:
                    metadata = dict()
                    for k in reader.GetMetaDataKeys(slice_ix):
                        metadata[k] = reader.GetMetaData(slice_ix, k)
                    df = pd.DataFrame.from_dict(metadata, orient='index', columns=['Valor'])
                    st.dataframe(df, height=600)
                except Exception as e:
                    st.error(f"Error al leer metadatos: {str(e)}")

# Pie de página
st.markdown("""
<hr style="margin-top: 30px;">
<div style="text-align: center; color: #28aec5; font-size: 14px;">
    DieSitCom - Visualizador de imágenes DICOM
</div>
""", unsafe_allow_html=True)

# Limpiar el directorio temporal si se creó uno
if option == "Subir archivos DICOM (ZIP)" and temp_dir and os.path.exists(temp_dir):
    # Nota: En una aplicación real, deberías limpiar los directorios temporales
    # cuando la aplicación se cierre, pero en Streamlit esto es complicado
    # ya que las sesiones persisten. Una solución es mantener un registro
    # de directorios temporales y limpiarlos al inicio.
    pass
