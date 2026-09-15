from __future__ import annotations
import smtplib
import imaplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
    REMITENTE_NOMBRE, REMITENTE_EMAIL, LOTE_DIARIO)
from db import leads_por_estado, actualizar_lead, ahora

LIMITE_DIARIO = LOTE_DIARIO

# Dominios de plataformas/directorios — nunca enviar
DOMINIOS_BLOQUEADOS = {
    "booksy.com", "treatwell.com", "doctoralia.com", "doctoralia.es",
    "topdoctors.es", "topdoctors.com", "tuotromedico.com", "doctorin.es",
    "webador.es", "webador.com", "website.com", "nginx.com",
    "divi.express", "example.com", "test.com", "domain.com",
    "sentry.io", "wixpress.com", "godaddy.com", "squarespace.com",
    "wordpress.com", "polyfill.io",
}


def dominio_email(email: str) -> str:
    try:
        return email.strip().lower().split("@")[1]
    except Exception:
        return ""


def guardar_copia_imap(msg):
    try:
        imap = imaplib.IMAP4_SSL("imap.strato.com", 993)
        imap.login(SMTP_USER, SMTP_PASS)
        carpetas = ["Sent Items", "Sent", "INBOX.Sent", "Enviados"]
        guardado = False
        for carpeta in carpetas:
            try:
                resultado = imap.append(
                    carpeta, "\\Seen",
                    imaplib.Time2Internaldate(time.time()),
                    msg.as_bytes()
                )
                if resultado[0] == "OK":
                    guardado = True
                    break
            except Exception:
                continue
        imap.logout()
        if not guardado:
            print("   WARN no se pudo guardar copia en Enviados")
    except Exception as e:
        print(f"   WARN copia IMAP fallida: {e}")


def enviar_lote():
    leads = leads_por_estado("listo_para_enviar")
    if not leads:
        print("[ENVIO] No hay leads listos para enviar")
        return 0

    # Cargar dominios a los que ya hemos enviado
    import httpx, os
    dominios_ya_enviados: set[str] = set()
    try:
        key = os.getenv("SUPABASE_SERVICE_KEY", "")
        url_sb = os.getenv("SUPABASE_URL", "")
        org = os.getenv("ORG_ID", "")
        headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        with httpx.Client(timeout=15) as c:
            r = c.get(
                f"{url_sb}/rest/v1/crm_leads"
                f"?org_id=eq.{org}&fecha_email_1=not.is.null&select=email&limit=10000",
                headers=headers,
            )
            if r.status_code == 200:
                for row in r.json():
                    d = dominio_email(row.get("email") or "")
                    if d:
                        dominios_ya_enviados.add(d)
    except Exception as e:
        print(f"   WARN no se pudieron cargar dominios enviados: {e}")

    # Filtrar lote
    lote_filtrado = []
    dominios_en_este_lote: set[str] = set()

    for lead in leads:
        email = lead.get("email", "") or ""
        if not email:
            continue
        d = dominio_email(email)

        if d in DOMINIOS_BLOQUEADOS:
            print(f"   SKIP {lead.get('nombre_negocio','')[:40]} -> dominio bloqueado ({d})")
            actualizar_lead(lead["id"], estado="descartado", notas=f"Dominio bloqueado: {d}")
            continue

        if d in dominios_ya_enviados or d in dominios_en_este_lote:
            print(f"   SKIP {lead.get('nombre_negocio','')[:40]} -> dominio duplicado ({d})")
            actualizar_lead(lead["id"], estado="descartado", notas=f"Dominio duplicado: {d}")
            continue

        dominios_en_este_lote.add(d)
        lote_filtrado.append(lead)
        if len(lote_filtrado) >= LIMITE_DIARIO:
            break

    if not lote_filtrado:
        print("[ENVIO] No hay leads validos tras filtrar")
        return 0

    print(f"[ENVIO] Enviando {len(lote_filtrado)} emails (de {len(leads)} pendientes)")
    enviados = 0
    errores = 0

    for lead in lote_filtrado:
        lid = lead.get("id")
        nombre = lead.get("nombre_negocio", "")
        email_to = lead.get("email", "")
        asunto = lead.get("email_asunto", "")
        html = lead.get("email_html", "")
        texto = lead.get("email_cuerpo", "")

        if not email_to or not asunto or not html:
            print(f"   SKIP {nombre} - faltan datos")
            continue
        if lead.get("dado_de_baja"):
            print(f"   SKIP {nombre} - dado de baja")
            actualizar_lead(lid, estado="descartado")
            continue

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = asunto
            msg["From"] = f"{REMITENTE_NOMBRE} <{REMITENTE_EMAIL}>"
            msg["To"] = email_to
            if texto:
                msg.attach(MIMEText(texto, "plain", "utf-8"))
            msg.attach(MIMEText(html, "html", "utf-8"))
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
            guardar_copia_imap(msg)
            actualizar_lead(lid, estado="email_1_enviado",
                           fecha_email=ahora(), fecha_email_1=ahora(), secuencia_email=1)
            enviados += 1
            print(f"   OK {nombre} -> {email_to}")

        except smtplib.SMTPRecipientsRefused:
            errores += 1
            actualizar_lead(lid, estado="descartado", notas="SMTP: email rechazado")
            print(f"   ERR {nombre} -> rechazado")
        except smtplib.SMTPException as e:
            errores += 1
            actualizar_lead(lid, notas=f"Error SMTP {type(e).__name__}: {str(e)[:100]}")
            print(f"   ERR {nombre} -> {e}")
        except Exception as e:
            errores += 1
            actualizar_lead(lid, notas=f"Error {type(e).__name__}: {str(e)[:100]}")
            print(f"   ERR {nombre} -> {e}")

        time.sleep(3)

    print(f"[ENVIO] {enviados}/{len(lote_filtrado)} enviados · {errores} errores")
    return enviados


if __name__ == "__main__":
    enviar_lote()
