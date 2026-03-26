from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AcaoSocialViewSet,
    ColaboradorViewSet,
    DataProjetoViewSet,
    InscricaoViewSet,
    ProjetoViewSet,
    SetorViewSet,
    colaborador_login,
)

router = DefaultRouter()
router.register("setores", SetorViewSet, basename="setor")
router.register("colaboradores", ColaboradorViewSet, basename="colaborador")
router.register("acoes_sociais", AcaoSocialViewSet, basename="acao-social")
router.register("projetos", ProjetoViewSet, basename="projeto")
router.register("datas_projeto", DataProjetoViewSet, basename="data-projeto")
router.register("inscricoes", InscricaoViewSet, basename="inscricao")

urlpatterns = [
    path("auth/colaborador-login/", colaborador_login, name="colaborador-login"),
    *router.urls,
]
