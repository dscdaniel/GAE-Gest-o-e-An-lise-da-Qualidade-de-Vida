from datetime import date, time, timedelta  # Gera datas e horários dos registros fictícios.
from io import BytesIO

from django.contrib.auth import get_user_model  # Obtém o modelo de usuário configurado no projeto.
from django.contrib.auth.models import Group  # Associa o usuário de teste ao perfil gestor.
from django.core.management.base import BaseCommand  # Permite executar este arquivo via manage.py.
from django.core.files.base import ContentFile

from reportlab.pdfgen import canvas

from gestor.models import (
    AnotacaoPreConselho,
    Atestado,
    Atraso,
    Aluno,
    Empresa,
    Ocorrencia,
    Periodo,
    PreConselho,
    SaidaAntecipada,
    Telefone,
    Turma,
)


class Command(BaseCommand):
    help = 'Cria dados ficticios para testar o GAE sem duplicar registros existentes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--com-usuario',
            action='store_true',
            help='Cria os usuarios gestor.teste e professor.teste com a senha teste123.',
        )

    def handle(self, *args, **options):
        # handle é o ponto de entrada executado quando o comando é chamado no terminal.
        gestor, professor = self._obter_usuarios_teste(options['com_usuario'])
        hoje = date.today()

        periodo, _ = Periodo.objects.get_or_create(
            nome='2026.2 - Demonstracao',
            defaults={
                'data_inicio': date(2026, 7, 1),
                'data_fim': date(2026, 12, 20),
                'ativo': True,
            },
        )

        empresas = self._criar_empresas()
        turmas = self._criar_turmas(periodo, professor)
        alunos = self._criar_alunos(turmas, empresas)
        self._criar_registros(alunos, gestor, turmas, periodo, hoje)

        self.stdout.write(self.style.SUCCESS(
            'Dados de teste prontos: 1 periodo, 10 empresas, 4 turmas, 40 alunos, '
            '10 telefones, 10 atrasos, 10 ocorrencias, 10 saidas, 10 atestados e '
            '4 pre-conselhos com anotacoes para os alunos.'
        ))
        if options['com_usuario']:
            self.stdout.write('Acesso de teste: gestor.teste e professor.teste | senha teste123')

    def _obter_usuarios_teste(self, criar_usuarios):
        # Mantém os usuários opcionais para não criar credenciais em toda execução.
        if not criar_usuarios:
            return None, None

        grupo_gestor, _ = Group.objects.get_or_create(name='gestor')
        grupo_professor, _ = Group.objects.get_or_create(name='professor')
        user_model = get_user_model()
        gestor, criado = user_model.objects.get_or_create(
            username='gestor.teste',
            defaults={'first_name': 'Gestor', 'last_name': 'Teste', 'email': 'gestor.teste@example.com', 'is_staff': True},
        )
        if criado:
            gestor.set_password('teste123')
            gestor.save()
        gestor.groups.add(grupo_gestor)

        professor, criado = user_model.objects.get_or_create(
            username='professor.teste',
            defaults={'first_name': 'Professor', 'last_name': 'Teste', 'email': 'professor.teste@example.com'},
        )
        if criado:
            professor.set_password('teste123')
            professor.save()
        professor.groups.add(grupo_professor)
        return gestor, professor

    def _criar_empresas(self):
        # get_or_create permite repetir o comando sem duplicar as empresas de demonstração.
        empresas = []
        for numero in range(1, 11):
            dados_empresa = {
                'cnpj': f'00.000.026/0001-{numero:02d}',
                'nome': f'Empresa Teste GAE {numero:02d}',
                'endereco': f'Rua de Teste, {100 + numero}',
                'cidade': 'Sao Jose do Rio Preto',
                'estado': 'SP',
                'telefone': f'(17) 3200-{numero:04d}',
                'email': f'empresa{numero:02d}@example.com',
            }
            empresa, _ = Empresa.objects.get_or_create(
                cnpj=dados_empresa['cnpj'],
                defaults=dados_empresa,
            )
            empresas.append(empresa)
        return empresas

    def _criar_turmas(self, periodo, professor):
        # Vincula as turmas criadas ao período e, quando informado, ao professor de teste.
        turmas = []
        for numero in range(1, 5):
            nome = f'Teste GAE - Turma {numero:02d}'
            turma, _ = Turma.objects.get_or_create(
                nome=nome,
                periodo=periodo,
                defaults={'professor': professor, 'curso': f'Curso de Teste {numero:02d}'},
            )
            if professor:
                turma.professores.add(professor)
            turmas.append(turma)
        return turmas

    def _criar_alunos(self, turmas, empresas):
        # Distribui alunos entre turmas e empresas de forma determinística.
        alunos = []
        for numero in range(40):
            turma = turmas[numero // 10]
            matricula = f'TST2026-{numero + 1:03d}'
            aluno, _ = Aluno.objects.update_or_create(
                matricula=matricula,
                defaults={
                    'nome': f'Aluno Teste {numero + 1:02d}',
                    'email': f'aluno.teste{numero + 1:02d}@example.com',
                    'data_nascimento': date(2008 + numero % 2, 1 + numero % 12, 1 + numero % 27),
                    'endereco': 'Rua de Exemplo, 100',
                    'cidade': 'Sao Jose do Rio Preto',
                    'estado': 'SP',
                    'turma': turma,
                    'empresa': empresas[numero % len(empresas)],
                    'observacoes': 'Dado ficticio criado pelo comando popular_dados_teste.',
                },
            )
            alunos.append(aluno)
        return alunos

    def _criar_registros(self, alunos, usuario, turmas, periodo, hoje):
        # Cria exemplos associados aos alunos e reuniões com anotações por turma.
        for numero in range(10):
            aluno = alunos[numero]
            data_registro = hoje - timedelta(days=numero + 1)
            Atraso.objects.get_or_create(
                aluno=aluno,
                data_atraso=data_registro,
                hora_chegada=time(8 + numero % 4, 5 + numero),
                defaults={
                    'minutos_atraso': 5 + numero * 2,
                    'motivo': f'Registro ficticio de teste {numero + 1:02d}.',
                    'registrado_por': usuario,
                },
            )
            Ocorrencia.objects.get_or_create(
                aluno=aluno,
                data_ocorrencia=data_registro,
                tipo='comportamento' if numero % 2 == 0 else 'indisciplina',
                defaults={
                    'descricao': f'Ocorrencia ficticia para teste {numero + 1:02d}.',
                    'disciplina': 'Atividade de teste',
                    'registrado_por': usuario,
                },
            )
            SaidaAntecipada.objects.get_or_create(
                aluno=aluno,
                data_saida=data_registro,
                hora_saida=time(14 + numero % 4, 30),
                defaults={
                    'motivo': f'Saida antecipada ficticia de teste {numero + 1:02d}.',
                    'responsavel_autorizacao': 'Responsavel de teste',
                    'status': 'pendente',
                    'registrado_por': usuario,
                },
            )
            atestado, criado = Atestado.objects.get_or_create(
                aluno=aluno,
                data_atestado=data_registro,
                defaults={
                    'status': ('pendente', 'aprovado', 'rejeitado')[numero % 3],
                    'observacoes': f'Atestado ficticio para teste {numero + 1:02d}.',
                },
            )
            if criado:
                atestado.arquivo.save(
                    f'atestado_teste_{numero + 1:02d}.pdf',
                    ContentFile(self._pdf_atestado(aluno.nome, data_registro)),
                    save=True,
                )

            Telefone.objects.get_or_create(
                aluno=aluno,
                tipo='responsavel',
                numero=f'(17) 99999-{numero + 1:04d}',
                defaults={'nome_contato': f'Responsavel Teste {numero + 1:02d}'},
            )

        for indice, turma in enumerate(turmas):
            data_reuniao = hoje + timedelta(days=indice + 1)
            preconselho, _ = PreConselho.objects.get_or_create(
                turma=turma,
                data_reuniao=data_reuniao,
                defaults={
                    'periodo': periodo,
                    'observacoes_gerais': 'Pre-conselho ficticio para teste.',
                    'criado_por': usuario,
                },
            )
            for aluno in alunos[indice * 10:(indice + 1) * 10]:
                AnotacaoPreConselho.objects.get_or_create(
                    preconselho=preconselho,
                    aluno=aluno,
                    defaults={
                        'situacao': AnotacaoPreConselho.SITUACOES[indice % len(AnotacaoPreConselho.SITUACOES)][0],
                        'anotacao': f'Anotacao ficticia de teste para {aluno.nome}.',
                        'encaminhamentos': 'Acompanhamento de rotina.',
                        'registrado_por': usuario,
                    },
                )

    def _pdf_atestado(self, nome_aluno, data_atestado):
        # Gera um PDF mínimo em memória para preencher o campo de arquivo dos exemplos.
        arquivo = BytesIO()
        pagina = canvas.Canvas(arquivo)
        pagina.drawString(72, 760, 'ATESTADO FICTICIO PARA TESTE')
        pagina.drawString(72, 730, f'Aluno: {nome_aluno}')
        pagina.drawString(72, 700, f'Data: {data_atestado:%d/%m/%Y}')
        pagina.save()
        return arquivo.getvalue()
