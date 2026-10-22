# GAE — Gestão do Apoio Educacional

Sistema web Django para apoiar rotinas de gestão educacional: cadastro de alunos, turmas e empresas, acompanhamento de atrasos, ocorrências, atestados, saídas antecipadas e relatórios.

> **Demonstração local:** use apenas dados fictícios. Valide as funcionalidades no seu ambiente antes de hospedar.

## Tecnologias
- Python e Django
- SQLite para teste local (padrão); MySQL opcional
- HTML, CSS e JavaScript
- Bibliotecas para importação de planilhas e geração de relatórios

## Executar no Windows (PowerShell)
Recomendado Python 3.11 ou 3.12. Na pasta do projeto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abra http://127.0.0.1:8000/ no navegador. O painel administrativo fica em http://127.0.0.1:8000/admin/.

Se `py -3.12` não existir, instale uma versão compatível do Python e use `python -m venv .venv`.

## Dados de demonstração
O repositório contém um comando de dados de teste em `gestor/management/commands/popular_dados_teste.py`. Como comandos personalizados podem depender do estado atual dos modelos, execute-o apenas depois de `migrate` e valide localmente. Não execute em produção e não use credenciais conhecidas em hospedagem.

Consulte **[GUIA_BANCO_DE_DADOS.md](GUIA_BANCO_DE_DADOS.md)** para o passo a passo de SQLite e MySQL Workbench.

## Usar MySQL (opcional)
Instale `requirements-mysql.txt`, crie um banco e usuário próprios e configure no PowerShell:

```powershell
pip install -r requirements-mysql.txt
$env:DB_ENGINE = "mysql"
$env:DB_NAME = "gae_db"
$env:DB_USER = "seu_usuario"
$env:DB_PASSWORD = "sua_senha"
$env:DB_HOST = "127.0.0.1"
$env:DB_PORT = "3306"
$env:DJANGO_SECRET_KEY = "uma-chave-longa-aleatoria"
python manage.py migrate
```

Nunca coloque senhas reais no código ou no GitHub.

## Segurança antes de hospedar
- Não use `DEBUG=True` em produção.
- Gere uma `DJANGO_SECRET_KEY` exclusiva e forte.
- Configure `DJANGO_ALLOWED_HOSTS` com seu domínio.
- Use HTTPS e cookies seguros na hospedagem.
- Não publique bancos, `.env`, uploads, documentos ou dados pessoais.
- Não execute o comando de dados fictícios em produção.
- Verifique o histórico Git por credenciais antigas antes de tornar o repositório público.

## Estrutura
- `aqv/`: configurações e URLs
- `gestor/`: fluxos principais
- `alunos/`, `atrasos/`, `ocorrencias/`, `atestado/`, `saidas/`: módulos
- `*/migrations/`: migrações do banco

Consulte `DIREITOS_AUTORAIS.md` antes de definir permissões de reutilização.
