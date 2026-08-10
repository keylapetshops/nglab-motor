from __future__ import annotations
import smtplib, time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
                    REMITENTE_NOMBRE, REMITENTE_EMAIL)
from db import leads_por_estado, actualizar_lead, ahora

LIMITE_DIARIO = 30

def enviar_lote():
    leads = leads_por_estado("listo_para_enviar")
    if not leads:
        print("[ENVIO] No hay leads listos para enviar")
        return 0

    lote = leads[:LIMITE_DIARIO]
    print(f"[ENVIO] Enviando {len(lote)} emails (de {len(leads)} pendientes)")
    enviados = 0

    for lead in lote:
        lid = lead.get("id")
        nombre = lead.get("nombre_negocio", "")
        email_to = lead.get("email", "")
        asunto = lead.get("email_asunto", "")
        html = lead.get("email_html", "")
        texto = lead.get("email_cuerpo", "")
        dado_de_baja = lead.get("dado_de_baja", False)

        if not email_to or not asunto or not html:
            print(f"  SKIP {nombre} - faltan datos")
            continue

        if dado_de_baja:
            print(f"  SKIP {nombre} - dado de baja")
            continue

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = asunto
            msg["From"] = f"{REMITENTE_NOMBRE} <{REMITENTE_EMAIL}>"
            msg["To"] = email_to
            msg["Reply-To"] = REMITENTE_EMAIL
            if texto:
                msg.attach(MIMEText(texto, "plain", "utf-8"))
            msg.attach(MIMEText(html, "html", "utf-8"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)

            actualizar_lead(lid,
                estado="email_1_enviado",
                fecha_email=ahora(),
                fecha_email_1=ahora(),
                secuencia_email=1
            )
            enviados += 1
            print(f"  OK {nombre} -> {email_to}")
        except Exception as e:
            print(f"  ERROR {nombre}: {e}")

        time.sleep(3)

    print(f"[ENVIO] {enviados}/{len(lote)} enviados")
    return enviados

if __name__ == "__main__":
    enviar_lote()
