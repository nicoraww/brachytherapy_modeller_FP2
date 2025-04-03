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

if option == "Seleccionar directorio":
    # Función original para seleccionar directorios
    def dir_selector(folder_path='.'):
        dirnames = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
        selected_folder = st.sidebar.selectbox('Select a folder', dirnames)
        if selected_folder is None:
            return None
        return os.path.join(folder_path, selected_folder)
    
    dirname = dir_selector()
else:
    # Opción para subir archivos como ZIP
    uploaded_file = st.sidebar.file_uploader("Sube un archivo ZIP con tus archivos DICOM", type="zip")
    dirname = None
    
    if uploaded_file is not None:
        # Crear un directorio temporal para extraer los archivos
        with tempfile.TemporaryDirectory() as temp_dir:
            # Leer el contenido del ZIP
            with zipfile.ZipFile(io.BytesIO(uploaded_file.read()), 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Establecer dirname al directorio temporal
            dirname = temp_dir
            st.sidebar.success(f"Archivos extraídos correctamente")

def plot_slice(vol, slice_ix):
    fig, ax = plt.subplots()
    plt.axis('off')
    selected_slice = vol[slice_ix, :, :]
    ax.imshow(selected_slice, origin='lower', cmap='gray')
    return fig

if dirname is not None:
    try:
        reader = sitk.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames(dirname)
        
        if not dicom_names:
            st.error("No se encontraron archivos DICOM en el directorio seleccionado/subido.")
        else:
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
