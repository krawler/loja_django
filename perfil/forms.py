from django import forms
from django.db.models import DateField
from django.contrib.auth.models import User
from . import models

class PerfilForm(forms.ModelForm):
    
    def __init__(self, perfil=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.perfil = perfil
         
    class Meta:
        model = models.PerfilUsuario
        fields = ('idade', 'data_nascimento', 'cpf', 'endereco', 'numero', 'complemento', 
                  'bairro', 'cep', 'cidade', 'estado')

class UserForm(forms.ModelForm):
    
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(),
        label='Senha',
        help_text='Usuario logados podem deixar esse campo em branco para manter a senha'
    )
    password2 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(),
        label='Confirmação de senha',
        help_text='Digite a senha igual ao campo acima'
    )
    
    def __init__(self, usuario=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario        
        
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'password', 'password2', 'email')
    
    def clean(self, *args, **kwargs):
        data = self.data
        cleaned = self.cleaned_data
        validation_error_msgs = {}
        
        first_name = data.get('first_name')
        last_name =  data.get('last_name')
        usuario_data = data.get('username')
        password_data = data.get('password')
        password2_data = data.get('password2')
        email_data = cleaned.get('email')
        
        usuario_db = User.objects.filter(username=usuario_data).first()
        email_db = User.objects.filter(email=email_data).first()
        
        error_msg_user_exists = 'Usuário já existe'
        error_msg_email_exists = 'Email já existe'
        error_msg_password_empty = 'Senha precisa ser informada'
        error_msg_firstname_empty = 'Primeiro nome precisa ser informado'
        error_msg_password_match = 'As duas senhas não conferem'
        error_msg_password_short = 'A senha precisa de pelo menos 6 caracteres'
        
        if self.usuario:
            
            if password_data:
                if password_data != password2_data:
                    validation_error_msgs['password'] = error_msg_password_match
                    validation_error_msgs['password2'] = error_msg_password_match
                if len(password_data) < 6:
                    validation_error_msgs['password'] = error_msg_password_match
        else:
            if email_db:
                if email_data == email_db.email:                
                    validation_error_msgs['email'] = error_msg_email_exists
            
            if usuario_db:
                validation_error_msgs['username'] = error_msg_user_exists
           
            if not password_data:
                validation_error_msgs['password'] = error_msg_password_empty            
            
            if not password2_data:
                validation_error_msgs['password2'] = error_msg_password_empty            
        
        if validation_error_msgs:
            raise(forms.ValidationError(validation_error_msgs))