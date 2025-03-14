# Generated by Django 5.1 on 2025-02-19 14:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0066_alter_estados_regiao_alter_vendedores_canal_venda'),
        ('rh', '0029_alter_setores_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comissoes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_vencimento', models.DateField(blank=True, null=True, verbose_name='Data Vencimento')),
                ('data_liquidacao', models.DateField(blank=True, null=True, verbose_name='Data Liquidação')),
                ('nota_fiscal', models.IntegerField(default=0, verbose_name='Nota Fiscal')),
                ('cliente', models.CharField(blank=True, max_length=50, null=True, verbose_name='Cliente')),
                ('inclusao_orcamento', models.CharField(blank=True, max_length=50, null=True, verbose_name='Inclusão Orçamento')),
                ('especie', models.CharField(blank=True, choices=[('SAIDA', 'Saida'), ('ENTRADA', 'Entrada')], max_length=10, null=True, verbose_name='Especie')),
                ('valor_mercadorias_parcelas', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Valor Mercadorias Parcelas R$')),
                ('abatimentos_totais', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Abatimentos Totais R$')),
                ('frete_item', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Frete no Item R$')),
                ('divisao', models.BooleanField(default=False, verbose_name='Divisão')),
                ('erro', models.BooleanField(default=False, verbose_name='Erro')),
                ('infra', models.BooleanField(default=False, verbose_name='Infra')),
                ('premoldado_poste', models.BooleanField(default=False, verbose_name='Pre-Moldado / Poste')),
                ('carteira_cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_carteira_cliente', to='home.vendedores', verbose_name='Carteira Cliente')),
                ('cidade_entrega', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s', to='home.cidades', verbose_name='Cidade Entrega')),
                ('representante_cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_representante_cliente', to='home.vendedores', verbose_name='Representante Cliente')),
                ('representante_nota', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_representante_nota', to='home.vendedores', verbose_name='Representante Nota')),
                ('segundo_representante_cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_segundo_representante_cliente', to='home.vendedores', verbose_name='Segundo Representante Cliente')),
                ('segundo_representante_nota', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_segundo_representante_nota', to='home.vendedores', verbose_name='Segundo Representante Nota')),
                ('uf_cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_uf_cliente', to='home.estados', verbose_name='UF Cliente')),
                ('uf_entrega', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_uf_entrega', to='home.estados', verbose_name='UF Entrega')),
            ],
            options={
                'verbose_name': 'Comissão',
                'verbose_name_plural': 'Comissões',
            },
        ),
    ]
