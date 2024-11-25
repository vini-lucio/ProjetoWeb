from django.db import models
from utils.converter import converter_data_django_para_str_ddmmyyyy


class Admissoes(models.Model):
    class Meta:
        managed = False
        db_table = 'rh_admissao_view'
        verbose_name = 'Relatorio Admissão'
        verbose_name_plural = 'Relatorio Admissões'

    id = models.IntegerField(primary_key=True)
    job = models.CharField("Job", max_length=30, null=True, blank=True)
    registro = models.IntegerField("Registro", null=True, blank=True)
    nome = models.CharField("Nome", max_length=100, null=True, blank=True)
    mes_entrada = models.DecimalField("Mes Entrada", max_digits=2, decimal_places=0, null=True, blank=True)
    data_entrada = models.DateField("Data Entrada", auto_now=False, auto_now_add=False, null=True, blank=True)
    tempo_casa_anos = models.DecimalField("Tempo Casa Anos", max_digits=5, decimal_places=1, null=True, blank=True)

    @property
    def data_entrada_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.data_entrada)

    data_entrada_as_ddmmyyyy.fget.short_description = 'Data Entrada'  # type:ignore

    def __str__(self) -> str:
        return f'{self.job} - {self.nome} - {self.data_entrada} - {self.tempo_casa_anos} anos'


class Aniversariantes(models.Model):
    class Meta:
        managed = False
        db_table = 'rh_aniversariantes_view'
        verbose_name = 'Relatorio Aniversariante'
        verbose_name_plural = 'Relatorio Aniversariantes'

    id = models.IntegerField(primary_key=True)
    job = models.CharField("Job", max_length=30, null=True, blank=True)
    nome = models.CharField("Nome", max_length=100, null=True, blank=True)
    mes_nascimento = models.DecimalField("Mes Nascimento", max_digits=2, decimal_places=0, null=True, blank=True)
    data_nascimento = models.DateField("Data Nascimento", auto_now=False, auto_now_add=False, null=True, blank=True)

    @property
    def data_nascimento_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.data_nascimento)

    data_nascimento_as_ddmmyyyy.fget.short_description = 'Data Nascimento'  # type:ignore

    def __str__(self) -> str:
        return f'{self.job} - {self.nome} - {self.data_nascimento}'


class Dependentes(models.Model):
    class Meta:
        managed = False
        db_table = 'rh_dependentes_view'
        verbose_name = 'Relatorio Dependente'
        verbose_name_plural = 'Relatorio Dependentes'

    id = models.IntegerField(primary_key=True)
    job = models.CharField("Job", max_length=30, null=True, blank=True)
    nome = models.CharField("Nome", max_length=100, null=True, blank=True)
    sexo = models.CharField("Sexo", max_length=10, null=True, blank=True)
    nome_dependente = models.CharField("Nome Dependente", max_length=100, null=True, blank=True)
    data_nascimento = models.DateField("Data Nascimento", auto_now=False, auto_now_add=False, null=True, blank=True)
    idade = models.DecimalField("Idade", max_digits=5, decimal_places=2, null=True, blank=True)
    crianca = models.BooleanField("Criança", null=True, blank=True)

    @property
    def data_nascimento_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.data_nascimento)

    data_nascimento_as_ddmmyyyy.fget.short_description = 'Data Nascimento'  # type:ignore

    def __str__(self) -> str:
        return f'{self.job} - {self.nome} - {self.nome_dependente}'


class FuncionariosListagem(models.Model):
    class Meta:
        managed = False
        db_table = 'rh_listagem_funcionarios_view'
        verbose_name = 'Listagem Funcionario'
        verbose_name_plural = 'Listagem Funcionarios'

    id = models.IntegerField(primary_key=True)
    job = models.CharField("Job", max_length=30, null=True, blank=True)
    nome = models.CharField("Nome", max_length=100, null=True, blank=True)
    funcao = models.CharField("Função", max_length=70, null=True, blank=True)
    sexo = models.CharField("Sexo", max_length=10, null=True, blank=True)
    data_nascimento = models.DateField("Data Nascimento", auto_now=False, auto_now_add=False, null=True, blank=True)
    rg = models.CharField("RG", max_length=20, null=True, blank=True)
    membro_cipa = models.BooleanField("Membro CIPA", null=True, blank=True)

    @property
    def data_nascimento_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.data_nascimento)

    data_nascimento_as_ddmmyyyy.fget.short_description = 'Data Nascimento'  # type:ignore

    def __str__(self) -> str:
        return f'{self.job} - {self.nome}'


class FuncionariosSalarioFuncaoAtual(models.Model):
    class Meta:
        managed = False
        db_table = 'rh_salario_funcao_atual_view'
        verbose_name = 'Relatorio Salario Função Atual de Funcionarios'
        verbose_name_plural = 'Relatorio Salario Função Atual de Funcionarios'

    id = models.IntegerField(primary_key=True)
    job = models.CharField("Job", max_length=30, null=True, blank=True)
    nome = models.CharField("Nome", max_length=100, null=True, blank=True)
    data_entrada = models.DateField("Data Nascimento", auto_now=False, auto_now_add=False, null=True, blank=True)
    funcao = models.CharField("Função", max_length=70, null=True, blank=True)
    salario = models.DecimalField("Salario", max_digits=10, decimal_places=2)
    salario_convertido = models.DecimalField("Salario Convertido (*220h)", max_digits=10, decimal_places=2)
    comissao_carteira = models.DecimalField("Comissão Carteira %", max_digits=7, decimal_places=4)
    comissao_dupla = models.DecimalField("Comissão Dupla %", max_digits=7, decimal_places=4)
    comissao_geral = models.DecimalField("Comissão Geral %", max_digits=7, decimal_places=4)

    @property
    def data_entrada_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.data_entrada)

    data_entrada_as_ddmmyyyy.fget.short_description = 'Data Entrada'  # type:ignore

    def __str__(self) -> str:
        return f'{self.job} - {self.nome} - R$ {self.salario} (*220h {self.salario_convertido})'


class FuncionariosHistoricoSalarios(models.Model):
    class Meta:
        managed = False
        db_table = 'rh_historico_salarios_view'
        verbose_name = 'Relatorio Historico de Salarios de Funcionarios'
        verbose_name_plural = 'Relatorio Historico de Salarios de Funcionarios'

    id = models.IntegerField(primary_key=True)
    job = models.CharField("Job", max_length=30, null=True, blank=True)
    nome = models.CharField("Nome", max_length=100, null=True, blank=True)
    data_entrada = models.DateField("Data Nascimento", auto_now=False, auto_now_add=False, null=True, blank=True)
    data_salario = models.DateField("Data Salario", auto_now=False, auto_now_add=False, null=True, blank=True)
    setor = models.CharField("Setor", max_length=50, null=True, blank=True)
    funcao = models.CharField("Função", max_length=70, null=True, blank=True)
    motivo = models.CharField("Motivo", max_length=30, null=True, blank=True)
    modalidade = models.CharField("Modalidade", max_length=20, null=True, blank=True)
    salario = models.DecimalField("Salario", max_digits=10, decimal_places=2)
    salario_convertido = models.DecimalField("Salario Convertido (*220h)", max_digits=10, decimal_places=2)
    comissao_carteira = models.DecimalField("Comissão Carteira %", max_digits=7, decimal_places=4)
    comissao_dupla = models.DecimalField("Comissão Dupla %", max_digits=7, decimal_places=4)
    comissao_geral = models.DecimalField("Comissão Geral %", max_digits=7, decimal_places=4)
    observacoes = models.CharField("Observações", max_length=100, null=True, blank=True)

    @property
    def data_entrada_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.data_entrada)

    data_entrada_as_ddmmyyyy.fget.short_description = 'Data Entrada'  # type:ignore

    @property
    def data_salario_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.data_salario)

    data_salario_as_ddmmyyyy.fget.short_description = 'Data Salario'  # type:ignore

    def __str__(self) -> str:
        return f'{self.job} - {self.nome} - R$ {self.salario} (*220h {self.salario_convertido})'


class FuncionariosQuadroHorarios(models.Model):
    class Meta:
        managed = False
        db_table = 'rh_quadro_horarios_view'
        verbose_name = 'Quadro de Horarios de Funcionarios'
        verbose_name_plural = 'Quadro de Horarios de Funcionarios'

    id = models.IntegerField(primary_key=True)
    job = models.CharField("Job", max_length=30, null=True, blank=True)
    registro = models.IntegerField("Registro", null=True, blank=True)
    nome = models.CharField("Nome", max_length=100, null=True, blank=True)
    carteira_profissional = models.CharField("Carteira Profissional", max_length=10, null=True, blank=True)
    setor = models.CharField("Setor", max_length=50, null=True, blank=True)
    funcao = models.CharField("Função", max_length=70, null=True, blank=True)
    horario = models.CharField("Horario", max_length=20, null=True, blank=True)
    almoco = models.CharField("Almoço", max_length=20, null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.job} - {self.nome} - Horario: {self.horario} - Almoço: {self.almoco})'
