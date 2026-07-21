from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0002_jobopening_extra_fields_jobseeker_extra_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobopening',
            name='job_type',
            field=models.CharField(
                blank=True,
                max_length=20,
                choices=[
                    ('Full Time', 'Full Time'),
                    ('Part Time', 'Part Time'),
                    ('Contract', 'Contract'),
                    ('Internship', 'Internship'),
                    ('Remote', 'Remote'),
                    ('Hybrid', 'Hybrid'),
                ],
                default='Full Time',
            ),
        ),
    ]

# Note: also add qualification_course to JobSeeker
