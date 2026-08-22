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
# MUNICIPIOS — Toda España
# Capitales de provincia + ciudades principales por comunidad autónoma
# ---------------------------------------------------------------------------
MUNICIPIOS: list[tuple[str, str]] = [
    # Comunidad Valenciana
    ("Valencia", "Valencia"),
    ("Alicante", "Alicante"),
    ("Castellón de la Plana", "Castellón"),
    ("Torrent", "Valencia"),
    ("Elche", "Alicante"),
    ("Paterna", "Valencia"),
    ("Torrevieja", "Alicante"),
    ("Gandía", "Valencia"),
    ("Benidorm", "Alicante"),
    ("Elda", "Alicante"),
    ("Sagunto", "Valencia"),
    ("Burjassot", "Valencia"),
    ("Mislata", "Valencia"),
    ("Quart de Poblet", "Valencia"),
    ("Manises", "Valencia"),
    ("Alzira", "Valencia"),
    ("Petrer", "Alicante"),
    ("Dénia", "Alicante"),
    ("Ontinyent", "Valencia"),
    ("Xàtiva", "Valencia"),
    ("Alcoy", "Alicante"),
    ("Orihuela", "Alicante"),
    ("Cullera", "Valencia"),
    ("Sueca", "Valencia"),
    ("Paiporta", "Valencia"),
    ("Aldaia", "Valencia"),
    ("Alaquàs", "Valencia"),
    ("Bétera", "Valencia"),
    ("Moncada", "Valencia"),
    ("Oliva", "Valencia"),

    # Madrid
    ("Madrid", "Madrid"),
    ("Móstoles", "Madrid"),
    ("Alcalá de Henares", "Madrid"),
    ("Fuenlabrada", "Madrid"),
    ("Leganés", "Madrid"),
    ("Getafe", "Madrid"),
    ("Alcorcón", "Madrid"),
    ("Torrejón de Ardoz", "Madrid"),
    ("Parla", "Madrid"),
    ("Alcobendas", "Madrid"),
    ("Pozuelo de Alarcón", "Madrid"),
    ("Tres Cantos", "Madrid"),
    ("Las Rozas", "Madrid"),
    ("Majadahonda", "Madrid"),
    ("Boadilla del Monte", "Madrid"),
    ("Arganda del Rey", "Madrid"),
    ("Collado Villalba", "Madrid"),
    ("San Sebastián de los Reyes", "Madrid"),

    # Cataluña
    ("Barcelona", "Barcelona"),
    ("Hospitalet de Llobregat", "Barcelona"),
    ("Badalona", "Barcelona"),
    ("Terrassa", "Barcelona"),
    ("Sabadell", "Barcelona"),
    ("Mataró", "Barcelona"),
    ("Santa Coloma de Gramenet", "Barcelona"),
    ("Reus", "Tarragona"),
    ("Girona", "Girona"),
    ("Lleida", "Lleida"),
    ("Tarragona", "Tarragona"),
    ("Cornellà de Llobregat", "Barcelona"),
    ("Sant Boi de Llobregat", "Barcelona"),
    ("Rubí", "Barcelona"),
    ("Vilanova i la Geltrú", "Barcelona"),
    ("Manresa", "Barcelona"),
    ("Vic", "Barcelona"),
    ("Igualada", "Barcelona"),

    # Andalucía
    ("Sevilla", "Sevilla"),
    ("Málaga", "Málaga"),
    ("Córdoba", "Córdoba"),
    ("Granada", "Granada"),
    ("Almería", "Almería"),
    ("Huelva", "Huelva"),
    ("Jaén", "Jaén"),
    ("Cádiz", "Cádiz"),
    ("Jerez de la Frontera", "Cádiz"),
    ("Algeciras", "Cádiz"),
    ("Marbella", "Málaga"),
    ("Fuengirola", "Málaga"),
    ("Torremolinos", "Málaga"),
    ("Estepona", "Málaga"),
    ("Vélez-Málaga", "Málaga"),
    ("Motril", "Granada"),
    ("Linares", "Jaén"),
    ("Dos Hermanas", "Sevilla"),
    ("Alcalá de Guadaíra", "Sevilla"),
    ("El Puerto de Santa María", "Cádiz"),
    ("Roquetas de Mar", "Almería"),
    ("El Ejido", "Almería"),

    # País Vasco
    ("Bilbao", "Vizcaya"),
    ("San Sebastián", "Guipúzcoa"),
    ("Vitoria-Gasteiz", "Álava"),
    ("Barakaldo", "Vizcaya"),
    ("Getxo", "Vizcaya"),
    ("Irún", "Guipúzcoa"),
    ("Portugalete", "Vizcaya"),
    ("Santurtzi", "Vizcaya"),

    # Galicia
    ("Vigo", "Pontevedra"),
    ("A Coruña", "A Coruña"),
    ("Ourense", "Ourense"),
    ("Santiago de Compostela", "A Coruña"),
    ("Lugo", "Lugo"),
    ("Pontevedra", "Pontevedra"),
    ("Ferrol", "A Coruña"),

    # Castilla y León
    ("Valladolid", "Valladolid"),
    ("Burgos", "Burgos"),
    ("Salamanca", "Salamanca"),
    ("León", "León"),
    ("Palencia", "Palencia"),
    ("Zamora", "Zamora"),
    ("Ávila", "Ávila"),
    ("Segovia", "Segovia"),
    ("Soria", "Soria"),

    # Castilla-La Mancha
    ("Albacete", "Albacete"),
    ("Ciudad Real", "Ciudad Real"),
    ("Cuenca", "Cuenca"),
    ("Guadalajara", "Guadalajara"),
    ("Toledo", "Toledo"),
    ("Talavera de la Reina", "Toledo"),
    ("Puertollano", "Ciudad Real"),
    ("Hellín", "Albacete"),

    # Aragón
    ("Zaragoza", "Zaragoza"),
    ("Huesca", "Huesca"),
    ("Teruel", "Teruel"),
    ("Calatayud", "Zaragoza"),

    # Murcia
    ("Murcia", "Murcia"),
    ("Cartagena", "Murcia"),
    ("Lorca", "Murcia"),
    ("Molina de Segura", "Murcia"),
    ("Alcantarilla", "Murcia"),
    ("Yecla", "Murcia"),
    ("Águilas", "Murcia"),

    # Extremadura
    ("Badajoz", "Badajoz"),
    ("Cáceres", "Cáceres"),
    ("Mérida", "Badajoz"),
    ("Plasencia", "Cáceres"),

    # Asturias
    ("Oviedo", "Asturias"),
    ("Gijón", "Asturias"),
    ("Avilés", "Asturias"),

    # Cantabria
    ("Santander", "Cantabria"),
    ("Torrelavega", "Cantabria"),

    # La Rioja
    ("Logroño", "La Rioja"),
    ("Calahorra", "La Rioja"),

    # Navarra
    ("Pamplona", "Navarra"),
    ("Tudela", "Navarra"),

    # Baleares
    ("Palma", "Baleares"),
    ("Ibiza", "Baleares"),
    ("Mahón", "Baleares"),
    ("Manacor", "Baleares"),

    # Canarias
    ("Las Palmas de Gran Canaria", "Las Palmas"),
    ("Santa Cruz de Tenerife", "Tenerife"),
    ("La Laguna", "Tenerife"),
    ("Telde", "Las Palmas"),
    ("Arona", "Tenerife"),
    ("Arrecife", "Las Palmas"),

    # Ceuta y Melilla
    ("Ceuta", "Ceuta"),
    ("Melilla", "Melilla"),
]

# ---------------------------------------------------------------------------
# NICHOS — 50 sectores de negocio local
# ---------------------------------------------------------------------------
NICHOS: dict[str, dict] = {
    # ── Salud ────────────────────────────────────────────────────────────
    "dental": {
        "nombre": "Clínicas dentales",
        "sector_label": "clínica dental",
        "queries": ["clínica dental en {m}, {p}", "dentista en {m}, {p}", "ortodoncia implantes {m}"],
        "dolor": "los pacientes buscan dentista en Google antes de llamar: si la web es lenta o no aparece bien posicionada, van a la clínica de al lado",
    },
    "clinica_medica": {
        "nombre": "Clínicas y centros médicos",
        "sector_label": "clínica médica",
        "queries": ["clínica médica en {m}, {p}", "médico privado {m}", "centro médico {m}, {p}"],
        "dolor": "los pacientes buscan especialista en Google: web lenta o sin visibilidad significa citas que van a otra clínica",
    },
    "fisioterapia": {
        "nombre": "Fisioterapia y osteopatía",
        "sector_label": "fisioterapeuta",
        "queries": ["fisioterapia en {m}, {p}", "fisioterapeuta {m}", "osteopatía {m}, {p}"],
        "dolor": "los pacientes buscan fisio en Google: sin presencia digital van al que aparece primero",
    },
    "psicologia": {
        "nombre": "Psicólogos y terapeutas",
        "sector_label": "psicólogo",
        "queries": ["psicólogo en {m}, {p}", "terapeuta psicología {m}", "psicología clínica {m}"],
        "dolor": "los pacientes buscan psicólogo con discreción online: sin web profesional pierden esa confianza inicial",
    },
    "nutricion": {
        "nombre": "Nutricionistas y dietistas",
        "sector_label": "nutricionista",
        "queries": ["nutricionista en {m}, {p}", "dietista {m}", "consulta nutrición {m}"],
        "dolor": "los clientes comparan nutricionistas online antes de elegir: sin visibilidad digital pierden esos contactos",
    },
    "veterinaria": {
        "nombre": "Clínicas veterinarias",
        "sector_label": "veterinario",
        "queries": ["clínica veterinaria en {m}, {p}", "veterinario {m}", "hospital veterinario {m}"],
        "dolor": "los dueños buscan veterinario en urgencias desde el móvil: sin visibilidad online pierden esos clientes",
    },
    "optica": {
        "nombre": "Ópticas y centros auditivos",
        "sector_label": "óptica",
        "queries": ["óptica en {m}, {p}", "centro auditivo {m}", "gafas lentillas {m}"],
        "dolor": "los clientes buscan óptica en Google antes de entrar: sin presencia digital pierden visitas",
    },
    "farmacia": {
        "nombre": "Farmacias",
        "sector_label": "farmacia",
        "queries": ["farmacia en {m}, {p}", "parafarmacia {m}", "farmacia online {m}"],
        "dolor": "sin web ni presencia digital, los clientes van a la farmacia que aparece en Google Maps",
    },

    # ── Estética y bienestar ────────────────────────────────────────────
    "estetica": {
        "nombre": "Centros de estética",
        "sector_label": "centro de estética",
        "queries": ["centro de estética en {m}, {p}", "salón de uñas {m}", "depilación láser {m}"],
        "dolor": "sin buena presencia online, las clientas van al centro que aparece primero en Google",
    },
    "peluqueria": {
        "nombre": "Peluquerías y barberías",
        "sector_label": "peluquería",
        "queries": ["peluquería en {m}, {p}", "barbería {m}", "salón de belleza {m}"],
        "dolor": "sin presencia online las citas van al salón que aparece primero en Google",
    },
    "spa": {
        "nombre": "Spas y centros de bienestar",
        "sector_label": "spa",
        "queries": ["spa en {m}, {p}", "centro de bienestar {m}", "masajes relajantes {m}"],
        "dolor": "los clientes buscan spa para regalos y escapadas: sin web atractiva pierden esas reservas",
    },
    "gimnasio": {
        "nombre": "Gimnasios y centros deportivos",
        "sector_label": "gimnasio",
        "queries": ["gimnasio en {m}, {p}", "crossfit {m}", "centro de yoga pilates {m}"],
        "dolor": "los interesados buscan gimnasio en Google: sin buena web van al centro de al lado",
    },
    "tatuaje": {
        "nombre": "Estudios de tatuaje y piercing",
        "sector_label": "estudio de tatuaje",
        "queries": ["estudio de tatuaje en {m}, {p}", "tatuador {m}", "piercing {m}"],
        "dolor": "los clientes eligen tatuador por el portfolio online: sin web con galería pierden esas reservas",
    },

    # ── Hostelería y restauración ───────────────────────────────────────
    "restauracion": {
        "nombre": "Restaurantes y bares",
        "sector_label": "restaurante",
        "queries": ["restaurante en {m}, {p}", "bar restaurante {m}", "cafetería {m}"],
        "dolor": "cada reserva perdida por web lenta o sin visibilidad es dinero directo a la competencia",
    },
    "catering": {
        "nombre": "Catering y eventos gastronómicos",
        "sector_label": "catering",
        "queries": ["catering en {m}, {p}", "catering bodas {m}", "servicio catering eventos {m}"],
        "dolor": "los novios y empresas buscan catering en Google meses antes: sin web profesional no llegan presupuestos",
    },
    "pasteleria": {
        "nombre": "Pastelerías y panaderías",
        "sector_label": "pastelería",
        "queries": ["pastelería en {m}, {p}", "panadería artesanal {m}", "tartas personalizadas {m}"],
        "dolor": "los clientes buscan pastelerías para celebraciones online: sin web ni pedidos online pierden ventas",
    },
    "hotel": {
        "nombre": "Hoteles y alojamientos",
        "sector_label": "hotel",
        "queries": ["hotel en {m}, {p}", "hostal {m}", "apartamentos turísticos {m}"],
        "dolor": "los viajeros comparan hoteles online antes de reservar: sin buena presencia digital las reservas van a la competencia",
    },

    # ── Servicios profesionales ─────────────────────────────────────────
    "legal": {
        "nombre": "Despachos de abogados",
        "sector_label": "abogado",
        "queries": ["abogado en {m}, {p}", "despacho de abogados {m}", "asesoría jurídica {m}"],
        "dolor": "los clientes buscan abogado en Google antes de preguntar: sin presencia digital los casos van al despacho que aparece primero",
    },
    "gestoria": {
        "nombre": "Gestorías y asesorías",
        "sector_label": "gestoría",
        "queries": ["gestoría en {m}, {p}", "asesoría fiscal {m}", "asesoría laboral {m}"],
        "dolor": "los autónomos y empresas buscan gestoría en Google: sin web clara pierden esos clientes",
    },
    "notaria": {
        "nombre": "Notarías",
        "sector_label": "notaría",
        "queries": ["notaría en {m}, {p}", "notario {m}", "notaría pública {m}"],
        "dolor": "los ciudadanos buscan notaría cercana en Google: sin visibilidad digital pierden esas consultas",
    },
    "seguros": {
        "nombre": "Agencias de seguros",
        "sector_label": "agencia de seguros",
        "queries": ["agencia de seguros en {m}, {p}", "correduría de seguros {m}", "seguros coches hogar {m}"],
        "dolor": "los clientes comparan seguros online antes de contratar: sin presencia digital las pólizas van a la competencia",
    },
    "contabilidad": {
        "nombre": "Contables y auditores",
        "sector_label": "contable",
        "queries": ["contable en {m}, {p}", "auditoría contabilidad {m}", "asesoría contable {m}"],
        "dolor": "sin web profesional, los clientes eligen al contable que aparece primero en Google",
    },

    # ── Inmobiliario y construcción ─────────────────────────────────────
    "inmobiliaria": {
        "nombre": "Inmobiliarias",
        "sector_label": "inmobiliaria",
        "queries": ["inmobiliaria en {m}, {p}", "agencia inmobiliaria {m}", "pisos en venta {m}"],
        "dolor": "compradores y vendedores buscan en Google: sin buena presencia esos contactos van a la competencia",
    },
    "arquitectura": {
        "nombre": "Arquitectos e interioristas",
        "sector_label": "arquitecto",
        "queries": ["arquitecto en {m}, {p}", "interiorista {m}", "estudio de arquitectura {m}"],
        "dolor": "los clientes buscan arquitecto en Google antes de pedir presupuesto: sin presencia digital los proyectos van a la competencia",
    },
    "construccion": {
        "nombre": "Empresas de construcción y reformas",
        "sector_label": "empresa de reformas",
        "queries": ["empresa de reformas en {m}, {p}", "construcción {m}", "reformas hogar {m}"],
        "dolor": "los propietarios buscan reformistas en Google y comparan: sin web con portfolio pierden presupuestos",
    },
    "fontaneria": {
        "nombre": "Fontaneros y gasfitters",
        "sector_label": "fontanero",
        "queries": ["fontanero en {m}, {p}", "fontanería urgente {m}", "instalaciones fontanería {m}"],
        "dolor": "en una urgencia los clientes llaman al primero que aparece en Google: sin visibilidad pierden esas llamadas",
    },
    "electricista": {
        "nombre": "Electricistas",
        "sector_label": "electricista",
        "queries": ["electricista en {m}, {p}", "electricista urgente {m}", "instalaciones eléctricas {m}"],
        "dolor": "los clientes buscan electricista en Google en urgencias: sin visibilidad van al competidor que aparece primero",
    },
    "cerrajeria": {
        "nombre": "Cerrajerías",
        "sector_label": "cerrajero",
        "queries": ["cerrajero en {m}, {p}", "cerrajería urgente {m}", "cambio cerradura {m}"],
        "dolor": "en una urgencia nocturna los clientes llaman al primero que aparece: sin buena presencia digital pierden esas llamadas",
    },
    "climatizacion": {
        "nombre": "Climatización y aire acondicionado",
        "sector_label": "empresa de climatización",
        "queries": ["aire acondicionado en {m}, {p}", "climatización {m}", "instalación aire acondicionado {m}"],
        "dolor": "en verano los clientes buscan instaladores urgentes en Google: sin visibilidad van al competidor",
    },

    # ── Educación y formación ───────────────────────────────────────────
    "academia": {
        "nombre": "Academias e idiomas",
        "sector_label": "academia",
        "queries": ["academia idiomas en {m}, {p}", "academia inglés {m}", "academia oposiciones {m}"],
        "dolor": "padres y alumnos buscan academia en Google: sin buena web esas matrículas van a otro centro",
    },
    "guarderia": {
        "nombre": "Guarderías y escuelas infantiles",
        "sector_label": "guardería",
        "queries": ["guardería en {m}, {p}", "escuela infantil {m}", "ludoteca {m}"],
        "dolor": "los padres buscan guardería con tiempo: sin web clara y valoraciones pierden esas plazas",
    },
    "autoescuela": {
        "nombre": "Autoescuelas",
        "sector_label": "autoescuela",
        "queries": ["autoescuela en {m}, {p}", "carnet de conducir {m}", "academia conducción {m}"],
        "dolor": "los jóvenes buscan autoescuela en Google y comparan precios: sin buena presencia van a la competencia",
    },
    "formacion_profesional": {
        "nombre": "Centros de formación profesional",
        "sector_label": "centro de formación",
        "queries": ["centro de formación en {m}, {p}", "FP formación profesional {m}", "cursos certificados {m}"],
        "dolor": "los alumnos comparan centros online antes de matricularse: sin web clara pierden esas inscripciones",
    },

    # ── Transporte y automoción ─────────────────────────────────────────
    "taller": {
        "nombre": "Talleres mecánicos",
        "sector_label": "taller mecánico",
        "queries": ["taller mecánico en {m}, {p}", "taller coches {m}", "chapa y pintura {m}"],
        "dolor": "los clientes buscan taller en Google antes de llamar: sin buena presencia van al taller de al lado",
    },
    "concesionario": {
        "nombre": "Concesionarios de vehículos",
        "sector_label": "concesionario",
        "queries": ["concesionario en {m}, {p}", "coches de segunda mano {m}", "venta coches {m}"],
        "dolor": "los compradores buscan y comparan coches online: sin visibilidad digital pierden visitas al concesionario",
    },
    "mudanzas": {
        "nombre": "Empresas de mudanzas",
        "sector_label": "empresa de mudanzas",
        "queries": ["mudanzas en {m}, {p}", "empresa de mudanzas {m}", "portes {m}"],
        "dolor": "los clientes buscan mudanzas en Google y piden varios presupuestos: sin web clara pierden esos contactos",
    },

    # ── Comercio ────────────────────────────────────────────────────────
    "joyeria": {
        "nombre": "Joyerías y relojerías",
        "sector_label": "joyería",
        "queries": ["joyería en {m}, {p}", "relojería {m}", "anillos compromiso {m}"],
        "dolor": "los clientes buscan joyería para ocasiones especiales online: sin web con catálogo pierden ventas",
    },
    "floristeria": {
        "nombre": "Floristerías",
        "sector_label": "floristería",
        "queries": ["floristería en {m}, {p}", "flores a domicilio {m}", "ramos bodas {m}"],
        "dolor": "los clientes buscan flores para regalos y bodas online: sin pedidos online y buena presencia pierden ventas",
    },
    "informatica": {
        "nombre": "Tiendas de informática y reparación",
        "sector_label": "tienda de informática",
        "queries": ["tienda informática en {m}, {p}", "reparación ordenadores {m}", "servicio técnico {m}"],
        "dolor": "los clientes buscan reparación urgente de dispositivos en Google: sin visibilidad van al competidor",
    },
    "papeleria": {
        "nombre": "Papelerías e imprentas",
        "sector_label": "papelería",
        "queries": ["papelería en {m}, {p}", "imprenta {m}", "copistería {m}"],
        "dolor": "sin presencia digital las empresas no encuentran a la imprenta local y van a servicios online",
    },
    "ferreteria": {
        "nombre": "Ferreterías",
        "sector_label": "ferretería",
        "queries": ["ferretería en {m}, {p}", "suministros industriales {m}", "bricolaje {m}"],
        "dolor": "los clientes buscan ferretería para proyectos urgentes: sin visibilidad online van al que aparece primero",
    },

    # ── Eventos y entretenimiento ───────────────────────────────────────
    "fotografia": {
        "nombre": "Fotógrafos y estudios",
        "sector_label": "fotógrafo",
        "queries": ["fotógrafo bodas en {m}, {p}", "estudio fotografía {m}", "fotógrafo eventos {m}"],
        "dolor": "las parejas buscan fotógrafo de bodas en Google meses antes: sin portfolio web pierden esas reservas",
    },
    "musica": {
        "nombre": "Escuelas de música",
        "sector_label": "escuela de música",
        "queries": ["escuela de música en {m}, {p}", "clases de guitarra piano {m}", "conservatorio {m}"],
        "dolor": "los padres buscan escuela de música online: sin web clara pierden esas matrículas",
    },
    "eventos": {
        "nombre": "Organización de eventos",
        "sector_label": "empresa de eventos",
        "queries": ["organización de eventos en {m}, {p}", "empresa eventos {m}", "wedding planner {m}"],
        "dolor": "los novios y empresas buscan organizadores de eventos en Google: sin portfolio web pierden esos presupuestos",
    },
    "agencia_viajes": {
        "nombre": "Agencias de viajes",
        "sector_label": "agencia de viajes",
        "queries": ["agencia de viajes en {m}, {p}", "viajes organizados {m}", "tours {m}"],
        "dolor": "los viajeros comparan paquetes online: sin web optimizada y buenas valoraciones van a la competencia",
    },

    # ── Animales ────────────────────────────────────────────────────────
    "peluqueria_canina": {
        "nombre": "Peluquerías caninas",
        "sector_label": "peluquería canina",
        "queries": ["peluquería canina en {m}, {p}", "grooming perros {m}", "peluquería mascotas {m}"],
        "dolor": "los dueños de mascotas buscan peluquería canina en Google: sin presencia digital van al que aparece primero",
    },
    "residencia_animales": {
        "nombre": "Residencias y guarderías para mascotas",
        "sector_label": "residencia de mascotas",
        "queries": ["residencia mascotas en {m}, {p}", "guardería perros {m}", "hotel mascotas {m}"],
        "dolor": "los dueños buscan residencia de confianza para sus mascotas online: sin web con fotos y valoraciones pierden esas reservas",
    },

    # ── Limpieza y mantenimiento ────────────────────────────────────────
    "limpieza": {
        "nombre": "Empresas de limpieza",
        "sector_label": "empresa de limpieza",
        "queries": ["empresa de limpieza en {m}, {p}", "limpieza oficinas {m}", "limpieza comunidades {m}"],
        "dolor": "las empresas buscan servicio de limpieza en Google y piden presupuestos: sin web profesional no llegan esos contactos",
    },
    "jardineria": {
        "nombre": "Jardinería y paisajismo",
        "sector_label": "empresa de jardinería",
        "queries": ["jardinería en {m}, {p}", "paisajismo {m}", "mantenimiento jardines {m}"],
        "dolor": "los propietarios buscan jardinero en Google para mantenimiento periódico: sin visibilidad pierden esos contratos",
    },
    "control_plagas": {
        "nombre": "Control de plagas",
        "sector_label": "empresa de control de plagas",
        "queries": ["control de plagas en {m}, {p}", "fumigación {m}", "desratización desinsectación {m}"],
        "dolor": "en urgencias los clientes llaman al primero que aparece en Google: sin visibilidad pierden esas llamadas",
    },

    # ── Turismo rural ───────────────────────────────────────────────────
    "turismo_rural": {
        "nombre": "Casas rurales y turismo rural",
        "sector_label": "casa rural",
        "queries": ["casa rural en {m}, {p}", "turismo rural {m}", "alquiler vacacional {m}"],
        "dolor": "los viajeros buscan alojamiento rural online: sin web atractiva y bien posicionada las reservas van a Airbnb o la competencia",
    },

    # ── Otro ────────────────────────────────────────────────────────────
    "otro": {
        "nombre": "Negocio local",
        "sector_label": "negocio local",
        "queries": ["{m} {p} empresa local"],
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
    "secretaria", "oficina", "correo", "email", "ventas", "servicios",
    "tienda", "farmacia", "clinica", "bufete", "despacho", "estudio",
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
