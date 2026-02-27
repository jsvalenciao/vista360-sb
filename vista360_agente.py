import google.generativeai as genai
from pymongo import MongoClient
from datetime import datetime
import json

# ─── CONFIGURACIÓN ────────────────────────────────────────────
import os
MONGODB_URI = os.environ.get("MONGODB_URI", "")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "vista360")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

genai.configure(api_key=GEMINI_API_KEY)
modelo = genai.GenerativeModel("gemini-2.0-flash")
client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]

# ─── CONSOLIDAR PERFIL DEL CLIENTE ────────────────────────────
def consolidar_perfil(cedula):
    perfil = {
        "cedula": cedula,
        "fuentes_encontradas": [],
        "datos_centra": None,
        "datos_flow360": [],
        "datos_leads": []
    }

    # Buscar en CENTRA
    centra = db.centra.find_one({"cedula_cliente": cedula})
    if centra:
        centra["_id"] = str(centra["_id"])
        for k, v in centra.items():
            if isinstance(v, datetime):
                centra[k] = v.strftime("%Y-%m-%d")
        perfil["datos_centra"] = centra
        perfil["fuentes_encontradas"].append("CENTRA")
        perfil["nombre"] = centra.get("nombre_cliente")
        perfil["email"] = centra.get("email")
        perfil["ciudad"] = centra.get("ciudad")

    # Buscar en FLOW360
    flow_registros = list(db.flow360.find({"identificacion": cedula}))
    for r in flow_registros:
        r["_id"] = str(r["_id"])
        for k, v in r.items():
            if isinstance(v, datetime):
                r[k] = v.strftime("%Y-%m-%d")
    if flow_registros:
        perfil["datos_flow360"] = flow_registros
        perfil["fuentes_encontradas"].append("FLOW360")
        if not perfil.get("nombre"):
            perfil["nombre"] = flow_registros[0].get("nombre_completo")

    # Buscar en GESTOR LEADS
    leads = list(db.gestor_leads.find({"documento": cedula}))
    for r in leads:
        r["_id"] = str(r["_id"])
        for k, v in r.items():
            if isinstance(v, datetime):
                r[k] = v.strftime("%Y-%m-%d")
    if leads:
        perfil["datos_leads"] = leads
        perfil["fuentes_encontradas"].append("GESTOR_LEADS")
        if not perfil.get("nombre"):
            perfil["nombre"] = leads[0].get("nombre")

    return perfil

# ─── GENERAR ANÁLISIS CON GEMINI ──────────────────────────────
def analizar_cliente(perfil):
    if not perfil["fuentes_encontradas"]:
        return "No se encontró información de este cliente en ningún CRM."

    prompt = f"""
Eres un analista experto de clientes de Seguros Bolívar, la aseguradora más grande de Colombia.
Tu tarea es analizar el perfil consolidado de un cliente que viene de múltiples sistemas CRM
y generar recomendaciones accionables para el asesor comercial.

PERFIL CONSOLIDADO DEL CLIENTE:
{json.dumps(perfil, ensure_ascii=False, indent=2)}

Por favor genera un análisis estructurado con las siguientes secciones:

1. RESUMEN DEL CLIENTE
   - Nombre, ciudad, fuentes donde aparece
   - Productos actuales y su estado

2. ALERTAS PRIORITARIAS
   - Pólizas próximas a vencer
   - Pólizas canceladas o suspendidas
   - Leads sin gestión reciente

3. OPORTUNIDADES COMERCIALES
   - Productos que podría necesitar según su perfil
   - Momento óptimo para contactar
   - Probabilidad estimada de cierre

4. RECOMENDACIÓN PARA EL ASESOR
   - Acción concreta que debe tomar hoy
   - Mensaje sugerido para contactar al cliente
   - Prioridad: ALTA / MEDIA / BAJA

Responde en español, de forma clara y directa. Usa el contexto de seguros colombianos.
"""

    respuesta = modelo.generate_content(prompt)
    return respuesta.text

# ─── OBTENER TODOS LOS CLIENTES ───────────────────────────────
def obtener_todas_cedulas():
    cedulas = set()
    for doc in db.centra.find({}, {"cedula_cliente": 1}):
        cedulas.add(doc["cedula_cliente"])
    for doc in db.flow360.find({}, {"identificacion": 1}):
        cedulas.add(doc["identificacion"])
    for doc in db.gestor_leads.find({}, {"documento": 1}):
        cedulas.add(doc["documento"])
    return list(cedulas)

# ─── GENERAR VISTA 360 COMPLETA ───────────────────────────────
def generar_vista360_todos():
    cedulas = obtener_todas_cedulas()
    resultados = []
    print(f"🔍 Procesando {len(cedulas)} clientes únicos...")

    for i, cedula in enumerate(cedulas[:10]):  # Primero 10 para prueba
        perfil = consolidar_perfil(cedula)
        if perfil["fuentes_encontradas"]:
            analisis = analizar_cliente(perfil)
            resultados.append({
                "cedula": cedula,
                "nombre": perfil.get("nombre", "Sin nombre"),
                "ciudad": perfil.get("ciudad", "Sin ciudad"),
                "fuentes": perfil["fuentes_encontradas"],
                "analisis": analisis,
                "perfil_completo": perfil
            })
            print(f"✅ {i+1}. {perfil.get('nombre', cedula)} procesado")

    # Guardar en MongoDB
    db.vista360.drop()
    if resultados:
        db.vista360.insert_many(resultados)
    print(f"\n✅ Vista 360 generada para {len(resultados)} clientes")
    print("   Colección creada: vista360")
    return resultados

# ─── EJECUTAR ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Iniciando Motor de Inteligencia VISTA 360...")
    resultados = generar_vista360_todos()
    if resultados:
        print("\n📋 EJEMPLO — Primer cliente analizado:")
        print("─" * 50)
        print(f"Cliente: {resultados[0]['nombre']}")
        print(f"Fuentes: {', '.join(resultados[0]['fuentes'])}")

        print(f"\nAnálisis:\n{resultados[0]['analisis']}")
