import os  # Localiza a logo e outros arquivos usados no documento.
from html import escape  # Evita que textos do banco quebrem a marcação do PDF.

from django.conf import settings  # Obtém o diretório base configurado no projeto.
from django.http import HttpResponse  # Envia o PDF diretamente para o navegador.
from reportlab.lib import colors  # Define cores de bordas e cabeçalhos das tabelas.
from reportlab.lib.enums import TA_CENTER  # Centraliza títulos no documento.
from reportlab.lib.pagesizes import A4  # Define o tamanho padrão das páginas.
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # Formata títulos e textos.
from reportlab.lib.units import cm  # Permite definir margens e colunas em centímetros.
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # Monta o conteúdo do PDF.


def resposta_pdf_deliberacao(ocorrencia):
    """Gera o formulário de deliberação preenchido a partir da ocorrência."""
    # Cria a resposta HTTP e organiza textos, tabelas e assinaturas no fluxo do PDF.
    # O ReportLab recebe uma lista de elementos e calcula a paginação durante build().
    aluno = ocorrencia.aluno
    resposta = HttpResponse(content_type='application/pdf')
    resposta['Content-Disposition'] = (
        f'attachment; filename="deliberacao-{aluno.matricula}-{ocorrencia.pk}.pdf"'
    )

    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle(
        'TituloDeliberacao', parent=estilos['Heading1'], fontName='Helvetica-Bold',
        fontSize=14, leading=17, alignment=TA_CENTER, spaceAfter=10,
    )
    secao = ParagraphStyle(
        'SecaoDeliberacao', parent=estilos['Heading3'], fontName='Helvetica-Bold',
        fontSize=9.5, leading=12, spaceBefore=8, spaceAfter=4,
    )
    texto = ParagraphStyle('TextoDeliberacao', parent=estilos['BodyText'], fontSize=8.5, leading=11)
    pequeno = ParagraphStyle('PequenoDeliberacao', parent=texto, fontSize=8, leading=10)

    documento = SimpleDocTemplate(
        resposta, pagesize=A4, rightMargin=1.35 * cm, leftMargin=1.35 * cm,
        topMargin=1.2 * cm, bottomMargin=1.15 * cm,
        title='Deliberação de Aluno', author='GAE',
    )
    # O fluxo preserva a ordem visual do formulario; o ReportLab quebra paginas no build.
    fluxo = [_cabecalho_pdf(titulo)]
    fluxo.append(_tabela_dados(ocorrencia, pequeno))
    fluxo.append(Paragraph('Motivos', secao))
    fluxo.append(_opcoes(ocorrencia.motivos, ocorrencia.MOTIVOS, texto))
    fluxo.append(Paragraph('Principais Dificuldades do Aluno', secao))
    fluxo.append(_opcoes(ocorrencia.dificuldades, ocorrencia.DIFICULDADES, texto))
    fluxo.append(_outro('Outras', ocorrencia.outras_dificuldades, texto))
    fluxo.append(Paragraph('Recomendações do Professor ao Aluno', secao))
    fluxo.append(_opcoes(ocorrencia.recomendacoes_aluno, ocorrencia.RECOMENDACOES_ALUNO, texto))
    fluxo.append(_outro('Outras', ocorrencia.outras_recomendacoes_aluno, texto))
    fluxo.append(Paragraph('Recomendações do Professor/Escola aos Pais ou Responsáveis', secao))
    fluxo.append(_opcoes(
        ocorrencia.recomendacoes_responsaveis, ocorrencia.RECOMENDACOES_RESPONSAVEIS, texto,
    ))
    fluxo.append(_outro('Outras', ocorrencia.outras_recomendacoes_responsaveis, texto))
    fluxo.append(Paragraph('Providências do Professor e da Escola para Auxiliar o Aluno', secao))
    fluxo.append(_opcoes(ocorrencia.providencias, ocorrencia.PROVIDENCIAS, texto))
    fluxo.append(_outro('Outras', ocorrencia.outras_providencias, texto))
    fluxo.append(Paragraph('Observações', secao))
    fluxo.append(Paragraph(_valor(ocorrencia.descricao) or '____________________________________________', texto))
    fluxo.append(Spacer(1, 14))
    fluxo.append(Paragraph('Cientes:', secao))
    fluxo.append(_assinaturas(ocorrencia, pequeno))
    fluxo.append(Spacer(1, 8))
    fluxo.append(Paragraph('801-FR-22  v.3', pequeno))
    documento.build(fluxo)
    return resposta


def resposta_pdf_preconselho(preconselho):
    """Gera o registro do conselho com as anotacoes dos alunos."""
    # O mesmo fluxo de elementos é usado aqui, mas a tabela é montada a partir das anotações.
    resposta = HttpResponse(content_type='application/pdf')
    resposta['Content-Disposition'] = (
        f'attachment; filename="conselho-{preconselho.turma.nome}-{preconselho.data_reuniao}.pdf"'
    )

    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle(
        'TituloPreConselho', parent=estilos['Heading1'], fontName='Helvetica-Bold',
        fontSize=14, leading=17, alignment=TA_CENTER, spaceAfter=10,
    )
    secao = ParagraphStyle(
        'SecaoPreConselho', parent=estilos['Heading3'], fontName='Helvetica-Bold',
        fontSize=9.5, leading=12, spaceBefore=8, spaceAfter=4,
    )
    texto = ParagraphStyle('TextoPreConselho', parent=estilos['BodyText'], fontSize=8, leading=10)
    pequeno = ParagraphStyle('PequenoPreConselho', parent=texto, fontSize=7.5, leading=9)

    documento = SimpleDocTemplate(
        resposta, pagesize=A4, rightMargin=1.15 * cm, leftMargin=1.15 * cm,
        topMargin=1.2 * cm, bottomMargin=1.15 * cm,
        title='Conselho', author='GAE',
    )
    turma = preconselho.turma
    data = preconselho.data_reuniao.strftime('%d/%m/%Y')
    # Junta dados da turma e observacoes com a tabela detalhada dos alunos.
    fluxo = [
        _cabecalho_preconselho_pdf(titulo),
        Paragraph(f'<b>Turma:</b> {_valor(turma.nome)} &nbsp;&nbsp; '
                  f'<b>Curso:</b> {_valor(turma.curso)} &nbsp;&nbsp; '
                  f'<b>Data:</b> {data}', pequeno),
        Paragraph(f'<b>Situação:</b> {_valor(preconselho.get_status_display())}', pequeno),
        Paragraph('Observações gerais', secao),
        Paragraph(_valor(preconselho.observacoes_gerais) or 'Nenhuma observação registrada.', texto),
        Spacer(1, 8),
        Paragraph('Anotações dos alunos', secao),
        _tabela_preconselho(preconselho, texto),
    ]
    documento.build(fluxo)
    return resposta


def _cabecalho_preconselho_pdf(titulo):
    logo_path = os.path.join(settings.BASE_DIR, 'gestor', 'static', 'img', 'logo.png')
    # O documento continua valido sem a imagem, por exemplo em instalacoes sem logo.
    if os.path.exists(logo_path):
        imagem = Image(logo_path, width=2.1 * cm, height=2.1 * cm, hAlign='LEFT')
        return Table(
            [[imagem, Paragraph('REGISTRO DE CONSELHO', titulo)]],
            colWidths=[2.8 * cm, 14.1 * cm],
            hAlign='LEFT',
        )
    return Paragraph('REGISTRO DE CONSELHO', titulo)


def _tabela_preconselho(preconselho, estilo):
    # Repetir a primeira linha ajuda a identificar as colunas em paginas seguintes.
    linhas = [[
        Paragraph('<b>Aluno</b>', estilo),
        Paragraph('<b>Situação</b>', estilo),
        Paragraph('<b>Anotação</b>', estilo),
        Paragraph('<b>Encaminhamentos</b>', estilo),
    ]]
    # Carrega cada aluno junto da anotação para evitar uma consulta por linha da tabela.
    anotacoes = preconselho.anotacoes.select_related('aluno').order_by('aluno__nome')
    for anotacao in anotacoes:
        linhas.append([
            Paragraph(_valor(anotacao.aluno.nome), estilo),
            Paragraph(_valor(anotacao.get_situacao_display()), estilo),
            Paragraph(_valor(anotacao.anotacao) or '—', estilo),
            Paragraph(_valor(anotacao.encaminhamentos) or '—', estilo),
        ])
    tabela = Table(linhas, colWidths=[4.1 * cm, 2.7 * cm, 5.2 * cm, 5.2 * cm], repeatRows=1)
    tabela.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#89949b')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9edef')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return tabela


def _cabecalho_pdf(titulo):
    logo_path = os.path.join(settings.BASE_DIR, 'gestor', 'static', 'img', 'logo.png')
    # O cabeçalho textual mantém o PDF válido quando a imagem institucional não está instalada.
    if os.path.exists(logo_path):
        imagem = Image(logo_path, width=2.1 * cm, height=2.1 * cm, hAlign='LEFT')
        return Table(
            [[imagem, Paragraph('DELIBERAÇÃO DE ALUNO', titulo)]],
            colWidths=[2.8 * cm, 13.5 * cm],
            hAlign='LEFT',
        )
    return Paragraph('DELIBERAÇÃO DE ALUNO', titulo)


def _tabela_dados(ocorrencia, estilo):
    aluno = ocorrencia.aluno
    docente = ocorrencia.registrado_por.get_full_name() if ocorrencia.registrado_por else ''
    # Usa o username quando o usuario nao possui nome completo cadastrado.
    if not docente and ocorrencia.registrado_por:
        docente = ocorrencia.registrado_por.username
    data = ocorrencia.data_ocorrencia.strftime('%d/%m/%Y')
    linhas = [
        [
            Paragraph(f'<b>Aluno:</b> {_valor(aluno.nome)}', estilo),
            Paragraph(f'<b>Nº:</b> {_valor(aluno.matricula)}', estilo),
            Paragraph(f'<b>Turma:</b> {_valor(aluno.turma.nome)}', estilo),
        ],
        [
            Paragraph(f'<b>Docente:</b> {_valor(docente)}', estilo),
            Paragraph(f'<b>Disciplina:</b> {_valor(ocorrencia.disciplina)}', estilo),
            Paragraph(f'<b>Data:</b> {data}', estilo),
        ],
        [
            Paragraph(f'<b>Nota média da classe:</b> {_numero(ocorrencia.nota_media_classe)}', estilo),
            Paragraph(f'<b>Nota do aluno:</b> {_numero(ocorrencia.nota_aluno)}', estilo),
            Paragraph(f'<b>Total de faltas:</b> {_numero(ocorrencia.total_faltas)}', estilo),
        ],
        [
            Paragraph(f'<b>AD:</b> {_valor(ocorrencia.ad)}', estilo),
            Paragraph(f'<b>AP:</b> {_valor(ocorrencia.ap)}', estilo),
            Paragraph(f'<b>Vínculo:</b> {aluno.get_vinculo_display()}', estilo),
        ],
    ]
    tabela = Table(linhas, colWidths=[7.25 * cm, 5.7 * cm, 5.7 * cm], hAlign='LEFT')
    tabela.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#89949b')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7f8f8')),
        ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return tabela


def _opcoes(selecionadas, opcoes, estilo):
    # O conjunto torna a busca por seleção rápida durante a montagem de cada opção.
    selecionadas = set(selecionadas or [])
    # Duas opcoes por linha mantem a ficha compacta; a ultima linha e completada se necessario.
    # Divide as alternativas em pares e completa a última linha para manter duas colunas.
    linhas = [
        [Paragraph(f"{'[X]' if chave in selecionadas else '[ ]'} {_valor(rotulo)}", estilo)
         for chave, rotulo in opcoes[indice:indice + 2]]
        for indice in range(0, len(opcoes), 2)
    ]
    if linhas and len(linhas[-1]) == 1:
        linhas[-1].append(Paragraph('', estilo))
    tabela = Table(linhas, colWidths=[9.3 * cm, 9.3 * cm], hAlign='LEFT')
    tabela.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return tabela


def _outro(rotulo, valor, estilo):
    return Paragraph(f'<b>{rotulo}:</b> {_valor(valor) or "____________________________"}', estilo)


def _assinaturas(ocorrencia, estilo):
    docente = ''
    if ocorrencia.registrado_por:
        docente = ocorrencia.registrado_por.get_full_name() or ocorrencia.registrado_por.username
    linhas = [
        [Paragraph('______________________________', estilo), Paragraph('______________________________', estilo)],
        [Paragraph(f'Docente: {_valor(docente)}', estilo), Paragraph('Aluno', estilo)],
        [Paragraph('______________________________', estilo), Paragraph('______________________________', estilo)],
        [Paragraph('Direção', estilo), Paragraph('Responsável', estilo)],
    ]
    tabela = Table(linhas, colWidths=[9.3 * cm, 9.3 * cm], hAlign='LEFT')
    tabela.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return tabela


def _valor(valor):
    # Paragraph interpreta HTML; escapar o valor evita que texto digitado vire marcacao.
    return escape(str(valor or '')).replace('\n', '<br/>')


def _numero(valor):
    return _valor(valor if valor is not None else '')
