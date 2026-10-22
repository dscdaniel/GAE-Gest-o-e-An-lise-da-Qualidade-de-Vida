from django.shortcuts import render, redirect, get_object_or_404  # Controla páginas, redirecionamentos e buscas com 404.
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout  # Valida credenciais e mantém a sessão do usuário.
from django.contrib.auth.models import Group  # Organiza usuários nos perfis gestor e professor.
from django.contrib import messages  # Envia feedback visual para as telas.
from django.db import transaction  # Agrupa operações que precisam ser salvas juntas.
from django.db.models import Count, Q  # Faz contagens e filtros compostos diretamente no banco.
from django.http import HttpResponse, HttpResponseBadRequest  # Retorna arquivos e respostas HTTP personalizadas.
from django.views.decorators.http import require_POST  # Limita ações sensíveis ao método POST.
from datetime import date, datetime  # Trabalha com datas usadas nos filtros e registros.
from django.utils import timezone  # Usa datas compatíveis com o fuso configurado no Django.
from openpyxl import Workbook  # Cria planilhas Excel para exportação de dados.
from .decorators import gestor_required, professor_required
from core.permissions import perfil_usuario
from .importacao import importar_alunos_da_planilha
from .pdf import resposta_pdf_deliberacao, resposta_pdf_preconselho
from .models import (Aluno, Atraso, Ocorrencia, SaidaAntecipada, 
                      Atestado, Turma, Empresa, Periodo, Telefone,
                      PreConselho, AnotacaoPreConselho, PastaAtestado,
                      DocumentoAtestado)
from .forms import (LoginForm, CadastroUsuarioForm, AlunoForm, TelefoneForm, AttrasoForm, 
                     OcorrenciaForm, SaidaAntecipadadaForm, AtestadoForm,
                     TurmaForm, EmpresaForm, PeriodoForm, FiltroAlunoForm,
                     ImportarAlunosForm, PreConselhoForm, AnotacaoPreConselhoForm,
                     PastaAtestadoForm, DocumentoAtestadoForm)


def turmas_visiveis(request):
    # Retorna somente as turmas que o perfil atual pode consultar.
    # select_related busca ForeignKey junto com a turma; prefetch_related faz uma
    # segunda consulta para o ManyToMany, evitando várias consultas repetidas.
    turmas = Turma.objects.select_related('periodo', 'professor').prefetch_related('professores').all()
    if perfil_usuario(request.user) == 'professor':
        # Considera o vínculo múltiplo atual e o campo singular legado durante a transição.
        # Q permite usar OR no banco; distinct remove duplicatas causadas pelo relacionamento.
        turmas = turmas.filter(Q(professores=request.user) | Q(professor=request.user)).distinct()
    return turmas


def alunos_visiveis(request):
    # O filtro é aplicado no banco, antes de carregar os alunos para a memória.
    alunos = Aluno.objects.select_related('turma', 'empresa').all()
    if perfil_usuario(request.user) == 'professor':
        # A matrícula só aparece se a turma estiver ligada ao professor por qualquer dos dois campos.
        alunos = alunos.filter(Q(turma__professores=request.user) | Q(turma__professor=request.user)).distinct()
    return alunos


def aluno_visivel_ou_404(request, pk):
    # Primeiro limita o queryset pelas permissões; depois retorna 404 se o aluno não estiver acessível.
    return get_object_or_404(alunos_visiveis(request), pk=pk)


def saidas_visiveis(request):
    """Gestor enxerga todas as saidas; professor somente as das suas turmas."""
    saidas = SaidaAntecipada.objects.select_related(
        'aluno', 'aluno__turma', 'registrado_por', 'autorizado_por'
    )
    if perfil_usuario(request.user) == 'professor': 
        saidas = saidas.filter(
            Q(aluno__turma__professores=request.user) |
            Q(aluno__turma__professor=request.user) 
        ).distinct()
    return saidas
#limitar as ocorrencias visiveis para o professor, apenas as de suas turmas

def saida_visivel_ou_404(request, pk):
    return get_object_or_404(saidas_visiveis(request), pk=pk)

def ocorrencia_visivel_ou_404(request, pk):
    ocorrencias = Ocorrencia.objects.select_related('aluno', 'aluno__turma', 'registrado_por')
    if perfil_usuario(request.user) == 'professor':
        # Retornar 404 também oculta se a ocorrência existe quando ela está fora do escopo do professor.
        ocorrencias = ocorrencias.filter(
            Q(aluno__turma__professores=request.user) | #busca a turma do aluno e verifica se o professor está na lista de professores da turma
            Q(aluno__turma__professor=request.user)
        ).distinct()
    return get_object_or_404(ocorrencias, pk=pk)


#AUTENTICAÇÃO
def login_view(request):
    # Autentica por usuário ou e-mail e só cria a sessão para perfis autorizados.
    if request.user.is_authenticated:
        perfil = perfil_usuario(request.user)
        if perfil == 'gestor':
            return redirect('dashboard') #define a página inicial do gestor
        if perfil == 'professor':
            return redirect('lista_turmas')
        logout(request)

    if request.method == 'POST': #serve para verificar se o formulário foi enviado via POST se foi POST deve pegar os dados do formulário e autenticar o usuário
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        user = None
        if email and senha:
            usuario = None
            # E-mail é resolvido sem diferenciar maiúsculas; entradas sem @ continuam aceitas como username.
            if '@' in str(email):
                from django.contrib.auth.models import User
                try: #email_iexact é usado para fazer a busca sem diferenciar maiúsculas e minúsculas
                    usuario = User.objects.get(email__iexact=email) #try para verificar se o usuário existe no banco de dados, se não existir retorna None e 
                except User.DoesNotExist:
                    usuario = None
            # Se o usuário não existir, o backend de autenticação do Django não consegue diferenciar se o e-mail ou a senha estão errados.
            if usuario is not None:
                username = usuario.username
            else:
                # O backend de autenticação do Django recebe sempre um username, nunca o e-mail digitado.
                username = str(email).strip()
        
            user = authenticate(request, username=username, password=senha) #autentica o usuário com o username e senha fornecidos, se for válido retorna o objeto do usuário, caso contrário retorna None
            if user is not None:
                perfil = perfil_usuario(user)
                if perfil in ('gestor', 'professor'):
                    if perfil == 'professor':
                        atribuir_turma_ao_professor(user)
                    login(request, user)
                    messages.success(request, f'Bem-vindo, {user.get_full_name() or user.username}!')
                    return redirect('dashboard' if perfil == 'gestor' else 'lista_turmas')
                messages.error(request, 'Seu usuário ainda não possui um perfil de acesso.')
        # Se o usuário for None, significa que a autenticação falhou, então exibe uma mensagem de erro
        if user is None:
            messages.error(request, 'E-mail/usuário ou senha inválidos!')

    return render(request, 'gestor/login.html')

#
def cadastro_usuario(request):
    # Salva o usuário e associa seu grupo, que será usado pelas permissões do sistema.
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            tipo_conta = form.cleaned_data['tipo_conta']
            grupo, _ = Group.objects.get_or_create(name=tipo_conta)
            # O segundo retorno informa se o grupo foi criado agora; ele não é necessário aqui.
            usuario.groups.add(grupo)

            if tipo_conta == 'professor':
                        # Salva a relação múltipla e preenche o campo singular enquanto consumidores antigos o usam.
                        turmas = form.cleaned_data.get('turma_professor')
                        if turmas:
                            for turma in turmas:
                                turma.professores.add(usuario)
                                if not turma.professor_id:
                                    turma.professor = usuario
                                    turma.save(update_fields=['professor'])

            messages.success(
                request,
                f'Cadastro de {tipo_conta} realizado com sucesso. Agora você já pode entrar.',
            )
            return redirect('login')
    else:
        form = CadastroUsuarioForm()

    return render(request, 'gestor/cadastro.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def atribuir_turma_ao_professor(usuario):
    # Primeiro acesso sem turma: associa o professor à primeira turma ainda sem responsável.
    if perfil_usuario(usuario) != 'professor':
        return False

    turma = Turma.objects.filter(professores__isnull=True, professor__isnull=True).order_by('nome').first() #professor__isnull=True para garantir que a turma não tenha um professor singular atribuído, evitando conflitos de responsabilidade
    if not turma:
        return False

    turma.professores.add(usuario)
    turma.professor = usuario
    turma.save(update_fields=['professor']) #update_fields=['professor'] para atualizar apenas o campo professor no banco de dados, evitando atualizações desnecessárias de outros campos do modelo Turma
    return True


# DASHBOARD 
@gestor_required
def dashboard(request):
    #Estatísticas gerais
    # Os contadores são agregados no banco para evitar carregar registros só para contá-los.
    total_alunos = Aluno.objects.count()
    total_atrasos_hoje = Atraso.objects.filter(data_atraso=datetime.now().date()).count()
    total_ocorrencias_mes = Ocorrencia.objects.filter(
        data_ocorrencia__month=datetime.now().month
    ).count()
    saidas_pendentes = SaidaAntecipada.objects.filter(status='pendente').count() # Conta as saídas pendentes
    pastas_atestados = PastaAtestado.objects.count()
    
    # annotate acrescenta uma contagem calculada na consulta sem alterar o modelo.
    # Assim o banco ordena pelos alunos com mais atrasos antes do [:5].
    alunos_atrasos = Aluno.objects.annotate(
        total_atrasos=Count('atrasos')
    ).order_by('-total_atrasos')[:5]
    
    # Últimos registros
    ultimos_atrasos = Atraso.objects.select_related('aluno').order_by('-data_atraso')[:5]
    ultimas_ocorrencias = Ocorrencia.objects.select_related('aluno').order_by('-data_ocorrencia')[:5]
    ultimas_saidas = SaidaAntecipada.objects.select_related('aluno').order_by('-data_saida')[:5]

    alunos_por_turma = list(
        Turma.objects.annotate(total_alunos=Count('alunos'))
        .values('nome', 'total_alunos')
        .order_by('-total_alunos', 'nome')[:8]
    )
    ocorrencias_por_tipo = dict(
        Ocorrencia.objects.values('tipo')
        .annotate(total=Count('id'))
        .values_list('tipo', 'total')
    )
    # Os valores persistidos são códigos; o dicionário converte cada código no rótulo do choice.
    tipos_ocorrencia = dict(Ocorrencia.TIPOS)
    ocorrencias_grafico = [
        {'label': tipos_ocorrencia[tipo], 'total': total}
        for tipo, total in ocorrencias_por_tipo.items()
    ]
    saidas_por_status = dict(
        SaidaAntecipada.objects.values('status')
        .annotate(total=Count('id'))
        .values_list('status', 'total')
    )
    # Traduz os códigos internos dos choices para rótulos que os gráficos podem exibir.
    status_saida = dict(SaidaAntecipada.STATUS)
    saidas_grafico = [
        {'label': status_saida[status], 'total': total}
        for status, total in saidas_por_status.items()
    ]
    # Prepara o contexto para a template
    context = {
        'total_alunos': total_alunos,
        'total_atrasos_hoje': total_atrasos_hoje,
        'total_ocorrencias_mes': total_ocorrencias_mes,
        'saidas_pendentes': saidas_pendentes,
        'pastas_atestados': pastas_atestados,
        'alunos_atrasos': alunos_atrasos,
        'ultimos_atrasos': ultimos_atrasos,
        'ultimas_ocorrencias': ultimas_ocorrencias,
        'ultimas_saidas': ultimas_saidas,
        'alunos_por_turma': alunos_por_turma,
        'ocorrencias_grafico': ocorrencias_grafico,
        'saidas_grafico': saidas_grafico,
    }
    
    return render(request, 'gestor/dashboard.html', context)


#ALUNOS
@professor_required
def lista_alunos(request):
    # Combina filtros opcionais sobre o queryset já limitado pelas permissões do usuário.
    alunos = alunos_visiveis(request)
    form = FiltroAlunoForm(request.GET, turmas_queryset=turmas_visiveis(request))
    
    if form.is_valid():
        if form.cleaned_data.get('turma'):
            alunos = alunos.filter(turma=form.cleaned_data['turma'])
        if form.cleaned_data.get('empresa'):
            alunos = alunos.filter(empresa=form.cleaned_data['empresa'])
        if form.cleaned_data.get('nome'):
            termo = form.cleaned_data['nome']
            alunos = alunos.filter(Q(nome__icontains=termo) | Q(matricula__icontains=termo))
        if form.cleaned_data.get('vinculo'):
            alunos = alunos.filter(vinculo=form.cleaned_data['vinculo'])
        if form.cleaned_data.get('destaque') == 'sim':
            alunos = alunos.filter(em_destaque=True)
        elif form.cleaned_data.get('destaque') == 'nao':
            alunos = alunos.filter(em_destaque=False)
    
    context = {'alunos': alunos, 'form': form}
    return render(request, 'gestor/alunos/lista.html', context)


@gestor_required
def criar_aluno(request):
    # Processa o cadastro no POST e reapresenta o formulário com erros quando inválido.
    if request.method == 'POST':
        form = AlunoForm(request.POST)
        if form.is_valid():
            aluno = form.save()
            messages.success(request, f'Aluno {aluno.nome} criado com sucesso!')
            return redirect('lista_alunos')
    else:
        form = AlunoForm()
    
    return render(request, 'gestor/alunos/form.html', {'form': form, 'titulo': 'Novo Aluno'})


@gestor_required
def importar_alunos(request):
    # Importa a planilha validada e devolve avisos sem expor mais erros do que a tela comporta.
    resultado = None

    if request.method == 'POST':
        form = ImportarAlunosForm(request.POST, request.FILES)
        
        if form.is_valid():
            resultado = importar_alunos_da_planilha(form.cleaned_data['arquivo'])
            if resultado.alunos_criados or resultado.alunos_atualizados:
                messages.success(
                    request,
                    f'{resultado.alunos_criados} aluno(s) cadastrado(s) e '
                    f'{resultado.alunos_atualizados} atualizado(s) com sucesso!',
                )
                # Exibe um limite de avisos na tela, mantendo o resumo da importação legível.
                for aviso in resultado.erros[:5]:
                    messages.warning(request, aviso)
                return redirect('lista_alunos')
            messages.error(request, 'Nenhum aluno válido foi encontrado na planilha.')
    else:
        form = ImportarAlunosForm()

    return render(request, 'gestor/alunos/importar.html', {
        'form': form,
        'resultado': resultado,
        'active_page': 'alunos',
    })


@gestor_required
def baixar_modelo_alunos(request):
    # Gera uma planilha de exemplo com os cabeçalhos esperados pelo importador.
    planilha = Workbook()
    aba = planilha.active
    aba.title = 'Alunos'
    aba.append([
        'Nº de Matrícula', 'Nome', 'Data de Nascimento', 'RG', 'CPF', 'Telefone',
        'Celular', 'Nome do Pai', 'Nome da Mãe', 'Endereço Aluno', 'Bairro',
        'Município', 'Estado', 'CEP', 'Curso', 'Turma', 'Tipo de turma', 'Horário', 'Carga Horária',
        'Data de Início', 'Data de Fim', 'Dias da Semana',
        'Empresa do contrato de aprendizagem', 'Observações/ Anotações',
    ])
    aba.append([
        '2027001', 'Aluno de Exemplo', date(2009, 1, 15), '00.000.000-0',
        '000.000.000-00', '(17) 3000-0000', '(17) 99999-9999', 'Nome do pai',
        'Nome da mãe', 'Rua de Exemplo, 100', 'Centro', 'São Paulo', 'SP',
        '00000-000', 'Curso de Exemplo', 'TURMA-1-26', 'CAI', 'Manhã', 1600,
        date(2026, 1, 1), date(2026, 12, 31), '2ª a 6ª Feira',
        'Nome da empresa (deixe em branco para AD)', 'Opcional',
    ])
    aba.freeze_panes = 'A2'
    aba.auto_filter.ref = aba.dimensions

    larguras = [16, 32, 18, 16, 16, 18, 18, 26, 26, 34, 18, 22, 15, 14, 32, 20, 20, 16, 18, 18, 20, 38, 38]
    # A lista acompanha a ordem dos cabeçalhos; chr converte cada índice em letra de coluna Excel.
    for coluna, largura in enumerate(larguras, start=1):
        aba.column_dimensions[chr(64 + coluna)].width = largura

    resposta = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    resposta['Content-Disposition'] = 'attachment; filename="modelo_importacao_alunos.xlsx"'
    planilha.save(resposta)
    return resposta


@gestor_required
def editar_aluno(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)
    
    if request.method == 'POST':
        form = AlunoForm(request.POST, instance=aluno)
        if form.is_valid():
            form.save()
            messages.success(request, f'Aluno {aluno.nome} atualizado com sucesso!')
            return redirect('detalhe_aluno', pk=aluno.pk)
    else:
        form = AlunoForm(instance=aluno)
    
    return render(request, 'gestor/alunos/form.html', {'form': form, 'titulo': f'Editar {aluno.nome}'})


@gestor_required
@require_POST
def deletar_aluno(request, pk):
    # A view só aceita POST para impedir exclusão por acesso direto a um link.
    aluno = get_object_or_404(Aluno, pk=pk)
    nome = aluno.nome
    aluno.delete()
    messages.success(request, f'Aluno {nome} removido com sucesso!')
    return redirect('lista_alunos')


@professor_required
def detalhe_aluno(request, pk):
    # O perfil gestor recebe também saídas e atestados; professores veem o histórico permitido.
    aluno = aluno_visivel_ou_404(request, pk)
    telefones = aluno.telefones.all()
    # Limita os históricos mostrados na ficha; o relatório completo fica na tela de relatórios.
    atrasos = aluno.atrasos.all()[:10]
    ocorrencias = aluno.ocorrencias.all()[:10]
    gestor = perfil_usuario(request.user) == 'gestor'
    saidas = aluno.saidas_antecipadas.all()[:5] if gestor else []
    atestados = aluno.atestados.all()[:5] if gestor else []
    
    context = {
        'aluno': aluno,
        'telefones': telefones,
        'atrasos': atrasos,
        'ocorrencias': ocorrencias,
        'saidas': saidas,
        'atestados': atestados,
    }
    
    return render(request, 'gestor/alunos/detalhe.html', context)


#ATRASOS
@professor_required
def lista_atrasos(request):
    # A contagem inclui todo o histórico do aluno, independentemente dos filtros da lista.
    atrasos = Atraso.objects.select_related('aluno', 'aluno__turma').annotate(
        total_atrasos=Count('aluno__atrasos', distinct=True)
    ).order_by('aluno__nome', '-data_atraso')
    if perfil_usuario(request.user) == 'professor':
        # Restringe primeiro ao escopo do professor antes de aplicar os filtros enviados pela tela.
        atrasos = atrasos.filter(
            Q(aluno__turma__professores=request.user) |
            Q(aluno__turma__professor=request.user)
        ).distinct()
    
    #Filtrar por turma e data
    turma = request.GET.get('turma')
    data = request.GET.get('data')
    
    if turma:
        atrasos = atrasos.filter(aluno__turma__id=turma)
    if data:
        atrasos = atrasos.filter(data_atraso=data)

    # Agrupa as ocorrências para mostrar uma linha por aluno e expandir o histórico.
    alunos_atrasos = {}
    for atraso in atrasos:
        if atraso.aluno_id not in alunos_atrasos:
            alunos_atrasos[atraso.aluno_id] = {
                'aluno': atraso.aluno,
                'total_atrasos': atraso.total_atrasos,
                'alerta_atrasos': (
                    atraso.aluno.alerta_atrasos_manual or
                    atraso.total_atrasos - atraso.aluno.atrasos_alerta_limpo_ate >= 3
                ),
                'registros': [],
            }
        alunos_atrasos[atraso.aluno_id]['registros'].append(atraso)
    
    turmas = turmas_visiveis(request)
    context = {'alunos_atrasos': alunos_atrasos.values(), 'turmas': turmas}
    return render(request, 'gestor/atrasos/lista.html', context)


@gestor_required
@require_POST
def alterar_alerta_atrasos(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)
    acao = request.POST.get('acao')

    if acao == 'ativar':
        aluno.alerta_atrasos_manual = True
        aluno.save(update_fields=['alerta_atrasos_manual'])
        messages.success(request, f'O alerta de atrasos de {aluno.nome} foi ativado.')
    elif acao == 'remover':
        # A contagem atual vira referência para o alerta voltar após três novos atrasos.
        aluno.alerta_atrasos_manual = False
        aluno.atrasos_alerta_limpo_ate = aluno.atrasos.count()
        aluno.save(update_fields=['alerta_atrasos_manual', 'atrasos_alerta_limpo_ate'])
        messages.success(request, f'O alerta de atrasos de {aluno.nome} foi removido.')
    else:
        return HttpResponseBadRequest('Ação de alerta inválida.')

    return redirect('lista_atrasos')


@gestor_required
def registrar_atraso(request):
    if request.method == 'POST':
        form = AttrasoForm(request.POST)
        if form.is_valid():
            # O responsável é definido no servidor para não confiar em um valor enviado pelo cliente.
            atraso = form.save(commit=False)
            atraso.registrado_por = request.user
            atraso.save()
            messages.success(request, f'Atraso registrado para {atraso.aluno.nome}!')
            return redirect('lista_atrasos')
    else:
        form = AttrasoForm()
    
    return render(request, 'gestor/atrasos/form.html', {'form': form, 'titulo': 'Registrar Atraso'})


@gestor_required
def editar_atraso(request, pk):
    atraso = get_object_or_404(Atraso, pk=pk)
    
    if request.method == 'POST':
        form = AttrasoForm(request.POST, instance=atraso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atraso atualizado com sucesso!')
            return redirect('lista_atrasos')
    else:
        form = AttrasoForm(instance=atraso)
    
    return render(request, 'gestor/atrasos/form.html', {'form': form, 'titulo': 'Editar Atraso'})


@gestor_required
def deletar_atraso(request, pk):
    atraso = get_object_or_404(Atraso, pk=pk)
    if request.method == 'POST':
        atraso.delete()
        messages.success(request, 'Atraso removido com sucesso!')
        return redirect('lista_atrasos')
    
    return render(request, 'gestor/confirmar_delecao.html', {'objeto': atraso})


# ====================== OCORRÊNCIAS ======================
@professor_required
def lista_ocorrencias(request):
    ocorrencias = Ocorrencia.objects.select_related('aluno').order_by('-data_ocorrencia')
    if perfil_usuario(request.user) == 'professor':
        # Aplica o controle de acesso antes dos filtros opcionais de turma e tipo.
        ocorrencias = ocorrencias.filter(
            Q(aluno__turma__professores=request.user) |
            Q(aluno__turma__professor=request.user)
        ).distinct()
    
    # Filtros
    turma = request.GET.get('turma')
    tipo = request.GET.get('tipo')
    
    if turma:
        ocorrencias = ocorrencias.filter(aluno__turma__id=turma)
    if tipo:
        ocorrencias = ocorrencias.filter(tipo=tipo)
    
    turmas = turmas_visiveis(request)
    tipos = Ocorrencia.TIPOS
    
    context = {'ocorrencias': ocorrencias, 'turmas': turmas, 'tipos': tipos}
    return render(request, 'gestor/ocorrencias/lista.html', context)


@professor_required
def registrar_ocorrencia(request):
    if request.method == 'POST':
        form = OcorrenciaForm(
            request.POST, request.FILES, alunos_queryset=alunos_visiveis(request),
        )
        if form.is_valid():
            # A autoria também é atribuída no servidor, não aceita do formulário.
            ocorrencia = form.save(commit=False)
            ocorrencia.registrado_por = request.user
            ocorrencia.save()
            messages.success(request, f'Ocorrência registrada para {ocorrencia.aluno.nome}!')
            return redirect('lista_ocorrencias')
    else:
        form = OcorrenciaForm(
            alunos_queryset=alunos_visiveis(request), initial={'data_ocorrencia': date.today()},
        )
    
    return render(request, 'gestor/ocorrencias/form.html', {'form': form, 'titulo': 'Registrar Ocorrência'})


@professor_required
def editar_ocorrencia(request, pk):
    # A consulta limitada por perfil impede editar ocorrências de turmas não acessíveis.
    ocorrencia = ocorrencia_visivel_ou_404(request, pk)
    
    if request.method == 'POST':
        form = OcorrenciaForm(
            request.POST, request.FILES, instance=ocorrencia, alunos_queryset=alunos_visiveis(request),
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Ocorrência atualizada com sucesso!')
            return redirect('lista_ocorrencias')
    else:
        form = OcorrenciaForm(instance=ocorrencia, alunos_queryset=alunos_visiveis(request))
    
    return render(request, 'gestor/ocorrencias/form.html', {'form': form, 'titulo': 'Editar Ocorrência'})


@gestor_required
def deletar_ocorrencia(request, pk):
    # A confirmação via POST evita excluir o registro por uma simples visita à URL.
    ocorrencia = get_object_or_404(Ocorrencia, pk=pk)
    if request.method == 'POST':
        ocorrencia.delete()
        messages.success(request, 'Ocorrência removida com sucesso!')
        return redirect('lista_ocorrencias')
    
    return render(request, 'gestor/confirmar_delecao.html', {'objeto': ocorrencia})


@professor_required
def baixar_deliberacao_pdf(request, pk):
    # Reutiliza a mesma verificação de acesso aplicada à tela da ocorrência.
    ocorrencia = ocorrencia_visivel_ou_404(request, pk)
    return resposta_pdf_deliberacao(ocorrencia)


@professor_required
def baixar_preconselho_pdf(request, pk):
    # Restringe a busca às turmas que o perfil atual pode consultar.
    preconselho = get_object_or_404(
        PreConselho.objects.select_related('turma').filter(
            turma__in=turmas_visiveis(request),
        ),
        pk=pk,
    )
    return resposta_pdf_preconselho(preconselho)


# ====================== SAÍDAS ANTECIPADAS ======================
@professor_required
def lista_saidas(request):
    """O gestor registra a saida e o professor da turma confirma/autoriza."""
    # A consulta inicial já limita as saídas às turmas acessíveis ao perfil atual.
    saidas = saidas_visiveis(request).order_by('-data_saida', '-hora_saida')

    # Filtros
    status = request.GET.get('status')
    turma_id = request.GET.get('turma')

    if status:
        saidas = saidas.filter(status=status)
    if turma_id:
        saidas = saidas.filter(aluno__turma_id=turma_id)

    context = {
        'saidas': saidas,
        'status_choices': SaidaAntecipada.STATUS,
        'turmas': turmas_visiveis(request),
        'turma_selecionada': turma_id,
        'active_page': 'saidas',
    }
    return render(request, 'gestor/saidas/lista.html', context)


@gestor_required
def registrar_saida(request):
    if request.method == 'POST':
        form = SaidaAntecipadadaForm(request.POST)
        if form.is_valid():
            # O usuário responsável não vem do formulário e é associado no servidor.
            saida = form.save(commit=False)
            saida.registrado_por = request.user
            saida.save()
            messages.success(request, f'Saída antecipada registrada para {saida.aluno.nome}!')
            return redirect('lista_saidas')
    else:
        form = SaidaAntecipadadaForm()
    
    return render(request, 'gestor/saidas/form.html', {'form': form, 'titulo': 'Registrar Saída Antecipada'})


@gestor_required
def editar_saida(request, pk):
    saida = get_object_or_404(SaidaAntecipada, pk=pk)
    
    if request.method == 'POST':
        form = SaidaAntecipadadaForm(request.POST, instance=saida)
        if form.is_valid():
            form.save()
            messages.success(request, 'Saída antecipada atualizada com sucesso!')
            return redirect('lista_saidas')
    else:
        form = SaidaAntecipadadaForm(instance=saida)
    
    return render(request, 'gestor/saidas/form.html', {'form': form, 'titulo': 'Editar Saída Antecipada'})


@professor_required
@require_POST
def aprovar_saida(request, pk):
    """Professor da turma (ou gestor) confirma a saida registrada pelo gestor."""
    # Registra quem autorizou, quando e a observação enviada na confirmação.
    saida = saida_visivel_ou_404(request, pk)
    saida.status = 'autorizada'
    saida.autorizado_por = request.user
    saida.data_autorizacao = timezone.now()
    saida.observacao_autorizacao = request.POST.get('observacao', '').strip()
    saida.save()
    messages.success(request, f'Saída de {saida.aluno.nome} autorizada!')
    return redirect('lista_saidas')


@professor_required
@require_POST
def rejeitar_saida(request, pk):
    # Mantém o histórico da decisão junto com o status de rejeição.
    saida = saida_visivel_ou_404(request, pk)
    saida.status = 'rejeitada'
    saida.autorizado_por = request.user
    saida.data_autorizacao = timezone.now()
    saida.observacao_autorizacao = request.POST.get('observacao', '').strip()
    saida.save()
    messages.warning(request, f'Saída de {saida.aluno.nome} rejeitada.')
    return redirect('lista_saidas')


# ====================== ATESTADOS ======================
@gestor_required
def lista_atestados(request):
    # Carrega os PDFs de cada pasta em lote e prepara o formulário da pasta selecionada.
    pastas = PastaAtestado.objects.prefetch_related('documentos').all()
    pasta_aberta = None
    form_documento = None
    pasta_id = request.GET.get('pasta')
    if pasta_id:
        pasta_aberta = get_object_or_404(PastaAtestado, pk=pasta_id)
        form_documento = DocumentoAtestadoForm()
    return render(request, 'gestor/atestados/lista.html', {
        'pastas': pastas,
        'pasta_aberta': pasta_aberta,
        'form_documento': form_documento,
    })


@gestor_required
def registrar_atestado(request):
    if request.method == 'POST':
        form = PastaAtestadoForm(request.POST, request.FILES)
        if form.is_valid():
            # A pasta e seu primeiro PDF formam uma única operação: ambas são salvas ou nenhuma.
            with transaction.atomic():
                pasta = form.save(commit=False)
                pasta.criada_por = request.user
                pasta.save()
                documento = DocumentoAtestado(
                    pasta=pasta,
                    enviado_por=request.user,
                )
                documento.arquivo = form.cleaned_data['pdf']
                documento.save()
            messages.success(request, 'Pasta de atestados criada e PDF enviado.')
            return redirect('lista_atestados')
    else:
        form = PastaAtestadoForm()
    
    return render(request, 'gestor/atestados/pasta_form.html', {
        'form': form,
        'titulo': 'Criar pasta de atestados',
    })

#PDF a uma pasta de atestados existente, associando o arquivo ao usuário que fez o upload e à pasta selecionada. Se o formulário for inválido, mantém a pasta aberta para que o usuário possa corrigir o erro sem perder o contexto.
@gestor_required
@require_POST
def adicionar_pdf_atestado(request, pk):
    # Associa o novo arquivo à pasta e ao usuário somente após a validação do formulário.
    pasta = get_object_or_404(PastaAtestado, pk=pk)
    form = DocumentoAtestadoForm(request.POST, request.FILES)
    if form.is_valid():
        documento = form.save(commit=False)
        documento.pasta = pasta
        documento.enviado_por = request.user
        documento.save()
        messages.success(request, 'PDF adicionado à pasta de atestados.')
    else:
        # Mantém a pasta selecionada aberta para que o usuário corrija o upload sem perder o contexto.
        messages.error(request, form.errors.get('arquivo', ['Não foi possível adicionar o PDF.'])[0])
    return redirect(f"{reverse('lista_atestados')}?pasta={pasta.pk}")

#permite que o gestor atualize informações como o aluno associado, a data do atestado e o arquivo PDF. A view verifica se o formulário enviado é válido antes de salvar as alterações no banco de dados e exibe mensagens de sucesso ou erro conforme necessário.
@gestor_required
def editar_atestado(request, pk):
    atestado = get_object_or_404(Atestado, pk=pk)
    
    if request.method == 'POST':
        form = AtestadoForm(request.POST, request.FILES, instance=atestado)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atestado atualizado com sucesso!')
            return redirect('lista_atestados')
    else:
        form = AtestadoForm(instance=atestado)
    
    return render(request, 'gestor/atestados/form.html', {'form': form, 'titulo': 'Editar Atestado'})

#permite que o gestor atualize informações como o aluno associado, a data do atestado e o arquivo PDF. A view verifica se o formulário enviado é válido antes de salvar as alterações no banco de dados e exibe mensagens de sucesso ou erro conforme necessário.
@gestor_required
@require_POST
def aprovar_atestado(request, pk):
    atestado = get_object_or_404(Atestado, pk=pk)
    atestado.status = 'aprovado'
    atestado.save()
    messages.success(request, 'Atestado aprovado!')
    return redirect('lista_atestados')


@gestor_required
@require_POST
def rejeitar_atestado(request, pk):
    atestado = get_object_or_404(Atestado, pk=pk)
    atestado.status = 'rejeitado'
    atestado.save()
    messages.success(request, 'Atestado rejeitado!')
    return redirect('lista_atestados')


@gestor_required
@require_POST
def deletar_atestado(request, pk):
    # Remove o arquivo físico antes do registro para não deixar o documento órfão no armazenamento.
    atestado = get_object_or_404(Atestado, pk=pk)
    nome_aluno = atestado.aluno.nome
    if atestado.arquivo:
        atestado.arquivo.delete(save=False)
    atestado.delete()
    messages.success(request, f'Atestado de {nome_aluno} excluído com sucesso!')
    return redirect('lista_atestados')


# ====================== RELATÓRIOS ======================
#funciona como uma visão que lista os alunos e permite filtrar por nome, matrícula, turma ou empresa. O resultado é exibido em uma página de relatórios, onde o gestor pode selecionar um aluno específico para visualizar detalhes adicionais.
@gestor_required
def lista_relatorios(request):
    alunos = Aluno.objects.select_related('turma', 'empresa').order_by('nome')
    busca = request.GET.get('busca', '').strip()

    if busca:
        alunos = alunos.filter(
            Q(nome__icontains=busca) | 
            Q(matricula__icontains=busca) |
            Q(turma__nome__icontains=busca) |
            Q(empresa__nome__icontains=busca)
        )

    return render(request, 'gestor/relatorios/lista.html', {
        'alunos': alunos,
        'busca': busca,
        'active_page': 'relatorios',
    })


@gestor_required
def relatorio_aluno(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)
    
    # Aplica o mesmo intervalo às quatro categorias para manter o relatório consistente.
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    atrasos = aluno.atrasos.all()
    ocorrencias = aluno.ocorrencias.all()
    saidas = aluno.saidas_antecipadas.all()
    atestados = aluno.atestados.all()
    # Filtra os registros de acordo com as datas fornecidas, se houver.
    if data_inicio:
        atrasos = atrasos.filter(data_atraso__gte=data_inicio)
        ocorrencias = ocorrencias.filter(data_ocorrencia__gte=data_inicio)
        saidas = saidas.filter(data_saida__gte=data_inicio)
        atestados = atestados.filter(data_atestado__gte=data_inicio)
    # Filtra os registros de acordo com as datas fornecidas, se houver.
    if data_fim:
        atrasos = atrasos.filter(data_atraso__lte=data_fim)
        ocorrencias = ocorrencias.filter(data_ocorrencia__lte=data_fim)
        saidas = saidas.filter(data_saida__lte=data_fim)
        atestados = atestados.filter(data_atestado__lte=data_fim)
    # Prepara o contexto para a template, incluindo os registros filtrados e o aluno selecionado.
    context = {
        'aluno': aluno,
        'atrasos': atrasos,
        'ocorrencias': ocorrencias,
        'saidas': saidas,
        'atestados': atestados,
        'active_page': 'relatorios',
    }
    
    return render(request, 'gestor/relatorios/aluno.html', context)


# ====================== TURMAS ======================
# A view lista_turmas exibe uma lista de turmas visíveis para o usuário atual, permitindo filtrar por nome da turma, período ou nome do professor. A contagem de alunos em cada turma é calculada no banco de dados para otimizar o desempenho. O resultado é renderizado em um template específico para exibir as turmas e os filtros aplicados.
@professor_required
def lista_turmas(request):
    # A contagem é calculada no banco; distinct evita repetir turmas após a busca por professores.
    busca = request.GET.get('busca', '').strip()
    turmas = turmas_visiveis(request).annotate(total_alunos=Count('alunos'))

    if busca:
        # A busca cobre os campos de nome dos vínculos atual e legado de professor.
        turmas = turmas.filter(
            Q(nome__icontains=busca) |
            Q(periodo__nome__icontains=busca) |
            Q(professores__first_name__icontains=busca) |
            Q(professores__last_name__icontains=busca) |
            Q(professores__username__icontains=busca) |
            Q(professor__first_name__icontains=busca) |
            Q(professor__last_name__icontains=busca) |
            Q(professor__username__icontains=busca)
        ).distinct()

    return render(request, 'gestor/turmas/lista.html', {
        'turmas': turmas,
        'busca': busca,
        'active_page': 'turmas',
    })

# ====================== PERÍODOS ======================
# A view criar_turma permite que o gestor crie uma nova turma. Se a requisição for do tipo POST, o formulário é validado e, se estiver correto, a turma é salva no banco de dados e uma mensagem de sucesso é exibida. Caso contrário, o formulário é renderizado novamente para correção. Se a requisição não for POST, um formulário vazio é apresentado para o usuário preencher.
@gestor_required
def criar_turma(request):
    if request.method == 'POST':
        form = TurmaForm(request.POST)
        if form.is_valid():
            turma = form.save()
            messages.success(request, f'Turma {turma.nome} cadastrada com sucesso!')
            return redirect('lista_turmas')
    else:
        form = TurmaForm()

    return render(request, 'gestor/turmas/form.html', {
        'form': form,
        'titulo': 'Cadastrar turma',
        'active_page': 'turmas',
    })


@gestor_required
def editar_turma(request, pk):
    turma = get_object_or_404(Turma, pk=pk)

    if request.method == 'POST':
        form = TurmaForm(request.POST, instance=turma)
        if form.is_valid():
            turma = form.save()
            messages.success(request, f'Turma {turma.nome} atualizada com sucesso!')
            return redirect('lista_turmas')
    else:
        form = TurmaForm(instance=turma)

    return render(request, 'gestor/turmas/form.html', {
        'form': form,
        'titulo': 'Editar turma',
        'active_page': 'turmas',
    })


@gestor_required
def lista_periodos(request):
    periodos = Periodo.objects.order_by('-data_inicio')
    return render(request, 'gestor/periodos/lista.html', {
        'periodos': periodos,
        'active_page': 'turmas',
    })

#
@gestor_required
def criar_periodo(request):
    if request.method == 'POST':
        form = PeriodoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Período letivo cadastrado com sucesso!')
            return redirect('lista_periodos')
    else:
        form = PeriodoForm()
    return render(request, 'gestor/periodos/form.html', {
        'form': form,
        'titulo': 'Cadastrar período letivo',
        'active_page': 'turmas',
    })


@gestor_required
def editar_periodo(request, pk):
    periodo = get_object_or_404(Periodo, pk=pk)
    if request.method == 'POST':
        form = PeriodoForm(request.POST, instance=periodo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Período letivo atualizado com sucesso!')
            return redirect('lista_periodos')
    else:
        form = PeriodoForm(instance=periodo)
    return render(request, 'gestor/periodos/form.html', {
        'form': form,
        'titulo': 'Editar período letivo',
        'active_page': 'turmas',
    })

#
@gestor_required
@require_POST
def deletar_periodo(request, pk):
    periodo = get_object_or_404(Periodo, pk=pk)
    # Impede remover um período ainda referenciado por turmas.
    if periodo.turma_set.exists():
        messages.error(request, 'Não é possível excluir um período que possui turmas. Edite ou exclua as turmas primeiro.')
    else:
        periodo.delete()
        messages.success(request, 'Período letivo removido com sucesso!')
    return redirect('lista_periodos')


@gestor_required
@require_POST
def deletar_turma(request, pk):
    turma = get_object_or_404(Turma, pk=pk)
    nome = turma.nome
    turma.delete()
    messages.success(request, f'Turma {nome} removida com sucesso!')
    return redirect('lista_turmas')


# ====================== EMPRESAS ======================
@gestor_required
def lista_empresas(request):
    busca = request.GET.get('busca', '').strip()
    empresas = Empresa.objects.annotate(total_alunos=Count('aluno'))

    if busca:
        empresas = empresas.filter(
            Q(nome__icontains=busca) |
            Q(cnpj__icontains=busca) |
            Q(cidade__icontains=busca) |
            Q(estado__icontains=busca)
        )

    return render(request, 'gestor/empresas/lista.html', {
        'empresas': empresas,
        'busca': busca,
        'active_page': 'empresas',
    })


@gestor_required
def criar_empresa(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save()
            messages.success(request, f'Empresa {empresa.nome} cadastrada com sucesso!')
            return redirect('lista_empresas')
    else:
        form = EmpresaForm()

    return render(request, 'gestor/empresas/form.html', {
        'form': form,
        'titulo': 'Cadastrar empresa',
        'active_page': 'empresas',
    })


@gestor_required
def editar_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)

    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            empresa = form.save()
            messages.success(request, f'Empresa {empresa.nome} atualizada com sucesso!')
            return redirect('lista_empresas')
    else:
        form = EmpresaForm(instance=empresa)

    return render(request, 'gestor/empresas/form.html', {
        'form': form,
        'titulo': 'Editar empresa',
        'active_page': 'empresas',
    })


@gestor_required
@require_POST
def deletar_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    nome = empresa.nome
    empresa.delete()
    messages.success(request, f'Empresa {nome} removida com sucesso!')
    return redirect('lista_empresas')


# ====================== PRÉ-CONSELHO (somente gestor) ======================
def _data_do_request(request, campo='data'):
    """Le uma data YYYY-MM-DD da query string; volta para hoje se invalida."""
    valor = request.GET.get(campo) or request.POST.get(campo)
    if valor:
        try:
            return datetime.strptime(valor, '%Y-%m-%d').date()
        except ValueError:
            pass
    return date.today()


@professor_required
def preconselho_turmas(request):
    """Passo 1: gestor ou professor escolhe uma turma visivel."""
    busca = request.GET.get('busca', '').strip()
    aba = request.GET.get('aba', 'turmas')
    turmas = (
        turmas_visiveis(request)
        .select_related('periodo', 'professor')
        .annotate(
            # distinct impede que joins com alunos e reuniões multipliquem as contagens.
            total_alunos=Count('alunos', distinct=True),
            total_preconselhos=Count('preconselhos', distinct=True),
        )
        .order_by('nome')
    )

    if busca:
        turmas = turmas.filter(
            Q(nome__icontains=busca) |
            Q(curso__icontains=busca) |
            Q(periodo__nome__icontains=busca) |
            Q(professores__first_name__icontains=busca) |
            Q(professores__last_name__icontains=busca) |
            Q(professores__username__icontains=busca) |
            Q(professor__first_name__icontains=busca) |
            Q(professor__last_name__icontains=busca) |
            Q(professor__username__icontains=busca)
            ).distinct()

    # Agrupa reuniões por turma; a ordenação descendente deixa a mais recente na posição zero.
    reunioes_por_turma = {}
    for pc in PreConselho.objects.filter(turma__in=turmas).order_by('turma_id', '-data_reuniao'):
        reunioes_por_turma.setdefault(pc.turma_id, []).append(pc)

    ultimos = {}
    for turma_id, reunioes in reunioes_por_turma.items():
        ultimos[turma_id] = reunioes[0]

    turmas = list(turmas)
    for turma in turmas:
        turma.reunioes_preconselho = reunioes_por_turma.get(turma.pk, [])
        turma.ultimo_preconselho = ultimos.get(turma.pk)

    reunioes_salvas = (
        PreConselho.objects.filter(turma__in=turmas)
        .select_related('turma')
        .annotate(total_anotacoes=Count('anotacoes', distinct=True))
        .order_by('-data_reuniao', 'turma__nome')
    )

    return render(request, 'gestor/preconselho/turmas.html', {
        'turmas': turmas,
        'reunioes_salvas': reunioes_salvas,
        'busca': busca,
        'aba': aba,
        'hoje': date.today(),
        'active_page': 'preconselho',
    })


@professor_required
def preconselho_turma(request, pk):
    """Passo 2: lista alunos visiveis e grava observacoes do pre-conselho."""
    turma = get_object_or_404(
        turmas_visiveis(request).select_related('periodo', 'professor'),
        pk=pk,
    )
    data_reuniao = _data_do_request(request)
    somente_observacoes = perfil_usuario(request.user) == 'professor'

    # Professores só podem preencher observações de uma reunião já criada pelo gestor.
    if somente_observacoes:
        preconselho = get_object_or_404(
            PreConselho,
            turma=turma,
            data_reuniao=data_reuniao,
        )
        criado = False
    else:
        preconselho, criado = PreConselho.objects.get_or_create(
            turma=turma,
            data_reuniao=data_reuniao,
            defaults={
                'periodo': turma.periodo,
                'criado_por': request.user,
            },
        )
    # O sinalizador informa ao template se esta reunião foi criada por esta própria consulta.
    # Uma reunião fechada fica somente para consulta, inclusive em tentativas via POST.
    pode_editar = preconselho.status == 'aberto'

    if request.method == 'POST' and not pode_editar:
        messages.error(request, 'Esta reunião está fechada e não pode mais ser editada.')
        return redirect(f'{request.path}?data={preconselho.data_reuniao:%Y-%m-%d}')

    alunos = turma.alunos.filter(ativo=True).order_by('nome')

    # Garante uma anotação (ainda vazia) para cada aluno ativo da turma.
    # O dicionário indexado por aluno evita buscas repetidas ao criar anotações faltantes.
    existentes = {a.aluno_id: a for a in preconselho.anotacoes.all()}
    for aluno in alunos:
        if aluno.pk not in existentes:
            existentes[aluno.pk] = AnotacaoPreConselho.objects.create(
                preconselho=preconselho,
                aluno=aluno,
                registrado_por=request.user,
            )

    if request.method == 'POST':
        form_cabecalho = PreConselhoForm(
            request.POST,
            instance=preconselho,
            somente_observacoes=somente_observacoes,
        )
        # O prefixo inclui o ID do aluno para que os campos de cada formulário não colidam no POST.
        formularios = [
            (aluno, AnotacaoPreConselhoForm(
                request.POST,
                instance=existentes[aluno.pk],
                prefix=f'aluno{aluno.pk}',
                somente_observacoes=somente_observacoes,
            ))
            for aluno in alunos
        ]

        # Valida o cabeçalho e todas as anotações antes de gravar qualquer alteração.
        tudo_ok = form_cabecalho.is_valid() and all(f.is_valid() for _, f in formularios)
        if tudo_ok:
            # A transação mantém cabeçalho e anotações da reunião sincronizados.
            with transaction.atomic():
                form_cabecalho.save()
                for _, formulario in formularios:
                    anotacao = formulario.save(commit=False)
                    anotacao.registrado_por = request.user
                    anotacao.save()
            messages.success(
                request,
                f'Anotações do conselho da turma {turma.nome} salvas com sucesso!',
            )
            url = f"{request.path}?data={preconselho.data_reuniao:%Y-%m-%d}"
            return redirect(url)
        messages.error(request, 'Confira os campos destacados antes de salvar.')
    else:
        form_cabecalho = PreConselhoForm(
            instance=preconselho,
            somente_observacoes=somente_observacoes,
        )
        formularios = [
            (aluno, AnotacaoPreConselhoForm(
                instance=existentes[aluno.pk],
                prefix=f'aluno{aluno.pk}',
                somente_observacoes=somente_observacoes,
            ))
            for aluno in alunos
        ]

    if not pode_editar:
        # Desabilita os campos no formulário além de bloquear a gravação no servidor.
        for campo in form_cabecalho.fields.values():
            campo.disabled = True
        for _, formulario in formularios:
            for campo in formulario.fields.values():
                campo.disabled = True

    linhas = []
    for aluno, formulario in formularios:
        linhas.append({
            'aluno': aluno,
            'form': formulario,
            'anotacao': existentes[aluno.pk],
            'total_atrasos': aluno.atrasos.count(),
            'total_ocorrencias': aluno.ocorrencias.count(),
            'total_saidas': aluno.saidas_antecipadas.count(),
        })

    # Conta apenas anotações com texto ou encaminhamentos para exibir o progresso da turma.
    total_preenchidas = sum(1 for linha in linhas if linha['anotacao'].preenchida)

    return render(request, 'gestor/preconselho/turma.html', {
        'turma': turma,
        'preconselho': preconselho,
        'form_cabecalho': form_cabecalho,
        'linhas': linhas,
        'total_alunos': len(linhas),
        'total_preenchidas': total_preenchidas,
        'reunioes': turma.preconselhos.order_by('-data_reuniao')[:12],
        'data_reuniao': preconselho.data_reuniao,
        'criado_agora': criado,
        'pode_editar': pode_editar,
        'active_page': 'preconselho',
    })


@gestor_required
@require_POST
def preconselho_excluir(request, pk):
    """Remove uma reuniao de pre-conselho (e as anotacoes dela)."""
    preconselho = get_object_or_404(PreConselho, pk=pk)
    turma_id = preconselho.turma_id
    # A relação em cascata remove também as anotações ligadas a esta reunião.
    preconselho.delete()
    messages.success(request, 'Conselho excluído.')
    return redirect('preconselho_turma', pk=turma_id)
