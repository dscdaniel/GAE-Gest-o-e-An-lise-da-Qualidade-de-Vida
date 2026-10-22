from django.conf import settings
from django.db import migrations, models


# Copia os professores do vínculo único antigo para a nova relação múltipla.
def copiar_professores_antigos(apps, schema_editor):
    Turma = apps.get_model('gestor', 'Turma')
    for turma in Turma.objects.exclude(professor__isnull=True):
        turma.professores.add(turma.professor_id)


# Adiciona professores múltiplos à turma e migra os vínculos existentes.
class Migration(migrations.Migration):
    dependencies = [
        ('gestor', '0003_saidaantecipada_autorizado_por_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='turma',
            name='professores',
            field=models.ManyToManyField(blank=True, related_name='turmas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(copiar_professores_antigos, migrations.RunPython.noop),
    ]