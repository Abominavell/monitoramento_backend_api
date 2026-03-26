import random
from datetime import timedelta

from django.utils import timezone

from core.models import Colaborador, DataProjeto, Inscricao, Projeto, Setor
from core.services import distribuir_vagas_proporcional


random.seed(42)


def slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")


def main() -> None:
    # Limpa apenas o domínio novo (projetos/datas/inscrições) para manter testes consistentes.
    Inscricao.objects.all().delete()
    DataProjeto.objects.all().delete()
    Projeto.objects.all().delete()

    # Garante alguns setores e colaboradores para a distribuição proporcional.
    setor_nomes = ["Sede", "Financeiro", "Jurídico", "RH", "Operações"]
    setores = []
    for nome in setor_nomes:
        setor, _ = Setor.objects.get_or_create(nome=nome)
        setores.append(setor)

    # Internos: precisamos para distribuir vagas por setor.
    internos_qtd = 30
    internos = []
    for i in range(internos_qtd):
        setor = random.choice(setores)
        c = Colaborador.objects.create(
            nome=f"Interno {i + 1}",
            setor=setor,
            is_externo=False,
        )
        internos.append(c)

    # Externos (filiais/comunidade): contam na tela, mas não na meta por setor.
    externos_qtd = 12
    externos = []
    for i in range(externos_qtd):
        c = Colaborador.objects.create(
            nome=f"Externo {i + 1} ({random.choice(['Comunidade', 'Parceria', 'OSC'])})",
            setor=None,
            is_externo=True,
        )
        externos.append(c)

    # Cria projetos com múltiplas datas/horários e soma das vagas por data igual ao total do projeto.
    projetos_qtd = 4
    for pidx in range(projetos_qtd):
        total_vagas = random.choice([40, 45, 50, 55])
        datas_qtd = random.choice([2, 3])
        project = Projeto.objects.create(
            titulo=f"Projeto {pidx + 1}",
            descricao=f"Descrição do Projeto {pidx + 1}",
            vagas_limite=total_vagas,
            ativo=True,
        )

        # Distribui total_vagas entre datas_qtd com parcelas aleatórias.
        weights = [random.random() + 0.5 for _ in range(datas_qtd)]
        weight_sum = sum(weights)
        raw = [int((w / weight_sum) * total_vagas) for w in weights]
        soma_raw = sum(raw)
        # Ajusta o saldo para fechar a soma.
        while soma_raw < total_vagas:
            raw[random.randrange(datas_qtd)] += 1
            soma_raw += 1
        while soma_raw > total_vagas:
            k = random.randrange(datas_qtd)
            if raw[k] > 1:
                raw[k] -= 1
                soma_raw -= 1

        datas = []
        base_dt = timezone.now() + timedelta(days=3 + pidx * 2)
        for didx in range(datas_qtd):
            dt = base_dt + timedelta(days=didx)
            # Variar horas/minutos para não ficarem idênticas.
            dt = dt.replace(hour=9 + didx * 2, minute=(10 + (pidx * 7 + didx * 3) % 50), second=0, microsecond=0)
            vagas_data = raw[didx]

            dp = DataProjeto.objects.create(
                projeto=project,
                data_evento=dt,
                vagas_limite=vagas_data,
                ativo=True,
                vagas_por_setor=distribuir_vagas_proporcional(vagas_data),
            )
            datas.append(dp)

        # Inscrições: escolhe colaboradores únicos por projeto e aloca entre as datas.
        # Garantimos unicidade por projeto via seleção única.
        internos_para_projeto = random.sample(internos, k=min(len(internos), random.randint(12, 22)))
        externos_para_projeto = random.sample(externos, k=min(len(externos), random.randint(4, 10)))

        participantes = internos_para_projeto + externos_para_projeto
        random.shuffle(participantes)

        for c in participantes:
            chosen_data = random.choice(datas)
            # Presença confirmada com probabilidade ~60% para ter dados nos dois lados.
            confirmado = random.random() < 0.6

            Inscricao.objects.create(
                projeto=project,
                data_projeto=chosen_data,
                colaborador=c,
                confirmado_presenca=confirmado,
            )

    print("seed_test_data.py: dados de teste criados com sucesso.")


main()

