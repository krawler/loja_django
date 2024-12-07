# Generated by Django 5.0.6 on 2024-11-29 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perfil', '0003_alter_perfilusuario_data_nascimento'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='perfilusuario',
            name='data_nascimento',
        ),
        migrations.RemoveField(
            model_name='perfilusuario',
            name='idade',
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='nome_completo',
            field=models.CharField(default='sem nome', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='telefone',
            field=models.CharField(default=1, max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='perfilusuario',
            name='cpf',
            field=models.CharField(blank=True, max_length=14, null=True),
        ),
    ]
