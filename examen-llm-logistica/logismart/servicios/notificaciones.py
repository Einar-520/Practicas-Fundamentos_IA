"""El correo se envía solo al pulsar y confirmar Enviar en la GUI."""
import os
import smtplib
import ssl
from email.message import EmailMessage


def notificar(incidente, simulacion=True):
    categoria = incidente['clasificacion']
    asunto = f"[{categoria['prioridad'].upper()}] {categoria['categoria']}"
    if simulacion:
        return f'SIMULACIÓN: mensaje preparado; no se envió ningún correo. Asunto: {asunto}'
    requeridas = ['SMTP_HOST', 'SMTP_USER', 'SMTP_PASSWORD', 'SMTP_FROM', 'SMTP_TO']
    if any(not os.getenv(k) for k in requeridas):
        raise ValueError('Completa SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM y SMTP_TO en .env.')
    try:
        mensaje = EmailMessage()
        mensaje['From'], mensaje['To'], mensaje['Subject'] = os.environ['SMTP_FROM'], os.environ['SMTP_TO'], asunto
        mensaje.set_content(f"Incidente {incidente['_id']}\n{categoria['resumen']}\nEstado: {incidente['estado']}\n")
        with smtplib.SMTP(os.environ['SMTP_HOST'], int(os.getenv('SMTP_PORT', '587')), timeout=15) as servidor:
            servidor.starttls(context=ssl.create_default_context())
            servidor.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
            rechazados = servidor.send_message(mensaje)
        if rechazados:
            raise RuntimeError('El servidor rechazó al destinatario.')
        return 'El servidor SMTP aceptó el mensaje. La entrega final depende del servidor receptor.'
    except (OSError, smtplib.SMTPException, ValueError):
        raise RuntimeError('No se pudo confirmar el envío SMTP. Revisa configuración y destinatario antes de repetirlo.') from None
