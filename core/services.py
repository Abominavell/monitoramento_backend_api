from datetime import datetime

from django.contrib.auth.models import User
from django.utils import timezone

from .models import Colaborador, DataProjeto, Inscricao


def _setor_member_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in Colaborador.objects.filter(is_externo=False, ativo=True).exclude(setor_id=None).values("setor_id"):
        key = str(row["setor_id"])
        counts[key] = counts.get(key, 0) + 1
    return counts


def _allocate_weighted(
    vagas_limite: int,
    weights: dict[str, int],
    caps: dict[str, int] | None = None,
) -> dict[str, int]:
    total_weight = sum(v for v in weights.values() if v > 0)
    if vagas_limite <= 0 or total_weight <= 0:
        return {}

    base: dict[str, int] = {k: 0 for k, v in weights.items() if v > 0}
    restos: list[tuple[str, float]] = []

    for key, weight in weights.items():
        if weight <= 0:
            continue
        quota = (weight / total_weight) * vagas_limite
        floor_val = int(quota)
        if caps is not None:
            floor_val = min(floor_val, max(0, caps.get(key, 0)))
        base[key] = floor_val
        restos.append((key, quota - floor_val))

    assigned = sum(base.values())
    sobrando = max(0, vagas_limite - assigned)
    restos.sort(key=lambda item: item[1], reverse=True)

    while sobrando > 0 and restos:
        moved = False
        for key, _ in restos:
            if caps is not None and base[key] >= max(0, caps.get(key, 0)):
                continue
            base[key] += 1
            sobrando -= 1
            moved = True
            if sobrando <= 0:
                break
        if not moved:
            break

    return {k: v for k, v in base.items() if v > 0}


def _confirmed_unique_by_setor_no_ano(data_referencia: datetime | None) -> dict[str, int]:
    if data_referencia is None:
        ref = timezone.now()
    elif timezone.is_naive(data_referencia):
        ref = timezone.make_aware(data_referencia, timezone.get_current_timezone())
    else:
        ref = data_referencia

    year_start = ref.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    year_end = year_start.replace(year=year_start.year + 1)

    qs = (
        Inscricao.objects.filter(
            confirmado_presenca=True,
            colaborador__is_externo=False,
            colaborador__ativo=True,
            data_projeto__data_evento__gte=year_start,
            data_projeto__data_evento__lt=year_end,
            data_projeto__data_evento__lte=ref,
        )
        .exclude(colaborador__setor_id=None)
        .values("colaborador_id", "colaborador__setor_id")
        .distinct()
    )

    counts: dict[str, int] = {}
    for row in qs:
        setor_id = row["colaborador__setor_id"]
        if not setor_id:
            continue
        key = str(setor_id)
        counts[key] = counts.get(key, 0) + 1
    return counts


def distribuir_vagas_proporcional(vagas_limite: int, data_referencia: datetime | None = None) -> dict[str, int]:
    """
    Distribui vagas por setor priorizando cobertura anual:
    - 1) foca no déficit anual de cada setor (internos ativos - confirmados únicos no ano);
    - 2) se sobrar vaga após cobrir déficits, usa proporcional por tamanho do setor.
    """
    counts = _setor_member_counts()
    total_funcionarios = sum(counts.values())
    if vagas_limite <= 0 or total_funcionarios <= 0:
        return {}

    confirmados_no_ano = _confirmed_unique_by_setor_no_ano(data_referencia)
    deficits = {setor_id: max(0, counts.get(setor_id, 0) - confirmados_no_ano.get(setor_id, 0)) for setor_id in counts.keys()}

    by_deficit = _allocate_weighted(vagas_limite, deficits, caps=deficits)
    assigned = sum(by_deficit.values())
    sobrando = max(0, vagas_limite - assigned)

    if sobrando <= 0:
        return by_deficit

    by_size = _allocate_weighted(sobrando, counts)
    merged: dict[str, int] = {}
    for setor_id in counts.keys():
        total = by_deficit.get(setor_id, 0) + by_size.get(setor_id, 0)
        if total > 0:
            merged[setor_id] = total
    return merged


def recalcular_vagas_todas_acoes() -> None:
    """
    Recalcula as metas proporcionais (`vagas_por_setor`) para todas as ocorrências de projetos.

    Mantém o nome da função para compatibilidade com calls existentes em `signals.py`,
    mas agora ela atua sobre `DataProjeto`.
    """

    for data_projeto in DataProjeto.objects.all().only("id", "vagas_limite", "data_evento"):
        data_projeto.vagas_por_setor = distribuir_vagas_proporcional(data_projeto.vagas_limite, data_projeto.data_evento)
        data_projeto.save(update_fields=["vagas_por_setor"])


def sync_colaborador_sede_user(colaborador: Colaborador) -> None:
    """
    Garante existência/sincronia do usuário Django para colaborador da sede.
    Username = CPF, senha = data_nascimento (DDMMAAAA).
    """
    if colaborador.is_externo:
        return

    password = colaborador.data_nascimento.strftime("%d%m%Y")
    user, _ = User.objects.get_or_create(
        username=colaborador.cpf,
        defaults={
            "first_name": colaborador.nome[:150],
            "is_staff": False,
            "is_superuser": False,
            "is_active": True,
        },
    )
    user.first_name = colaborador.nome[:150]
    user.is_active = True
    user.set_password(password)
    user.save()
