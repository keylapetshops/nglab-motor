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
        "dolor": "El 23% de las citas dentales se quedan vacías por ausencias sin avisar. Sus competidores con recordatorio automático por WhatsApp recuperan hasta 180€ por hueco.",
    },
    "clinica_medica": {
        "nombre": "Clínicas y centros médicos",
        "sector_label": "clínica médica",
        "queries": ["clínica médica en {m}, {p}", "médico privado {m}", "centro médico {m}, {p}"],
        "dolor": "Recepción dedica 3 horas diarias a confirmar citas por teléfono. La automatización de recordatorios reduce ausencias un 50% y libera al personal.",
    },
    "fisioterapia": {
        "nombre": "Fisioterapia y osteopatía",
        "sector_label": "fisioterapeuta",
        "queries": ["fisioterapia en {m}, {p}", "fisioterapeuta {m}", "osteopatía {m}, {p}"],
        "dolor": "Un 10% de ausencias no cobradas supone más de 5.000€/año en pérdidas. Cada ausente en fisio cuesta entre 30€ y 50€ por hueco vacío.",
    },
    "psicologia": {
        "nombre": "Psicólogos y terapeutas",
        "sector_label": "psicólogo",
        "queries": ["psicólogo en {m}, {p}", "terapeuta psicología {m}", "psicología clínica {m}"],
        "dolor": "El 30% de los pacientes busca terapia fuera del horario comercial por privacidad. Sin reserva online al instante esos pacientes se van a otra consulta.",
    },
    "nutricion": {
        "nombre": "Nutricionistas y dietistas",
        "sector_label": "nutricionista",
        "queries": ["nutricionista en {m}, {p}", "dietista {m}", "consulta nutrición {m}"],
        "dolor": "La gestión manual de revisiones provoca un 40% de abandono del tratamiento. Sin agenda automatizada pierden clientes antes de que vean resultados.",
    },
    "veterinaria": {
        "nombre": "Clínicas veterinarias",
        "sector_label": "veterinario",
        "queries": ["clínica veterinaria en {m}, {p}", "veterinario {m}", "hospital veterinario {m}"],
        "dolor": "El 88% de los dueños busca veterinario en Google Maps y contacta en 24 horas. Sin cita online inmediata pierde las revisiones anuales.",
    },
    "optica": {
        "nombre": "Ópticas y centros auditivos",
        "sector_label": "óptica",
        "queries": ["óptica en {m}, {p}", "centro auditivo {m}", "gafas lentillas {m}"],
        "dolor": "Sin recordatorio automático de revisión anual se pierde el 35% de clientes. Sin sistema automático olvidan volver y se gradúan en la competencia.",
    },
    "farmacia": {
        "nombre": "Farmacias",
        "sector_label": "farmacia",
        "queries": ["farmacia en {m}, {p}", "parafarmacia {m}", "farmacia online {m}"],
        "dolor": "Solo el 31,6% de pymes vende online. El margen real está en dermoestética pero sin presencia digital esos clientes van a otra farmacia.",
    },

    # ── Estética y bienestar ────────────────────────────────────────────
    "estetica": {
        "nombre": "Centros de estética",
        "sector_label": "centro de estética",
        "queries": ["centro de estética en {m}, {p}", "salón de uñas {m}", "depilación láser {m}"],
        "dolor": "Cabinas vacías por ausencias generan pérdidas de más de 180€ por tratamiento. Sin fianza previa en la reserva online los no-shows destruyen la agenda.",
    },
    "peluqueria": {
        "nombre": "Peluquerías y barberías",
        "sector_label": "peluquería",
        "queries": ["peluquería en {m}, {p}", "barbería {m}", "salón de belleza {m}"],
        "dolor": "Atender llamadas mientras se realiza un servicio pierde citas activas. Sin reserva online 24/7 los clientes van al salón que sí permite reservar desde Instagram.",
    },
    "spa": {
        "nombre": "Spas y centros de bienestar",
        "sector_label": "spa",
        "queries": ["spa en {m}, {p}", "centro de bienestar {m}", "masajes relajantes {m}"],
        "dolor": "Los agregadores de descuentos se quedan con hasta el 30% del margen. Sin venta directa trabajan para las plataformas en vez de para sí mismos.",
    },
    "gimnasio": {
        "nombre": "Gimnasios y centros deportivos",
        "sector_label": "gimnasio",
        "queries": ["gimnasio en {m}, {p}", "crossfit {m}", "centro de yoga pilates {m}"],
        "dolor": "El 78% de quien busca gimnasio en el móvil se inscribe en el primero que ofrece prueba online. Sin reserva de clase de prueba pierde esas altas.",
    },
    "tatuaje": {
        "nombre": "Estudios de tatuaje y piercing",
        "sector_label": "estudio de tatuaje",
        "queries": ["estudio de tatuaje en {m}, {p}", "tatuador {m}", "piercing {m}"],
        "dolor": "Sin fianza obligatoria en la reserva los no-shows arruinan la agenda. El tiempo perdido en presupuestos por chat reduce la productividad un 25%.",
    },

    # ── Hostelería y restauración ───────────────────────────────────────
    "restauracion": {
        "nombre": "Restaurantes y bares",
        "sector_label": "restaurante",
        "queries": ["restaurante en {m}, {p}", "bar restaurante {m}", "cafetería {m}"],
        "dolor": "Las cancelaciones de última hora reducen el margen mensual un 15%. Solo 2 de cada 10 bares aparece en la primera página de Google.",
    },
    "catering": {
        "nombre": "Catering y eventos gastronómicos",
        "sector_label": "catering",
        "queries": ["catering en {m}, {p}", "catering bodas {m}", "servicio catering eventos {m}"],
        "dolor": "El 60% de presupuestos de eventos se pierden por tardar más de 24 horas en responder. Sin agenda online para catas la competencia cierra antes.",
    },
    "pasteleria": {
        "nombre": "Pastelerías y panaderías",
        "sector_label": "pastelería",
        "queries": ["pastelería en {m}, {p}", "panadería artesanal {m}", "tartas personalizadas {m}"],
        "dolor": "Sin canal de encargo online la producción es ineficiente y hay desperdicio. Solo el 31,6% de pymes alimentarias vende online.",
    },
    "hotel": {
        "nombre": "Hoteles y alojamientos",
        "sector_label": "hotel",
        "queries": ["hotel en {m}, {p}", "hostal {m}", "apartamentos turísticos {m}"],
        "dolor": "Las OTAs cobran entre el 15% y el 25% de comisión por reserva. Sin motor de reservas directas trabajan para Booking en vez de para sí mismos.",
    },

    # ── Servicios profesionales ─────────────────────────────────────────
    "legal": {
        "nombre": "Despachos de abogados",
        "sector_label": "abogado",
        "queries": ["abogado en {m}, {p}", "despacho de abogados {m}", "asesoría jurídica {m}"],
        "dolor": "Solo el 29% de despachos profesionales usa captación digital. Sin agenda con primera consulta de pago atienden consultas informativas gratuitas.",
    },
    "gestoria": {
        "nombre": "Gestorías y asesorías",
        "sector_label": "gestoría",
        "queries": ["gestoría en {m}, {p}", "asesoría fiscal {m}", "asesoría laboral {m}"],
        "dolor": "El intercambio de documentación por email manual consume 15 horas mensuales por cliente. Solo el 10% de gestorías ofrece servicios online.",
    },
    "notaria": {
        "nombre": "Notarías",
        "sector_label": "notaría",
        "queries": ["notaría en {m}, {p}", "notario {m}", "notaría pública {m}"],
        "dolor": "La acumulación en sala de espera por falta de coordinación previa genera fricción. Sin cita previa online el cliente vive una experiencia deficiente.",
    },
    "seguros": {
        "nombre": "Agencias de seguros",
        "sector_label": "agencia de seguros",
        "queries": ["agencia de seguros en {m}, {p}", "correduría de seguros {m}", "seguros coches hogar {m}"],
        "dolor": "El 88% de asegurados consulta en Google antes de renovar su póliza. Sin cotizador exprés 24/7 pierden renovaciones frente a comparadores online.",
    },
    "contabilidad": {
        "nombre": "Contables y auditores",
        "sector_label": "contable",
        "queries": ["contable en {m}, {p}", "auditoría contabilidad {m}", "asesoría contable {m}"],
        "dolor": "La recogida física de facturas retrasa el cierre trimestral. Los contables que automatizan ahorran 15 horas al mes por PYME.",
    },

    # ── Inmobiliario y construcción ─────────────────────────────────────
    "inmobiliaria": {
        "nombre": "Inmobiliarias",
        "sector_label": "inmobiliaria",
        "queries": ["inmobiliaria en {m}, {p}", "agencia inmobiliaria {m}", "pisos en venta {m}"],
        "dolor": "Las inmobiliarias pierden el 70% del tiempo en visitas con compradores no cualificados. Sin tours virtuales malgastan su agenda.",
    },
    "arquitectura": {
        "nombre": "Arquitectos e interioristas",
        "sector_label": "arquitecto",
        "queries": ["arquitecto en {m}, {p}", "interiorista {m}", "estudio de arquitectura {m}"],
        "dolor": "Proyectos paralizados por falta de presentación visual interactiva. Sin portfolio 3D y agenda online la reunión con el promotor nunca llega.",
    },
    "construccion": {
        "nombre": "Empresas de construcción y reformas",
        "sector_label": "empresa de reformas",
        "queries": ["empresa de reformas en {m}, {p}", "construcción {m}", "reformas hogar {m}"],
        "dolor": "La construcción es el sector menos digitalizado de España — solo el 11,4% usa IA. Sus competidores que aparecen en Google se llevan las reformas.",
    },
    "fontaneria": {
        "nombre": "Fontaneros y gasfitters",
        "sector_label": "fontanero",
        "queries": ["fontanero en {m}, {p}", "fontanería urgente {m}", "instalaciones fontanería {m}"],
        "dolor": "El 88% de quien sufre una fuga busca en Google Maps y llama al instante. Sin ficha en el TOP 3 local regala urgencias de alto valor a la competencia.",
    },
    "electricista": {
        "nombre": "Electricistas",
        "sector_label": "electricista",
        "queries": ["electricista en {m}, {p}", "electricista urgente {m}", "instalaciones eléctricas {m}"],
        "dolor": "Las búsquedas de cargadores de coche eléctrico se han triplicado. Sin presencia digital pierde contratos de mayor ticket frente a la competencia.",
    },
    "cerrajeria": {
        "nombre": "Cerrajerías",
        "sector_label": "cerrajero",
        "queries": ["cerrajero en {m}, {p}", "cerrajería urgente {m}", "cambio cerradura {m}"],
        "dolor": "El 78% de las búsquedas urgentes en móvil busca llamada en menos de 5 minutos. Sin estar en el TOP 3 de Google Maps local las urgencias van a la competencia.",
    },
    "climatizacion": {
        "nombre": "Climatización y aire acondicionado",
        "sector_label": "empresa de climatización",
        "queries": ["aire acondicionado en {m}, {p}", "climatización {m}", "instalación aire acondicionado {m}"],
        "dolor": "Agenda vacía en primavera y otoño por falta de mantenimiento preventivo automatizado. Sin recordatorios por WhatsApp pierde contratos recurrentes.",
    },

    # ── Educación y formación ───────────────────────────────────────────
    "academia": {
        "nombre": "Academias e idiomas",
        "sector_label": "academia",
        "queries": ["academia idiomas en {m}, {p}", "academia inglés {m}", "academia oposiciones {m}"],
        "dolor": "Fuga de matrículas al inicio de curso por no ofrecer reserva de prueba de nivel online. El 54% de pymes educativas tiene software pero pierde alumnos en la web.",
    },
    "guarderia": {
        "nombre": "Guarderías y escuelas infantiles",
        "sector_label": "guardería",
        "queries": ["guardería en {m}, {p}", "escuela infantil {m}", "ludoteca {m}"],
        "dolor": "Los padres buscan guardería fuera del horario lectivo y exigen cita inmediata. Sin agenda online 24/7 pierden esas plazas ante centros más ágiles.",
    },
    "autoescuela": {
        "nombre": "Autoescuelas",
        "sector_label": "autoescuela",
        "queries": ["autoescuela en {m}, {p}", "carnet de conducir {m}", "academia conducción {m}"],
        "dolor": "Los jóvenes exigen procesos 100% digitales para elegir horario de práctica. Sin reserva online saturan la administración y se van a otra autoescuela.",
    },
    "formacion_profesional": {
        "nombre": "Centros de formación profesional",
        "sector_label": "centro de formación",
        "queries": ["centro de formación en {m}, {p}", "FP formación profesional {m}", "cursos certificados {m}"],
        "dolor": "Los formularios estáticos pierden hasta el 70% de solicitudes de información. Sin cita instantánea con orientador el interesado se va a otro centro.",
    },

    # ── Transporte y automoción ─────────────────────────────────────────
    "taller": {
        "nombre": "Talleres mecánicos",
        "sector_label": "taller mecánico",
        "queries": ["taller mecánico en {m}, {p}", "taller coches {m}", "chapa y pintura {m}"],
        "dolor": "Las entradas caóticas a primera hora generan cuellos de botella. Sin cita previa online los clientes se van al taller que sí tiene agenda digital.",
    },
    "concesionario": {
        "nombre": "Concesionarios de vehículos",
        "sector_label": "concesionario",
        "queries": ["concesionario en {m}, {p}", "coches de segunda mano {m}", "venta coches {m}"],
        "dolor": "Responder tarde a leads web reduce la probabilidad de venta un 80%. Sin agendado de prueba de conducción online pierde el cliente en las primeras 2 horas.",
    },
    "mudanzas": {
        "nombre": "Empresas de mudanzas",
        "sector_label": "empresa de mudanzas",
        "queries": ["mudanzas en {m}, {p}", "empresa de mudanzas {m}", "portes {m}"],
        "dolor": "Las visitas para calcular cúbicos generan costes antes de confirmar la contratación. El 88% elige empresa local en Google — sin visibilidad no existes.",
    },

    # ── Comercio ────────────────────────────────────────────────────────
    "joyeria": {
        "nombre": "Joyerías y relojerías",
        "sector_label": "joyería",
        "queries": ["joyería en {m}, {p}", "relojería {m}", "anillos compromiso {m}"],
        "dolor": "El comercio minorista con e-commerce crece a doble dígito pero pierde la venta de alto ticket. Sin citas VIP el cliente compra en plataformas online.",
    },
    "floristeria": {
        "nombre": "Floristerías",
        "sector_label": "floristería",
        "queries": ["floristería en {m}, {p}", "flores a domicilio {m}", "ramos bodas {m}"],
        "dolor": "Sin canal de pedido online y citas para novias pierde ventas fuera del horario. Los ramos de boda se contratan meses antes — sin web no llegan.",
    },
    "informatica": {
        "nombre": "Tiendas de informática y reparación",
        "sector_label": "tienda de informática",
        "queries": ["tienda informática en {m}, {p}", "reparación ordenadores {m}", "servicio técnico {m}"],
        "dolor": "Bajos márgenes en hardware por no vender mantenimientos recurrentes. Solo el 44% de pymes usa ERP/CRM — hay demanda local de soporte IT sin cubrir.",
    },
    "papeleria": {
        "nombre": "Papelerías e imprentas",
        "sector_label": "papelería",
        "queries": ["papelería en {m}, {p}", "imprenta {m}", "copistería {m}"],
        "dolor": "Pérdida de ventas de material escolar frente a grandes superficies online. Sin tienda online con recogida rápida el barrio compra en Amazon.",
    },
    "ferreteria": {
        "nombre": "Ferreterías",
        "sector_label": "ferretería",
        "queries": ["ferretería en {m}, {p}", "suministros industriales {m}", "bricolaje {m}"],
        "dolor": "Sin catálogo web sincronizado el cliente profesional va a grandes almacenes. El comercio minorista con e-commerce crece — sin stock online pierden contratos.",
    },

    # ── Eventos y entretenimiento ───────────────────────────────────────
    "fotografia": {
        "nombre": "Fotógrafos y estudios",
        "sector_label": "fotógrafo",
        "queries": ["fotógrafo bodas en {m}, {p}", "estudio fotografía {m}", "fotógrafo eventos {m}"],
        "dolor": "El caos en campañas de minisesiones por chat manual reduce productividad un 25%. Sin fianza online los no-shows arruinan la campaña de Navidad.",
    },
    "musica": {
        "nombre": "Escuelas de música",
        "sector_label": "escuela de música",
        "queries": ["escuela de música en {m}, {p}", "clases de guitarra piano {m}", "conservatorio {m}"],
        "dolor": "La coordinación manual de aulas y profesores genera solapamientos. Sin reserva online de salas y clases de prueba pierde alumnos ante academias más ágiles.",
    },
    "eventos": {
        "nombre": "Organización de eventos",
        "sector_label": "empresa de eventos",
        "queries": ["organización de eventos en {m}, {p}", "empresa eventos {m}", "wedding planner {m}"],
        "dolor": "El 60% del tiempo se pierde en llamadas de cualificación sin conocer el presupuesto. Sin agenda online y galería los organizadores van al que responde antes.",
    },
    "agencia_viajes": {
        "nombre": "Agencias de viajes",
        "sector_label": "agencia de viajes",
        "queries": ["agencia de viajes en {m}, {p}", "viajes organizados {m}", "tours {m}"],
        "dolor": "El 32% de los españoles compra viajes online. Sin citas VIP para viajes a medida pierden los clientes de mayor valor frente a las plataformas.",
    },

    # ── Animales ────────────────────────────────────────────────────────
    "peluqueria_canina": {
        "nombre": "Peluquerías caninas",
        "sector_label": "peluquería canina",
        "queries": ["peluquería canina en {m}, {p}", "grooming perros {m}", "peluquería mascotas {m}"],
        "dolor": "Atender llamadas con las manos ocupadas genera retrasos y cancelaciones. Sin citas online segmentadas por raza y tamaño la agenda es un caos.",
    },
    "residencia_animales": {
        "nombre": "Residencias y guarderías para mascotas",
        "sector_label": "residencia de mascotas",
        "queries": ["residencia mascotas en {m}, {p}", "guardería perros {m}", "hotel mascotas {m}"],
        "dolor": "Las cancelaciones en agosto dejan plazas vacías imposibles de reasignar. Sin reserva con fianza online las pérdidas en temporada alta son inevitables.",
    },

    # ── Limpieza y mantenimiento ────────────────────────────────────────
    "limpieza": {
        "nombre": "Empresas de limpieza",
        "sector_label": "empresa de limpieza",
        "queries": ["empresa de limpieza en {m}, {p}", "limpieza oficinas {m}", "limpieza comunidades {m}"],
        "dolor": "Las cotizaciones lentas provocan la pérdida del contrato. El 88% elige la primera empresa de limpieza que responde — sin automatización se pierde.",
    },
    "jardineria": {
        "nombre": "Jardinería y paisajismo",
        "sector_label": "empresa de jardinería",
        "queries": ["jardinería en {m}, {p}", "paisajismo {m}", "mantenimiento jardines {m}"],
        "dolor": "Negocio estacional sin contacto automatizado para trabajos de poda. Sin recordatorios por WhatsApp pierde contratos de mantenimiento recurrente.",
    },
    "control_plagas": {
        "nombre": "Control de plagas",
        "sector_label": "empresa de control de plagas",
        "queries": ["control de plagas en {m}, {p}", "fumigación {m}", "desratización desinsectación {m}"],
        "dolor": "Un aviso no atendido al instante en un restaurante supone la pérdida del contrato anual. Sin reserva urgente desde Google la competencia se lleva el cliente.",
    },

    # ── Turismo rural ───────────────────────────────────────────────────
    "turismo_rural": {
        "nombre": "Casas rurales y turismo rural",
        "sector_label": "casa rural",
        "queries": ["casa rural en {m}, {p}", "turismo rural {m}", "alquiler vacacional {m}"],
        "dolor": "Los portales cobran entre el 15% y el 30% de comisión por reserva. Sin motor de reservas directas trabajan para las plataformas en vez de para sí mismos.",
    },

    # ── Otro ────────────────────────────────────────────────────────────
    "otro": {
        "nombre": "Negocio local",
        "sector_label": "negocio local",
        "queries": ["{m} {p} empresa local"],
        "dolor": "El 46% de búsquedas en Google tienen intención local y el 88% de usuarios lo visita en 24 horas. Sin presencia digital no existen.",
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

