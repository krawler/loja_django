from email.mime.multipart import  MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
from string import Template
from datetime import datetime

class PyEmail:
    
    def __init__(self, email, ):
        self.msg = MIMEMultipart()   
        self.msg['from'] = 'Rafael'
        self.msg['to'] = email 
    
    def set_body(self):
        html = open('template.html', 'r')
        template = Template(html.read())
        data = datetime.now().strftime('%d/%m/%Y')
        self.corpo_msg  = template.safe_substitute(
                                    nome='Rafael Ramos', 
                                    data=data)       
        self.msg['subject'] = 'Atenção este é um email de teste criado e enviado pelo Python'
        #corpo = 
        self.msg.attach(MIMEText(self.corpo_msg, 'html'))

    def attach_image(self, image_path):
        image = open(image_path, 'rb')
        img = MIMEImage(image.read())
        self.msg.attach(img)

    def enviar(self):
        with smtplib.SMTP(host='smtp.gmail.com', port=587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login('august.rafael@gmail.com', '4G5b84k4y2b!')
            smtp.send_message(self.msg)
            print('email enviado com sucesso')

py_email = PyEmail('august.rafael@gmail.com')
py_email.set_body()
py_email.enviar()
