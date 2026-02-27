import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pandas as pd

# ─── CONFIGURACIÓN ────────────────────────────────────────────
import streamlit as st
MONGODB_URI = st.secrets["MONGODB_URI"]
DATABASE_NAME = st.secrets["DATABASE_NAME"]

# ─── CONEXIÓN MONGODB ─────────────────────────────────────────
@st.cache_resource
def init_connection():
    return MongoClient(MONGODB_URI)

client = init_connection()
db = client[DATABASE_NAME]

# ─── CARGAR DATOS ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_clientes():
    datos = list(db.vista360.find({}, {
        "cedula": 1,
        "nombre": 1,
        "ciudad": 1,
        "fuentes": 1,
        "analisis": 1,
        "perfil_completo": 1
    }))
    for d in datos:
        d["_id"] = str(d["_id"])
    return datos

# ─── CONFIGURACIÓN DE PÁGINA ──────────────────────────────────
st.set_page_config(
    page_title="VISTA 360 — Seguros Bolívar",
    page_icon="🛡️",
    layout="wide"
)

# ─── ESTILOS ──────────────────────────────────────────────────
st.markdown("""
<style>
    .header-title {
        background: linear-gradient(90deg, #00A859, #007a3d);
        padding: 20px 30px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .metric-card {
        background: #f8f9fa;
        border-left: 4px solid #00A859;
        padding: 15px;
        border-radius: 8px;
        margin: 5px 0;
    }
    .alert-alta {
        background: #fff3cd;
        border-left: 4px solid #FDB71A;
        padding: 10px 15px;
        border-radius: 6px;
        margin: 5px 0;
    }
    .fuente-badge {
        display: inline-block;
        background: #00A859;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)

# ─── HEADER ───────────────────────────────────────────────────
st.markdown("""
<div class="header-title">
    <h1 style="margin:0; font-size:28px;">🛡️ VISTA 360 — Seguros Bolívar</h1>
    <p style="margin:5px 0 0 0; opacity:0.9;">Motor de Inteligencia del Cliente · Gerencia de Arquitectura I+D+I</p>
</div>
""", unsafe_allow_html=True)

# ─── CARGAR DATOS ─────────────────────────────────────────────
clientes = cargar_clientes()

if not clientes:
    st.error("No se encontraron clientes en la colección vista360. Ejecuta primero el agente en Colab.")
    st.stop()

# ─── MÉTRICAS GENERALES ───────────────────────────────────────
st.markdown("### 📊 Resumen General")
col1, col2, col3, col4 = st.columns(4)

total = len(clientes)
multi_fuente = sum(1 for c in clientes if len(c.get("fuentes", [])) > 1)
tres_fuentes = sum(1 for c in clientes if len(c.get("fuentes", [])) == 3)
ciudades = len(set(c.get("ciudad", "") for c in clientes))

with col1:
    st.metric("👥 Clientes Analizados", total)
with col2:
    st.metric("🔗 En múltiples CRMs", multi_fuente)
with col3:
    st.metric("🎯 En los 3 CRMs", tres_fuentes)
with col4:
    st.metric("📍 Ciudades", ciudades)

st.markdown("---")

# ─── LAYOUT PRINCIPAL ─────────────────────────────────────────
col_lista, col_detalle = st.columns([1, 2])

# ─── LISTA DE CLIENTES ────────────────────────────────────────
with col_lista:
    st.markdown("### 👥 Clientes")

    busqueda = st.text_input("🔍 Buscar por nombre o cédula", placeholder="Ej: Eduardo o 12345678")

    clientes_filtrados = clientes
    if busqueda:
        busqueda_lower = busqueda.lower()
        clientes_filtrados = [
            c for c in clientes
            if busqueda_lower in c.get("nombre", "").lower()
            or busqueda_lower in c.get("cedula", "").lower()
        ]

    if not clientes_filtrados:
        st.warning("No se encontraron clientes con ese criterio.")
    else:
        for c in clientes_filtrados:
            fuentes = c.get("fuentes", [])
            num_fuentes = len(fuentes)
            emoji = "🟢" if num_fuentes == 3 else "🟡" if num_fuentes == 2 else "🔵"

            if st.button(
                f"{emoji} {c.get('nombre', 'Sin nombre')} — {c.get('ciudad', '')}",
                key=c["cedula"],
                use_container_width=True
            ):
                st.session_state["cliente_seleccionado"] = c

# ─── DETALLE DEL CLIENTE ──────────────────────────────────────
with col_detalle:
    if "cliente_seleccionado" not in st.session_state:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px; color:#888;">
            <h2>👈 Selecciona un cliente</h2>
            <p>Haz clic en cualquier cliente de la lista para ver su Vista 360 completa</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        c = st.session_state["cliente_seleccionado"]
        perfil = c.get("perfil_completo", {})
        fuentes = c.get("fuentes", [])

        # Nombre y datos básicos
        st.markdown(f"### 👤 {c.get('nombre', 'Sin nombre')}")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown(f"**📍 Ciudad:** {c.get('ciudad', 'N/A')}")
        with col_b:
            st.markdown(f"**🪪 Cédula:** {c.get('cedula', 'N/A')}")
        with col_c:
            badges = " ".join([f"`{f}`" for f in fuentes])
            st.markdown(f"**🔗 Fuentes:** {badges}")

        st.markdown("---")

        # Tabs de información
        tab1, tab2, tab3, tab4 = st.tabs([
            "🤖 Análisis IA",
            "📋 CENTRA",
            "🚗 FLOW360",
            "🎯 Gestor Leads"
        ])

        with tab1:
            st.markdown("#### 🤖 Análisis Gemini — Recomendaciones para el Asesor")
            analisis = c.get("analisis", "Sin análisis disponible")
            st.markdown(analisis)

        with tab2:
            datos_centra = perfil.get("datos_centra")
            if datos_centra:
                st.markdown("#### 📋 Datos en CENTRA")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Producto:** {datos_centra.get('producto', 'N/A')}")
                    st.markdown(f"**Estado póliza:** {datos_centra.get('estado_poliza', 'N/A')}")
                    st.markdown(f"**Prima mensual:** ${datos_centra.get('prima_mensual', 0):,.0f}")
                with col2:
                    st.markdown(f"**Asesor:** {datos_centra.get('asesor', 'N/A')}")
                    st.markdown(f"**Fecha inicio:** {datos_centra.get('fecha_inicio', 'N/A')}")
                    st.markdown(f"**Fecha vencimiento:** {datos_centra.get('fecha_vencimiento', 'N/A')}")
            else:
                st.info("Este cliente no tiene registros en CENTRA.")

        with tab3:
            datos_flow = perfil.get("datos_flow360", [])
            if datos_flow:
                st.markdown(f"#### 🚗 Pólizas en FLOW360 ({len(datos_flow)} registros)")
                for i, poliza in enumerate(datos_flow):
                    with st.expander(f"Póliza {i+1}: {poliza.get('ramo', 'N/A')} — {poliza.get('numero_poliza', 'N/A')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Estado:** {poliza.get('estado', 'N/A')}")
                            st.markdown(f"**Valor asegurado:** ${poliza.get('valor_asegurado', 0):,.0f}")
                            st.markdown(f"**Ejecutivo:** {poliza.get('ejecutivo', 'N/A')}")
                        with col2:
                            st.markdown(f"**Expedición:** {poliza.get('fecha_expedicion', 'N/A')}")
                            st.markdown(f"**Renovación:** {poliza.get('fecha_renovacion', 'N/A')}")
                            st.markdown(f"**Último contacto:** {poliza.get('ultimo_contacto', 'N/A')}")
            else:
                st.info("Este cliente no tiene registros en FLOW360.")

        with tab4:
            datos_leads = perfil.get("datos_leads", [])
            if datos_leads:
                st.markdown(f"#### 🎯 Leads en Gestor ({len(datos_leads)} registros)")
                for i, lead in enumerate(datos_leads):
                    prob = lead.get("probabilidad_cierre", 0)
                    color = "🟢" if prob >= 70 else "🟡" if prob >= 40 else "🔴"
                    with st.expander(f"Lead {i+1}: {lead.get('producto_interes', 'N/A')} — {color} {prob}% probabilidad"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Estado:** {lead.get('estado_lead', 'N/A')}")
                            st.markdown(f"**Valor estimado:** ${lead.get('valor_estimado', 0):,.0f}")
                            st.markdown(f"**Asesor:** {lead.get('asesor_asignado', 'N/A')}")
                        with col2:
                            st.markdown(f"**Creación:** {lead.get('fecha_creacion', 'N/A')}")
                            st.markdown(f"**Último seguimiento:** {lead.get('fecha_ultimo_seguimiento', 'N/A')}")
                        st.markdown(f"**Observaciones:** {lead.get('observaciones', 'N/A')}")
            else:

                st.info("Este cliente no tiene leads en Gestor de Leads.")
