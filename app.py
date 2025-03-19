import streamlit as st
import base64

def generate_download_link(code):
    """Genera un link para descargar el código como archivo .py"""
    b64 = base64.b64encode(code.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="template_braquiterapia.py">Descargar código</a>'
    return href

st.title("Generador de Templates de Braquiterapia")
st.subheader("Personalización de parámetros para impresión 3D")

# Imagen de muestra (opcional)
st.image("https://via.placeholder.com/400x200?text=Template+de+Braquiterapia", caption="Ejemplo de template")

# Parámetros generales
st.header("Parámetros Generales")
col1, col2 = st.columns(2)
with col1:
    diametro_base = st.number_input("Diámetro de la base (mm)", value=50.0, step=0.5)
    altura_base = st.number_input("Altura de la base (mm)", value=10.0, step=0.5)
    
with col2:
    radio_curvatura = st.number_input("Radio de curvatura de la base (mm)", value=150.0, step=5.0)
    angulo_curvatura = st.number_input("Ángulo de curvatura (grados)", value=30.0, step=1.0)

# Parámetros del cilindro central
st.header("Cilindro Central")
col1, col2 = st.columns(2)
with col1:
    diametro_cilindro = st.number_input("Diámetro del cilindro (mm)", value=20.0, step=0.5)
    altura_cilindro = st.number_input("Altura del cilindro (mm)", value=80.0, step=0.5)
    
with col2:
    diametro_orificio_central = st.number_input("Diámetro del orificio central (mm)", value=5.0, step=0.1)
    forma_punta = st.selectbox("Forma de la punta del cilindro", ["Redondeada", "Cónica", "Plana"])

# Parámetros de los orificios para agujas
st.header("Orificios para Agujas")
num_orificios = st.slider("Número de orificios para agujas", 5, 30, 15)
diametro_orificios = st.number_input("Diámetro de los orificios (mm)", value=1.5, step=0.1)

# Patrones de distribución
patron_distribucion = st.selectbox("Patrón de distribución de orificios", 
                                   ["Rectangular", "Circular", "Hexagonal", "Personalizado"])

# Opciones avanzadas
with st.expander("Opciones avanzadas"):
    tolerancia = st.number_input("Tolerancia para impresión 3D (mm)", value=0.1, step=0.01)
    material = st.selectbox("Material recomendado", ["PLA", "ABS", "PETG", "Resina médica"])
    infill = st.slider("Porcentaje de relleno recomendado", 50, 100, 80)

# Botón para generar código
if st.button("Generar Código FreeCAD"):
    # Generar el código Python para FreeCAD
    code = f"""# Código generado automáticamente para FreeCAD
# Template de Braquiterapia para tratamiento de cáncer de cérvix
# Parámetros personalizados:
# - Diámetro base: {diametro_base} mm
# - Altura base: {altura_base} mm
# - Radio curvatura: {radio_curvatura} mm
# - Diámetro cilindro: {diametro_cilindro} mm
# - Altura cilindro: {altura_cilindro} mm

import FreeCAD as App
import Part
import Draft
from FreeCAD import Base

# Crear un nuevo documento
doc = App.newDocument("TemplateBraquiterapia")

# Crear la base con curvatura
def crear_base_curva():
    # Crear un cilindro base
    cilindro = Part.makeCylinder({diametro_base/2}, {altura_base})
    
    # Crear un plano de corte para la curvatura
    plano = Part.makeBox({diametro_base*2}, {diametro_base*2}, {diametro_base*2})
    plano.translate(Base.Vector(-{diametro_base}, -{diametro_base}, -{radio_curvatura}))
    plano.rotate(Base.Vector(0,0,0), Base.Vector(1,0,0), {angulo_curvatura})
    
    # Cortar la base con el plano
    base_curva = cilindro.cut(plano)
    return base_curva

# Crear el cilindro central
def crear_cilindro_central():
    cilindro = Part.makeCylinder({diametro_cilindro/2}, {altura_cilindro})
    cilindro.translate(Base.Vector(0, 0, {altura_base}))
    
    # Crear la punta según la forma seleccionada
    if "{forma_punta}" == "Redondeada":
        punta = Part.makeSphere({diametro_cilindro/2})
        punta.translate(Base.Vector(0, 0, {altura_base + altura_cilindro}))
    elif "{forma_punta}" == "Cónica":
        punta = Part.makeCone({diametro_cilindro/2}, 0, {diametro_cilindro/2})
        punta.translate(Base.Vector(0, 0, {altura_base + altura_cilindro}))
    
    # Combinar cilindro y punta si no es plana
    if "{forma_punta}" != "Plana":
        cilindro = cilindro.fuse(punta)
    
    return cilindro

# Crear el orificio central
def crear_orificio_central():
    orificio = Part.makeCylinder({diametro_orificio_central/2}, {altura_base + altura_cilindro + diametro_cilindro/2})
    return orificio

# Crear los orificios para las agujas
def crear_orificios_agujas():
    orificios = []
    
    if "{patron_distribucion}" == "Rectangular":
        # Calcular cuántas filas y columnas necesitamos
        filas = int({num_orificios}**0.5)
        cols = int({num_orificios} / filas) + 1
        
        # Espacio entre orificios
        espacio_x = {diametro_base - diametro_cilindro} / 2 / (cols + 1)
        espacio_y = {diametro_base - diametro_cilindro} / 2 / (filas + 1)
        
        # Posición inicial
        x_start = -{diametro_base/2} + {diametro_cilindro/2} + espacio_x
        y_start = -{diametro_base/2} + {diametro_cilindro/2} + espacio_y
        
        count = 0
        for i in range(filas):
            for j in range(cols):
                if count < {num_orificios}:
                    x = x_start + j * espacio_x
                    y = y_start + i * espacio_y
                    
                    # Verificar si está dentro del área útil (fuera del cilindro central)
                    if (x**2 + y**2)**0.5 > {diametro_cilindro/2 + diametro_orificios}:
                        orificio = Part.makeCylinder({diametro_orificios/2}, {altura_base + altura_cilindro})
                        orificio.translate(Base.Vector(x, y, 0))
                        orificios.append(orificio)
                        count += 1
    
    elif "{patron_distribucion}" == "Circular":
        # Distribuir en anillos concéntricos
        radio_primer_anillo = {diametro_cilindro/2} + {diametro_orificios} * 2
        radio_ultimo_anillo = {diametro_base/2} - {diametro_orificios} * 2
        
        num_anillos = 3
        orificios_por_anillo = {num_orificios} // num_anillos
        
        for anillo in range(num_anillos):
            radio = radio_primer_anillo + anillo * (radio_ultimo_anillo - radio_primer_anillo)/(num_anillos-1)
            for i in range(orificios_por_anillo):
                angulo = i * 360 / orificios_por_anillo
                x = radio * App.Units.Quantity("1 deg").getValueAs("rad").cos()
                y = radio * App.Units.Quantity("1 deg").getValueAs("rad").sin()
                
                orificio = Part.makeCylinder({diametro_orificios/2}, {altura_base + altura_cilindro})
                orificio.translate(Base.Vector(x, y, 0))
                orificios.append(orificio)
    
    return orificios

# Ejecutar el modelado
base = crear_base_curva()
base_obj = doc.addObject("Part::Feature", "Base")
base_obj.Shape = base

cilindro = crear_cilindro_central()
cilindro_obj = doc.addObject("Part::Feature", "Cilindro")
cilindro_obj.Shape = cilindro

# Fusionar base y cilindro
template = base.fuse(cilindro)

# Crear el orificio central
orificio_central = crear_orificio_central()
template = template.cut(orificio_central)

# Crear orificios para agujas
orificios = crear_orificios_agujas()
for i, orificio in enumerate(orificios):
    template = template.cut(orificio)

# Crear el objeto final
template_obj = doc.addObject("Part::Feature", "TemplateBraquiterapia")
template_obj.Shape = template

# Actualizar la vista
doc.recompute()
Gui.SendMsgToActiveView("ViewFit")

print("Template de braquiterapia generado con éxito")
"""
    
    st.code(code, language="python")
    
    # Generar enlace de descarga
    st.markdown(generate_download_link(code), unsafe_allow_html=True)
    
    # Instrucciones para el usuario
    st.success("Código generado con éxito. Copia este código o descárgalo y pégalo en la consola Python de FreeCAD.")
    
    with st.expander("Instrucciones de uso"):
        st.markdown("""
        ### Pasos para usar este código en FreeCAD:
        
        1. Abre FreeCAD
        2. Ve a Ver > Paneles > Consola Python
        3. Copia el código generado
        4. Pégalo en la consola Python y presiona Enter
        5. El modelo se generará automáticamente
        6. Puedes exportarlo como archivo STL para impresión 3D
        
        ### Recomendaciones:
        - Utiliza FreeCAD versión 0.19 o superior
        - Verifica las dimensiones antes de imprimir
        - Para materiales de uso médico, consulta con un especialista
        """)

# Verificación de parámetros y recomendaciones
st.sidebar.title("Verificación y Recomendaciones")

# Verificar proporciones
area_base = 3.14159 * (diametro_base/2)**2
area_cilindro = 3.14159 * (diametro_cilindro/2)**2
proporcion = area_cilindro / area_base

if proporcion > 0.5:
    st.sidebar.warning("⚠️ El cilindro ocupa más del 50% de la base. Considera reducir su diámetro.")
else:
    st.sidebar.success("✅ Proporción cilindro-base adecuada.")

# Verificar diámetro orificios
if diametro_orificios < 1.0:
    st.sidebar.warning("⚠️ Orificios muy pequeños pueden ser difíciles de imprimir con precisión.")
elif diametro_orificios > 3.0:
    st.sidebar.warning("⚠️ Orificios muy grandes pueden comprometer la integridad estructural.")
else:
    st.sidebar.success("✅ Diámetro de orificios adecuado.")

# Instrucciones generales
st.sidebar.subheader("Flujo de trabajo recomendado")
st.sidebar.markdown("""
1. Ajusta los parámetros según las necesidades médicas
2. Genera el código
3. Verifica el modelo en FreeCAD
4. Realiza ajustes si es necesario
5. Exporta a STL
6. Imprime con material biocompatible
""")

# Información sobre el proyecto
st.sidebar.info("Esta herramienta está diseñada para estandarizar el modelado de templates de braquiterapia para tratamiento de cáncer de cérvix.")
