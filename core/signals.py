from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Colaborador
from .services import recalcular_vagas_todas_acoes, sync_colaborador_sede_user


@receiver(post_save, sender=Colaborador)
def recalculate_targets_on_colaborador_save(sender, instance, **kwargs):
    sync_colaborador_sede_user(instance)
    recalcular_vagas_todas_acoes()


@receiver(post_delete, sender=Colaborador)
def recalculate_targets_on_colaborador_delete(sender, instance, **kwargs):
    recalcular_vagas_todas_acoes()
