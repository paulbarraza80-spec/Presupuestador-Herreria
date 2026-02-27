import streamlit as st
import math
import urllib.parse
import json
import os
from fpdf import FPDF
from PIL import Image

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Herrería Pro v4.2", page_icon="⚒️")

# --- PERSISTENCIA (JSON) ---
CONFIG_FILE = "precios_config.json"

def cargar_precios():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {
        "p_barra_ref": 35000.0, "p_m2_malla": 14000.0, "p_litro_pintura": 15000.0,
        "p_consumibles_perc": 5, "nombre_herreria": "Mi Herrería"
    }

precios_db = cargar_precios()

# --- BASE DE DATOS TÉCNICA ---
PESOS_H = {"1/2 (12.7mm)": 0.99, "9/16 (14mm)": 1.21, "5/8 (15.8mm)": 1.55}
PESOS_C = {
    "Caño 30x30x1.6": 1.41, "Caño 40x30x1.6": 1.66, "Caño 40x40x1.6": 1.91,
    "Caño 60x30x1.6": 2.16, "Caño 60x40x1.6": 2.41,
    "Caño 60x60x2.0": 3.70, "Caño 80x80x2.0": 4.90, "Caño 100x100x2.0": 6.10
}
PESO_ANGULO_MARCO = 1.10 
PRECIOS_HERRAJES = {
    "Cerradura Seg.": 35000, "Pomelas (Par)": 12000, "Caja Cerradura": 8500,
    "Kit Ruedas (Par)": 22000, "Rodillo Guía (Set)": 15000, "Angulo Guía 1 1/4 (m)": 5800
}

def redon(n): return math.ceil(n / 1000) * 1000
def gen_ws(txt): return f"https://wa.me/?text={urllib.parse.quote(txt)}"

# --- PDF CLASS CON LOGO ---
class PDF(FPDF):
    def __init__(self, logo_img=None):
        super().__init__()
        self.logo_img = logo_img

    def header(self):
        if self.logo_img:
            # Insertar logo si existe (ancho de 30mm)
            self.image(self.logo_img, 10, 8, 30)
            self.set_x(45) # Desplazar texto a la derecha del logo
        
        self.set_font('helvetica', 'B', 16)
        self.cell(0, 10, nombre_h.upper(), 0, 1, 'L' if self.logo_img else 'C')
        self.set_font('helvetica', 'I', 10)
        self.set_x(45 if self.logo_img else 10)
        self.cell(0, 5, 'Presupuesto Profesional', 0, 1, 'L' if self.logo_img else 'C')
        self.ln(15)

# --- SIDEBAR: CONFIGURACIÓN ---
st.sidebar.header("⚙️ Configuración")
nombre_h = st.sidebar.text_input("Nombre de Herrería", precios_db['nombre_herreria'])
logo_file = st.sidebar.file_uploader("Subir Logo (JPG/PNG)", type=['png', 'jpg', 'jpeg'])

p_barra_ref = st.sidebar.number_input("Precio Barra 40x40 (6m)", value=float(precios_db['p_barra_ref']))
p_kg = p_barra_ref / (1.91 * 6)
p_m2_malla = st.sidebar.number_input("Precio m2 Malla", value=float(precios_db['p_m2_malla']))
p_litro_pintura = st.sidebar.number_input("Precio Litro Pintura", value=float(precios_db['p_litro_pintura']))
p_consum_perc = st.sidebar.slider("Consumibles %", 1, 15, int(precios_db['p_consumibles_perc']))

if st.sidebar.button("💾 Guardar Configuración"):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"p_barra_ref": p_barra_ref, "p_m2_malla": p_m2_malla, "p_litro_pintura": p_litro_pintura, "p_consumibles_perc": p_consum_perc, "nombre_herreria": nombre_h}, f)
    st.sidebar.success("¡Datos guardados!")

st.sidebar.divider()
st.sidebar.header("👷 Mano de Obra")
metodo_mo = st.sidebar.selectbox("Cálculo MO", ["% de Materiales", "Por Día / Jornal", "Por Metro Cuadrado"])
dias_trabajo = 1
if metodo_mo == "Por Día / Jornal":
    val_mo = st.sidebar.number_input("Precio por Día $", 20000, 150000, 45000)
    dias_trabajo = st.sidebar.number_input("Días estimados", 1, 60, 3)
elif metodo_mo == "% de Materiales":
    val_mo = st.sidebar.number_input("% sobre materiales", 50, 250, 100)
else:
    val_mo = st.sidebar.number_input("Precio por m2 $", 10000, 120000, 35000)

nivel_mo = st.sidebar.select_slider("Calidad", options=["Económico", "Estándar", "Premium"], value="Estándar")
perc_desp = st.sidebar.slider("% Desperdicio", 0, 20, 10) / 100

st.title(f"🛡️ {nombre_h}")
cliente = st.text_input("Nombre del Cliente", "Presupuesto Particular")

# --- VARIABLES ---
m_barrotes = 0; m_planchuela = 0; listado_caños = {}; m2_malla_total = 0; m_angulo_interno = 0
costo_herrajes = 0; detalles_obra = []; m_angulo_guia_porton = 0; area_total_m2 = 0

# --- MÓDULOS ---
st.header("1. Paños Fijos / Rejas")
if st.checkbox("Incluir Paños", value=True):
    c1, c2 = st.columns(2)
    cant_f = c1.number_input("Cantidad", 1, 20, 1, key="nf")
    an_f = c1.number_input("Ancho (m)", 0.1, 10.0, 2.0, key="wf")
    al_f = c1.number_input("Alto (m)", 0.1, 5.0, 1.5, key="hf")
    area_total_m2 += (an_f * al_f) * cant_f
    if c2.checkbox("Lleva Bastidor", value=True, key="bf"):
        m_c = c2.selectbox("Caño", list(PESOS_C.keys()), key="cf")
        listado_caños[m_c] = listado_caños.get(m_c, 0) + (an_f + al_f) * 2 * cant_f
    m_barrotes += (math.ceil(an_f / 0.12) + 1) * al_f * cant_f
    m_planchuela += an_f * 2 * cant_f
    detalles_obra.append(f"{cant_f} Rejas ({an_f}x{al_f}m)")

st.divider()
if st.checkbox("Incluir Puerta"):
    c1p, c2p = st.columns(2)
    an_p = c1p.number_input("Ancho", 0.5, 2.0, 0.9, key="wp")
    al_p = c1p.number_input("Alto", 1.5, 3.0, 2.0, key="hp")
    area_total_m2 += (an_p * al_p)
    if c2p.checkbox("Lleva Bastidor", value=True, key="bp"):
        m_c_p = c2p.selectbox("Caño Puerta", list(PESOS_C.keys()), key="cp")
        listado_caños[m_c_p] = listado_caños.get(m_c_p, 0) + (an_p + al_p) * 2
    m_barrotes += (math.ceil(an_p / 0.12) + 1) * al_p
    costo_herrajes += sum([PRECIOS_HERRAJES["Cerradura Seg."], PRECIOS_HERRAJES["Pomelas (Par)"], PRECIOS_HERRAJES["Caja Cerradura"]])
    detalles_obra.append("1 Puerta Peatonal")

st.divider()
if st.checkbox("Incluir Portón"):
    c1po, c2po = st.columns(2)
    an_po = c1po.number_input("Ancho Total", 2.0, 10.0, 3.0, key="wpo")
    tipo_po = c1po.radio("Movimiento", ["Corredizo", "Batiente"])
    area_total_m2 += (an_po * 2.1)
    if c2po.checkbox("Lleva Bastidor", value=True, key="bpo"):
        m_c_po = c2po.selectbox("Caño Portón", list(PESOS_C.keys()), key="cpo")
        listado_caños[m_c_po] = listado_caños.get(m_c_po, 0) + (an_po * 2 + 8.0)
    m_barrotes += (math.ceil(an_po / 0.12) + 1) * 2.1
    if tipo_po == "Corredizo":
        costo_herrajes += PRECIOS_HERRAJES["Kit Ruedas (Par)"] + PRECIOS_HERRAJES["Rodillo Guía (Set)"] + (an_po * 2 * PRECIOS_HERRAJES["Angulo Guía 1 1/4 (m)"])
    detalles_obra.append(f"1 Portón {tipo_po}")

st.divider()
st.header("Servicios")
col_f, col_c = st.columns(2)
p_flete = col_f.number_input("Costo Flete $", value=20000)
b_flete = col_f.checkbox("Bonificar Flete")
p_coloc = col_c.number_input("Costo Colocación $", value=35000)
b_coloc = col_c.checkbox("Bonificar Colocación")

# --- CALCULO ---
if st.button("🚀 GENERAR PRESUPUESTO", type="primary", use_container_width=True):
    # Materiales
    c_caños = sum([m * PESOS_C[med] * p_kg for med, m in listado_caños.items()])
    c_mats_puros = c_caños + (m_barrotes * 1.2 * p_kg) + (m_planchuela * 0.9 * p_kg) + costo_herrajes
    c_consum = c_mats_puros * (p_consum_perc / 100)
    mats_redon = redon((c_mats_puros + c_consum) * (1 + perc_desp))

    # Mano de Obra
    if metodo_mo == "% de Materiales": mo_base = mats_redon * (val_mo / 100)
    elif metodo_mo == "Por Día / Jornal": mo_base = dias_trabajo * val_mo
    else: mo_base = area_total_m2 * val_mo
    mo_redon = redon(mo_base * {"Económico": 0.8, "Estándar": 1.0, "Premium": 1.4}[nivel_mo])

    v_flete = 0 if b_flete else p_flete
    v_coloc = 0 if b_coloc else p_coloc
    total_gral = mats_redon + mo_redon + v_flete + v_coloc

    # --- SALIDA ---
    st.success(f"## TOTAL: ${total_gral:,.0f}")
    
    # PDF
    pdf = PDF(logo_img=logo_file if logo_file else None)
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, f"Cliente: {cliente}", 0, 1)
    pdf.set_font("helvetica", '', 11)
    pdf.multi_cell(0, 8, f"Trabajo: {', '.join(detalles_obra)}")
    pdf.ln(5)
    pdf.cell(0, 8, f"- Materiales y Consumibles: ${mats_redon:,.0f}", 0, 1)
    pdf.cell(0, 8, f"- Mano de Obra y Taller: ${mo_redon:,.0f}", 0, 1)
    pdf.cell(0, 8, f"- Flete: {'BONIFICADO' if b_flete else f'${p_flete:,.0f}'}", 0, 1)
    pdf.cell(0, 8, f"- Colocación: {'BONIFICADO' if b_coloc else f'${p_coloc:,.0f}'}", 0, 1)
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 15, f"TOTAL FINAL: ${total_gral:,.0f}", 0, 1)
    
    pdf_bytes = bytes(pdf.output())
    st.download_button("📥 Descargar PDF con Logo", data=pdf_bytes, file_name=f"Presupuesto_{cliente}.pdf", mime="application/pdf")
    
    st.markdown(f'[📩 Enviar por WhatsApp]({gen_ws("Hola " + cliente + ", presupuesto de " + nombre_h + ": $" + str(total_gral))})')