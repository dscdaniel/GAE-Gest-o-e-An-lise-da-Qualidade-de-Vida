"""Importação das planilhas institucionais de alunos.

Os cabeçalhos variam entre CAI, CT e cursos superiores. Este módulo lê os
nomes de coluna, e não a posição delas, para preservar os dados de cada aba.
"""

from dataclasses import dataclass, field  # Guarda o resumo da importação com estrutura simples.
from datetime import date, datetime  # Converte datas da planilha para os modelos Django.
import re  # Normaliza textos e identifica padrões nos valores importados.
import unicodedata  # Remove acentos ao comparar nomes de colunas.
from zipfile import BadZipFile  # Identifica arquivos Excel corrompidos ou inválidos.

from django.db import IntegrityError, transaction  # Garante gravações consistentes no banco.
from openpyxl import load_workbook  # Lê planilhas .xlsx mantendo acesso às abas e células.
from openpyxl.utils.exceptions import InvalidFileException  # Trata arquivos Excel malformados.

from .models import Aluno, Empresa, Periodo, Turma


MAX_LINHAS = 5000
MAX_ERROS = 100


class ImportacaoInvalida(Exception):
    pass

# Converte variações de cabeçalho para nomes internos antes de ler as linhas.
ALIASES_CABECALHO = {
    'empresa do contrato de aprendizagem': 'empresa',
    'empresa': 'empresa',
    'n de matricula': 'matricula',
    'no de matricula': 'matricula',
    'numero de matricula': 'matricula',
    'matricula': 'matricula',
    'nome': 'nome',
    'data de nascimento': 'data_nascimento',
    'rg': 'rg',
    'cpf': 'cpf',
    'telefone': 'telefone',
    'celular': 'celular',
    'e mail': 'email',
    'email': 'email',
    'nome do pai': 'nome_pai',
    'nome da mae': 'nome_mae',
    'endereco aluno': 'endereco',
    'endereco': 'endereco',
    'bairro': 'bairro',
    'municipio': 'cidade',
    'cidade': 'cidade',
    'estado': 'estado',
    'cep': 'cep',
    'curso': 'curso',
    'turma': 'turma',
    'tipo turma': 'tipo_turma',
    'tipo de turma': 'tipo_turma',
    'horario': 'horario',
    'turno': 'horario',
    'horario inicial': 'horario_inicial',
    'horario final': 'horario_final',
    'carga horaria': 'carga_horaria',
    'data de inicio': 'data_inicio',
    'data de fim': 'data_fim',
    'dias da semana': 'dias_semana',
    'observacoes anotacoes': 'observacoes',
    'observacoes': 'observacoes',
    'anotacoes': 'observacoes',
}


@dataclass
class ResultadoImportacao:
    linhas_lidas: int = 0
    alunos_criados: int = 0
    alunos_atualizados: int = 0
    turmas_criadas: int = 0
    empresas_criadas: int = 0
    erros: list[str] = field(default_factory=list)

    def adicionar_erro(self, mensagem):
        # Limita a quantidade de mensagens para não sobrecarregar a resposta da importação.
        if len(self.erros) < MAX_ERROS:
            self.erros.append(mensagem)


def importar_alunos_da_planilha(arquivo):
    """Importa ou atualiza alunos de todas as abas de uma planilha .xlsx."""
    # O fluxo aceita .xlsx e .xls, valida cada linha e grava cada aluno em uma transação.
    # O bloco finally fecha a planilha mesmo quando ocorre uma exceção no processamento.
    resultado = ResultadoImportacao()
    planilha = None
    try:
        nome = getattr(arquivo, 'name', '').lower()
        # O .xls usa xlrd; os formatos XML do Excel usam openpyxl.
        if nome.endswith('.xls') and not nome.endswith(('.xlsx', '.xlsm')):
            try:
                import xlrd
            except ImportError:
                resultado.adicionar_erro(
                    'O suporte ao formato .xls não está instalado. Use .xlsx ou instale a dependência xlrd.'
                )
                return resultado
            planilha = xlrd.open_workbook(file_contents=arquivo.read())
        else:
            planilha = load_workbook(arquivo, data_only=True)
        # _ler_linhas usa yield; list() executa o gerador e materializa suas linhas aqui.
        linhas = list(_ler_linhas(planilha, resultado))
        if not linhas:
            resultado.adicionar_erro('A planilha não possui alunos para importar.')
            return resultado

        # Os caches evitam consultar/criar a mesma turma, empresa ou período várias vezes.
        cache_periodos, cache_turmas, cache_empresas = {}, {}, {}
        matriculas_lidas = set()
        for dados_linha in linhas:
            matricula = dados_linha['dados'].get('matricula', '')
            # Em uma mesma planilha, a primeira ocorrência da matrícula é preservada.
            if matricula and matricula in matriculas_lidas:
                resultado.adicionar_erro(
                    f"{dados_linha['aba']} — linha {dados_linha['linha']}: "
                    f'a matrícula {matricula} repetida; linha ignorada.'
                )
                continue
            if matricula:
                matriculas_lidas.add(matricula)
            try:
                # Se uma linha falhar, sua transação é desfeita sem perder as outras linhas.
                with transaction.atomic():
                    _salvar_linha(
                        dados_linha, resultado, cache_periodos, cache_turmas, cache_empresas,
                    )
            except IntegrityError:
                resultado.adicionar_erro(
                    f"{dados_linha['aba']} — linha {dados_linha['linha']}: dados incompatíveis; linha ignorada."
                )
        return resultado
    except ImportacaoInvalida:
        return resultado
    except (BadZipFile, InvalidFileException, OSError, ValueError):
        resultado.adicionar_erro('Não foi possível ler a planilha. Envie um arquivo .xlsx válido.')
        return resultado
    except IntegrityError:
        resultado.adicionar_erro('Não foi possível gravar a planilha por conflito de dados. Tente novamente.')
        return resultado
    finally:
        if planilha is not None:
            planilha.close()


def _ler_linhas(planilha, resultado):
    # yield transforma a função em gerador: cada linha é produzida sob demanda.
    # A verificação de atributos adapta o leitor às APIs diferentes de xlrd e openpyxl.
    abas = planilha.sheets() if hasattr(planilha, 'sheets') else planilha.worksheets
    for aba in abas:
        cabecalhos = _mapear_cabecalhos(aba)
        if 'nome' not in cabecalhos:
            continue
        total_linhas = aba.nrows if hasattr(aba, 'nrows') else aba.max_row
        # A primeira linha contém cabeçalhos; os dados começam na linha seguinte.
        for numero_linha in range(2, total_linhas + 1):
            dados = {
                campo: _texto(_valor_celula(aba, numero_linha, coluna))
                for campo, coluna in cabecalhos.items()
            }
            if not any(dados.values()):
                continue
            resultado.linhas_lidas += 1
            if resultado.linhas_lidas > MAX_LINHAS:
                resultado.adicionar_erro(f'A planilha pode ter no máximo {MAX_LINHAS} alunos.')
                return
            nome = dados.get('nome', '')
            if not nome:
                resultado.adicionar_erro(
                    f'{aba.title} — linha {numero_linha}: informe o nome do aluno.'
                )
                continue
            yield {
                'aba': _nome_aba(aba),
                'linha': numero_linha,
                'dados': dados,
                'em_destaque': _nome_destacado(aba, numero_linha, cabecalhos['nome']),
            }


def _mapear_cabecalhos(aba):
    colunas = {}
    total_colunas = aba.ncols if hasattr(aba, 'ncols') else aba.max_column
    for coluna in range(1, total_colunas + 1):
        # Se um mesmo campo aparecer mais de uma vez, usa a primeira coluna encontrada.
        campo = ALIASES_CABECALHO.get(_chave_texto(_valor_celula(aba, 1, coluna)))
        if campo and campo not in colunas:
            colunas[campo] = coluna
    return colunas


def _salvar_linha(dados_linha, resultado, cache_periodos, cache_turmas, cache_empresas):
    dados = dados_linha['dados']
    # Resolve primeiro os relacionamentos para que o aluno seja salvo com referências válidas.
    ano = _ano_referencia(dados.get('data_inicio'))
    periodo = _periodo(ano, cache_periodos)
    turma = _turma(dados, periodo, cache_turmas, resultado)
    if turma is None:
        return
    empresa, observacao_empresa = _empresa(dados.get('empresa', ''), cache_empresas, resultado)
    observacoes = _juntar_textos(observacao_empresa, dados.get('observacoes', ''))

    nascimento = _converter_data(dados.get('data_nascimento'))
    if dados.get('data_nascimento') and nascimento is None:
        resultado.adicionar_erro(
            f"{dados_linha['aba']} — linha {dados_linha['linha']}: data de nascimento inválida; deixada em branco."
        )

    horario = dados.get('horario') or _juntar_horarios(
        dados.get('horario_inicial'), dados.get('horario_final'),
    )
    # Campos derivados mantêm consistência entre a empresa, o vínculo e o status do aluno.
    valores = {
        'nome': dados['nome'], 'email': dados.get('email', ''),
        'data_nascimento': nascimento, 'rg': dados.get('rg', ''), 'cpf': dados.get('cpf', ''),
        'telefone': dados.get('telefone', ''), 'celular': dados.get('celular', ''),
        'nome_pai': dados.get('nome_pai', ''), 'nome_mae': dados.get('nome_mae', ''),
        'endereco': dados.get('endereco', ''), 'bairro': dados.get('bairro', ''),
        'cidade': dados.get('cidade', ''), 'estado': dados.get('estado', ''),
        'cep': dados.get('cep', ''), 'curso': dados.get('curso', ''), 'horario': horario,
        'carga_horaria': _inteiro(dados.get('carga_horaria')),
        'data_inicio': _converter_data(dados.get('data_inicio')),
        'data_fim': _converter_data(dados.get('data_fim')),
        'dias_semana': dados.get('dias_semana', ''), 'turma': turma, 'empresa': empresa,
        'tipo_turma': dados.get('tipo_turma') if dados.get('tipo_turma') in {'CAI', 'CT'} else 'CAI',
        'vinculo': 'AE' if empresa else 'AD', 'observacoes': observacoes,
        'origem_planilha': dados_linha['aba'], 'em_destaque': dados_linha['em_destaque'],
        'ativo': 'desistiu' not in _chave_texto(dados['nome']),
    }
    matricula = dados.get('matricula') or None
    if matricula:
        # Atualiza o aluno existente pela matrícula ou cria um novo registro se não encontrar.
        _, criado = Aluno.objects.update_or_create(matricula=matricula, defaults=valores)
    else:
        Aluno.objects.create(matricula=None, **valores)
        criado = True
    if criado:
        resultado.alunos_criados += 1
    else:
        resultado.alunos_atualizados += 1


def _periodo(ano, cache):
    if ano not in cache:
        periodo, _ = Periodo.objects.get_or_create(
            nome=str(ano),
            defaults={'data_inicio': date(ano, 1, 1), 'data_fim': date(ano, 12, 31), 'ativo': True},
        )
        cache[ano] = periodo
    return cache[ano]


def _turma(dados, periodo, cache, resultado):
    nome_informado = dados.get('turma')
    nome = nome_informado or f"Sem turma — {periodo.nome}"
    chave = (nome.casefold(), periodo.pk)
    if chave not in cache:
        if nome_informado:
            # Prefere a turma do período calculado; se não houver, reutiliza a mais recente com esse nome.
            turma_existente = Turma.objects.filter(
                periodo=periodo, nome__iexact=nome_informado,
            ).first() or Turma.objects.filter(
                nome__iexact=nome_informado,
            ).order_by('-periodo__data_inicio').first()
            if turma_existente is None:
                # Usa uma turma neutra para não descartar o aluno por uma referência desconhecida.
                resultado.adicionar_erro(
                    f'Turma "{nome_informado}" nao esta cadastrada; campo deixado em branco.'
                )
                nome = f"Sem turma — {periodo.nome}"
                chave = (nome.casefold(), periodo.pk)
            else:
                cache[chave] = turma_existente
                return turma_existente
        horario = dados.get('horario') or _juntar_horarios(
            dados.get('horario_inicial'), dados.get('horario_final'),
        )
        turma, criada = Turma.objects.get_or_create(
            nome=nome, periodo=periodo,
            defaults={
                'curso': dados.get('curso', ''),
                'horario': horario,
                'tipo_turma': dados.get('tipo_turma') if dados.get('tipo_turma') in {'CAI', 'CT'} else 'CAI',
            },
        )
        if criada:
            resultado.turmas_criadas += 1
        else:
            campos = []
            if dados.get('curso') and not turma.curso:
                # Completa dados ausentes sem substituir informações já cadastradas na turma.
                turma.curso = dados['curso']
                campos.append('curso')
            if horario and not turma.horario:
                turma.horario = horario
                campos.append('horario')
            if campos:
                turma.save(update_fields=campos)
        cache[chave] = turma
    return cache[chave]


def _empresa(valor, cache, resultado):
    valor = _texto(valor)
    if not valor:
        return None, ''
    # Textos longos ou frases típicas de observação não devem virar cadastro de empresa.
    if _parece_observacao(valor):
        return None, valor
    chave = valor.casefold()
    if chave not in cache:
        empresa = Empresa.objects.filter(nome__iexact=valor).first()
        if empresa is None:
            empresa = Empresa.objects.create(nome=valor)
            resultado.empresas_criadas += 1
        cache[chave] = empresa
    return cache[chave], ''


def _nome_destacado(aba, linha, coluna_nome):
    """A planilha usa preenchimento no nome como sinalização visual."""
    # xlrd não expõe o estilo da célula neste fluxo, então esse formato não marca destaques.
    if hasattr(aba, 'nrows'):
        return False
    return aba.cell(linha, coluna_nome).fill.fill_type == 'solid'


def _valor_celula(aba, linha, coluna):
    if hasattr(aba, 'nrows'):
        return aba.cell_value(linha - 1, coluna - 1)
    return aba.cell(linha, coluna).value


def _nome_aba(aba):
    return (aba.name if hasattr(aba, 'name') else aba.title).strip()


def _parece_observacao(valor):
    # Evita criar empresas quando uma observação foi colocada por engano nessa coluna.
    chave = _chave_texto(valor)
    gatilhos = ('aluno mora', 'aluna mora', 'sem renda', 'encaminha', 'pensão', 'pensao')
    return len(valor) > 120 or any(gatilho in chave for gatilho in gatilhos)


def _ano_referencia(valor):
    data_referencia = _converter_data(valor)
    # Sem data de início válida, agrupa o aluno no período do ano corrente.
    return data_referencia.year if data_referencia else date.today().year


def _converter_data(valor):
    # Aceita datas nativas do Excel e os três formatos textuais usados nas planilhas recebidas.
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = _texto(valor)
    if not texto:
        return None
    for formato in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            pass
    return None


def _inteiro(valor):
    # Trata números lidos como texto ou float e aceita vírgula como separador decimal.
    texto = _texto(valor)
    if not texto:
        return None
    try:
        return int(float(texto.replace(',', '.')))
    except ValueError:
        return None


def _juntar_horarios(inicio, fim):
    # Constrói o turno com os horários disponíveis, tolerando que uma das pontas esteja vazia.
    inicio, fim = _texto(inicio), _texto(fim)
    return f'{inicio} às {fim}' if inicio and fim else inicio or fim


def _juntar_textos(*textos):
    # Junta observações não vazias sem produzir linhas extras por campos em branco.
    return '\n'.join(texto for texto in textos if texto)


def _texto(valor):
    # Normaliza tipos que o Excel entrega de forma diferente antes de aplicar str().
    if valor is None:
        return ''
    if isinstance(valor, datetime):
        return valor.strftime('%d/%m/%Y')
    if isinstance(valor, date):
        return valor.strftime('%d/%m/%Y')
    if hasattr(valor, 'strftime'):
        return valor.strftime('%H:%M')
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor).strip()


def _chave_texto(valor):
    # Remove acentos, pontuação e espaços repetidos para comparar cabeçalhos de forma estável.
    texto = unicodedata.normalize('NFKD', _texto(valor)).encode('ASCII', 'ignore').decode('ASCII')
    texto = re.sub(r'[^a-zA-Z0-9]+', ' ', texto).strip().lower()
    return re.sub(r'\s+', ' ', texto)
