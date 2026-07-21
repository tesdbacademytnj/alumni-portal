from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_rename_default_code_adminprofile_access_code_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='current_company',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='customuser',
            name='designation',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='customuser',
            name='domain',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='customuser',
            name='experience_years',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='customuser',
            name='salary',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='customuser',
            name='skills',
            field=models.TextField(blank=True),
        ),
    ]
