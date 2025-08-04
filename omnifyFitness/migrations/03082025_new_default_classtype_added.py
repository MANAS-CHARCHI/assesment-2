from django.db import migrations

def create_default_class_types(apps, schema_editor):
    ClassType = apps.get_model('omnifyFitness', 'ClassType')
    default_classes = [
        {'name': 'JUMBA', 'description': 'Energetic dance fitness class'},
        {'name': 'YOGA', 'description': 'Relaxing and strength-focused'},
        {'name': 'HIIT', 'description': 'High intensity interval training'},
    ]
    for cls in default_classes:
        ClassType.objects.get_or_create(name=cls['name'], defaults={'description': cls['description']})

class Migration(migrations.Migration):

    dependencies = [
        ('omnifyFitness', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_class_types),
    ]
