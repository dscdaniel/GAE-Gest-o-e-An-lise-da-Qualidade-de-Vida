"""Testes automatizados da página de relatório individual do aluno."""

from datetime import date, time

# Importa o modelo de grupos para autorizar o usuário de teste como gestor.
from django.contrib.auth.models import Group, User
# Usa o cliente de testes integrado do Django para chamadas HTTP sem servidor.
from django.test import TestCase
# Gera a URL pelo nome da rota, evitando deixar caminhos fixos nos testes.
from django.urls import reverse

# Importa os modelos apresentados pelas quatro abas do relatório e suas dependências.
from .models import Atraso, Aluno, Atestado, Empresa, Ocorrencia, Periodo, SaidaAntecipada, Turma


class RelatorioAlunoTemplateTests(TestCase):
    """Valida os dados e estados apresentados pelo template do relatório."""

    def setUp(self):
        # Cria um usuário autorizado e os relacionamentos mínimos exigidos pelo cadastro do aluno.
        grupo_gestor, _ = Group.objects.get_or_create(name="gestor")
        self.gestor = User.objects.create_user(username="gestor_relatorio", password="senha-segura")
        self.gestor.groups.add(grupo_gestor)
        # Mantém a sessão autenticada para acessar a view protegida por permissão de gestor.
        self.client.force_login(self.gestor)

        # Mantém o período fixo para que os testes não dependam da data em que forem executados.
        periodo = Periodo.objects.create(
            nome="2026.1",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 12, 31),
        )
        # Cria turma e empresa porque esses relacionamentos são necessários para cadastrar o aluno.
        turma = Turma.objects.create(nome="Turma de teste", periodo=periodo)
        empresa = Empresa.objects.create(nome="Empresa de teste")
        # Guarda o aluno em self para reutilizá-lo nos testes e nos registros relacionados.
        self.aluno = Aluno.objects.create(
            nome="Estudante de teste",
            matricula="RELATORIO001",
            turma=turma,
            empresa=empresa,
        )

    def criar_registros_do_relatorio(self, data_registro, identificador):
        # Cria um registro de cada categoria para validar o relatório de ponta a ponta.
        Atraso.objects.create(
            aluno=self.aluno,
            data_atraso=data_registro,
            hora_chegada=time(8, 15),
            minutos_atraso=15,
            motivo=f"Motivo {identificador}",
            registrado_por=self.gestor,
        )
        Ocorrencia.objects.create(
            aluno=self.aluno,
            data_ocorrencia=data_registro,
            tipo="outro",
            descricao=f"Descrição {identificador}",
            registrado_por=self.gestor,
        )
        SaidaAntecipada.objects.create(
            aluno=self.aluno,
            data_saida=data_registro,
            hora_saida=time(12, 0),
            motivo=f"Saída {identificador}",
            responsavel_autorizacao="Responsável de teste",
            status="autorizada",
            registrado_por=self.gestor,
        )
        Atestado.objects.create(
            aluno=self.aluno,
            arquivo=f"atestados/{identificador}.pdf",
            data_atestado=data_registro,
            status="aprovado",
            observacoes=f"Observação {identificador}",
        )

    def test_relatorio_exibe_dados_e_totais_de_todas_as_categorias(self):
        # Confirma que o template apresenta os registros e os totais das quatro categorias.
        self.criar_registros_do_relatorio(date(2026, 5, 10), "exibido")

        # Solicita o relatório pela rota nomeada usando o identificador do aluno preparado.
        resposta = self.client.get(reverse("relatorio_aluno", args=[self.aluno.pk]))

        # Verifica se a página carregou com sucesso e identifica o aluno correto.
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, self.aluno.nome)
        self.assertContains(resposta, self.aluno.matricula)
        # Confirma que os detalhes exclusivos de cada registro foram renderizados no HTML.
        self.assertContains(resposta, "Motivo exibido")
        self.assertContains(resposta, "Descrição exibido")
        self.assertContains(resposta, "Saída exibido")
        self.assertContains(resposta, "Observação exibido")
        for categoria in ("atrasos", "ocorrencias", "saidas", "atestados"):
            # Cada consulta entregue ao template deve conter o único registro criado.
            with self.subTest(categoria=categoria):
                self.assertEqual(resposta.context[categoria].count(), 1)

    def test_filtro_de_datas_aplica_intervalo_a_todas_as_categorias(self):
        # Cria registros dentro e fora do período para verificar os limites inclusivos do filtro.
        self.criar_registros_do_relatorio(date(2026, 5, 10), "dentro")
        self.criar_registros_do_relatorio(date(2026, 6, 20), "fora")

        # Envia as datas pelo query string como faria o formulário GET da página.
        resposta = self.client.get(
            reverse("relatorio_aluno", args=[self.aluno.pk]),
            {"data_inicio": "2026-05-01", "data_fim": "2026-05-31"},
        )

        # Confirma que o filtro não impede o carregamento normal da página.
        self.assertEqual(resposta.status_code, 200)
        # Verifica que os dados dentro do intervalo continuam visíveis.
        self.assertContains(resposta, "Motivo dentro")
        self.assertContains(resposta, "Descrição dentro")
        self.assertContains(resposta, "Saída dentro")
        self.assertContains(resposta, "Observação dentro")
        # Verifica que nenhum registro posterior ao limite final aparece no resultado.
        self.assertNotContains(resposta, "Motivo fora")
        self.assertNotContains(resposta, "Descrição fora")
        self.assertNotContains(resposta, "Saída fora")
        self.assertNotContains(resposta, "Observação fora")
        for categoria in ("atrasos", "ocorrencias", "saidas", "atestados"):
            # Garante que o filtro não seja aplicado somente ao conteúdo visível no HTML.
            with self.subTest(categoria=categoria):
                self.assertEqual(resposta.context[categoria].count(), 1)

    def test_relatorio_informa_quando_nao_ha_registros(self):
        # Valida as mensagens de estado vazio e os totais zerados para um aluno sem ocorrências.
        # Carrega o relatório sem filtros e sem criar nenhum registro para o aluno.
        resposta = self.client.get(reverse("relatorio_aluno", args=[self.aluno.pk]))

        # A página deve continuar disponível mesmo quando todas as categorias estão vazias.
        self.assertEqual(resposta.status_code, 200)
        for mensagem in (
            "Sem atrasos no período",
            "Sem ocorrências no período",
            "Sem saídas no período",
            "Sem atestados no período",
        ):
            # Cada categoria deve oferecer uma mensagem própria quando não há dados.
            with self.subTest(mensagem=mensagem):
                self.assertContains(resposta, mensagem)
        for categoria in ("atrasos", "ocorrencias", "saidas", "atestados"):
            # Confirma que todos os totais apresentados começam em zero.
            with self.subTest(categoria=categoria):
                self.assertEqual(resposta.context[categoria].count(), 0)
