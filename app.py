import os
import io
import zipfile
import tempfile
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import SimpleITK as sitk

st.sidebar.title('DieSitCom')

# Opción para seleccionar entre directorios existentes o subir archivos
option = st.sidebar.radio("Seleccionar método de entrada:", ["Seleccionar directorio", "Subir archivos DICOM (ZIP)"])

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
            st.sidebar.warning(f"Advertencia al buscar en {root}: {str(e)}")
            continue
    
    return series_found

if option == "Seleccionar directorio":
    # Función original para seleccionar directorios
    def dir_selector(folder_path='.'):
        dirnames = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
        selected_folder = st.sidebar.selectbox('Select a folder', dirnames)
        if selected_folder is None:
            return None
        return os.path.join(folder_path, selected_folder)
    
    dirname = dir_selector()
    temp_dir = None  # No hay directorio temporal para este caso
else:
    # Opción para subir archivos como ZIP
    uploaded_file = st.sidebar.file_uploader("Sube un archivo ZIP con tus archivos DICOM", type="zip")
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
            st.sidebar.success(f"Archivos extraídos correctamente a: {temp_dir}")
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
    dicom_series = find_dicom_series(dirname)
    
    if not dicom_series:
        st.error("No se encontraron archivos DICOM válidos en el directorio seleccionado/subido.")
        # Mostrar el contenido del directorio para depuración
        st.write("Contenido del directorio:")
        files_found = []
        for root, dirs, files in os.walk(dirname):
            for file in files:
                files_found.append(os.path.join(root, file))
        if files_found:
            st.write(files_found[:20])  # Mostrar hasta 20 archivos
            if len(files_found) > 20:
                st.write(f"... y {len(files_found) - 20} archivos más")
        else:
            st.write("No se encontraron archivos en el directorio")
    else:
        # Mostrar las series encontradas
        st.sidebar.write(f"Se encontraron {len(dicom_series)} series DICOM")
        
        # Si hay múltiples series, permitir seleccionar una
        selected_series_idx = 0
        if len(dicom_series) > 1:
            series_options = [f"Serie {i+1}: {series_id[:10]}... ({len(files)} archivos)" 
                             for i, (series_id, _, files) in enumerate(dicom_series)]
            selected_series_option = st.sidebar.selectbox("Seleccionar serie DICOM:", series_options)
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
            slice_ix = st.sidebar.slider('Slice', 0, n_slices - 1, int(n_slices/2))
            output = st.sidebar.radio('Output', ['Image', 'Metadata'], index=0)
            
            if output == 'Image':
                fig = plot_slice(img, slice_ix)
                plot = st.pyplot(fig)
            else:
                metadata = dict()
                for k in reader.GetMetaDataKeys(slice_ix):
                    metadata[k] = reader.GetMetaData(slice_ix, k)
                df = pd.DataFrame.from_dict(metadata, orient='index', columns=['Value'])
                st.dataframe(df)
        except Exception as e:
            st.error(f"Error al procesar los archivos DICOM: {str(e)}")
            st.write("Detalles del error:", str(e))

# Limpiar el directorio temporal si se creó uno
if option == "Subir archivos DICOM (ZIP)" and temp_dir and os.path.exists(temp_dir):
    # Nota: En una aplicación real, deberías limpiar los directorios temporales
    # cuando la aplicación se cierre, pero en Streamlit esto es complicado
    # ya que las sesiones persisten. Una solución es mantener un registro
    # de directorios temporales y limpiarlos al inicio.
    pass
