from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        # JobOpening new fields
        migrations.AddField(
            model_name='jobopening',
            name='roles_responsibilities',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='jobopening',
            name='salary_package',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='jobopening',
            name='last_date_to_apply',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='jobopening',
            name='skills',
            field=models.TextField(blank=True),
        ),
        # JobSeeker new fields
        migrations.AddField(
            model_name='jobseeker',
            name='qualification',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='jobseeker',
            name='employment_status',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='jobseeker',
            name='joining_preference',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='jobseeker',
            name='joining_months_others',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='jobseeker',
            name='current_company',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='jobseeker',
            name='current_designation',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='jobseeker',
            name='current_city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='jobseeker',
            name='expected_salary',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='jobseeker',
            name='salary_not_disclosed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jobseeker',
            name='skills',
            field=models.TextField(blank=True),
        ),
    ]
