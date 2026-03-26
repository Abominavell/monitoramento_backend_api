import uuid

from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Setor(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class Colaborador(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    setor = models.ForeignKey(
        Setor,
        on_delete=models.PROTECT,
        related_name="colaboradores",
    )
    nome = models.CharField(max_length=160)
    cpf = models.CharField(max_length=14, unique=True)
    data_nascimento = models.DateField()
    is_externo = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class AcaoSocial(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=160)
    descricao = models.TextField(null=True, blank=True)
    data_evento = models.DateTimeField()
    vagas_limite = models.PositiveIntegerField(default=20)
    ativo = models.BooleanField(default=True)
    vagas_por_setor = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-data_evento"]

    def __str__(self) -> str:
        return self.titulo


class Projeto(TimeStampedModel):
    """
    Projeto agrupa várias datas/horários (DataProjeto).
    Um colaborador pode se inscrever apenas uma vez por projeto (independente da data).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=160)
    descricao = models.TextField(null=True, blank=True)
    vagas_limite = models.PositiveIntegerField(default=20)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.titulo


class DataProjeto(TimeStampedModel):
    """
    Uma ocorrência específica de um Projeto (data/horário) com seu próprio limite
    e meta proporcional por setor.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    projeto = models.ForeignKey(
        Projeto,
        on_delete=models.CASCADE,
        related_name="datas",
    )
    data_evento = models.DateTimeField()
    vagas_limite = models.PositiveIntegerField(default=20)
    ativo = models.BooleanField(default=True)
    vagas_por_setor = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["data_evento"]

    def __str__(self) -> str:
        return f"{self.projeto.titulo} - {self.data_evento}"


class Inscricao(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Projeto (unicidade por projeto)
    projeto = models.ForeignKey(
        Projeto,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="inscricoes",
    )
    # Data/horário escolhido (uma inscrição pertence a uma ocorrência)
    data_projeto = models.ForeignKey(
        DataProjeto,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="inscricoes",
    )
    colaborador = models.ForeignKey(
        Colaborador,
        on_delete=models.CASCADE,
        related_name="inscricoes",
    )
    confirmado_presenca = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["projeto", "colaborador"],
                name="unique_inscricao_por_colaborador_e_projeto",
            )
        ]

    def clean(self):
        # Garante integridade entre projeto e a data escolhida.
        if self.data_projeto_id and self.projeto_id:
            if self.data_projeto.projeto_id != self.projeto_id:
                from django.core.exceptions import ValidationError

                raise ValidationError({"data_projeto": "A data escolhida não pertence ao projeto selecionado."})

    def __str__(self) -> str:
        return f"{self.colaborador} - {self.projeto} ({self.data_projeto})"
