from django.contrib import admin

from .models import AcaoSocial, Colaborador, DataProjeto, Inscricao, Projeto, Setor


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ("nome", "created_at")
    search_fields = ("nome",)


@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf", "data_nascimento", "setor", "is_externo", "ativo", "created_at")
    list_filter = ("is_externo", "ativo", "setor")
    search_fields = ("nome", "cpf")


@admin.register(AcaoSocial)
class AcaoSocialAdmin(admin.ModelAdmin):
    list_display = ("titulo", "data_evento", "vagas_limite", "ativo", "created_at")
    list_filter = ("ativo",)
    search_fields = ("titulo", "descricao")


@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    list_display = ("projeto", "data_projeto", "colaborador", "confirmado_presenca", "created_at")
    list_filter = ("confirmado_presenca",)
    search_fields = ("projeto__titulo", "colaborador__nome")


@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "vagas_limite", "ativo", "created_at")
    list_filter = ("ativo",)
    search_fields = ("titulo", "descricao")


@admin.register(DataProjeto)
class DataProjetoAdmin(admin.ModelAdmin):
    list_display = ("projeto", "data_evento", "vagas_limite", "ativo", "created_at")
    list_filter = ("ativo",)
    search_fields = ("projeto__titulo",)
