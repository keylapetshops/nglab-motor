from __future__ import annotations
"""NGLAB Motor — Configuración central."""
import os
from dotenv import load_dotenv

load_dotenv()


def _limpiar(valor: str) -> str:
    return (valor or "").strip().strip("\r\n").strip()


# APIs
GOOGLE_PLACES_API_KEY = _limpiar(os.getenv("GOOGLE_PLACES_API_KEY", ""))
PAGESPEED_API_KEY     = _limpiar(os.getenv("PAGESPEED_API_KEY", ""))
ANTHROPIC_API_KEY     = _limpiar(os.getenv("ANTHROPIC_API_KEY", ""))

# Supabase
SUPABASE_URL         = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = _limpiar(os.getenv("SUPABASE_SERVICE_KEY", ""))
ORG_ID               = os.getenv("ORG_ID", "")

# Servidor
BASE_URL      = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
MOTOR_API_KEY = _limpiar(os.getenv("MOTOR_API_KEY", ""))

# Informe (Vercel)
INFORMES_BASE = os.getenv("INFORMES_BASE", "https://nglab-informes.vercel.app")

# Email
REMITENTE_NOMBRE = os.getenv("REMITENTE_NOMBRE", "N&G LAB Digital")
REMITENTE_EMAIL  = os.getenv("REMITENTE_EMAIL", "hola@nglabdigital.com")
EMPRESA_LEGAL    = os.getenv("EMPRESA_LEGAL", "N&G LAB Digital S.L.")
SMTP_HOST        = os.getenv("SMTP_HOST", "smtp.strato.com")
SMTP_PORT        = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER        = os.getenv("SMTP_USER", "hola@nglabdigital.com")
SMTP_PASS        = _limpiar(os.getenv("SMTP_PASS", ""))
LOTE_DIARIO      = int(os.getenv("LOTE_DIARIO", "25"))

# ---------------------------------------------------------------------------
# MUNICIPIOS (ordenados por proximidad a Benimamet, Valencia)
# ---------------------------------------------------------------------------
MUNICIPIOS: list[tuple[str, str]] = [
    ("Valencia", "Valencia"),
    ("Burjassot", "Valencia"),
    ("Mislata", "Valencia"),
    ("Paterna", "Valencia"),
    ("Torrent", "Valencia"),
    ("Quart de Poblet", "Valencia"),
    ("Manises", "Valencia"),
    ("Alboraya", "Valencia"),
    ("Catarroja", "Valencia"),
    ("Paiporta", "Valencia"),
    ("Xirivella", "Valencia"),
    ("Aldaia", "Valencia"),
    ("Alaquàs", "Valencia"),
    ("Moncada", "Valencia"),
    ("Bétera", "Valencia"),
    ("Sagunto", "Valencia"),
    ("Alzira", "Valencia"),
    ("Cullera", "Valencia"),
    ("Sueca", "Valencia"),
    ("Gandía", "Valencia"),
    ("Oliva", "Valencia"),
    ("Dénia", "Valencia"),
    ("Xàtiva", "Valencia"),
    ("Algemesí", "Valencia"),
    ("Ontinyent", "Valencia"),
    ("Alicante", "Alicante"),
    ("Elche", "Alicante"),
    ("Torrevieja", "Alicante"),
    ("Benidorm", "Alicante"),
    ("Elda", "Alicante"),
    ("Petrer", "Alicante"),
    ("Castellón", "Castellón"),
]

# ---------------------------------------------------------------------------
# NICHOS — abiertos a cualquier sector local
# ---------------------------------------------------------------------------
NICHOS: dict[str, dict] = {
    "dental": {
        "nombre": "Clínicas dentales",
        "queries": [
            "clínica dental en {m}, {p}",
            "dentista en {m}, {p}",
            "ortodoncia implantes {m}, {p}",
        ],
        "productos": "Visibilidad digital, posicionamiento local en Google, web rápida y optimizada",
        "dolor": "los pacientes buscan dentista en Google antes de llamar: si la web es lenta o no aparece bien posicionada, esos pacientes van a la clínica de al lado",
    },
    "estetica": {
        "nombre": "Centros de estética",
        "queries": [
            "centro de estética en {m}, {p}",
            "salón de uñas manicura {m}, {p}",
            "depilación láser {m}, {p}",
        ],
        "productos": "Visibilidad digital, web optimizada, presencia en Google Maps",
        "dolor": "sin buena presencia online, las clientas van al centro que aparece primero en Google",
    },
    "restauracion": {
        "nombre": "Restaurantes y hostelería",
        "queries": [
            "restaurante en {m}, {p}",
            "bar restaurante {m}, {p}",
            "cafetería en {m}, {p}",
        ],
        "productos": "Visibilidad digital, web rápida, presencia en Google Maps",
        "dolor": "cada reserva perdida por web lenta o sin visibilidad online es dinero directo a la competencia",
    },
    "legal": {
        "nombre": "Despachos de abogados y asesorías",
        "queries": [
            "abogado en {m}, {p}",
            "asesoría jurídica {m}, {p}",
            "gestoría en {m}, {p}",
        ],
        "productos": "Posicionamiento local, web profesional, visibilidad en Google",
        "dolor": "los clientes buscan abogado en Google antes de preguntar: sin presencia digital, los casos van al despacho que aparece primero",
    },
    "inmobiliaria": {
        "nombre": "Inmobiliarias",
        "queries": [
            "inmobiliaria en {m}, {p}",
            "agencia inmobiliaria {m}, {p}",
        ],
        "productos": "Visibilidad digital, web optimizada, posicionamiento local",
        "dolor": "compradores y vendedores buscan en Google: sin buena presencia, esos contactos van a la competencia",
    },
    "academia": {
        "nombre": "Academias y centros de formación",
        "queries": [
            "academia idiomas en {m}, {p}",
            "centro de formación {m}, {p}",
            "academia oposiciones {m}, {p}",
        ],
        "productos": "Visibilidad digital, web optimizada, posicionamiento local",
        "dolor": "padres y alumnos buscan academia en Google: sin buena web, esas matrículas van a otro centro",
    },
    "clinica": {
        "nombre": "Clínicas y centros médicos",
        "queries": [
            "clínica médica en {m}, {p}",
            "fisioterapia en {m}, {p}",
            "psicólogo en {m}, {p}",
            "nutricionista en {m}, {p}",
        ],
        "productos": "Visibilidad digital, web optimizada, presencia en Google Maps",
        "dolor": "los pacientes buscan especialista en Google: web lenta o sin visibilidad significa citas que van a otra clínica",
    },
    "taller": {
        "nombre": "Talleres mecánicos",
        "queries": [
            "taller mecánico en {m}, {p}",
            "taller de coches {m}, {p}",
            "chapa y pintura {m}, {p}",
        ],
        "productos": "Visibilidad digital, web optimizada, presencia en Google Maps",
        "dolor": "los clientes buscan taller en Google antes de llamar: sin buena presencia online van al taller de al lado",
    },
    "barberias": {
        "nombre": "Barberías y peluquerías",
        "queries": [
            "barbería en {m}, {p}",
            "peluquería en {m}, {p}",
        ],
        "productos": "Visibilidad digital, web optimizada, presencia en Google Maps",
        "dolor": "sin buena presencia online las citas van al salón que aparece primero en Google",
    },
    "veterinaria": {
        "nombre": "Clínicas veterinarias",
        "queries": [
            "clínica veterinaria en {m}, {p}",
            "veterinario en {m}, {p}",
        ],
        "productos": "Visibilidad digital, web optimizada, presencia en Google Maps",
        "dolor": "los dueños buscan veterinario en Google en urgencias: sin visibilidad online pierden esos clientes",
    },
    "optica": {
        "nombre": "Ópticas y centros auditivos",
        "queries": [
            "óptica en {m}, {p}",
            "centro auditivo en {m}, {p}",
        ],
        "productos": "Visibilidad digital, web optimizada, presencia en Google Maps",
        "dolor": "los clientes buscan óptica en Google antes de entrar: sin presencia digital pierden visitas",
    },
    "gimnasio": {
        "nombre": "Gimnasios y centros deportivos",
        "queries": [
            "gimnasio en {m}, {p}",
            "centro de yoga pilates {m}, {p}",
            "crossfit en {m}, {p}",
        ],
        "productos": "Visibilidad digital, web optimizada, presencia en Google Maps",
        "dolor": "los interesados buscan gimnasio en Google: sin buena web y posicionamiento van al centro de al lado",
    },
    "fotografia": {
        "nombre": "Fotógrafos y estudios",
        "queries": [
            "fotógrafo bodas en {m}, {p}",
            "estudio de fotografía {m}, {p}",
        ],
        "productos": "Portfolio web optimizado, visibilidad en Google, presencia digital",
        "dolor": "las parejas buscan fotógrafo de bodas en Google meses antes: sin buena presencia digital pierden esas reservas",
    },
    "arquitectura": {
        "nombre": "Arquitectos e interioristas",
        "queries": [
            "arquitecto en {m}, {p}",
            "interiorista diseño de interiores {m}, {p}",
        ],
        "productos": "Portfolio web optimizado, visibilidad en Google, presencia digital",
        "dolor": "los clientes buscan arquitecto en Google antes de pedir presupuesto: sin presencia digital los proyectos van a la competencia",
    },
    "otro": {
        "nombre": "Negocio local",
        "queries": [
            "{m} {p} empresa local",
        ],
        "productos": "Visibilidad digital, web optimizada, presencia en Google Maps",
        "dolor": "los clientes buscan en Google antes de comprar: sin presencia online van a la competencia",
    },
}


def nicho_config(clave: str) -> dict:
    if clave not in NICHOS:
        disponibles = ", ".join(NICHOS)
        raise SystemExit(f"Nicho '{clave}' no existe. Disponibles: {disponibles}")
    return NICHOS[clave]


# ---------------------------------------------------------------------------
# Filtros para extracción de emails
# ---------------------------------------------------------------------------
PREFIJOS_GENERICOS = [
    "info", "hola", "contacto", "reservas", "pedidos", "citas", "clinica",
    "taller", "admin", "administracion", "gerencia", "comercial",
    "hello", "contact", "consultas", "atencion", "recepcion", "direccion",
    "secretaria", "oficina", "correo", "email",
]

DOMINIOS_BASURA = [
    "example.com", "sentry.io", "wixpress.com", "godaddy.com",
    "domain.com", "email.com", "yourdomain", "mysite.com",
    "squarespace.com", "wordpress.com", "polyfill", "sentry-next",
]

EXTENSIONES_FALSAS = (
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js",
    ".woff", ".woff2", ".ttf", ".eot",
)
