from faker import Faker
from pymongo import MongoClient
from datetime import datetime, timedelta
import random
import os
from dotenv import load_dotenv

load_dotenv()
fake = Faker('es_CO')

client = MongoClient(os.getenv("MONGODB_URI"))
db = client[os.getenv("DATABASE_NAME")]

# ─── DATOS BASE ───────────────────────────────────────────────
PRODUCTOS_CENTRA = ["Vida Individual", "Vida Grupo", "Accidentes Personales", "Salud"]
PRODUCTOS_FLOW360 = ["SOAT", "Hogar", "Pyme", "Autos"]
ESTADOS_LEAD = ["Nuevo", "En gestión", "Cotizado", "Cerrado ganado", "Cerrado perdido"]
ASESORES = ["Carlos Martínez", "Laura Gómez", "Andrés Pérez", "María López", "Felipe Torres"]
CIUDADES = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga"]

def generar_cedula():
    return str(random.randint(10000000, 1099999999))

def generar_fecha_pasada(dias=365):
    return datetime.now() - timedelta(days=random.randint(1, dias))

def generar_fecha_futura(dias=365):
    return datetime.now() + timedelta(days=random.randint(30, dias))

# ─── CLIENTES BASE (pool compartido) ──────────────────────────
def generar_clientes_base(n=50):
    clientes = []
    for _ in range(n):
        clientes.append({
            "cedula": generar_cedula(),
            "nombre": fake.name(),
            "email": fake.email(),
            "telefono": fake.phone_number(),
            "ciudad": random.choice(CIUDADES)
        })
    return clientes

# ─── CENTRA ───────────────────────────────────────────────────
def generar_centra(clientes):
    db.centra.drop()
    registros = []
    for c in clientes:
        if random.random() > 0.3:
            registros.append({
                "fuente": "CENTRA",
                "cedula_cliente": c["cedula"],
                "nombre_cliente": c["nombre"],
                "email": c["email"],
                "telefono": c["telefono"],
                "ciudad": c["ciudad"],
                "producto": random.choice(PRODUCTOS_CENTRA),
                "estado_poliza": random.choice(["Activa", "Vencida", "Suspendida"]),
                "fecha_inicio": generar_fecha_pasada(730),
                "fecha_vencimiento": generar_fecha_futura(365),
                "prima_mensual": round(random.uniform(50000, 500000), 0),
                "asesor": random.choice(ASESORES),
                "ultima_gestion": generar_fecha_pasada(90),
                "created_at": datetime.now()
            })
    db.centra.insert_many(registros)
    print(f"✅ CENTRA: {len(registros)} registros insertados")

# ─── FLOW 360 ─────────────────────────────────────────────────
def generar_flow360(clientes):
    db.flow360.drop()
    registros = []
    for c in clientes:
        if random.random() > 0.4:
            num_polizas = random.randint(1, 3)
            for _ in range(num_polizas):
                registros.append({
                    "fuente": "FLOW360",
                    "identificacion": c["cedula"],
                    "nombre_completo": c["nombre"],
                    "correo": c["email"],
                    "celular": c["telefono"],
                    "municipio": c["ciudad"],
                    "ramo": random.choice(PRODUCTOS_FLOW360),
                    "numero_poliza": f"POL-{random.randint(100000, 999999)}",
                    "estado": random.choice(["Vigente", "Por vencer", "Cancelada"]),
                    "valor_asegurado": round(random.uniform(5000000, 500000000), 0),
                    "fecha_expedicion": generar_fecha_pasada(500),
                    "fecha_renovacion": generar_fecha_futura(180),
                    "ejecutivo": random.choice(ASESORES),
                    "ultimo_contacto": generar_fecha_pasada(60),
                    "created_at": datetime.now()
                })
    db.flow360.insert_many(registros)
    print(f"✅ FLOW360: {len(registros)} registros insertados")

# ─── GESTOR DE LEADS ──────────────────────────────────────────
def generar_gestor_leads(clientes):
    db.gestor_leads.drop()
    registros = []
    for c in clientes:
        if random.random() > 0.5:
            registros.append({
                "fuente": "GESTOR_LEADS",
                "documento": c["cedula"],
                "nombre": c["nombre"],
                "email_contacto": c["email"],
                "telefono_contacto": c["telefono"],
                "ciudad_interes": c["ciudad"],
                "producto_interes": random.choice(PRODUCTOS_CENTRA + PRODUCTOS_FLOW360),
                "estado_lead": random.choice(ESTADOS_LEAD),
                "probabilidad_cierre": random.randint(10, 95),
                "valor_estimado": round(random.uniform(100000, 2000000), 0),
                "asesor_asignado": random.choice(ASESORES),
                "fecha_creacion": generar_fecha_pasada(180),
                "fecha_ultimo_seguimiento": generar_fecha_pasada(30),
                "observaciones": fake.text(max_nb_chars=100),
                "created_at": datetime.now()
            })
    db.gestor_leads.insert_many(registros)
    print(f"✅ GESTOR LEADS: {len(registros)} registros insertados")

# ─── EJECUTAR ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Generando datos sintéticos para VISTA 360...")
    clientes_base = generar_clientes_base(50)
    generar_centra(clientes_base)
    generar_flow360(clientes_base)
    generar_gestor_leads(clientes_base)
    print("\n✅ Base de datos lista en MongoDB Atlas")
    print(f"   Colecciones creadas: centra, flow360, gestor_leads")