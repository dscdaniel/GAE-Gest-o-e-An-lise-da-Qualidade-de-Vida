# Guia de preparação do banco de dados do GAE

Este guia explica como preparar o banco para **teste local**. Use somente dados fictícios. Não use informações reais de alunos no GitHub ou em uma demonstração pública.

## Opção A — Testar rapidamente com SQLite (recomendado para primeira execução)

SQLite não exige instalação de servidor nem configuração no MySQL Workbench. O projeto usa SQLite por padrão.

1. Instale Python 3.12 ou mais recente.
2. Extraia o ZIP e abra o PowerShell na pasta `GAE` (a pasta que contém `manage.py`).
3. Execute:

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

4. Abra `http://127.0.0.1:8000/`. O painel administrativo fica em `http://127.0.0.1:8000/admin/`.
5. Se quiser popular o banco local com dados fictícios, execute o comando de demonstração descrito no README **somente depois de confirmar que o comando está disponível**. Não use os usuários de demonstração em produção.

O arquivo `db.sqlite3` será criado automaticamente. Ele é ignorado pelo `.gitignore` e não deve ser enviado ao GitHub.

## Opção B — MySQL com MySQL Workbench

### 1. Criar o banco

Abra o MySQL Workbench, conecte-se ao seu servidor local e execute este SQL:

```sql
CREATE DATABASE gae_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'gae_app'@'localhost' IDENTIFIED BY 'TROQUE_POR_UMA_SENHA_FORTE';
GRANT ALL PRIVILEGES ON gae_db.* TO 'gae_app'@'localhost';
FLUSH PRIVILEGES;
```

Troque a senha de exemplo por uma senha forte. Não use o usuário `root` na aplicação.

Se o usuário já existir, não repita o `CREATE USER`; ajuste a senha/permissões conforme necessário. Se a conexão vier de outro computador, a configuração do usuário MySQL e do firewall será diferente; não exponha a porta do MySQL à internet sem uma configuração segura.

### 2. Instalar o driver

No PowerShell, dentro da pasta `GAE` e com o ambiente virtual ativado:

```powershell
pip install -r requirements-mysql.txt
```

No Windows, `mysqlclient` pode exigir ferramentas de compilação ou uma wheel compatível. Se a instalação falhar, use primeiro a opção SQLite para validar a aplicação; não altere o código aleatoriamente.

### 3. Configurar a conexão (PowerShell)

Configure as variáveis abaixo na mesma janela do PowerShell em que executará o Django:

```powershell
$env:DB_ENGINE = "mysql"
$env:DB_NAME = "gae_db"
$env:DB_USER = "gae_app"
$env:DB_PASSWORD = "COLOQUE_A_SENHA_QUE_VOCE_CRIou"
$env:DB_HOST = "127.0.0.1"
$env:DB_PORT = "3306"
$env:DJANGO_SECRET_KEY = "substitua-por-uma-chave-aleatoria-longa"
$env:DJANGO_DEBUG = "True"
$env:DJANGO_ALLOWED_HOSTS = "127.0.0.1,localhost"
```

Use a senha real que definiu no MySQL Workbench no valor de `DB_PASSWORD`. Não salve a senha no README nem no Git.

### 4. Criar as tabelas

Ainda na pasta que contém `manage.py`, execute:

```powershell
python manage.py check
python manage.py showmigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

O comando `migrate` cria/atualiza as tabelas com base nas migrações incluídas no projeto. Não é necessário criar cada tabela manualmente no Workbench.

### 5. Se ocorrer erro

- `Access denied`: confira usuário, senha e permissões.
- `Unknown database`: confirme se `gae_db` foi criado.
- `Can't connect`: confira se o serviço MySQL está iniciado e se host/porta estão corretos.
- Erro de driver: confirme que `requirements-mysql.txt` foi instalado no ambiente virtual correto.
- Erro de migração: pare e guarde a mensagem completa; não apague migrações existentes nem rode `makemigrations` às cegas.

## Antes de hospedar online

Para produção, use um banco separado e credenciais próprias, `DJANGO_DEBUG=False`, uma `DJANGO_SECRET_KEY` aleatória e `DJANGO_ALLOWED_HOSTS` limitado ao domínio publicado. Configure HTTPS. Não execute scripts de dados fictícios em produção.
