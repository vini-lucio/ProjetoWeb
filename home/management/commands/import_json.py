import json
from pathlib import Path
from django.core.management.base import BaseCommand
# ########### alterar model do import #########################################
from rh.models import Funcionarios
# ########### alterar/comentar get do import ##################################
from utils.site_setup import get_jobs, get_escolaridades, get_cidades, get_estados, get_paises, get_bancos

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# ########### alterar/comentar get ############################################
estrangeiro_jobs = get_jobs()
estrangeiro_escolaridades = get_escolaridades()
estrangeiro_cidades = get_cidades()
estrangeiro_estados = get_estados()
estrangeiro_paises = get_paises()
estrangeiro_bancos = get_bancos()


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            # ########### alterar/comentar chave estrangeira ##################
            fk_verdadeira_job = estrangeiro_jobs.filter(chave_migracao=item['job']).first()
            fk_verdadeira_escolaridade = estrangeiro_escolaridades.filter(chave_migracao=item['escolaridade']).first()
            fk_verdadeira_cidade = estrangeiro_cidades.filter(chave_migracao=item['cidade']).first()
            fk_verdadeira_uf = estrangeiro_estados.filter(chave_migracao=item['uf']).first()
            fk_verdadeira_pais = estrangeiro_paises.filter(chave_migracao=item['pais']).first()
            fk_verdadeira_cidade_nascimento = estrangeiro_cidades.filter(
                chave_migracao=item['cidade_nascimento']).first()
            fk_verdadeira_uf_nascimento = estrangeiro_estados.filter(chave_migracao=item['uf_nascimento']).first()
            fk_verdadeira_pais_nascimento = estrangeiro_paises.filter(chave_migracao=item['pais_nascimento']).first()
            fk_verdadeira_banco = estrangeiro_bancos.filter(nome=item['banco']).first()
            # ########### alterar model do import #############################
            instancia = Funcionarios(
                # ########### alterar campos json vs model e chave estrangeira
                # ########### usar str() em float #############################
                chave_migracao=item['chave_migracao'],
                job=fk_verdadeira_job,
                escolaridade=fk_verdadeira_escolaridade,
                cidade=fk_verdadeira_cidade,
                uf=fk_verdadeira_uf,
                pais=fk_verdadeira_pais,
                cidade_nascimento=fk_verdadeira_cidade_nascimento,
                uf_nascimento=fk_verdadeira_uf_nascimento,
                pais_nascimento=fk_verdadeira_pais_nascimento,
                banco=fk_verdadeira_banco,
                registro=item['registro'],
                data_entrada=item['data_entrada'],
                data_saida=item['data_saida'],
                data_inicio_experiencia=item['data_inicio_experiencia'],
                data_fim_experiencia=item['data_fim_experiencia'],
                data_inicio_prorrogacao=item['data_inicio_prorrogacao'],
                data_fim_prorrogacao=item['data_fim_prorrogacao'],
                nome=item['nome'],
                endereco=item['endereco'],
                numero=item['numero'],
                complemento=item['complemento'],
                cep=item['cep'],
                bairro=item['bairro'],
                data_nascimento=item['data_nascimento'],
                sexo=item['sexo'],
                estado_civil=item['estado_civil'],
                fone_1=item['fone_1'],
                fone_2=item['fone_2'],
                fone_recado=item['fone_recado'],
                email=item['email'],
                rg=item['rg'],
                rg_orgao_emissor=item['rg_orgao_emissor'],
                cpf=item['cpf'],
                pis=item['pis'],
                carteira_profissional=item['carteira_profissional'],
                carteira_profissional_serie=item['carteira_profissional_serie'],
                titulo_eleitoral=item['titulo_eleitoral'],
                titulo_eleitoral_zona=item['titulo_eleitoral_zona'],
                titulo_eleitoral_sessao=item['titulo_eleitoral_sessao'],
                certificado_militar=item['certificado_militar'],
                cnh=item['cnh'],
                cnh_categoria=item['cnh_categoria'],
                cnh_data_emissao=item['cnh_data_emissao'],
                cnh_data_vencimento=item['cnh_data_vencimento'],
                certidao_tipo=item['certidao_tipo'],
                certidao_data_emissao=item['certidao_data_emissao'],
                certidao_termo_matricula=item['certidao_termo_matricula'],
                certidao_livro=item['certidao_livro'],
                certidao_folha=item['certidao_folha'],
                escolaridade_status=item['escolaridade_status'],
                agencia=item['agencia'],
                conta=item['conta'],
                conta_tipo=item['conta_tipo'],
                data_ultimo_exame=item['data_ultimo_exame'],
                exame_tipo=item['exame_tipo'],
                exame_observacoes=item['exame_observacoes'],
                observacoes_gerais=item['observacoes_gerais'],
            )
            instancia.full_clean()
            instancia.save()

        self.stdout.write(self.style.SUCCESS("Dados importados com sucesso"))
