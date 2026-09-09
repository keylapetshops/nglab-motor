from __future__ import annotations
import smtplib
import imaplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
                    REMITENTE_NOMBRE, REMITENTE_EMAIL, LOTE_DIARIO)
from db import leads_por_estado, actualizar_lead, ahora

# FIX: antes hardcodeado a 30, ahora viene de config.py (LOTE_DIARIO=25 por defecto)
# Se puede cambiar via variable de entorno LOTE_DIARIO en Railway
LIMITE_DIARIO = LOTE_DIARIO


def guardar_copia_imap(msg):
    """Guarda una copia del email en la carpeta Enviados de Strato via IMAP."""
    try:
        imap = imaplib.IMAP4_SSL("imap.strato.com", 993)
        imap.login(SMTP_USER, SMTP_PASS)
        # Strato usa "Sent Items"
        carpetas = ["Sent Items", "Sent", "INBOX.Sent", "Enviados"]
        guardado = False
        for carpeta in carpetas:
            try:
                resultado = imap.append(
                    carpeta,
                    "\\Seen",
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
            print("  WARN no se pudo guardar copia en Enviados")
    except Exception as e:
        print(f"  WARN copia IMAP fallida: {e}")


def enviar_lote():
    leads = leads_por_estado("listo_para_enviar", nicho="estetica")
    if not leads:
        print("[ENVIO] No hay leads listos para enviar")
        return 0

    lote = leads[:LIMITE_DIARIO]
    print(f"[ENVIO] Enviando {len(lote)} emails (de {len(leads)} pendientes)")
    enviados = 0
    errores = 0

    for lead in lote:
        lid          = lead.get("id")
        nombre       = lead.get("nombre_negocio", "")
        email_to     = lead.get("email", "")
        asunto       = lead.get("email_asunto", "")
        html         = lead.get("email_html", "")
        texto        = lead.get("email_cuerpo", "")
        dado_de_baja = lead.get("dado_de_baja", False)

        if not email_to or not asunto or not html:
            print(f"  SKIP {nombre} - faltan datos")
            continue

        if dado_de_baja:
            print(f"  SKIP {nombre} - dado de baja")
            actualizar_lead(lid, estado="descartado")
            continue

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = asunto
            msg["From"]    = f"{REMITENTE_NOMBRE} <{REMITENTE_EMAIL}>"
            msg["To"]      = email_to

            if texto:
                msg.attach(MIMEText(texto, "plain", "utf-8"))
            msg.attach(MIMEText(html, "html", "utf-8"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)

            # Guardar copia en carpeta Enviados de Strato
            guardar_copia_imap(msg)

            actualizar_lead(
                lid,
                estado="email_1_enviado",
                fecha_email=ahora(),
                fecha_email_1=ahora(),
                secuencia_email=1,
            )
            enviados += 1
            print(f"  OK  {nombre} -> {email_to}")

        except smtplib.SMTPRecipientsRefused:
            # Email rechazado por el servidor destino — descartamos
            errores += 1
            actualizar_lead(lid, estado="descartado",
                            notas=f"SMTP: email rechazado por servidor destino")
            print(f"  ERR {nombre} -> email rechazado por servidor")

        except smtplib.SMTPException as e:
            # Error SMTP genérico — dejamos en listo_para_enviar para reintentar
            errores += 1
            actualizar_lead(lid,
                            notas=f"Error SMTP {type(e).__name__}: {str(e)[:100]}")
            print(f"  ERR {nombre} -> {type(e).__name__}: {e}")

        except Exception as e:
            # Error inesperado — dejamos en listo_para_enviar para reintentar
            errores += 1
            actualizar_lead(lid,
                            notas=f"Error envío {type(e).__name__}: {str(e)[:100]}")
            print(f"  ERR {nombre} -> {type(e).__name__}: {e}")

        time.sleep(3)

    print(f"[ENVIO] {enviados}/{len(lote)} enviados · {errores} errores")
    return enviados


if __name__ == "__main__":
    enviar_lote()
