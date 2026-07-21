from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_jobopening_job_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobseeker',
            name='qualification_course',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
