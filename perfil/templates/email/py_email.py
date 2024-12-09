from email.mime.multipart import  MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
import os
from string import Template
from datetime import datetime

class PyEmail:
    
    def __init__(self, email, ):
        self.msg = MIMEMultipart()   
        self.msg['from'] = 'Rafael'
        self.msg['to'] = email 
    
    def set_body(self, nome_completo, codigo, request):
        base_path = request.build_absolute_uri()
        base_path = base_path.replace(request.path, '').replace('http//', 'http://')
        module_dir = os.path.dirname(__file__) 
        file_path = os.path.join(module_dir, 'template_password_reset.html')
        html =   open(file_path, 'r')
        template = Template(html.read())
        data = datetime.now().strftime('%d/%m/%Y')
        self.corpo_msg  = template.safe_substitute(
                                    nome=nome_completo, 
                                    codigo=codigo,
                                    base_url=base_path)       
        self.msg['subject'] = f'Código para recadastramento de senha'
        self.msg.attach(MIMEText(self.corpo_msg, 'html'))   

    def attach_image(self, image_path):
        image = open(image_path, 'rb')
        img = MIMEImage(image.read())
        self.msg.attach(img)

    def enviar(self):
        with smtplib.SMTP(host='smtp.gmail.com', port=587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login('august.rafael@gmail.com', 'kvdm oomm rozo bjti')
            smtp.send_message(self.msg)
            print('email enviado com sucesso')