import streamlit as st
import math
import urllib.parse
import json
import os
from fpdf import FPDF
from PIL import Image

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Herrería Pro v4.4", page_icon="⚒️")

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
        "p_consumibles_perc": 5, "nombre_herreria": "Herrería Roma"
    }

precios_db = cargar_precios()

# --- BASE DE DATOS TÉCNICA ARGENTINA ---
PESOS_H = {"1/2 (12.7mm)": 0.99, "9/16 (14mm)": 1.21, "5/8 (15.8mm)": 1.55}
PESOS_C = {
    "Caño 30x30x1.6": 1.41, "Caño 40x30x1.6": 1.66, "Caño 40x40x1.6": 1.91,
    "Caño 60x30x1.6": 2.16, "Caño 60x40x1.6": 2.41,
    "Caño 60x60x2.0": 3.70, "Caño 80x80x2.0": 4.90, "Caño 100x100x2.0": 6.10
}
PRECIOS_HERRAJES = {
    "Cerradura Seg.": 35000, "Pomelas (Par)": 12000, "Caja Cerradura": 8500,
    "Kit Ruedas (Par)": 22000, "Rodillo Guía (Set)": 15000, "Angulo Guía 1 1/4 (m)": 5800
}

def redon(n): return math.ceil(n / 1000) * 1000
def gen_ws(txt): return f"https://wa.me/?text={urllib.parse.quote(txt)}"

# --- PDF CLASS ---
class PDF(FPDF):
    def __init__(self, logo_img=None):
        super().__init__()
        self.logo_img = logo_img

    def header(self):
        # Logo fijo: si no se sube uno, busca 'logo_roma.png' en la carpeta
        final_logo = self.logo_img
        if not final_logo and os.path.exists("logo_roma.png"):
            final_logo = "logo_roma.png"
            
        if final_logo:
            try:
                self.image(final_logo, 10, 8, 30)
                self.set_x(45)
            except: pass
        self.set_font('helvetica', 'B', 16)
        self.cell(0, 10, nombre_h.upper(), 0, 1, 'L' if final_logo else 'C')
        self.set_font('helvetica', 'I', 10)
        self.set_x(45 if final_logo else 10)
        self.cell(0, 5, 'Presupuesto Profesional de Herrería', 0, 1, 'L' if final_logo else 'C')
        self.ln(15)

# --- SIDEBAR: CONFIGURACIÓN ---
st.sidebar.header("⚙️ Configuración")
nombre_h = st.sidebar.text_input("Nombre de Herrería", precios_db.get('nombre_herreria', 'Herrería Roma'))
logo_file = st.sidebar.file_uploader("Subir Logo Temporal", type=['png', 'jpg', 'jpeg'])

p_barra_ref = st.sidebar.number_input("Precio Caño 40x40 (6m) ref.", value=float(precios_db['p_barra_ref']))
p_kg = p_barra_ref / (1.91 * 6)
p_m2_malla = st.sidebar.number_input("Precio m2 Metal Desplegado $", value=float(precios_db['p_m2_malla']))
p_litro_pintura = st.sidebar.number_input("Precio Litro Pintura $", value=float(precios_db['p_litro_pintura']))
p_consum_perc = st.sidebar.slider("Consumibles %", 1, 15, int(precios_db['p_consumibles_perc']))

if st.sidebar.button("💾 Guardar Configuración"):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"p_barra_ref": p_barra_ref, "p_m2_malla": p_m2_malla, "p_litro_pintura": p_litro_pintura, "p_consumibles_perc": p_consum_perc, "nombre_herreria": nombre_h}, f)
    st.sidebar.success("¡Configuración guardada!")

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

nivel_mo = st.sidebar.select_slider("Calidad Final", options=["Económico", "Estándar", "Premium"], value="Estándar")
perc_desp = st.sidebar.slider("% Desperdicio Mat.", 0, 20, 10) / 100

st.title(f"🛡️ {nombre_h}")
cliente = st.text_input("Nombre del Cliente", "Presupuesto Particular")

# --- VARIABLES GLOBALES ---
m_barrotes = 0; m_planchuela = 0; listado_caños = {}; m2_malla_total = 0; m_angulo_interno = 0
costo_herrajes = 0; detalles_obra = []; area_total_m2 = 0
mat_barrote_elegido = "1/2 (12.7mm)"
lista_herrajes_taller = []

# --- MÓDULOS ---

# 1. PAÑOS DE FRENTE
st.header("1. Paños de Frente")
if st.checkbox("Incluir Paños Frente", value=True):
    c1, c2 = st.columns(2)
    cant_f = c1.number_input("Cantidad", 1, 20, 2, key="nf")
    an_f = c1.number_input("Ancho (m)", 0.1, 10.0, 2.5, key="wf")
    al_f = c1.number_input("Alto (m)", 0.1, 5.0, 1.8, key="hf")
    area_total_m2 += (an_f * al_f) * cant_f
    
    relleno = c2.radio("Tipo de Relleno", ["Barrotes", "Metal Desplegado"], key="rel_f")
    
    if c2.checkbox("¿Lleva Bastidor?", value=True, key="bf"):
        m_c = c2.selectbox("Caño Bastidor", list(PESOS_C.keys()), key="cf")
        listado_caños[m_c] = listado_caños.get(m_c, 0) + (an_f + al_f) * 2 * cant_f
    
    if relleno == "Barrotes":
        mat_barrote_elegido = c2.selectbox("Hierro Barrotes", list(PESOS_H.keys()), key="hf_f")
        m_barrotes += (math.ceil(an_f / 0.12) + 1) * al_f * cant_f
        m_planchuela += an_f * c2.number_input("Filas Planchuela", 1, 6, 2, key="pf") * cant_f
    else:
        m2_malla_total += (an_f * al_f) * cant_f
        
    detalles_obra.append(f"{cant_f} Paños de {relleno} ({an_f}x{al_f}m)")

# 2. VENTANAS
st.divider()
st.header("2. Ventanas")
if st.checkbox("Incluir Ventanas"):
    c1v, c2v = st.columns(2)
    cant_v = c1v.number_input("Cantidad", 1, 20, 1, key="nv")
    an_v = c1v.number_input("Ancho", 0.1, 10.0, 1.2, key="wv")
    al_v = c1v.number_input("Alto", 0.1, 5.0, 1.1, key="hv")
    area_total_m2 += (an_v * al_v) * cant_v
    
    relleno_v = c2v.radio("Tipo de Relleno", ["Barrotes", "Metal Desplegado"], key="rel_v")
    
    if c2v.checkbox("¿Lleva Bastidor?", value=True, key="bv"):
        m_c_v = c2v.selectbox("Caño", list(PESOS_C.keys()), key="cv")
        listado_caños[m_c_v] = listado_caños.get(m_c_v, 0) + (an_v + al_v) * 2 * cant_v
    
    if relleno_v == "Barrotes":
        m_barrotes += (math.ceil(an_v / 0.12) + 1) * al_v * cant_v
        m_planchuela += an_v * c2v.number_input("Planchuelas", 1, 6, 2, key="pv") * cant_v
    else:
        m2_malla_total += (an_v * al_v) * cant_v
    detalles_obra.append(f"{cant_v} Rejas Ventana ({relleno_v})")

# 3. PUERTA PEATONAL
st.divider()
st.header("3. Puerta Peatonal")
if st.checkbox("Incluir Puerta"):
    c1p, c2p = st.columns(2)
    an_p = c1p.number_input("Ancho", 0.5, 2.0, 0.9, key="wp")
    al_p = c1p.number_input("Alto", 1.5, 3.0, 2.0, key="hp")
    area_total_m2 += (an_p * al_p)
    
    relleno_p = c2p.radio("Tipo de Relleno", ["Barrotes", "Metal Desplegado"], key="rel_p")
    
    if c2p.checkbox("¿Lleva Bastidor?", value=True, key="bp"):
        m_c_p = c2p.selectbox("Caño Puerta", list(PESOS_C.keys()), key="cp")
        listado_caños[m_c_p] = listado_caños.get(m_c_p, 0) + (an_p + al_p) * 2
        
    if relleno_p == "Barrotes":
        m_barrotes += (math.ceil(an_p / 0.12) + 1) * al_p
        m_planchuela += an_p * c2p.number_input("Planchuelas", 1, 6, 2, key="pp")
    else:
        m2_malla_total += (an_p * al_p)
        
    costo_herrajes += sum([PRECIOS_HERRAJES["Cerradura Seg."], PRECIOS_HERRAJES["Pomelas (Par)"], PRECIOS_HERRAJES["Caja Cerradura"]])
    lista_herrajes_taller.extend(["Cerradura de Seguridad", "Juego de Pomelas", "Caja para Cerradura"])
    detalles_obra.append(f"1 Puerta Peatonal de {relleno_p} ({an_p}x{al_p}m)")

# 4. PORTÓN VEHICULAR
st.divider()
st.header("4. Portón Vehicular")
if st.checkbox("Incluir Portón"):
    c1po, c2po = st.columns(2)
    an_po = c1po.number_input("Ancho Total", 2.0, 10.0, 3.0, key="wpo")
    tipo_po = c1po.radio("Tipo", ["Corredizo", "Batiente"])
    area_total_m2 += (an_po * 2.1)
    
    relleno_po = c2po.radio("Tipo de Relleno", ["Barrotes", "Metal Desplegado"], key="rel_po")
    
    if c2po.checkbox("¿Lleva Bastidor?", value=True, key="bpo"):
        m_c_po = c2po.selectbox("Caño Portón", list(PESOS_C.keys()), key="cpo")
        listado_caños[m_c_po] = listado_caños.get(m_c_po, 0) + (an_po * 2 + 8.0)
    
    if relleno_po == "Barrotes":
        m_barrotes += (math.ceil(an_po / 0.12) + 1) * 2.1
        m_planchuela += an_po * c2po.number_input("Planchuelas", 1, 6, 2, key="ppo")
    else:
        m2_malla_total += (an_po * 2.1)
        
    if tipo_po == "Corredizo":
        costo_herrajes += PRECIOS_HERRAJES["Kit Ruedas (Par)"] + PRECIOS_HERRAJES["Rodillo Guía (Set)"] + (an_po * 2 * PRECIOS_HERRAJES["Angulo Guía 1 1/4 (m)"])
        lista_herrajes_taller.extend(["Kit Ruedas Corredizo", "Rodillo Guía", f"{an_po*2:.1f}m Ángulo Guía"])
    else:
        costo_herrajes += PRECIOS_HERRAJES["Pomelas (Par)"] * 2
        lista_herrajes_taller.extend(["2 Juegos de Pomelas Reforzadas"])
    detalles_obra.append(f"1 Portón {tipo_po} de {relleno_po}")

# 5. POSTES
st.divider()
st.header("5. Postes")
if st.checkbox("Agregar Postes"):
    c1ps, c2ps = st.columns(2)
    cant_ps = c1ps.number_input("Cantidad", 1, 20, 2)
    h_ps = c1ps.number_input("Altura (m)", 0.5, 4.0, 2.2)
    m_c_ps = c2ps.selectbox("Caño Poste", list(PESOS_C.keys()), key="cps")
    listado_caños[m_c_ps] = listado_caños.get(m_c_ps, 0) + (cant_ps * h_ps)
    detalles_obra.append(f"{cant_ps} Postes de apoyo")

st.divider()
st.header("6. Servicios")
col_f, col_c = st.columns(2)
p_flete = col_f.number_input("Costo Flete $", value=20000)
b_flete = col_f.checkbox("Bonificar Flete")
p_coloc = col_c.number_input("Costo Colocación $", value=35000)
b_coloc = col_c.checkbox("Bonificar Colocación")

# --- CALCULO FINAL ---
if st.button("🚀 GENERAR PRESUPUESTO", type="primary", use_container_width=True):
    # Pintura: Estimación por superficie
    sup_pint = (sum(listado_caños.values()) * 0.15) + (m_barrotes * 0.05) + (m2_malla_total * 2)
    l_pint = math.ceil(sup_pint / 10 * 2)

    p_b = PESOS_H.get(mat_barrote_elegido, 1.21)
    c_caños = sum([m * PESOS_C[med] * p_kg for med, m in listado_caños.items()])
    
    # COSTO DE MALLA INCLUIDO AQUÍ
    c_mats_puros = c_caños + (m_barrotes * p_b * p_kg) + (m_planchuela * 0.9 * p_kg) + (m2_malla_total * p_m2_malla) + (l_pint * p_litro_pintura) + costo_herrajes
    
    c_consum = c_mats_puros * (p_consum_perc / 100)
    mats_redon = redon((c_mats_puros + c_consum) * (1 + perc_desp))

    if metodo_mo == "% de Materiales": mo_base = mats_redon * (val_mo / 100)
    elif metodo_mo == "Por Día / Jornal": mo_base = dias_trabajo * val_mo
    else: mo_base = area_total_m2 * val_mo
    mo_redon = redon(mo_base * {"Económico": 0.8, "Estándar": 1.0, "Premium": 1.4}[nivel_mo])

    v_flete = 0 if b_flete else p_flete
    v_coloc = 0 if b_coloc else p_coloc
    total_gral = mats_redon + mo_redon + v_flete + v_coloc

    st.success(f"## TOTAL FINAL: ${total_gral:,.0f}")
    txt_resumen = f"• MATERIALES: ${mats_redon:,.0f}\n• MANO DE OBRA: ${mo_redon:,.0f}\n• FLETE: {'$0 (BONIF.)' if b_flete else f'${p_flete:,.0f}'}\n• COLOCACIÓN: {'$0 (BONIF.)' if b_coloc else f'${p_coloc:,.0f}'}"
    st.info(f"**Desglose:**\n{txt_resumen}")

    pdf = PDF(logo_img=logo_file if logo_file else None)
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, f"Cliente: {cliente}", 0, 1)
    pdf.set_font("helvetica", '', 11)
    pdf.multi_cell(0, 8, f"Detalle de Obra: {', '.join(detalles_obra)}")
    pdf.ln(5)
    pdf.cell(0, 8, f"- Materiales y Consumibles: ${mats_redon:,.0f}", 0, 1)
    pdf.cell(0, 8, f"- Mano de Obra y Taller: ${mo_redon:,.0f}", 0, 1)
    pdf.cell(0, 8, f"- Flete: {'BONIFICADO' if b_flete else f'${p_flete:,.0f}'}", 0, 1)
    pdf.cell(0, 8, f"- Colocación: {'BONIFICADO' if b_coloc else f'${p_coloc:,.0f}'}", 0, 1)
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 15, f"TOTAL FINAL: ${total_gral:,.0f}", 0, 1)
    
    pdf_bytes = bytes(pdf.output())
    st.download_button("📥 DESCARGAR PDF PROFESIONAL", data=pdf_bytes, file_name=f"Presupuesto_{cliente}.pdf", mime="application/pdf")
    st.markdown(f'[📩 Enviar por WhatsApp]({gen_ws("Hola " + cliente + ", te envío el presupuesto de " + nombre_h + ". Total: $" + str(total_gral))})')

    with st.expander("🛠️ LISTA DE MATERIALES PARA TALLER"):
        st.write("### Hierros y Caños:")
        for med, met in listado_caños.items():
            st.write(f"- {med}: {math.ceil((met*1.1)/6)} barras de 6m")
        if m_barrotes > 0:
            st.write(f"- Hierro {mat_barrote_elegido} (Barrotes): {math.ceil((m_barrotes*1.1)/6)} barras")
        if m_planchuela > 0:
            st.write(f"- Planchuela 1 1/4 (Para barrotes): {math.ceil((m_planchuela*1.1)/6)} barras")
        if m2_malla_total > 0:
            st.write(f"### Metal Desplegado:")
            st.write(f"- Superficie neta: {m2_malla_total:.2f} m²")
            st.write(f"- Comprar aprox: {math.ceil(m2_malla_total/2.4)} planchas (de 3.00x0.80m)")
        
        if lista_herrajes_taller:
            st.write("### Herrajes y Accesorios:")
            for h in lista_herrajes_taller:
                st.write(f"- {h}")
        
        st.write(f"### Varios:\n- Pintura: {l_pint} Lts.\n- Consumibles (Electrodos, discos, etc.): Incluidos en costo mat.")