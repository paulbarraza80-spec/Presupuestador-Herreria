import streamlit as st
import math
import urllib.parse

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Rejas Pro v3.2.1", page_icon="⚒️")

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
    "Kit Ruedas (Par)": 22000, "Rodillo Guía (Set)": 15000, "Cremallera (m)": 12000,
    "Angulo Guía 1 1/4 (m)": 5800, "Cerradura Portón": 28000
}

def redon(n): return math.ceil(n / 1000) * 1000
def gen_ws(txt): return f"https://wa.me/?text={urllib.parse.quote(txt)}"

# --- BARRA LATERAL (CONFIGURACIÓN) ---
st.sidebar.header("⚙️ Costos Base")
p_barra_ref = st.sidebar.number_input("Precio Barra 40x40 (6m)", value=35000)
p_kg = p_barra_ref / (1.91 * 6)
p_m2_malla = st.sidebar.number_input("Precio m2 Malla", value=14000)
p_litro_pintura = st.sidebar.number_input("Precio Litro Pintura", value=15000)
p_consumibles_perc = st.sidebar.slider("Consumibles (% sobre material)", 1, 15, 5) / 100

st.sidebar.divider()
st.sidebar.header("👷 Mano de Obra")
metodo_mo = st.sidebar.selectbox("Método de Cálculo", ["% de Materiales", "Por Día / Jornal", "Por Metro Cuadrado"])

dias_trabajo = 1
if metodo_mo == "% de Materiales": 
    val_mo = st.sidebar.number_input("% sobre materiales", 50, 250, 100)
elif metodo_mo == "Por Día / Jornal": 
    val_mo = st.sidebar.number_input("Precio por Día $", 15000, 150000, 40000)
    dias_trabajo = st.sidebar.number_input("Cantidad de Días de obra", 1, 60, 3)
else: 
    val_mo = st.sidebar.number_input("Precio por m2 $", 10000, 120000, 30000)

nivel_mo = st.sidebar.select_slider("Calidad de Terminación", options=["Económico", "Estándar", "Premium"], value="Estándar")
dict_calidad = {"Económico": 0.8, "Estándar": 1.0, "Premium": 1.4}
perc_desp = st.sidebar.slider("% Desperdicio Material", 0, 20, 10) / 100

st.title("🛡️ Calculador Rejas v3.2.1")

# --- VARIABLES DE CÁLCULO ---
m_barrotes = 0; m_planchuela = 0; listado_caños = {}; m2_malla_total = 0; m_angulo_interno = 0
costo_herrajes = 0; detalles_obra = []; m_angulo_guia_porton = 0
area_total_m2 = 0; mat_barrote_elegido = "1/2 (12.7mm)"

# --- SECCIONES DE LA APP ---

# 1. PAÑOS FRENTE
st.header("1. Paños Fijos")
if st.checkbox("Incluir Paños de Frente", value=True, key="chk_f"):
    c1, c2 = st.columns(2)
    with c1:
        cant_f = st.number_input("Cantidad Paños", 1, 20, 2, key="n_f")
        ancho_f = st.number_input("Ancho (m)", 0.1, 10.0, 2.5, key="w_f")
        alto_f = st.number_input("Alto (m)", 0.1, 5.0, 1.8, key="h_f")
        area_total_m2 += (ancho_f * alto_f) * cant_f
    with c2:
        estilo_f = st.selectbox("Estilo", ["Barrotes", "Malla/Desplegado"], key="st_f")
        if st.checkbox("¿Lleva Bastidor?", value=True, key="bas_f"):
            m_c_f = st.selectbox("Caño Bastidor", list(PESOS_C.keys()), key="pipe_f")
            listado_caños[m_c_f] = listado_caños.get(m_c_f, 0) + (ancho_f + alto_f) * 2 * cant_f
        if estilo_f == "Barrotes":
            mat_barrote_elegido = st.selectbox("Hierro", list(PESOS_H.keys()), key="mat_f")
            m_barrotes += (math.ceil(ancho_f / 0.12) + 1) * alto_f * cant_f
            m_planchuela += ancho_f * st.number_input("Filas Planchuela", 2, 6, 2, key="pl_f") * cant_f
        else:
            m2_malla_total += (ancho_f * alto_f) * cant_f
            m_angulo_interno += (ancho_f + alto_f) * 2 * cant_f
    detalles_obra.append(f"{cant_f} Paños Frente")

# 2. OTROS PAÑOS
st.divider()
st.header("2. Ventanas / Otros")
if st.checkbox("Incluir Otros Paños", key="chk_v"):
    c1v, c2v = st.columns(2)
    with c1v:
        cant_v = st.number_input("Cantidad", 1, 20, 1, key="n_v")
        ancho_v = st.number_input("Ancho", 0.1, 10.0, 1.2, key="w_v")
        alto_v = st.number_input("Alto", 0.1, 5.0, 1.1, key="h_v")
        area_total_m2 += (ancho_v * alto_v) * cant_v
    with c2v:
        estilo_v = st.selectbox("Estilo", ["Barrotes", "Malla/Desplegado"], key="st_v")
        if st.checkbox("¿Lleva Bastidor?", value=True, key="bas_v"):
            m_c_v = st.selectbox("Caño", list(PESOS_C.keys()), key="pipe_v")
            listado_caños[m_c_v] = listado_caños.get(m_c_v, 0) + (ancho_v + alto_v) * 2 * cant_v
        if estilo_v == "Barrotes":
            m_barrotes += (math.ceil(ancho_v / 0.12) + 1) * alto_v * cant_v
            m_planchuela += ancho_v * st.number_input("Filas Planchuela", 2, 6, 2, key="pl_v_v") * cant_v
        else:
            m2_malla_total += (ancho_v * alto_v) * cant_v
            m_angulo_interno += (ancho_v + alto_v) * 2 * cant_v
    detalles_obra.append(f"{cant_v} Paños Ventana")

# 3. PUERTA
st.divider()
st.header("3. Puerta Peatonal")
if st.checkbox("Incluir Puerta", key="chk_p"):
    c1p, c2p = st.columns(2)
    with c1p:
        an_p = st.number_input("Ancho", 0.5, 2.0, 0.9, key="w_p")
        al_p = st.number_input("Alto", 1.5, 3.0, 2.0, key="h_p")
        area_total_m2 += (an_p * al_p)
    with c2p:
        est_p = st.selectbox("Estilo", ["Barrotes", "Malla/Desplegado"], key="st_p")
        if st.checkbox("¿Lleva Bastidor?", value=True, key="bas_p"):
            m_c_p = st.selectbox("Caño Puerta", list(PESOS_C.keys()), key="pipe_p")
            listado_caños[m_c_p] = listado_caños.get(m_c_p, 0) + (an_p + al_p) * 2
        if est_p == "Barrotes":
            m_barrotes += (math.ceil(an_p / 0.12) + 1) * al_p
            m_planchuela += an_p * st.number_input("Filas Planchuela", 2, 6, 2, key="pl_p_p")
        else:
            m2_malla_total += (an_p * al_p)
            m_angulo_interno += (an_p + al_p) * 2
        costo_herrajes += PRECIOS_HERRAJES["Cerradura Seg."] + PRECIOS_HERRAJES["Pomelas (Par)"] + PRECIOS_HERRAJES["Caja Cerradura"]
    detalles_obra.append("1 Puerta")

# 4. PORTÓN
st.divider()
st.header("4. Portón Vehicular")
if st.checkbox("Incluir Portón", key="chk_port"):
    c1port, c2port = st.columns(2)
    with c1port:
        an_port = st.number_input("Ancho Portón", 2.0, 10.0, 3.0, key="w_port")
        tipo_v = st.radio("Movimiento", ["Corredizo", "Batiente (2 hojas)"], key="tp_v")
        area_total_m2 += (an_port * 2.1)
    with c2port:
        est_v = st.selectbox("Estilo", ["Barrotes", "Malla/Desplegado"], key="st_port")
        if st.checkbox("¿Lleva Bastidor?", value=True, key="bas_port"):
            m_c_v = st.selectbox("Caño Portón", list(PESOS_C.keys()), key="pi_v")
            listado_caños[m_c_v] = listado_caños.get(m_c_v, 0) + (an_port * 2 + 6.0 if tipo_v == "Corredizo" else an_port * 2 + 8.0)
        if est_v == "Barrotes":
            m_barrotes += (math.ceil(an_port / 0.12) + 1) * 2.1
            m_planchuela += an_port * st.number_input("Filas Planchuela", 2, 6, 2, key="pl_port")
        else:
            m2_malla_total += (an_port * 2.1)
            m_angulo_interno += (an_port + 2.1) * 2
        if tipo_v == "Corredizo":
            m_angulo_guia_porton = an_port * 2
            costo_herrajes += PRECIOS_HERRAJES["Kit Ruedas (Par)"] + PRECIOS_HERRAJES["Rodillo Guía (Set)"] + (m_angulo_guia_porton * PRECIOS_HERRAJES["Angulo Guía 1 1/4 (m)"])
    detalles_obra.append(f"1 Portón {tipo_v}")

# 5. POSTES
st.divider()
st.header("5. Postes / Columnas")
if st.checkbox("¿Lleva Postes Adicionales?", key="chk_postes"):
    c1pos, c2pos = st.columns(2)
    with c1pos:
        cant_postes = st.number_input("Cantidad de Postes", 1, 20, 2)
        h_poste = st.number_input("Altura Poste (m)", 0.5, 4.0, 2.2)
    with c2pos:
        m_c_poste = st.selectbox("Material Poste", list(PESOS_C.keys()), key="pipe_poste")
        listado_caños[m_c_poste] = listado_caños.get(m_c_poste, 0) + (cant_postes * h_poste)
    detalles_obra.append(f"{cant_postes} Postes")

# 6. SERVICIOS
st.divider()
st.header("6. Flete y Colocación")
col_f, col_c = st.columns(2)
with col_f:
    p_flete = st.number_input("Costo Flete $", 0, 200000, 15000)
    bonif_flete = st.checkbox("Bonificar Flete")
with col_c:
    p_coloc = st.number_input("Costo Colocación $", 0, 500000, 30000)
    bonif_coloc = st.checkbox("Bonificar Colocación")

# --- CÁLCULO FINAL Y SALIDA ---
st.divider()
if st.button("🚀 GENERAR PRESUPUESTO", type="primary", use_container_width=True):
    # Pintura
    sup_pint = (sum(listado_caños.values()) * 0.15) + (m_barrotes * 0.05) + (m2_malla_total * 2)
    l_pint = math.ceil(sup_pint / 10 * 2)
    
    # Materiales
    p_b = PESOS_H.get(mat_barrote_elegido, 1.21)
    c_caños = sum([m * PESOS_C[med] * p_kg for med, m in listado_caños.items()])
    c_mats_puros = c_caños + (m_angulo_interno + m_angulo_guia_porton) * PESO_ANGULO_MARCO * p_kg + (m_barrotes * p_b * p_kg) + (m_planchuela * 0.9 * p_kg) + (m2_malla_total * p_m2_malla) + costo_herrajes + (l_pint * p_litro_pintura)
    c_consumibles = c_mats_puros * p_consumibles_perc
    
    # Monto Materiales Discriminado
    mats_redon = redon((c_mats_puros + c_consumibles) * (1 + perc_desp))

    # Mano de Obra
    if metodo_mo == "% de Materiales": mo_base = (c_mats_puros + c_consumibles) * (val_mo / 100)
    elif metodo_mo == "Por Día / Jornal": mo_base = dias_trabajo * val_mo
    else: mo_base = area_total_m2 * val_mo
    
    # Monto Mano de Obra Discriminado
    mo_redon = redon(mo_base * dict_calidad[nivel_mo])

    # Servicios y Total
    v_flete = 0 if bonif_flete else p_flete
    v_coloc = 0 if bonif_coloc else p_coloc
    total_gral = mats_redon + mo_redon + v_flete + v_coloc

    # --- TEXTO FINAL PARA CLIENTE ---
    txt_cli = f"PRESUPUESTO DE HERRERÍA\n"
    txt_cli += f"{'='*30}\n"
    txt_cli += f"Trabajo: {', '.join(detalles_obra)}\n"
    txt_cli += f"Nivel de terminación: {nivel_mo}\n\n"
    txt_cli += f"DETALLE DE COSTOS:\n"
    txt_cli += f"• MATERIALES Y CONSUMIBLES: ${mats_redon:,.0f}\n"
    txt_cli += f"• MANO DE OBRA Y TALLER: ${mo_redon:,.0f}\n"
    txt_cli += f"• FLETE: {'$0 (BONIFICADO)' if bonif_flete else f'${p_flete:,.0f}'}\n"
    txt_cli += f"• COLOCACIÓN: {'$0 (BONIFICADO)' if bonif_coloc else f'${p_coloc:,.0f}'}\n"
    txt_cli += f"{'-'*30}\n"
    txt_cli += f"TOTAL FINAL: ${total_gral:,.0f}"

    st.success(f"## TOTAL: ${total_gral:,.0f}")
    st.info(txt_cli)

    # --- LISTA TALLER ---
    txt_tal = f"LISTA DE TALLER\n{'='*30}\n"
    for med, met in listado_caños.items(): txt_tal += f"- {med}: {math.ceil((met*1.1)/6)} barras\n"
    if m_barrotes > 0: txt_tal += f"- Barrotes {mat_barrote_elegido}: {math.ceil((m_barrotes*1.1)/6)} barras\n"
    if m_planchuela > 0: txt_tal += f"- Planchuela: {math.ceil((m_planchuela*1.1)/6)} barras\n"
    if m2_malla_total > 0: txt_tal += f"- Malla: {m2_malla_total:.2f} m2\n"
    txt_tal += f"- Pintura: {l_pint} Lts."

    with st.expander("🛠️ Ver detalle de materiales para compra"):
        st.text(txt_tal)
    
    st.markdown(f'[📩 Enviar por WhatsApp]({gen_ws(txt_cli)})')