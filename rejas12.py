import streamlit as st
import math
import urllib.parse
import json
import os
from fpdf import FPDF

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Herrería Roma v4.5", page_icon="⚒️")

# --- PERSISTENCIA ---
CONFIG_FILE = "precios_config.json"
def cargar_precios():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {"p_barra_ref": 35000.0, "p_m2_malla": 14000.0, "p_litro_pintura": 15000.0, "p_consumibles_perc": 5, "nombre_herreria": "Herrería Roma"}

precios_db = cargar_precios()

# --- DATA TÉCNICA ARGENTINA ---
PESOS_H = {"1/2 (12.7mm)": 0.99, "9/16 (14mm)": 1.21, "5/8 (15.8mm)": 1.55}
PESOS_C = {
    "Caño 30x30x1.6": 1.41, "Caño 40x30x1.6": 1.66, "Caño 40x40x1.6": 1.91,
    "Caño 60x30x1.6": 2.16, "Caño 60x40x1.6": 2.41, "Caño 60x60x2.0": 3.70, 
    "Caño 80x80x2.0": 4.90, "Caño 100x100x2.0": 6.10
}
PESOS_ANGULO_T = {
    "1/2 x 1/8": 0.88, "3/4 x 1/8": 1.35, "1 x 1/8": 1.83, "1 1/4 x 1/8": 2.30, 
    "1 1/2 x 1/8": 2.80, "2 x 1/8": 3.80, "1 x 3/16": 2.65, "1 1/4 x 3/16": 3.35,
    "1 1/2 x 3/16": 4.05, "2 x 3/16": 5.50, "1 1/2 x 1/4": 5.30, "2 x 1/4": 7.30
}
PRECIOS_HERRAJES = {
    "Cerradura Seg.": 35000, "Pomelas (Par)": 12000, "Caja Cerradura": 8500,
    "Kit Ruedas (Par)": 22000, "Rodillo Guía (Set)": 15000, "Angulo Guía 1 1/4 (m)": 5800
}

def redon(n): return math.ceil(n / 1000) * 1000

class PDF(FPDF):
    def __init__(self, nombre_h="Herrería"):
        super().__init__()
        self.nombre_h = nombre_h
    def header(self):
        if os.path.exists("logo_roma.png"): self.image("logo_roma.png", 10, 8, 33)
        self.set_font('helvetica', 'B', 16); self.set_x(45)
        self.cell(0, 10, self.nombre_h.upper(), 0, 1, 'L')
        self.set_font('helvetica', 'I', 10); self.set_x(45)
        self.cell(0, 5, 'Presupuesto Profesional - Validez 10 días', 0, 1, 'L')
        self.ln(15)

# --- UI SIDEBAR ---
st.sidebar.header("⚙️ Configuración")
nombre_h = st.sidebar.text_input("Nombre de Herrería", precios_db['nombre_herreria'])
p_barra_ref = st.sidebar.number_input("Precio Caño 40x40 (6m)", value=float(precios_db['p_barra_ref']))
p_kg = p_barra_ref / (1.91 * 6)
p_m2_malla = st.sidebar.number_input("Precio m2 Malla", value=float(precios_db['p_m2_malla']))
p_litro_pintura = st.sidebar.number_input("Precio Litro Pintura", value=float(precios_db['p_litro_pintura']))
p_consum_perc = st.sidebar.slider("Consumibles %", 1, 15, int(precios_db['p_consumibles_perc']))
perc_desp = st.sidebar.slider("% Desperdicio Mat.", 0, 20, 10) / 100

st.sidebar.divider()
st.sidebar.header("👷 Mano de Obra")
metodo_mo = st.sidebar.selectbox("Cálculo MO", ["% de Materiales", "Por Día", "Por m2"])
val_mo = st.sidebar.number_input("Valor Base MO $", value=45000)

# --- VARIABLES DE CALCULO ---
m_barrotes = 0; m_planchuela = 0; listado_caños = {}; m2_malla_total = 0
m_angulo_total = 0; m_perfilT_total = 0; costo_herrajes = 0; detalles_obra = []
lista_herrajes_taller = []; area_total_m2 = 0
mat_barrote_elegido = "1/2 (12.7mm)"; medida_marco_desplegado = "1 x 1/8"

st.title(f"🛡️ {nombre_h}")
cliente = st.text_input("Nombre del Cliente", "Presupuesto Particular")

# --- MÓDULO 1: PAÑOS ---
st.header("1. Paños de Frente / Rejas")
if st.checkbox("Incluir Paños", value=True):
    c1, c2 = st.columns(2)
    cant_f = c1.number_input("Cantidad", 1, 20, 2, key="nf")
    an_f = c1.number_input("Ancho (m)", 0.1, 10.0, 2.5, key="wf")
    al_f = c1.number_input("Alto (m)", 0.1, 5.0, 1.8, key="hf")
    area_total_m2 += (an_f * al_f) * cant_f
    relleno_f = c2.radio("Relleno", ["Barrotes", "Metal Desplegado"], key="rel_f")
    if c2.checkbox("¿Lleva Bastidor?", value=True, key="bf"):
        m_c_f = c2.selectbox("Caño Bastidor", list(PESOS_C.keys()), key="cf")
        listado_caños[m_c_f] = listado_caños.get(m_c_f, 0) + (an_f + al_f) * 2 * cant_f
    if relleno_f == "Barrotes":
        mat_barrote_elegido = c2.selectbox("Hierro", list(PESOS_H.keys()), key="hf_f")
        m_barrotes += (math.ceil(an_f / 0.12) + 1) * al_f * cant_f
        m_planchuela += an_f * c2.number_input("Planchuelas", 1, 6, 2, key="pf") * cant_f
    else:
        medida_marco_desplegado = c2.selectbox("Medida Ángulo/T", list(PESOS_ANGULO_T.keys()), key="med_f")
        m2_malla_total += (an_f * al_f) * cant_f
        m_angulo_total += ((an_f * al_f) * cant_f) * 3
        m_perfilT_total += ((an_f * al_f) * cant_f) * 1
    detalles_obra.append(f"{cant_f} Paños de {relleno_f}")

# --- MÓDULO 2: PUERTA ---
st.divider()
st.header("2. Puerta Peatonal")
if st.checkbox("Incluir Puerta"):
    cp1, cp2 = st.columns(2)
    an_p = cp1.number_input("Ancho (m)", 0.5, 2.0, 0.9, key="wp")
    al_p = cp1.number_input("Alto (m)", 1.5, 3.0, 2.0, key="hp")
    area_total_m2 += (an_p * al_p)
    relleno_p = cp2.radio("Relleno", ["Barrotes", "Metal Desplegado"], key="rel_p")
    if cp2.checkbox("¿Lleva Bastidor?", value=True, key="bp"):
        m_c_p = cp2.selectbox("Caño Puerta", list(PESOS_C.keys()), key="cp")
        listado_caños[m_c_p] = listado_caños.get(m_c_p, 0) + (an_p + al_p) * 2
    if relleno_p == "Barrotes":
        m_barrotes += (math.ceil(an_p / 0.12) + 1) * al_p
        m_planchuela += an_p * cp2.number_input("Planchuelas", 1, 6, 2, key="pp")
    else:
        m2_malla_total += (an_p * al_p)
        m_angulo_total += (an_p * al_p) * 3
        m_perfilT_total += (an_p * al_p) * 1
    costo_herrajes += sum([PRECIOS_HERRAJES["Cerradura Seg."], PRECIOS_HERRAJES["Pomelas (Par)"], PRECIOS_HERRAJES["Caja Cerradura"]])
    lista_herrajes_taller.extend(["Cerradura Seg.", "2 Pomelas", "Caja Cerradura"])
    detalles_obra.append(f"1 Puerta Peatonal de {relleno_p}")

# --- MÓDULO 3: PORTÓN ---
st.divider()
st.header("3. Portón Vehicular")
if st.checkbox("Incluir Portón"):
    cpo1, cpo2 = st.columns(2)
    an_po = cpo1.number_input("Ancho Total (m)", 2.0, 10.0, 3.0, key="wpo")
    tipo_po = cpo1.radio("Apertura", ["Corredizo", "Batiente"], key="tpo")
    area_total_m2 += (an_po * 2.1)
    relleno_po = cpo2.radio("Relleno", ["Barrotes", "Metal Desplegado"], key="rel_po")
    if cpo2.checkbox("¿Lleva Bastidor?", value=True, key="bpo"):
        m_c_po = cpo2.selectbox("Caño Portón", list(PESOS_C.keys()), key="cpo")
        listado_caños[m_c_po] = listado_caños.get(m_c_po, 0) + (an_po * 2 + 8.0)
    if relleno_po == "Barrotes":
        m_barrotes += (math.ceil(an_po / 0.12) + 1) * 2.1
        m_planchuela += an_po * cpo2.number_input("Planchuelas", 1, 6, 2, key="ppo")
    else:
        m2_malla_total += (an_po * 2.1)
        m_angulo_total += (an_po * 2.1) * 3
        m_perfilT_total += (an_po * 2.1) * 1
    if tipo_po == "Corredizo":
        costo_herrajes += PRECIOS_HERRAJES["Kit Ruedas (Par)"] + PRECIOS_HERRAJES["Rodillo Guía (Set)"] + (an_po * 2 * PRECIOS_HERRAJES["Angulo Guía 1 1/4 (m)"])
        lista_herrajes_taller.extend(["Kit Ruedas", "Set Rodillos", f"{an_po*2:.1f}m Ángulo Guía"])
    else:
        costo_herrajes += PRECIOS_HERRAJES["Pomelas (Par)"] * 2
        lista_herrajes_taller.append("2 Juegos Pomelas Ref.")
    detalles_obra.append(f"1 Portón {tipo_po} de {relleno_po}")

# --- SECCIÓN: EXTRAS ---
st.divider()
st.header("4. Servicios y Extras")
cs1, cs2 = st.columns(2)
p_flete = cs1.number_input("Flete $", value=20000)
p_coloc = cs2.number_input("Colocación $", value=35000)
p_adicional = st.number_input("Adicional (Altura / Distancia / Viáticos) $", value=0)

# --- PROCESO DE CÁLCULO ---
if st.button("🚀 GENERAR PRESUPUESTO", type="primary", use_container_width=True):
    p_b = PESOS_H.get(mat_barrote_elegido, 1.21)
    p_ang = PESOS_ANGULO_T.get(medida_marco_desplegado, 1.83)
    
    peso_caños = sum([m * PESOS_C[med] for med, m in listado_caños.items()])
    peso_barrotes = (m_barrotes * p_b)
    peso_extra = (m_planchuela * 0.9) + ((m_angulo_total + m_perfilT_total) * p_ang)
    peso_total_hierro = peso_caños + peso_barrotes + peso_extra
    
    kg_electrodos = math.ceil(peso_total_hierro / 40)
    discos_corte = math.ceil(peso_total_hierro / 30)
    
    c_hierros = peso_total_hierro * p_kg
    sup_pint = (peso_total_hierro * 0.05) + (m2_malla_total * 2)
    l_pint = math.ceil(max(1, sup_pint / 10 * 2))
    
    c_mats_puros = c_hierros + (m2_malla_total * p_m2_malla) + (l_pint * p_litro_pintura) + costo_herrajes
    c_consum = c_mats_puros * (p_consum_perc / 100)
    mats_redon = redon((c_mats_puros + c_consum) * (1 + perc_desp))
    
    mo_base = mats_redon * (val_mo/100) if metodo_mo == "% de Materiales" else area_total_m2 * val_mo
    mo_redon = redon(mo_base)
    
    total_gral = mats_redon + mo_redon + p_flete + p_coloc + p_adicional

    st.success(f"## TOTAL FINAL: ${total_gral:,.0f}")
    
    pdf = PDF(nombre_h=nombre_h)
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 12); pdf.cell(0, 10, f"Cliente: {cliente}", 0, 1)
    pdf.set_font("helvetica", '', 11); pdf.multi_cell(0, 8, f"Detalle: {', '.join(detalles_obra)}")
    pdf.ln(5)
    pdf.cell(0, 8, f"- Materiales y Consumibles: ${mats_redon:,.0f}", 0, 1)
    pdf.cell(0, 8, f"- Mano de Obra: ${mo_redon:,.0f}", 0, 1)
    pdf.cell(0, 8, f"- Otros (Flete/Coloc/Extras): ${p_flete + p_coloc + p_adicional:,.0f}", 0, 1)
    pdf.ln(5); pdf.set_font("helvetica", 'B', 14); pdf.cell(0, 15, f"TOTAL FINAL: ${total_gral:,.0f}", 0, 1)
    pdf.set_font("helvetica", 'I', 9); pdf.cell(0, 10, "* Presupuesto valido por 10 dias corridos por inestabilidad de precios.", 0, 1)
    
    st.download_button("📥 DESCARGAR PDF", data=bytes(pdf.output()), file_name=f"Presupuesto_{cliente}.pdf")

    with st.expander("🛠️ LISTA PARA COMPRAS / TALLER"):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.write("### Hierros:")
            for med, met in listado_caños.items(): st.write(f"- {med}: {math.ceil((met*1.1)/6)} barras")
            if m_barrotes > 0: st.write(f"- Hierro {mat_barrote_elegido}: {math.ceil((m_barrotes*1.1)/6)} barras")
            if m_angulo_total > 0:
                st.write(f"- Ángulo {medida_marco_desplegado}: {math.ceil((m_angulo_total*1.1)/6)} barras")
                st.write(f"- Perfil T {medida_marco_desplegado}: {math.ceil((m_perfilT_total*1.1)/6)} barras")
                st.write(f"- Malla Desplegada: {math.ceil(m2_malla_total/2.4)} planchas")
        with col_t2:
            st.write("### Insumos:")
            st.write(f"- **Pintura:** {l_pint} Litros")
            st.write(f"- **Electrodos:** {kg_electrodos} kg")
            st.write(f"- **Discos de Corte:** {discos_corte} unidades")
            if lista_herrajes_taller:
                st.write("### Herrajes:")
                for h in set(lista_herrajes_taller): st.write(f"- {h}")