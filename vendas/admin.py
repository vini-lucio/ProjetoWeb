from django.contrib import admin
from django.http import HttpRequest
from utils.base_models import BaseModelAdminRedRequiredLog, BaseModelAdminRedRequired
from .models import RncNotas, MotivosRnc


@admin.register(MotivosRnc)
class MotivosRncAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'descricao',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'descricao',


@admin.register(RncNotas)
class RncNotasAdmin(BaseModelAdminRedRequiredLog):
    list_display = ('id', 'job__descricao', 'nota_fiscal', 'cliente', 'responsavel__nome', 'follow_up_preenchido',
                    'link_abrir_sacpm',)
    list_display_links = 'id', 'job__descricao', 'nota_fiscal', 'cliente', 'responsavel__nome', 'follow_up_preenchido',
    ordering = '-pk',
    search_fields = 'nota_fiscal', 'responsavel__nome',
    list_filter = [('follow_up', admin.EmptyFieldListFilter),]
    readonly_fields = ['criado_por', 'criado_em', 'atualizado_por', 'atualizado_em', 'cliente',
                       'descricao_cancelamento', 'link_abrir_sacpm',]

    fieldsets = (
        (None, {
            "fields": (
                'job', 'nota_fiscal', 'data', 'responsavel', 'link_abrir_sacpm',
            ),
        }),
        ('Detalhes', {
            "fields": (
                'cliente', 'origem', 'motivo', 'descricao_cancelamento', 'descricao', 'acao_imediata',
            ),
        }),
        ('Resolução', {
            "fields": (
                'custo_adicional', 'custo_recuperado', 'follow_up',
            ),
        }),
        ('Logs', {
            "fields": (
                'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em',
            ),
        }),
    )

    @admin.display(boolean=True, description='Follow-up?')
    def follow_up_preenchido(self, obj):
        return bool(obj.follow_up)

    def get_readonly_fields(self, request: HttpRequest, obj):
        """Usuarios do grupo Vendas tem restrição na edição dos campos."""
        usuario_vendas = request.user.groups.filter(name='Vendas').exists()
        campos = list(super().get_readonly_fields(request, obj))

        if not usuario_vendas:
            return campos

        campos += ['job', 'nota_fiscal', 'data', 'responsavel', 'acao_imediata', 'origem', 'motivo', 'custo_adicional',
                   'descricao']

        return campos
