from __future__ import annotations
"""NGLAB Motor â€” Paso 5: Validar emails (sintaxis + DNS + MX + SMTP).

Cuatro niveles de validaciÃ³n:
  1. Sintaxis estricta (RFC simplificado)
  2. El dominio existe (DNS)
  3. El dominio acepta correo (registros MX)
  4. El buzÃ³n existe (verificaciÃ³n SMTP MAIL FROM/RCPT TO, sin enviar email)

Los emails con sintaxis invÃ¡lida o dominio desechable â†’ lead pasa a
'sin_email' (cola WhatsApp/llamada). NUNCA aparecen en la cola de email.

Los emails sin MX vÃ¡lido o cuyo buzÃ³n no se pudo verificar por SMTP â†’
lead pasa a 'descartado' con nota 'email no verificado - rebote probable'
(incluye leads que ya estaban en 'listo_para_enviar').

Nota: la verificaciÃ³n SMTP requiere que el puerto 25 saliente estÃ© abierto
hacia el servidor MX del destinatario. Muchos proveedores de hosting/ISP
bloquean ese puerto; si ocurre, la verificaciÃ³n no podrÃ¡ confirmarse y el
lead se tratarÃ¡ de forma prudente como no verificado.
"""
import re
import smtplib
import time

import dns.resolver
import httpx

from config import REMITENTE_EMAIL
from db import leads_por_estado, actualizar_lead, stats

REGEX_ESTRICTA = re.compile(
    r"^[a-zA-Z0-9][a-zA-Z0-9._%+\-]{0,63}@"
    r"[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
    r"(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+$"
)

DOMINIOS_INVALIDOS = {
    "gmail.co", "gmail.con", "gmial.com", "hotmail.co", "hotmail.con",
    "yahoo.co", "outlook.co", "mailinator.com", "tempmail.com",
    "guerrillamail.com", "10minutemail.com",
}

_cache_mx: dict[str, bool] = {}
_cache_mx_hosts: dict[str, list[str]] = {}


def dominio_acepta_correo(dominio: str) -> bool:
    """True si el dominio tiene registros MX (o A como fallback RFC 5321)."""
    if dominio in _cache_mx:
        return _cache_mx[dominio]
    resultado = False
    try:
        respuesta = dns.resolver.resolve(dominio, "MX", lifetime=6)
        resultado = len(respuesta) > 0
    except dns.resolver.NoAnswer:
        try:
            resultado = len(dns.resolver.resolve(dominio, "A", lifetime=6)) > 0
        except Exception:
            resultado = False
    except Exception:
        resultado = False
    _cache_mx[dominio] = resultado
    return resultado


def obtener_mx_hosts(dominio: str) -> list[str]:
    """Devuelve los servidores MX del dominio ordenados por preferencia."""
    if dominio in _cache_mx_hosts:
        return _cache_mx_hosts[dominio]
    hosts: list[str] = []
    try:
        respuesta = dns.resolver.resolve(dominio, "MX", lifetime=6)
        hosts = [str(r.exchange).rstrip(".")
                 for r in sorted(respuesta, key=lambda r: r.preference)]
    except Exception:
        hosts = []
    _cache_mx_hosts[dominio] = hosts
    return hosts


def verificar_buzon_smtp(email: str, dominio: str) -> bool:
    """Verifica que el buzÃ³n existe vÃ­a protocolo SMTP (MAIL FROM / RCPT TO),
    sin enviar ningÃºn email (sin comando DATA)."""
    hosts = obtener_mx_hosts(dominio)
    if not hosts:
        return False

    remitente_dominio = REMITENTE_EMAIL.split("@")[-1] or "nglabdigital.com"

    for host in hosts:
        try:
            smtp = smtplib.SMTP(timeout=8)
            smtp.connect(host, 25)
            smtp.helo(remitente_dominio)
            smtp.mail(REMITENTE_EMAIL)
            codigo, _ = smtp.rcpt(email)
            smtp.quit()
            return codigo in (250, 251)
        except Exception:
            continue
    return False


def validar(email: str) -> tuple[bool, str]:
    email = (email or "").strip().lower()
    if not REGEX_ESTRICTA.match(email):
        return False, "sintaxis_invalida"
    dominio = email.split("@")[1]
    if dominio in DOMINIOS_INVALIDOS:
        return False, "dominio_desechable"
    if not dominio_acepta_correo(dominio):
        return False, "dominio_sin_mx"
    if not verificar_buzon_smtp(email, dominio):
        return False, "smtp_no_verificado"
    return True, "ok"


def main():
    # Solo validar leads con email en estados relevantes
    estados = ["pendiente_revision", "auditado", "listo_para_enviar"]
    leads = []
    for estado in estados:
        leads.extend(leads_por_estado(estado))

    # Filtrar solo los que tienen email
    leads = [l for l in leads if l.get("email")]
    print(f"Emails a validar: {len(leads)}")

    validos, descartados = 0, 0

    for i, lead in enumerate(leads, 1):
        ok, motivo = validar(lead["email"])
        if ok:
            validos += 1
            print(f"[{i}/{len(leads)}] {lead['nombre_negocio'][:38]:38} "
                  f"{lead['email']:42} OK")
        else:
            descartados += 1
            if motivo in ("dominio_sin_mx", "smtp_no_verificado"):
                # Sin MX vÃ¡lido o buzÃ³n no verificable â†’ rebote probable, se descarta
                # (incluye leads que ya estaban en 'listo_para_enviar')
                actualizar_lead(lead["id"],
                                email_invalido=True,
                                estado="descartado",
                                notas="email no verificado - rebote probable")
            else:
                # SintÃ¡xis invÃ¡lida o dominio desechable â†’ cola WhatsApp, NUNCA email
                actualizar_lead(lead["id"],
                                email_invalido=True,
                                estado="sin_email" if lead.get("estado") == "pendiente_revision"
                                else lead.get("estado"))
            print(f"[{i}/{len(leads)}] {lead['nombre_negocio'][:38]:38} "
                  f"{lead['email']:42} DESCARTADO ({motivo})")
        time.sleep(0.05)

    print(f"\nVÃ¡lidos: {validos} Â· Descartados: {descartados}")
    print("Resumen:", stats())


if __name__ == "__main__":
    main()

