from django.contrib import admin
from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from sistema.api import (
    DocenteViewSet, AulaViewSet, SalaViewSet, PresencaViewSet,
    FolhaPagamentoListView, FolhaPagamentoGerarView,
)
from sistema import views, views_coordenacao, views_rh

router = DefaultRouter()
router.register(r"docentes", DocenteViewSet, basename="docente")
router.register(r"aulas", AulaViewSet, basename="aula")
router.register(r"salas", SalaViewSet, basename="sala")
router.register(r"presencas", PresencaViewSet, basename="presenca")

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # API do RH
    re_path(r"^api/rh/folha-pagamento/?$", FolhaPagamentoListView.as_view(), name="api_folha_lista"),
    re_path(r"^api/rh/folha-pagamento/gerar/?$", FolhaPagamentoGerarView.as_view(), name="api_folha_gerar"),

    # API REST
    path("api/", include(router.urls)),

    # Frontend
    path("", views.pagina_inicial, name="inicio"),
    path("login/", views.pagina_login, name="login"),
    path("logout/", views.pagina_logout, name="logout"),
    path("painel/", views.painel_docente, name="painel"),
    path("aula/<int:aula_id>/", views.detalhe_aula, name="detalhe_aula"),

    # Propor Horário (Docente)
    path("propor-horario/", views.propor_horario, name="propor_horario"),

    # Ganhos do Docente
    path("ganhos/", views.pagina_ganhos, name="ganhos"),

    # Mudança de Sala (Docente)
    path("aula/<int:aula_id>/mudar-sala/", views.pedir_mudanca_sala, name="pedir_mudanca_sala"),

    # Auditoria (Superuser / Coordenação)
    path("auditoria/", views.pagina_auditoria, name="auditoria"),
    # Presenças do Docente
    path("presencas/", views.pagina_presencas, name="presencas"),
    
    # Painel da Coordenação
    path("coordenacao/", views_coordenacao.coordenacao_painel, name="coordenacao"),
    path("coordenacao/pedidos/<int:pedido_id>/decidir/", views_coordenacao.coordenacao_decidir_pedido, name="coordenacao_decidir_pedido"),
    path("coordenacao/horarios/<int:pedido_id>/decidir/", views_coordenacao.coordenacao_aprovar_horario, name="coordenacao_aprovar_horario"),
    path("coordenacao/horas/<int:hora_id>/aprovar/", views_coordenacao.coordenacao_aprovar_horas, name="coordenacao_aprovar_horas"),
    path("coordenacao/gerar-aulas/", views_coordenacao.coordenacao_gerar_aulas, name="coordenacao_gerar_aulas"),
    path("coordenacao/criar-horario/", views_coordenacao.coordenacao_criar_horario, name="coordenacao_criar_horario"),
    path("coordenacao/mudanca-sala/<int:pedido_id>/decidir/", views_coordenacao.coordenacao_aprovar_mudanca_sala, name="coordenacao_aprovar_mudanca_sala"),

    # RH (Recursos Humanos)
    path("rh/", views_rh.rh_painel, name="rh_painel"),
    path("rh/horas/<int:hora_id>/aprovar/", views_rh.rh_aprovar_horas, name="rh_aprovar_horas"),
    path("rh/gerar-folha/", views_rh.rh_gerar_folha, name="rh_gerar_folha"),
    path("rh/folha/<int:folha_id>/validar/", views_rh.rh_validar_folha, name="rh_validar_folha"),
    path("rh/folha/<int:folha_id>/pagar/", views_rh.rh_pagar_folha, name="rh_pagar_folha"),
    path("rh/exportar-excel/", views_rh.rh_exportar_excel, name="rh_exportar_excel"),

    # API AJAX
    path("ajax/aula/<int:aula_id>/iniciar/", views.api_iniciar_aula, name="api_iniciar"),
    path("ajax/aula/<int:aula_id>/validar/", views.api_validar_local, name="api_validar"),
    path("ajax/aula/<int:aula_id>/presencas/", views.api_registar_presencas, name="api_presencas"),
    path("ajax/aula/<int:aula_id>/encerrar/", views.api_encerrar_aula, name="api_encerrar"),
    path("ajax/aula/<int:aula_id>/pedir-revisao/", views.api_pedir_revisao, name="api_pedir_revisao"),
]