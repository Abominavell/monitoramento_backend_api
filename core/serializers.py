from datetime import date
import uuid

from rest_framework import serializers

from .models import AcaoSocial, Colaborador, DataProjeto, Inscricao, Projeto, Setor
from .services import distribuir_vagas_proporcional, sync_colaborador_sede_user


class SetorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setor
        fields = ["id", "nome", "created_at"]


class ColaboradorSerializer(serializers.ModelSerializer):
    setor_id = serializers.PrimaryKeyRelatedField(
        source="setor",
        queryset=Setor.objects.all(),
        required=False,
        allow_null=True,
    )
    setores = SetorSerializer(source="setor", read_only=True)

    class Meta:
        model = Colaborador
        fields = [
            "id",
            "setor_id",
            "nome",
            "cpf",
            "data_nascimento",
            "is_externo",
            "ativo",
            "created_at",
            "setores",
        ]

    @staticmethod
    def _normalize_cpf(value: str) -> str:
        return "".join(ch for ch in value if ch.isdigit())

    def validate(self, attrs):
        setor = attrs.get("setor", getattr(self.instance, "setor", None))
        is_externo = attrs.get("is_externo", getattr(self.instance, "is_externo", False))
        cpf = attrs.get("cpf", getattr(self.instance, "cpf", None))
        data_nascimento = attrs.get("data_nascimento", getattr(self.instance, "data_nascimento", None))

        if is_externo:
            if setor is None:
                setor, _ = Setor.objects.get_or_create(nome="Sem setor")
                attrs["setor"] = setor
            if not cpf:
                attrs["cpf"] = f"EXT{uuid.uuid4().hex[:11]}"
            if not data_nascimento:
                attrs["data_nascimento"] = date(1900, 1, 1)
            return attrs

        if cpf:
            cpf_digits = self._normalize_cpf(cpf)
            if len(cpf_digits) != 11:
                raise serializers.ValidationError({"cpf": "CPF inválido. Informe 11 dígitos."})
            attrs["cpf"] = cpf_digits

        if setor is None:
            raise serializers.ValidationError({"setor_id": "Setor é obrigatório."})
        if not cpf:
            raise serializers.ValidationError({"cpf": "CPF é obrigatório."})
        if not data_nascimento:
            raise serializers.ValidationError({"data_nascimento": "Data de nascimento é obrigatória."})
        return attrs

    def create(self, validated_data):
        colaborador = super().create(validated_data)
        sync_colaborador_sede_user(colaborador)
        return colaborador

    def update(self, instance, validated_data):
        colaborador = super().update(instance, validated_data)
        sync_colaborador_sede_user(colaborador)
        return colaborador


class AcaoSocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcaoSocial
        fields = [
            "id",
            "titulo",
            "descricao",
            "data_evento",
            "vagas_limite",
            "ativo",
            "created_at",
            "vagas_por_setor",
        ]

    def validate_vagas_limite(self, value: int):
        if value <= 0:
            raise serializers.ValidationError("vagas_limite deve ser maior que zero.")
        return value

    def create(self, validated_data):
        vagas_limite = validated_data.get("vagas_limite", 0)
        data_evento = validated_data.get("data_evento")
        validated_data["vagas_por_setor"] = distribuir_vagas_proporcional(vagas_limite, data_evento)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        vagas_limite = validated_data.get("vagas_limite", instance.vagas_limite)
        data_evento = validated_data.get("data_evento", instance.data_evento)
        validated_data["vagas_por_setor"] = distribuir_vagas_proporcional(vagas_limite, data_evento)
        return super().update(instance, validated_data)


class ProjetoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Projeto
        fields = [
            "id",
            "titulo",
            "descricao",
            "vagas_limite",
            "ativo",
            "created_at",
        ]


class DataProjetoSerializer(serializers.ModelSerializer):
    projeto_id = serializers.PrimaryKeyRelatedField(source="projeto", queryset=Projeto.objects.all())
    projetos = ProjetoSerializer(source="projeto", read_only=True)

    class Meta:
        model = DataProjeto
        fields = [
            "id",
            "projeto_id",
            "data_evento",
            "vagas_limite",
            "ativo",
            "created_at",
            "vagas_por_setor",
            "projetos",
        ]

    def create(self, validated_data):
        vagas_limite = validated_data.get("vagas_limite", 0)
        validated_data["vagas_por_setor"] = distribuir_vagas_proporcional(vagas_limite)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        vagas_limite = validated_data.get("vagas_limite", instance.vagas_limite)
        validated_data["vagas_por_setor"] = distribuir_vagas_proporcional(vagas_limite)
        return super().update(instance, validated_data)


class InscricaoSerializer(serializers.ModelSerializer):
    projeto_id = serializers.PrimaryKeyRelatedField(source="projeto", queryset=Projeto.objects.all())
    data_projeto_id = serializers.PrimaryKeyRelatedField(source="data_projeto", queryset=DataProjeto.objects.all())
    colaborador_id = serializers.PrimaryKeyRelatedField(source="colaborador", queryset=Colaborador.objects.all())
    colaboradores = ColaboradorSerializer(source="colaborador", read_only=True)
    projetos = ProjetoSerializer(source="projeto", read_only=True)
    datas_projeto = DataProjetoSerializer(source="data_projeto", read_only=True)

    class Meta:
        model = Inscricao
        fields = [
            "id",
            "projeto_id",
            "data_projeto_id",
            "colaborador_id",
            "confirmado_presenca",
            "created_at",
            "colaboradores",
            "projetos",
            "datas_projeto",
        ]

    def validate(self, attrs):
        projeto = attrs.get("projeto", getattr(self.instance, "projeto", None))
        data_projeto = attrs.get("data_projeto", getattr(self.instance, "data_projeto", None))
        colaborador = attrs.get("colaborador", getattr(self.instance, "colaborador", None))

        if data_projeto and projeto and data_projeto.projeto_id != projeto.id:
            raise serializers.ValidationError("Data escolhida não pertence ao projeto selecionado.")

        if self.instance is None and Inscricao.objects.filter(projeto=projeto, colaborador=colaborador).exists():
            raise serializers.ValidationError("Inscrição duplicada: colaborador já inscrito neste projeto.")

        return attrs
