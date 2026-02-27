import streamlit as st
import math
import urllib.parse

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Rejas Pro v3.0", page_icon="⚒️")

# --- BASE DE DATOS TÉCNICA ARGENTINA ---
PESOS_H = {"1/2 (12.7mm)": 0.99, "9/16 (14mm)": 1.21, "5/8 (15.8mm)": 1.55}
PESOS_C = {
    "Caño 30x30x1.6": 1.41, "Caño 40x30x1.6": 1.66, "Caño 40x40x1.6": 1.91,
    "Caño 60x30x1.6": 2.16, "Caño 60x40x1.6": 2.41,
    "Caño 60x60x2.0": 3.70, "Caño 80x80x2.0": 4.90, "Caño 100x100x2.0": 6.10
}
PESO_ANGULO_MARCO = 1.10 # Peso aprox metro lineal Angulo 3/4 x 1/8

PRECIOS_HERRAJES = {
    "Cerradura Seg.": 35000, "Pomelas (Par)": 12000, "Caja Cerradura": 8500,
    "Kit Ruedas (Par)": 22000, "Rodillo Guía (Set)": 15000, "Cremallera (m)": 12000,
    "Angulo Guía 1 1/4 x 3/16 (m)": 5800, "Cerradura Portón": 28000
}

def redon(n): return math.ceil(n / 1000) * 1000
def gen_ws(txt): return f"https://wa.me/?text={urllib.parse.quote(txt)}"

# --- SIDEBAR ---
st.sidebar.header("⚙️ Costos y Materiales")
p_barra_ref = st.sidebar.number_input("Precio Barra 40x40 (6m)", value=32000)
p_kg = p_barra_ref / (1.91 * 6)
p_m2_malla = st.sidebar.number_input("Precio m2 Metal Desplegado", value=13500)
p_litro_pintura = st.sidebar.number_input("Precio Litro Pintura", value=14500)
perc_desp = st.sidebar.slider("% Desperdicio Mat.", 0, 20, 10) / 100
nivel_mo = st.sidebar.select_slider("Calidad Terminación", options=["Económico", "Estándar", "Premium"], value="Estándar")
dict_mo = {"Económico": 0.8, "Estándar": 1.0, "Premium": 1.4}

st.title("🛡️ Calculador Integral de Rejas v3.0")

# --- VARIABLES GLOBALES ---
m_barrotes = 0; m_planchuela = 0; listado_caños = {}; m2_malla_total = 0; m_angulo_interno = 0
costo_herrajes = 0; detalles_obra = []; lista_herrajes_txt = []; m_angulo_guia_porton = 0
mat_barrote_elegido = "1/2 (12.7mm)"

# --- 1. PAÑOS FRENTE ---
st.header("1. Paños Fijos del Frente")
if st.checkbox("Incluir Paños de Frente", value=True, key="chk_f"):
    c1, c2 = st.columns(2)
    with c1:
        cant_f = st.number_input("Cantidad Paños", 1, 20, 2, key="n_f")
        ancho_f = st.number_input("Ancho (m)", 0.1, 10.0, 2.5, key="w_f")
        alto_f = st.number_input("Alto (m)", 0.1, 5.0, 1.8, key="h_f")
    with c2:
        estilo_f = st.selectbox("Estilo", ["Barrotes", "Malla/Desplegado"], key="st_f")
        m_c_f = st.selectbox("Caño Bastidor", list(PESOS_C.keys()), key="pipe_f")
        listado_caños[m_c_f] = listado_caños.get(m_c_f, 0) + (ancho_f + alto_f) * 2 * cant_f
        
        if estilo_f == "Barrotes":
            mat_barrote_elegido = st.selectbox("Hierro", list(PESOS_H.keys()), key="mat_f")
            filas_f = st.number_input("Filas de Planchuela", 2, 6, 2, key="pl_f")
            m_barrotes += (math.ceil(ancho_f / 0.12) + 1) * alto_f * cant_f
            m_planchuela += ancho_f * filas_f * cant_f
        else:
            m2_malla_total += (ancho_f * alto_f) * cant_f
            m_angulo_interno += (ancho_f + alto_f) * 2 * cant_f
    detalles_obra.append(f"{cant_f} Paños Frente")

# --- 2. PAÑOS ADICIONALES ---
st.divider()
st.header("2. Paños Adicionales (Ventanas)")
if st.checkbox("Incluir Otros Paños", key="chk_v"):
    c1v, c2v = st.columns(2)
    with c1v:
        cant_v = st.number_input("Cantidad", 1, 20, 1, key="n_v")
        ancho_v = st.number_input("Ancho", 0.1, 10.0, 1.2, key="w_v")
        alto_v = st.number_input("Alto", 0.1, 5.0, 1.1, key="h_v")
    with c2v:
        estilo_v = st.selectbox("Estilo Otros", ["Barrotes", "Malla/Desplegado"], key="st_v")
        m_c_v = st.selectbox("Caño Otros", list(PESOS_C.keys()), key="pipe_v")
        listado_caños[m_c_v] = listado_caños.get(m_c_v, 0) + (ancho_v + alto_v) * 2 * cant_v
        
        if estilo_v == "Barrotes":
            filas_v = st.number_input("Filas de Planchuela", 2, 6, 2, key="pl_v")
            m_barrotes += (math.ceil(ancho_v / 0.12) + 1) * alto_v * cant_v
            m_planchuela += ancho_v * filas_v * cant_v
        else:
            m2_malla_total += (ancho_v * alto_v) * cant_v
            m_angulo_interno += (ancho_v + alto_v) * 2 * cant_v
    detalles_obra.append(f"{cant_v} Rejas Ventana")

# --- 3. PUERTA ---
st.divider()
st.header("3. Puerta Peatonal")
if st.checkbox("Incluir Puerta", key="chk_p"):
    c1p, c2p = st.columns(2)
    with c1p:
        ancho_p = st.number_input("Ancho Puerta", 0.5, 2.0, 0.9, key="w_p")
        alto_p = st.number_input("Alto Puerta", 1.5, 3.0, 2.0, key="h_p")
        m_c_p = st.selectbox("Caño Puerta", list(PESOS_C.keys()), key="pipe_p")
    with c2p:
        estilo_p = st.selectbox("Estilo Puerta", ["Barrotes", "Malla/Desplegado"], key="st_p")
        listado_caños[m_c_p] = listado_caños.get(m_c_p, 0) + (ancho_p + alto_p) * 2
        
        if estilo_p == "Barrotes":
            filas_p_p = st.number_input("Filas de Planchuela", 2, 6, 2, key="pl_p")
            m_barrotes += (math.ceil(ancho_p / 0.12) + 1) * alto_p
            m_planchuela += ancho_p * filas_p_p
        else:
            m2_malla_total += (ancho_p * alto_p)
            m_angulo_interno += (ancho_p + alto_p) * 2
            
        costo_herrajes += PRECIOS_HERRAJES["Cerradura Seg."] + PRECIOS_HERRAJES["Pomelas (Par)"] + PRECIOS_HERRAJES["Caja Cerradura"]
        lista_herrajes_txt.extend(["1 Cerradura Seguridad", "1 Par Pomelas 3 alas", "1 Caja Cerradura"])
    detalles_obra.append("1 Puerta Peatonal")

# --- 4. PORTÓN ---
st.divider()
st.header("4. Portón Vehicular")
if st.checkbox("Incluir Portón", key="chk_port"):
    c1port, c2port = st.columns(2)
    with c1port:
        ancho_port = st.number_input("Ancho Portón", 2.0, 10.0, 3.0, key="w_port")
        tipo_v = st.radio("Movimiento", ["Corredizo", "Batiente (2 hojas)"], key="tp_v")
        m_c_v = st.selectbox("Caño Portón", list(PESOS_C.keys()), key="pi_v")
    with c2port:
        estilo_v = st.selectbox("Estilo Portón", ["Barrotes", "Malla/Desplegado"], key="st_port")
        listado_caños[m_c_v] = listado_caños.get(m_c_v, 0) + (ancho_port * 2 + 6.0 if tipo_v == "Corredizo" else ancho_port * 2 + 8.0)
        
        if estilo_v == "Barrotes":
            filas_port = st.number_input("Filas de Planchuela", 2, 6, 2, key="pl_port")
            m_barrotes += (math.ceil(ancho_port / 0.12) + 1) * 2.0
            m_planchuela += ancho_port * filas_port
        else:
            m2_malla_total += (ancho_port * 2.0)
            m_angulo_interno += (ancho_port + 2.0) * 2 # Perímetro aproximado
        
        auto = st.checkbox("¿Automatizar?", key="auto_port")
        if tipo_v == "Corredizo":
            m_angulo_guia_porton = ancho_port * 2
            costo_herrajes += PRECIOS_HERRAJES["Kit Ruedas (Par)"] + PRECIOS_HERRAJES["Rodillo Guía (Set)"] + (m_angulo_guia_porton * PRECIOS_HERRAJES["Angulo Guía 1 1/4 x 3/16 (m)"])
            lista_herrajes_txt.extend(["1 Kit Ruedas", "1 Set Rodillos Guía", f"{m_angulo_guia_porton:.2f}m Angulo Guía 1 1/4x3/16"])
            if auto: 
                costo_herrajes += (ancho_port * PRECIOS_HERRAJES["Cremallera (m)"])
                lista_herrajes_txt.append(f"{math.ceil(ancho_port)}m Cremalleras")
        else:
            costo_herrajes += (PRECIOS_HERRAJES["Pomelas (Par)"] * 2) + PRECIOS_HERRAJES["Cerradura Portón"]
            lista_herrajes_txt.extend(["2 Pares Pomelas", "1 Cerradura Portón"])
    detalles_obra.append(f"1 Portón {tipo_v}")

# --- CÁLCULO FINAL ---
st.divider()
if "presupuesto_listo" not in st.session_state: st.session_state.presupuesto_listo = False

if st.button("🚀 GENERAR PRESUPUESTO COMPLETO", type="primary", use_container_width=True):
    st.session_state.presupuesto_listo = True

if st.session_state.presupuesto_listo:
    # Cálculo Pintura
    sup_caños = sum([m * 0.15 for m in listado_caños.values()])
    sup_barrotes = m_barrotes * 0.05
    sup_angulos = (m_angulo_interno + m_angulo_guia_porton) * 0.10
    superficie_total = sup_caños + sup_barrotes + sup_angulos + (m2_malla_total * 2)
    litros_pintura = math.ceil(superficie_total / 10 * 2)

    # Costos Materiales
    p_b = PESOS_H.get(mat_barrote_elegido, 1.21)
    costo_caños = sum([m * PESOS_C[med] * p_kg for med, m in listado_caños.items()])
    costo_angulos = (m_angulo_interno + m_angulo_guia_porton) * PESO_ANGULO_MARCO * p_kg
    costo_mats = costo_caños + costo_angulos + (m_barrotes * p_b * p_kg) + (m_planchuela * 0.9 * p_kg) + (m2_malla_total * p_m2_malla) + costo_herrajes + (litros_pintura * p_litro_pintura)
    
    mo = ((m_barrotes * 5000) + (sum(listado_caños.values()) * 4000) + (m2_malla_total * 3000)) * dict_mo[nivel_mo]
    total = redon((costo_mats * (1 + perc_desp)) + mo)

    st.success(f"## TOTAL ESTIMADO: ${total:,.0f}")
    
    txt_f = f"LISTA DE COMPRA - {nivel_mo}\n" + "="*35 + "\n"
    for med, met in listado_caños.items():
        txt_f += f"- {med}: {math.ceil((met*1.1)/6)} barras de 6m\n"
    if m_barrotes > 0: txt_f += f"- Hierro Barrotes ({mat_barrote_elegido}): {math.ceil((m_barrotes*1.1)/6)} barras\n"
    if m_planchuela > 0: txt_f += f"- Planchuela Perforada: {math.ceil((m_planchuela*1.1)/6)} barras\n"
    if m_angulo_interno > 0: txt_f += f"- Angulo 3/4 x 1/8 (Contramarco Malla): {math.ceil((m_angulo_interno*1.1)/6)} barras\n"
    if m_angulo_guia_porton > 0: txt_f += f"- Angulo 1 1/4 x 3/16 (Guía Portón): {math.ceil((m_angulo_guia_porton*1.1)/6)} barras\n"
    if m2_malla_total > 0: txt_f += f"- Metal Desplegado: {m2_malla_total:.2f} m2\n"
    txt_f += f"- Pintura: {litros_pintura} Litros\n"
    
    if lista_herrajes_txt:
        txt_f += "\nHERRAJES:\n" + "\n".join([f" * {h}" for h in lista_herrajes_txt])

    st.text_area("📋 Detalle de Materiales:", txt_f, height=350)
    st.download_button("📥 Descargar Lista .txt", txt_f, file_name="pedido_final.txt")