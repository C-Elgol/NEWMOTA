from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from email.mime.image import MIMEImage
import os

def send_email_with_logo(subject: str, plain_text: str, html_content: str, from_email: str, to: list):
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_text,
        from_email=from_email,
        to=to,
    )
    email.attach_alternative(html_content, "text/html")

    # Attach logo with Content-ID
    logo_path = os.path.join(settings.STATIC_ROOT, 'images', 'Logo.webp')
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as img:
            mime_image = MIMEImage(img.read())
            mime_image.add_header('Content-ID', '<logo_image>')
            mime_image.add_header('Content-Disposition', 'inline', filename='Logo.webp')
            email.attach(mime_image)

    email.send(fail_silently=False)
    return email