from datetime import date, time, timedelta  # Cria datas e horários previsíveis nos testes.
from io import BytesIO  # Mantém arquivos de teste em memória, sem criar arquivos temporários.
from tempfile import TemporaryDirectory

from django.contrib.auth.models import Group, User  # Cria usuários e grupos para testar permissões.
from django.core.files.uploadedfile import SimpleUploadedFile  # Simula uploads durante os testes.
from django.test import TestCase, override_settings  # Isola cada teste em um banco temporário.
from django.urls import reverse  # Obtém URLs pelos nomes usados no projeto.
from openpyxl import Workbook  # Cria planilhas de teste para o fluxo de importação.

from .models import (
    AnotacaoPreConselho,
    Atraso,
    Aluno,
    Atestado,
    DocumentoAtestado,
    Empresa,
    PastaAtestado,
    Periodo,
    PreConselho,
    SaidaAntecipada,
    Turma,
)


class GestorViewsTests(TestCase):
    # Testa permissões por perfil, fluxos de cadastro e integridade dos registros relacionados.
    def setUp(self):
    # setUp é executado antes de cada teste para montar um cenário independente.
        grupo_gestor, _ = Group.objects.get_or_create(name='gestor')
        grupo_professor, _ = Group.objects.get_or_create(name='professor')
        self.user = User.objects.create_user('gestor', password='senha-segura')
        self.user.groups.add(grupo_gestor)
        self.professor = User.objects.create_user('professor', password='senha-segura')
        self.professor.groups.add(grupo_professor)

        periodo = Periodo.objects.create(
            nome='2026.2', data_inicio=date(2026, 7, 1), data_fim=date(2026, 12, 20)
        )
        self.turma = Turma.objects.create(nome='T-01', periodo=periodo, professor=self.professor)
        empresa = Empresa.objects.create(
            nome='Empresa Teste', cnpj='12.345.678/0001-90', endereco='Rua Teste',
            cidade='São Paulo', estado='SP', telefone='11999999999', email='teste@empresa.com'
        )
        self.aluno = Aluno.objects.create(
            nome='Aluno Teste', matricula='2026001', email='aluno@example.com',
            data_nascimento=date(2010, 1, 1), endereco='Rua Teste', cidade='São Paulo',
            estado='SP', turma=self.turma, empresa=empresa
        )
        self.saida = SaidaAntecipada.objects.create(
            aluno=self.aluno, data_saida=date.today(), hora_saida=time(12, 0),
            motivo='Consulta', responsavel_autorizacao='Responsável', registrado_por=self.user
        )
        self.atraso = Atraso.objects.create(
            aluno=self.aluno, data_atraso=date.today(), hora_chegada=time(8, 15),
            minutos_atraso=15, motivo='Transporte', registrado_por=self.user
        )
        self.atestado = Atestado.objects.create(
            aluno=self.aluno, arquivo='atestados/teste.pdf', data_atestado=date.today()
        )
        self.client.force_login(self.user)

    def test_professor_can_only_view_allowed_modules(self):
        self.client.force_login(self.professor)
        urls_permitidas = [
            reverse('lista_alunos'),
            reverse('detalhe_aluno', args=[self.aluno.pk]),
            reverse('lista_turmas'),
            reverse('lista_atrasos'),
            reverse('lista_ocorrencias'),
            reverse('registrar_ocorrencia'),
        ]
        # subTest identifica a rota específica caso uma permissão deixe de funcionar.
        for url in urls_permitidas:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_atraso_alerta_aparece_com_tres_registros_e_gestor_pode_remover(self):
        for minuto in (20, 25):
            Atraso.objects.create(
                aluno=self.aluno,
                data_atraso=date.today() - timedelta(days=1),
                hora_chegada=time(8, minuto),
                minutos_atraso=minuto,
                registrado_por=self.user,
            )

        url_lista = reverse('lista_atrasos')
        resposta = self.client.get(url_lista, {'data': date.today().isoformat()})
        self.assertContains(resposta, 'atraso-alerta')
        self.assertContains(resposta, '3 atrasos')

        resposta = self.client.post(
            reverse('alterar_alerta_atrasos', args=[self.aluno.pk]),
            {'acao': 'remover'},
        )
        self.assertRedirects(resposta, url_lista)
        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.atrasos_alerta_limpo_ate, 3)
        self.assertNotContains(self.client.get(url_lista), 'atraso-alerta')

        for minuto in (30, 35, 40):
            Atraso.objects.create(
                aluno=self.aluno,
                data_atraso=date.today(),
                hora_chegada=time(8, minuto),
                minutos_atraso=minuto,
                registrado_por=self.user,
            )
        self.assertContains(self.client.get(url_lista), 'atraso-alerta')

    def test_gestor_pode_ativar_alerta_manual_e_remover_depois(self):
        url = reverse('alterar_alerta_atrasos', args=[self.aluno.pk])
        url_lista = reverse('lista_atrasos')

        self.assertContains(self.client.get(url_lista), 'Colocar alerta')

        resposta = self.client.post(url, {'acao': 'ativar'})
        self.assertRedirects(resposta, url_lista)
        self.aluno.refresh_from_db()
        self.assertTrue(self.aluno.alerta_atrasos_manual)
        lista_com_alerta = self.client.get(url_lista)
        self.assertContains(lista_com_alerta, 'atraso-alerta')
        self.assertContains(lista_com_alerta, 'Remover alerta')

        resposta = self.client.post(url, {'acao': 'remover'})
        self.assertRedirects(resposta, url_lista)
        self.aluno.refresh_from_db()
        self.assertFalse(self.aluno.alerta_atrasos_manual)
        self.assertNotContains(self.client.get(url_lista), 'atraso-alerta')

    def test_professor_nao_pode_alterar_alerta_de_atrasos(self):
        for minuto in (20, 25):
            Atraso.objects.create(
                aluno=self.aluno,
                data_atraso=date.today(),
                hora_chegada=time(8, minuto),
                minutos_atraso=minuto,
                registrado_por=self.user,
            )

        self.client.force_login(self.professor)
        resposta = self.client.post(
            reverse('alterar_alerta_atrasos', args=[self.aluno.pk]),
            {'acao': 'ativar'},
        )

        self.assertEqual(resposta.status_code, 403)
        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.atrasos_alerta_limpo_ate, 0)
        self.assertFalse(self.aluno.alerta_atrasos_manual)

    def test_lista_atrasos_agrupa_registros_e_expande_detalhes_do_aluno(self):
        for minuto in (20, 25):
            Atraso.objects.create(
                aluno=self.aluno,
                data_atraso=date.today(),
                hora_chegada=time(8, minuto),
                minutos_atraso=minuto,
                registrado_por=self.user,
            )

        resposta = self.client.get(reverse('lista_atrasos'))
        conteudo = resposta.content.decode()

        self.assertEqual(conteudo.count(self.aluno.nome), 1)
        self.assertContains(resposta, '<details class="atraso-aluno">')
        self.assertContains(resposta, '3 atrasos')
        self.assertContains(resposta, '08:15')
        self.assertContains(resposta, '08:20')
        self.assertContains(resposta, '08:25')

    def test_professor_without_turma_assignment_still_can_see_students(self):
        self.client.force_login(self.professor)
        resposta = self.client.get(reverse('lista_alunos'))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, self.aluno.nome)

    def test_professor_can_only_add_preconselho_observations_for_assigned_turma(self):
        # Confirma que o professor acessa apenas reunião existente e não altera campos de gestor.
        self.client.force_login(self.professor)
        lista_url = reverse('preconselho_turmas')
        resposta_lista = self.client.get(lista_url)
        self.assertEqual(resposta_lista.status_code, 200)
        self.assertContains(resposta_lista, self.turma.nome)
        self.assertContains(resposta_lista, lista_url)
        self.assertNotContains(resposta_lista, reverse('dashboard'))

        turma_nao_atribuida = Turma.objects.create(nome='T-02', periodo=self.turma.periodo)
        self.assertEqual(
            self.client.get(reverse('preconselho_turma', args=[turma_nao_atribuida.pk])).status_code,
            404,
        )

        url = reverse('preconselho_turma', args=[self.turma.pk])
        data = date.today()
        resposta_sem_reuniao = self.client.get(url)
        self.assertEqual(resposta_sem_reuniao.status_code, 404)
        self.assertFalse(PreConselho.objects.filter(turma=self.turma, data_reuniao=data).exists())
        PreConselho.objects.create(
            turma=self.turma,
            data_reuniao=data,
            periodo=self.turma.periodo,
            criado_por=self.user,
        )

        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(resposta, 'Excluir esta reunião')
        self.assertNotContains(resposta, 'Situacao')
        self.assertNotContains(resposta, 'Encaminhamentos')

        # Envia também campos privilegiados para garantir que o servidor ignore dados não autorizados.
        resposta_post = self.client.post(url, {
            'data': data.isoformat(),
            'status': 'fechado',
            'observacoes_gerais': 'Observação geral feita pelo professor.',
            f'aluno{self.aluno.pk}-situacao': 'critico',
            f'aluno{self.aluno.pk}-anotacao': 'Observação individual feita pelo professor.',
            f'aluno{self.aluno.pk}-encaminhamentos': 'Campo que o professor não pode alterar.',
        })
        self.assertRedirects(resposta_post, f'{url}?data={data.isoformat()}')

        preconselho = PreConselho.objects.get(turma=self.turma, data_reuniao=data)
        self.assertEqual(preconselho.status, 'aberto')
        self.assertEqual(preconselho.observacoes_gerais, 'Observação geral feita pelo professor.')
        anotacao = AnotacaoPreConselho.objects.get(preconselho=preconselho, aluno=self.aluno)
        self.assertEqual(anotacao.anotacao, 'Observação individual feita pelo professor.')
        self.assertEqual(anotacao.situacao, 'satisfatorio')
        self.assertEqual(anotacao.encaminhamentos, '')

    def test_professor_cannot_delete_preconselho(self):
        preconselho = PreConselho.objects.create(
            turma=self.turma,
            data_reuniao=date.today(),
            periodo=self.turma.periodo,
        )
        self.client.force_login(self.professor)

        resposta = self.client.post(reverse('preconselho_excluir', args=[preconselho.pk]))

        self.assertEqual(resposta.status_code, 403)
        self.assertTrue(PreConselho.objects.filter(pk=preconselho.pk).exists())

    def test_gestor_keeps_preconselho_management_controls(self):
        self.client.force_login(self.user)

        resposta = self.client.get(reverse('preconselho_turma', args=[self.turma.pk]))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Excluir esta reunião')
        self.assertContains(resposta, 'Encaminhamentos')
    #Testar se o professor consegue criar ou editar registros restritos, como alunos, turmas, atrasos, empresas, saídas antecipadas, atestados e relatórios.
    def test_professor_cannot_create_or_edit_restricted_records(self):
        self.client.force_login(self.professor)
        # Reúne áreas administrativas para garantir que todas respondam 403 ao professor.
        urls_bloqueadas = [
            reverse('criar_aluno'),
            reverse('criar_turma'),
            reverse('registrar_atraso'),
            reverse('editar_atraso', args=[self.atraso.pk]),
            reverse('lista_empresas'),
            reverse('lista_saidas'),
            reverse('lista_atestados'),
            reverse('registrar_atestado'),
            reverse('lista_relatorios'),
            reverse('dashboard'),
        ]
        for url in urls_bloqueadas:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_professor_can_create_but_not_edit_occurrence(self):
        self.client.force_login(self.professor)
        resposta = self.client.post(reverse('registrar_ocorrencia'), {
            'aluno': self.aluno.pk,
            'data_ocorrencia': date.today(),
            'tipo': 'outro',
            'descricao': 'Ocorrência registrada pelo professor.',
        })
        self.assertRedirects(resposta, reverse('lista_ocorrencias'))

        ocorrencia = self.aluno.ocorrencias.order_by('-pk').first()
        self.assertEqual(ocorrencia.registrado_por, self.professor)
        self.assertEqual(
            self.client.get(reverse('editar_ocorrencia', args=[ocorrencia.pk])).status_code,
            403,
        )

    def test_principal_pages_are_available_to_professor(self):
        urls = [
            reverse('dashboard'), reverse('lista_alunos'), reverse('detalhe_aluno', args=[self.aluno.pk]),
            reverse('lista_turmas'), reverse('criar_turma'),
            reverse('lista_empresas'), reverse('criar_empresa'),
            reverse('lista_atrasos'), reverse('lista_ocorrencias'), reverse('lista_saidas'),
            reverse('lista_atestados'), reverse('lista_relatorios'),
            reverse('relatorio_aluno', args=[self.aluno.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_relatorio_aluno_renderiza_abas_acessiveis_para_todas_as_categorias(self):
        resposta = self.client.get(reverse('relatorio_aluno', args=[self.aluno.pk]))

        # Confirma que cada link controla seu painel e não depende do JavaScript do Bootstrap.
        for categoria in ('atrasos', 'ocorrencias', 'saidas', 'atestados'):
            with self.subTest(categoria=categoria):
                self.assertContains(resposta, f'href="#{categoria}" role="tab"')
                self.assertContains(resposta, f'aria-controls="{categoria}"')
                self.assertContains(resposta, f'id="{categoria}" class="tab-pane')
        self.assertContains(resposta, "window.addEventListener('popstate'")

    def test_sidebar_links_to_cadastros_and_reports(self):
        resposta = self.client.get(reverse('dashboard'))

        self.assertContains(resposta, reverse('dashboard'))
        self.assertContains(resposta, reverse('lista_turmas'))
        self.assertContains(resposta, reverse('lista_empresas'))
        self.assertContains(resposta, reverse('lista_relatorios'))

    def test_turma_and_empresa_can_be_created(self):
        periodo = Periodo.objects.first()

        resposta_turma = self.client.post(reverse('criar_turma'), {
            'nome': 'T-02',
            'periodo': periodo.pk,
            'professor': self.user.pk,
        })
        self.assertRedirects(resposta_turma, reverse('lista_turmas'))
        self.assertTrue(Turma.objects.filter(nome='T-02').exists())

        resposta_empresa = self.client.post(reverse('criar_empresa'), {
            'nome': 'Nova Empresa',
            'cnpj': '98.765.432/0001-10',
            'endereco': 'Rua Nova, 100',
            'cidade': 'Sao Paulo',
            'estado': 'SP',
            'telefone': '(11) 99999-9999',
            'email': 'contato@novaempresa.com',
        })
        self.assertRedirects(resposta_empresa, reverse('lista_empresas'))
        self.assertTrue(Empresa.objects.filter(cnpj='98.765.432/0001-10').exists())

    def criar_planilha_alunos(self, linhas):
        # Monta uma planilha em memória para exercitar a importação sem arquivos no disco.
        planilha = Workbook()
        aba = planilha.active
        aba.append([
            'matricula', 'nome', 'email', 'data_nascimento', 'endereco',
            'cidade', 'estado', 'turma', 'empresa', 'observacoes',
        ])
        for linha in linhas:
            aba.append(linha)

        arquivo = BytesIO()
        planilha.save(arquivo)
        return SimpleUploadedFile(
            'alunos.xlsx',
            arquivo.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    def test_planilha_de_alunos_importa_registros_validos(self):
        resposta = self.client.post(reverse('importar_alunos'), {
            'arquivo': self.criar_planilha_alunos([[
                '2027001', 'Maria Importada', 'maria.importada@example.com', date(2009, 2, 3),
                'Rua Nova, 200', 'Sao Paulo', 'SP', 'T-01', 'Empresa Teste', 'Importado do Excel',
            ]]),
        })

        self.assertRedirects(resposta, reverse('lista_alunos'))
        aluno = Aluno.objects.get(matricula='2027001')
        self.assertEqual(aluno.nome, 'Maria Importada')
        self.assertEqual(aluno.turma.nome, 'T-01')
        self.assertEqual(aluno.empresa.nome, 'Empresa Teste')

    def test_planilha_com_erro_nao_importa_parcialmente(self):
        resposta = self.client.post(reverse('importar_alunos'), {
            'arquivo': self.criar_planilha_alunos([
                [
                    '2027002', 'Aluno Valido', 'valido@example.com', date(2009, 2, 3),
                    'Rua Nova, 200', 'Sao Paulo', 'SP', 'T-01', 'Empresa Teste', '',
                ],
                [
                    '2027003', 'Aluno Invalido', 'invalido@example.com', date(2009, 2, 3),
                    'Rua Nova, 200', 'Sao Paulo', 'SP', 'Turma inexistente', 'Empresa Teste', '',
                ],
            ]),
        })

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Turma &quot;Turma inexistente&quot; nao esta cadastrada.')
        self.assertFalse(Aluno.objects.filter(matricula='2027002').exists())
        self.assertFalse(Aluno.objects.filter(matricula='2027003').exists())

    def test_modelo_de_importacao_pode_ser_baixado(self):
        resposta = self.client.get(reverse('baixar_modelo_alunos'))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertTrue(b''.join(resposta.streaming_content) if resposta.streaming else resposta.content.startswith(b'PK'))

    def test_saida_status_can_only_change_via_post(self):
        url = reverse('aprovar_saida', args=[self.saida.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), reverse('lista_saidas'))
        self.saida.refresh_from_db()
        self.assertEqual(self.saida.status, 'autorizada')

    def test_atestado_status_can_only_change_via_post(self):
        url = reverse('aprovar_atestado', args=[self.atestado.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), reverse('lista_atestados'))
        self.atestado.refresh_from_db()
        self.assertEqual(self.atestado.status, 'aprovado')

    def test_gestor_creates_period_folder_and_adds_multiple_pdf_files(self):
        # Verifica a criação atômica da pasta e o vínculo de uploads subsequentes.
        data_inicio = date(2026, 10, 1)
        data_fim = date(2026, 10, 22)
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            resposta = self.client.post(reverse('registrar_atestado'), {
                'data_inicio': data_inicio.isoformat(),
                'data_fim': data_fim.isoformat(),
                'pdf': SimpleUploadedFile('atestados-outubro.pdf', b'%PDF-1.4 primeiro arquivo'),
            })

            self.assertRedirects(resposta, reverse('lista_atestados'))
            pasta = PastaAtestado.objects.get(data_inicio=data_inicio, data_fim=data_fim)
            self.assertEqual(pasta.criada_por, self.user)
            primeiro_pdf = pasta.documentos.get()
            self.assertEqual(primeiro_pdf.enviado_por, self.user)

            resposta = self.client.post(
                reverse('adicionar_pdf_atestado', args=[pasta.pk]),
                {'arquivo': SimpleUploadedFile('complemento.pdf', b'%PDF-1.7 segundo arquivo')},
            )
            self.assertRedirects(resposta, f'{reverse("lista_atestados")}?pasta={pasta.pk}')
            self.assertEqual(pasta.documentos.count(), 2)

            resposta_lista = self.client.get(reverse('lista_atestados') + f'?pasta={pasta.pk}')
            self.assertContains(resposta_lista, '1/10/2026 a 22/10/2026')
            self.assertContains(resposta_lista, 'atestados-outubro.pdf')
            self.assertContains(resposta_lista, 'complemento.pdf')

    def test_atestado_folder_rejects_invalid_period_and_non_pdf(self):
        # Confirma que a validação rejeita datas invertidas e conteúdo que apenas finge ser PDF.
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            url = reverse('registrar_atestado')
            periodo_invertido = self.client.post(url, {
                'data_inicio': date(2026, 10, 22).isoformat(),
                'data_fim': date(2026, 10, 1).isoformat(),
                'pdf': SimpleUploadedFile('atestados.pdf', b'%PDF-1.4 conteudo'),
            })
            self.assertEqual(periodo_invertido.status_code, 200)
            self.assertFalse(PastaAtestado.objects.exists())

            pdf_invalido = self.client.post(url, {
                'data_inicio': date(2026, 10, 1).isoformat(),
                'data_fim': date(2026, 10, 22).isoformat(),
                'pdf': SimpleUploadedFile('nao-e-pdf.pdf', b'arquivo invalido'),
            })
            self.assertEqual(pdf_invalido.status_code, 200)
            self.assertFalse(PastaAtestado.objects.exists())

    def test_professor_cannot_create_atestado_folder_or_upload_pdf(self):
        self.client.force_login(self.professor)
        self.assertEqual(self.client.get(reverse('registrar_atestado')).status_code, 403)

        pasta = PastaAtestado.objects.create(
            data_inicio=date(2026, 10, 1),
            data_fim=date(2026, 10, 22),
            criada_por=self.user,
        )
        resposta = self.client.post(
            reverse('adicionar_pdf_atestado', args=[pasta.pk]),
            {'arquivo': SimpleUploadedFile('atestados.pdf', b'%PDF-1.4 conteudo')},
        )
        self.assertEqual(resposta.status_code, 403)
        self.assertFalse(DocumentoAtestado.objects.exists())
