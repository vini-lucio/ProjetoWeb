from django.db import models
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from home.models import Jobs, Cidades, Estados, Paises, Bancos
from utils.imagens import redimensionar_imagem
from utils.base_models import BaseLogModel
from utils.converter import (converter_data_django_para_str_ddmmyyyy, converter_hora_django_para_str_hh24mm,
                             somar_dias_django_para_str_ddmmyyyy)
from utils.conferir_alteracao import campo_django_mudou
from utils.choices import certidao_tipos


class Cbo(models.Model):
    class Meta:
        verbose_name = 'CBO'
        verbose_name_plural = 'CBO'
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='cbo_unique_descricao',
                violation_error_message="Descrição é unico em CBO"
            ),
        ]

    numero = models.CharField("Numero", max_length=10)
    descricao = models.CharField("Descrição", max_length=70)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.numero} - {self.descricao}'


class Dissidios(BaseLogModel):
    class Meta:
        verbose_name = 'Dissidio'
        verbose_name_plural = 'Dissidios'
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'data',],
                name='dissidios_unique_job_data',
                violation_error_message="Job e Data são unicos em Dissidios"
            ),
            models.CheckConstraint(
                check=Q(dissidio_real__gte=0),
                name='dissidios_check_dissidio_real',
                violation_error_message="Dissidio Real precisa ser maior ou igual a 0"
            ),
            models.CheckConstraint(
                check=Q(dissidio_adicional__gte=0),
                name='dissidios_check_dissidio_adicional',
                violation_error_message="Dissidio Adicional precisa ser maior ou igual a 0"
            ),
        ]

    job = models.ForeignKey(Jobs, verbose_name="Job", on_delete=models.PROTECT, related_name="%(class)s")
    data = models.DateField("Data", auto_now=False, auto_now_add=False)
    dissidio_real = models.DecimalField("Dissidio Real %", max_digits=5, decimal_places=2, default=0.00)  # type:ignore
    dissidio_adicional = models.DecimalField("Dissidio Adicional %", max_digits=5, decimal_places=2,
                                             default=0.00)  # type:ignore
    observacoes = models.CharField("Observações", max_length=300, null=True, blank=True)
    aplicado = models.BooleanField("Dissidio Aplicado?", default=False)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    @property
    def data_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.data)

    data_as_ddmmyyyy.fget.short_description = 'Data'  # type:ignore

    @property
    def dissidio_total(self):
        return self.dissidio_real + self.dissidio_adicional

    dissidio_total.fget.short_description = 'Dissidio Total %'  # type:ignore

    def __str__(self) -> str:
        return f'{self.job} - {self.data_as_ddmmyyyy}'


class Escolaridades(models.Model):
    class Meta:
        verbose_name = 'Escolaridade'
        verbose_name_plural = 'Escolaridades'
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='escolaridades_unique_descricao',
                violation_error_message="Descrição é unico em Escolaridades"
            ),
        ]

    descricao = models.CharField("Descrição", max_length=70)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return self.descricao


class TransporteLinhas(models.Model):
    class Meta:
        verbose_name = 'Transporte Linha'
        verbose_name_plural = 'Transporte Linhas'
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='transportelinhas_unique_descricao',
                violation_error_message="Descrição é unico em Transporte Linhas"
            ),
        ]

    descricao = models.CharField("Descrição", max_length=50)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return self.descricao


class TransporteTipos(models.Model):
    class Meta:
        verbose_name = 'Transporte Tipo'
        verbose_name_plural = 'Transporte Tipos'
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='transportetipos_unique_descricao',
                violation_error_message="Descrição é unico em Transporte Tipos"
            ),
        ]

    descricao = models.CharField("Descrição", max_length=50)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return self.descricao


class DependentesTipos(models.Model):
    class Meta:
        verbose_name = 'Dependentes Tipo'
        verbose_name_plural = 'Dependentes Tipos'
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='dependentestipos_unique_descricao',
                violation_error_message="Descrição é unico em Dependentes Tipos"
            ),
        ]

    descricao = models.CharField("Descrição", max_length=50)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return self.descricao


class Setores(models.Model):
    class Meta:
        verbose_name = 'Setor'
        verbose_name_plural = 'Setores'
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='setores_unique_descricao',
                violation_error_message="Descrição é unico em Setores"
            ),
        ]

    plano_conta = {
        'MK': 'MK - Adm., Logistica, Comercial, etc',
        'CP': 'CP - Produção, Manutenção, etc',
        'MK/CP': 'MK/CP - Compras, Limpeza, etc',
    }

    help_text_plano_contas = "Pedir ajuda se tiver duvida em escolher, este campo interfere diretamente no custo dos produtos"

    descricao = models.CharField("Descrição", max_length=50)
    plano_contas = models.CharField("Plano de Contas", max_length=5, choices=plano_conta,  # type: ignore
                                    help_text=help_text_plano_contas)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return self.descricao


class Funcoes(models.Model):
    class Meta:
        verbose_name = 'Função'
        verbose_name_plural = 'Funções'
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='funcoes_unique_descricao',
                violation_error_message="Descrição é unico em Funções"
            ),
        ]

    cbo = models.ForeignKey(Cbo, verbose_name="CBO", on_delete=models.PROTECT, related_name="%(class)s")
    descricao = models.CharField("Descrição", max_length=70)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return self.descricao


class Horarios(models.Model):
    class Meta:
        verbose_name = 'Horario'
        verbose_name_plural = 'Horarios'
        constraints = [
            models.UniqueConstraint(
                fields=['inicio', 'intervalo_inicio', 'intervalo_fim', 'fim', 'sexta_fim',],
                name='horarios_unique_horario',
                violation_error_message="Horario é unico em Horarios"
            ),
        ]

    inicio = models.TimeField("Inicio", auto_now=False, auto_now_add=False)
    intervalo_inicio = models.TimeField("Intervalo Inicio", auto_now=False, auto_now_add=False)
    intervalo_fim = models.TimeField("Intervalo Fim", auto_now=False, auto_now_add=False)
    fim = models.TimeField("Fim", auto_now=False, auto_now_add=False)
    sexta_fim = models.TimeField("Sexta Fim", auto_now=False, auto_now_add=False)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    @property
    def horario(self):
        h_inicio = converter_hora_django_para_str_hh24mm(self.inicio)
        h_intervalo_inicio = converter_hora_django_para_str_hh24mm(self.intervalo_inicio)
        h_intervalo_fim = converter_hora_django_para_str_hh24mm(self.intervalo_fim)
        h_fim = converter_hora_django_para_str_hh24mm(self.fim)
        h_sexta_fim = converter_hora_django_para_str_hh24mm(self.sexta_fim)
        return f'Horario: {h_inicio} - {h_fim} Sexta: {h_sexta_fim}. Intervalo: {h_intervalo_inicio} - {h_intervalo_fim}'

    horario.fget.short_description = 'Horario'  # type:ignore

    @property
    def horario_inicio_fim_sexta(self):
        h_inicio = converter_hora_django_para_str_hh24mm(self.inicio)
        h_fim = converter_hora_django_para_str_hh24mm(self.fim)
        h_sexta_fim = converter_hora_django_para_str_hh24mm(self.sexta_fim)
        return f'{h_inicio} - {h_fim} / Sexta: {h_sexta_fim}'

    horario_inicio_fim_sexta.fget.short_description = 'Horario Inicio - Fim / Sexta'  # type:ignore

    @property
    def intervalo_inicio_fim(self):
        h_intervalo_inicio = converter_hora_django_para_str_hh24mm(self.intervalo_inicio)
        h_intervalo_fim = converter_hora_django_para_str_hh24mm(self.intervalo_fim)
        return f'{h_intervalo_inicio} - {h_intervalo_fim}'

    intervalo_inicio_fim.fget.short_description = 'Intervalo Inicio - Fim'  # type:ignore

    def __str__(self) -> str:
        return self.horario


class Funcionarios(BaseLogModel):
    class Meta:
        verbose_name = 'Funcionario'
        verbose_name_plural = 'Funcionarios'
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'registro',],
                name='funcionarios_unique_registro',
                violation_error_message="Job e Registro são unicos em Funcionarios"
            ),
        ]

    sexos = {
        'MASCULINO': 'Masculino',
        'FEMININO': 'Feminino',
        'OUTROS': 'Outros',
    }

    estados_civis = {
        'CASADO': 'Casado',
        'SOLTEIRO': 'Solteiro',
        'DIVORCIADO': 'Divorciado',
        'VIUVO': 'Viuvo',
        'UNIAO ESTAVEL': 'União Estavel',
    }

    cnh_categorias = {
        'A': 'A',
        'B': 'B',
        'C': 'C',
        'D': 'D',
        'E': 'E',
        'AB': 'AB',
        'AC': 'AC',
        'AD': 'AD',
        'AE': 'AE',
        'ACC': 'ACC',
    }

    certidao_tipos_funcionarios = certidao_tipos

    escolaridades_status = {
        'CURSANDO': 'Cursando',
        'INCOMPLETO': 'Incompleto',
        'COMPLETO': 'Completo',
    }

    exames_tipos = {
        'ADMISSIONAL': 'Admissional',
        'PERIODICO': 'Periodico',
        'MUDANCA DE FUNCAO': 'Mudança de Função',
    }

    contas_tipos = {
        'CORRENTE': 'Corrente',
        'POUPANCA': 'Poupança',
        'SALARIO': 'Salario',
    }

    help_text_foto = (
        "A imagem será redimensionada proporcionalmente ao incluir nova imagem para ter no maximo 500px de largura"
    )

    job = models.ForeignKey(Jobs, verbose_name="Job", on_delete=models.PROTECT, related_name="%(class)s")
    registro = models.IntegerField("Registro")
    data_entrada = models.DateField("Data Entrada", auto_now=False, auto_now_add=False)
    data_saida = models.DateField("Data Saida", auto_now=False, auto_now_add=False, null=True, blank=True)
    data_inicio_experiencia = models.DateField("Data Inicio Experiencia", auto_now=False, auto_now_add=False,
                                               null=True, blank=True)
    data_fim_experiencia = models.DateField("Data Fim Experiencia", auto_now=False, auto_now_add=False,
                                            null=True, blank=True)
    data_inicio_prorrogacao = models.DateField("Data Inicio Prorrogacao", auto_now=False, auto_now_add=False,
                                               null=True, blank=True)
    data_fim_prorrogacao = models.DateField("Data Fim Prorrogacao", auto_now=False, auto_now_add=False,
                                            null=True, blank=True)
    foto = models.ImageField("Foto", upload_to="rh/funcionarios/%Y/%m/", null=True, blank=True,
                             help_text=help_text_foto)
    nome = models.CharField("Nome", max_length=100)
    endereco = models.CharField("Endereço", max_length=100)
    numero = models.CharField("Numero", max_length=30)
    complemento = models.CharField("Complemento", max_length=30, null=True, blank=True)
    cep = models.CharField("CEP", max_length=9)
    bairro = models.CharField("Bairro", max_length=70)
    cidade = models.ForeignKey(Cidades, verbose_name="Cidade", on_delete=models.PROTECT,
                               related_name="%(class)s_cidade")
    uf = models.ForeignKey(Estados, verbose_name="Estado", on_delete=models.PROTECT, related_name="%(class)s_uf")
    pais = models.ForeignKey(Paises, verbose_name="País", on_delete=models.PROTECT, related_name="%(class)s_pais")
    data_nascimento = models.DateField("Data Nascimento", auto_now=False, auto_now_add=False)
    cidade_nascimento = models.ForeignKey(Cidades, verbose_name="Cidade Nascimento", on_delete=models.PROTECT,
                                          related_name="%(class)s_cidade_nascimento")
    uf_nascimento = models.ForeignKey(Estados, verbose_name="Estado Nascimento", on_delete=models.PROTECT,
                                      related_name="%(class)s_uf_nascimento")
    pais_nascimento = models.ForeignKey(Paises, verbose_name="País Nascimento", on_delete=models.PROTECT,
                                        related_name="%(class)s_pais_nascimento")
    sexo = models.CharField("Sexo", max_length=10, choices=sexos)  # type:ignore
    estado_civil = models.CharField("Estado Civil", max_length=20, choices=estados_civis)  # type:ignore
    fone_1 = models.CharField("Telefone 1", max_length=30)
    fone_2 = models.CharField("Telefone 2", max_length=30, null=True, blank=True)
    fone_recado = models.CharField("Telefone Recado", max_length=30, null=True, blank=True)
    email = models.EmailField("e-mail", max_length=254, null=True, blank=True)
    rg = models.CharField("RG", max_length=20)
    rg_orgao_emissor = models.CharField("RG Orgão Emissor", max_length=10, null=True, blank=True)
    cpf = models.CharField("CPF", max_length=14)
    pis = models.CharField("PIS", max_length=14, null=True, blank=True)
    carteira_profissional = models.CharField("Carteira Profissional", max_length=10, null=True, blank=True)
    carteira_profissional_serie = models.CharField("Carteira Profissional Serie", max_length=5, null=True, blank=True)
    titulo_eleitoral = models.CharField("Titutlo Eleitoral", max_length=15, null=True, blank=True)
    titulo_eleitoral_zona = models.CharField("Titutlo Eleitoral Zona", max_length=5, null=True, blank=True)
    titulo_eleitoral_sessao = models.CharField("Titutlo Eleitoral Sessao", max_length=5, null=True, blank=True)
    certificado_militar = models.CharField("Certificado Militar", max_length=15, null=True, blank=True)
    cnh = models.CharField("CNH", max_length=20, null=True, blank=True)
    cnh_categoria = models.CharField("CNH Categoria", max_length=5, null=True, blank=True,
                                     choices=cnh_categorias)  # type:ignore
    cnh_data_emissao = models.DateField("CNH Data Emissão", auto_now=False, auto_now_add=False, null=True, blank=True)
    cnh_data_vencimento = models.DateField("CNH Data Vencimento", auto_now=False, auto_now_add=False, null=True,
                                           blank=True)
    certidao_tipo = models.CharField("Certidão Tipo", max_length=10, null=True, blank=True,
                                     choices=certidao_tipos_funcionarios)  # type:ignore
    certidao_data_emissao = models.DateField("Certidão Data Emissão", auto_now=False, auto_now_add=False, null=True,
                                             blank=True)
    certidao_termo_matricula = models.CharField("Certidão Termo / Matricula", max_length=32, null=True, blank=True)
    certidao_livro = models.CharField("Certidão Livro", max_length=5, null=True, blank=True)
    certidao_folha = models.CharField("Certidão Folha", max_length=5, null=True, blank=True)
    escolaridade = models.ForeignKey(Escolaridades, verbose_name="Escolaridade", on_delete=models.PROTECT,
                                     related_name="%(class)s")
    escolaridade_status = models.CharField("Escolaridade Status", max_length=20, null=True, blank=True,
                                           choices=escolaridades_status)  # type:ignore
    data_ultimo_exame = models.DateField("Data Ultimo Exame", auto_now=False, auto_now_add=False, null=True,
                                         blank=True)
    exame_tipo = models.CharField("Exame Tipo", max_length=20, null=True, blank=True,
                                  choices=exames_tipos)  # type:ignore
    exame_observacoes = models.CharField("Exame Observações", max_length=100, null=True, blank=True)
    banco = models.ForeignKey(Bancos, verbose_name="Banco", on_delete=models.PROTECT, related_name="%(class)s",
                              null=True, blank=True)
    agencia = models.CharField("Agencia", max_length=10, null=True, blank=True)
    conta = models.CharField("Conta", max_length=10, null=True, blank=True)
    conta_tipo = models.CharField("Conta Tipo", max_length=10, null=True, blank=True,
                                  choices=contas_tipos)  # type:ignore
    observacoes_gerais = models.TextField("Observações Gerais", null=True, blank=True)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    @property
    def status(self):
        if self.data_saida:
            return "Inativo"
        return "Ativo"

    status.fget.short_description = 'Status'  # type:ignore

    def image_tag(self):
        if self.foto:
            return mark_safe(f'<img src="{self.foto.url}"/>')
        return "Sem foto"

    image_tag.short_description = 'Visualização Foto'

    def save(self, *args, **kwargs) -> None:
        foto_anteior = self.foto.name
        super_save = super().save(*args, **kwargs)

        if self.foto and self.foto.name != foto_anteior:
            if self.foto.width > 500:
                largura = 500
                redimensionar_imagem(self.foto, largura)

        return super_save

    def __str__(self) -> str:
        return f'{self.nome} - {self.status}'


class Afastamentos(BaseLogModel):
    class Meta:
        verbose_name = 'Afastamento'
        verbose_name_plural = 'Afastamentos'
        constraints = [
            models.UniqueConstraint(
                fields=['funcionario', 'data_afastamento',],
                name='afastamentos_unique_afastamento',
                violation_error_message="Afastamento é unico em Afastamentos por Funcionario"
            ),
        ]

    funcionario = models.ForeignKey(Funcionarios, verbose_name="Funcionario", on_delete=models.PROTECT,
                                    related_name="%(class)s")
    data_afastamento = models.DateField("Data Afastamento", auto_now=False, auto_now_add=False)
    data_previsao_retorno = models.DateField("Data Previsão Retorno", auto_now=False, auto_now_add=False, null=True,
                                             blank=True)
    data_retorno = models.DateField("Data Retorno", auto_now=False, auto_now_add=False, null=True, blank=True)
    motivo = models.CharField("Motivo", max_length=100)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    @property
    def data_afastamento_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.data_afastamento)

    data_afastamento_as_ddmmyyyy.fget.short_description = 'Data Afastamento'  # type:ignore

    @property
    def data_retorno_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.data_retorno)

    data_retorno_as_ddmmyyyy.fget.short_description = 'Data Retorno'  # type:ignore

    def clean(self) -> None:
        super_clean = super().clean()

        try:
            if not self.data_retorno:
                afastamentos_em_aberto = Afastamentos.objects.filter(
                    funcionario=self.funcionario, data_retorno__isnull=True).exclude(id=self.pk).count()
                if afastamentos_em_aberto >= 1:
                    raise ValidationError(
                        {'data_retorno': "Só é possivel ter um afastamento em aberto por funcionario"})  # type:ignore
        except ObjectDoesNotExist:
            raise ValidationError({'funcionario': "Funcionario é obrigatorio"})  # type:ignore

        return super_clean

    def __str__(self) -> str:
        return f'{self.funcionario} - Afastamento: {self.data_afastamento_as_ddmmyyyy}'


class Dependentes(BaseLogModel):
    class Meta:
        verbose_name = 'Dependente'
        verbose_name_plural = 'Dependentes'
        constraints = [
            models.UniqueConstraint(
                fields=['funcionario', 'dependente_tipo', 'nome',],
                name='dependentes_unique_dependente',
                violation_error_message="Nome e Tipo são unicos em Dependentes por Funcionario"
            ),
        ]

    certidao_tipos_dependentes = certidao_tipos

    funcionario = models.ForeignKey(Funcionarios, verbose_name="Funcionario", on_delete=models.PROTECT,
                                    related_name="%(class)s")
    dependente_tipo = models.ForeignKey(DependentesTipos, verbose_name="Dependente Tipo", on_delete=models.PROTECT,
                                        related_name="%(class)s")
    nome = models.CharField("Nome", max_length=100)
    data_nascimento = models.DateField("Data Nascimento", auto_now=False, auto_now_add=False, null=True, blank=True)
    rg = models.CharField("RG", max_length=20, null=True, blank=True)
    cpf = models.CharField("CPF", max_length=14, null=True, blank=True)
    certidao_tipo = models.CharField("Certidão Tipo", max_length=10, null=True, blank=True,
                                     choices=certidao_tipos_dependentes)  # type:ignore
    certidao_data_emissao = models.DateField("Certidão Data Emissão", auto_now=False, auto_now_add=False, null=True,
                                             blank=True)
    certidao_termo_matricula = models.CharField("Certidão Termo / Matricula", max_length=32, null=True, blank=True)
    certidao_livro = models.CharField("Certidão Livro", max_length=5, null=True, blank=True)
    certidao_folha = models.CharField("Certidão Folha", max_length=5, null=True, blank=True)
    dependente_ir = models.BooleanField("Dependente IR", default=False)
    observacoes = models.CharField("Observações", max_length=100, null=True, blank=True)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.funcionario} - {self.nome}'


class HorariosFuncionarios(BaseLogModel):
    class Meta:
        verbose_name = 'Horario Funcionario'
        verbose_name_plural = 'Horarios Funcionario'

    dias_horarios = {
        'SEGUNDA A SABADO, DOMINGO LIVRE': 'Segunda a sabado, domingo livre',
        'SEGUNDA A SEXTA, SABADO E DOMINGO LIVRE': 'Srgunda a sexta, sabado e domingo livre',
        'SEGUNDA A SEXTA E SABADO ALTERNADO, DOMINGO LIVRE': 'Segunda a sexta e sabado alternado, domingo livre',
    }

    funcionario = models.ForeignKey(Funcionarios, verbose_name="Funcionario", on_delete=models.PROTECT,
                                    related_name="%(class)s")
    horario = models.ForeignKey(Horarios, verbose_name="Horario", on_delete=models.PROTECT, related_name="%(class)s")
    dias = models.CharField("Dias", max_length=50, choices=dias_horarios)  # type:ignore
    data_inicio = models.DateField("Data Inicio", auto_now=False, auto_now_add=False)
    data_fim = models.DateField("Data Fim", auto_now=False, auto_now_add=False, null=True, blank=True)

    @property
    def data_inicio_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.data_inicio)

    data_inicio_as_ddmmyyyy.fget.short_description = 'Data Inicio'  # type:ignore

    @property
    def data_fim_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.data_fim)

    data_fim_as_ddmmyyyy.fget.short_description = 'Data Fim'  # type:ignore

    def clean(self) -> None:
        super_clean = super().clean()

        try:
            if not self.data_fim:
                horarios_em_aberto = HorariosFuncionarios.objects.filter(
                    funcionario=self.funcionario, data_fim__isnull=True).exclude(id=self.pk).count()
                if horarios_em_aberto >= 1:
                    raise ValidationError(
                        {'data_fim': "Só é possivel ter um horario em aberto por funcionario"})  # type:ignore
        except ObjectDoesNotExist:
            raise ValidationError({'funcionario': "Funcionario é obrigatorio"})  # type:ignore

        return super_clean

    def __str__(self) -> str:
        return f'{self.funcionario} - {self.horario}'


class Cipa(BaseLogModel):
    class Meta:
        verbose_name = 'CIPA'
        verbose_name_plural = 'CIPA'

    funcionario = models.ForeignKey(Funcionarios, verbose_name="Funcionario", on_delete=models.PROTECT,
                                    related_name="%(class)s")
    integrante_cipa_inicio = models.DateField("Integrante CIPA Inicio", auto_now=False, auto_now_add=False)
    integrante_cipa_fim = models.DateField("Integrante CIPA Fim", auto_now=False, auto_now_add=False)
    estabilidade_inicio = models.DateField("Estabilidade Inicio", auto_now=False, auto_now_add=False)
    estabilidade_fim = models.DateField("Estabilidade Fim", auto_now=False, auto_now_add=False)

    @property
    def integrante_cipa_inicio_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.integrante_cipa_inicio)

    integrante_cipa_inicio_as_ddmmyyyy.fget.short_description = 'Integrante CIPA Inicio'  # type:ignore

    @property
    def integrante_cipa_fim_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.integrante_cipa_fim)

    integrante_cipa_fim_as_ddmmyyyy.fget.short_description = 'Integrante CIPA Fim'  # type:ignore

    @property
    def estabilidade_inicio_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.estabilidade_inicio)

    estabilidade_inicio_as_ddmmyyyy.fget.short_description = 'Estabilidade Inicio'  # type:ignore

    @property
    def estabilidade_fim_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.estabilidade_fim)

    estabilidade_fim_as_ddmmyyyy.fget.short_description = 'Estabilidade Fim'  # type:ignore

    def __str__(self) -> str:
        return f'{self.funcionario} - {self.integrante_cipa_inicio_as_ddmmyyyy} - Estabilidade até: {self.estabilidade_fim_as_ddmmyyyy}'


class ValeTransportes(BaseLogModel):
    class Meta:
        verbose_name = 'Vale Transporte'
        verbose_name_plural = 'Vale Transportes'
        constraints = [
            models.UniqueConstraint(
                fields=['linha', 'tipo',],
                name='valetransportes_unique_valetransporte',
                violation_error_message="Linha e Tipo são unicos em Vale Transportes"
            ),
            models.CheckConstraint(
                check=Q(valor_unitario__gt=0),
                name='valetransportes_check_valor_unitario',
                violation_error_message="Valor Unitario precisa ser maior que 0"
            ),
            models.CheckConstraint(
                check=Q(quantidade_por_dia__gt=0),
                name='valetransportes_check_quantidade_por_dia',
                violation_error_message="Quantidade por Dia precisa ser maior que 0"
            ),
            models.CheckConstraint(
                check=Q(dias__gt=0),
                name='valetransportes_check_dias',
                violation_error_message="Dias precisa ser maior que 0"
            ),
        ]

    help_text_aviso = "Atenção! Alterar esse campo alterará todos os funcionarios ativos com essa linha e tipo"

    linha = models.ForeignKey(TransporteLinhas, verbose_name="Linha", on_delete=models.PROTECT,
                              related_name="%(class)s")
    tipo = models.ForeignKey(TransporteTipos, verbose_name="Tipo", on_delete=models.PROTECT, related_name="%(class)s")
    valor_unitario = models.DecimalField("Valor Unitario R$", max_digits=10, decimal_places=2,
                                         default=0, help_text=help_text_aviso)  # type:ignore
    quantidade_por_dia = models.DecimalField("Quantidade por Dia", max_digits=3, decimal_places=0,
                                             default=0, help_text=help_text_aviso)  # type:ignore
    dias = models.DecimalField("Dias", max_digits=3, decimal_places=0,
                               default=0, help_text=help_text_aviso)  # type:ignore
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    @property
    def valor_total(self):
        return self.valor_unitario * self.quantidade_por_dia * self.dias

    valor_total.fget.short_description = 'Valor Total R$'  # type:ignore

    def save(self, *args, **kwargs) -> None:
        mudou = campo_django_mudou(ValeTransportes, self, quantidade_por_dia=self.quantidade_por_dia, dias=self.dias)

        super_save = super().save(*args, **kwargs)

        if mudou:
            self.valetransportesfuncionarios.update(  # type:ignore
                quantidade_por_dia=self.quantidade_por_dia, dias=self.dias)

        return super_save

    def __str__(self) -> str:
        return f'{self.linha} - {self.tipo}'


class ValeTransportesFuncionarios(BaseLogModel):
    class Meta:
        verbose_name = 'Vale Transporte Funcionario'
        verbose_name_plural = 'Vale Transportes Funcionarios'
        constraints = [
            models.UniqueConstraint(
                fields=['funcionario', 'vale_transporte',],
                name='valetransportesfuncionarios_unique_valetransporte',
                violation_error_message="Vale Transporte é unico em Vale Transportes de Funcionarios"
            ),
            models.CheckConstraint(
                check=Q(quantidade_por_dia__gte=0),
                name='valetransportesfuncionarios_check_quantidade_por_dia',
                violation_error_message="Quantidade por Dia precisa ser maior ou igual a 0"
            ),
            models.CheckConstraint(
                check=Q(dias__gte=0),
                name='valetransportesfuncionarios_check_dias',
                violation_error_message="Dias precisa ser maior ou igual a 0"
            ),
        ]

    help_text_quantidade_por_dia = "Preencher 0 para usar a quantidade por dia do vale transporte"
    help_text_dias = "Preencher 0 para usar os dias do vale transporte"

    funcionario = models.ForeignKey(Funcionarios, verbose_name="Funcionario", on_delete=models.PROTECT,
                                    related_name="%(class)s")
    vale_transporte = models.ForeignKey(ValeTransportes, verbose_name="Vale Transporte", on_delete=models.PROTECT,
                                        related_name="%(class)s")
    quantidade_por_dia = models.DecimalField("Quantidade por Dia", max_digits=3, decimal_places=0,
                                             default=0, help_text=help_text_quantidade_por_dia)  # type:ignore
    dias = models.DecimalField("Dias", max_digits=3, decimal_places=0,
                               default=0, help_text=help_text_dias)  # type:ignore
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    @property
    def valor_unitario(self):
        return self.vale_transporte.valor_unitario

    valor_unitario.fget.short_description = 'Valor Unitario R$'  # type:ignore

    @property
    def valor_total(self):
        return self.vale_transporte.valor_unitario * self.quantidade_por_dia * self.dias

    valor_total.fget.short_description = 'Valor Total R$'  # type:ignore

    def save(self, *args, **kwargs) -> None:
        if self.quantidade_por_dia == 0:
            self.quantidade_por_dia = self.vale_transporte.quantidade_por_dia
        if self.dias == 0:
            self.dias = self.vale_transporte.dias
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.funcionario} - {self.vale_transporte}'


class Ferias(BaseLogModel):
    class Meta:
        verbose_name = 'Ferias'
        verbose_name_plural = 'Ferias'
        constraints = [
            models.CheckConstraint(
                check=Q(dias_ferias__gt=0),
                name='ferias_check_dias_ferias',
                violation_error_message="Dias de Ferias precisa ser maior que 0"
            ),
            models.CheckConstraint(
                check=Q(dias_desconsiderar__gte=0),
                name='ferias_check_dias_desconsiderar',
                violation_error_message="Dias Desconsiderar precisa ser maior ou igual a 0"
            ),
            models.CheckConstraint(
                check=Q(dias_abono__gte=0),
                name='ferias_check_dias_abono',
                violation_error_message="Dias Abono precisa ser maior ou igual a 0"
            ),
        ]

    funcionario = models.ForeignKey(Funcionarios, verbose_name="Funcionario", on_delete=models.PROTECT,
                                    related_name="%(class)s")
    periodo_trabalhado_inicio = models.DateField("Periodo Trabalhado Inicio", auto_now=False, auto_now_add=False)
    periodo_trabalhado_fim = models.DateField("Periodo Trabalhado Fim", auto_now=False, auto_now_add=False)
    dias_ferias = models.DecimalField("Dias de Ferias", max_digits=2, decimal_places=0, default=0)  # type:ignore
    dias_desconsiderar = models.DecimalField("Dias Desconsiderar", max_digits=2, decimal_places=0,
                                             default=0)  # type:ignore
    dias_abono = models.DecimalField("Dias Abono", max_digits=2, decimal_places=0, default=0)  # type:ignore
    antecipar_abono = models.BooleanField("Antecipar Abono", default=False)
    antecipar_13 = models.BooleanField("Antecipar 1ª parcela 13º", default=False)
    periodo_descanso_inicio = models.DateField("Periodo Descanso Inicio", auto_now=False, auto_now_add=False,
                                               null=True, blank=True)
    observacoes = models.CharField("Observações", max_length=100, null=True, blank=True)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    @property
    def periodo_trabalhado_inicio_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.periodo_trabalhado_inicio)

    periodo_trabalhado_inicio_as_ddmmyyyy.fget.short_description = 'Periodo Trabalhado Inicio'  # type:ignore

    @property
    def periodo_trabalhado_fim_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.periodo_trabalhado_fim)

    periodo_trabalhado_fim_as_ddmmyyyy.fget.short_description = 'Periodo Trabalhado Fim'  # type:ignore

    @property
    def periodo_descanso_inicio_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.periodo_descanso_inicio)

    periodo_descanso_inicio_as_ddmmyyyy.fget.short_description = 'Periodo Descanso Inicio'  # type:ignore

    @property
    def periodo_descanso_fim_as_ddmmyyyy(self):
        return somar_dias_django_para_str_ddmmyyyy(self.periodo_descanso_inicio,
                                                   self.dias_ferias + self.dias_desconsiderar - 1)

    periodo_descanso_fim_as_ddmmyyyy.fget.short_description = 'Periodo Descanso Fim'  # type:ignore

    @property
    def periodo_abono_inicio_as_ddmmyyyy(self):
        if self.dias_abono == 0:
            return ''
        if self.antecipar_abono:
            return somar_dias_django_para_str_ddmmyyyy(self.periodo_descanso_inicio, self.dias_abono * (-1))
        return somar_dias_django_para_str_ddmmyyyy(self.periodo_descanso_inicio,
                                                   self.dias_ferias + self.dias_desconsiderar)

    periodo_abono_inicio_as_ddmmyyyy.fget.short_description = 'Periodo Abono Inicio'  # type:ignore

    @property
    def periodo_abono_fim_as_ddmmyyyy(self):
        if self.dias_abono == 0:
            return ''
        if self.antecipar_abono:
            return somar_dias_django_para_str_ddmmyyyy(self.periodo_descanso_inicio, -1)
        return somar_dias_django_para_str_ddmmyyyy(self.periodo_descanso_inicio,
                                                   self.dias_ferias + self.dias_desconsiderar + self.dias_abono - 1)

    periodo_abono_fim_as_ddmmyyyy.fget.short_description = 'Periodo Abono Fim'  # type:ignore

    def clean(self) -> None:
        super_clean = super().clean()

        try:
            if not self.periodo_descanso_inicio:
                ferias_em_aberto = Ferias.objects.filter(
                    funcionario=self.funcionario, periodo_descanso_inicio__isnull=True).exclude(id=self.pk).count()
                if ferias_em_aberto >= 1:
                    raise ValidationError(
                        {'periodo_descanso_inicio': "Só é possivel ter uma ferias em aberto por funcionario"})  # type:ignore
        except ObjectDoesNotExist:
            raise ValidationError({'funcionario': "Funcionario é obrigatorio"})  # type:ignore

        return super_clean

    def __str__(self) -> str:
        return f'{self.funcionario} - Férias: {self.periodo_descanso_inicio_as_ddmmyyyy} - {self.periodo_descanso_fim_as_ddmmyyyy}'
