from .models import PasswordResetCode
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect, reverse, render
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from datetime import datetime, timedelta
from perfil.templates.email.py_email import PyEmail
import random
import string
import re

class PerfilService():

    def validar_email(self, email):
        regex = r'\S+@\S+\.\S+'
        # Verifica se a string corresponde ao padrão
        if re.match(regex, email):
            return True
        else:
            return False

    def password_reset(self, form, request):

        if form.is_valid():
            email = form.cleaned_data['email']

            try:    
                user = User.objects.get(email=email)

                past_30_minutes = timezone.now() - timedelta(minutes=30)
                last_token_claimed = PasswordResetCode.objects.filter(usuario=user.id, criado_em__gte=past_30_minutes).first()

                if last_token_claimed:
                    # If a code was claimed within the past 30 minutes, send a message
                    messages.info(
                        request,
                        'Um código de redefinição de senha já foi enviado para este e-mail recentemente. Por favor, verifique sua caixa de entrada ou spam.'
                    )
                    return redirect('perfil:password_reset')

                PasswordResetCode.objects.filter(usuario=user).delete()                            
                code = ''.join(random.choices(string.digits, k=8))
                token = default_token_generator.make_token(user)
                password_reset = PasswordResetCode.objects.create(usuario=user, codigo=code, token=token)
                subject = 'Recuperação de Senha'
                message = render_to_string('email/template_password_reset.html', {'code': code})
                
                py_email = PyEmail(email)
                py_email.set_body(user.perfilusuario.nome_completo, code, request)
                py_email.enviar()

                if user is not None:    
                    uidb64 = urlsafe_base64_encode(force_bytes(user.id))
                    request.session['uidb64'] = uidb64
                    request.session.save()

                return redirect('perfil:code_verification')

            except User.DoesNotExist:
                messages.error(
                    request,
                    'Usuário não encontrado com base no email informado'
                )
                return render(request, 'perfil/password_reset.html', {'form': form})            
        else:
            messages.error(
                request,
                'Email não foi informado ou está inválido'
            )
            return render(request, 'perfil/password_reset.html', {'form': form})  