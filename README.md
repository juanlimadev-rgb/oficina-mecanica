# Sistema para Oficina Mecânica

Aplicação de gestão de clientes, motos e ordens de serviço, desenvolvida por Juan Pablo Oliveira Lima com **Python, Flask, SQLAlchemy, SQLite, HTML, CSS e JavaScript**. Mantém a arquitetura original de modelos, blueprints e templates Jinja.

## Funcionalidades

- Login com senha protegida por hash e cadastro de usuários autenticados.
- Cadastro, pesquisa, edição e exclusão de clientes.
- Ordens com itens, quantidades, valores, pagamento e status.
- Histórico e filtros por cliente, período e situação.
- Faturamento e financeiro: apenas ordens **finalizadas** entram na receita.
- Recibo PDF com dados da oficina, cliente, serviços e total.
- Persistência local em SQLite; configuração opcional para MySQL.

Os usuários pertencem à mesma oficina e compartilham os registros. Não há separação de empresas ou ambientes por usuário.

## Executar no Windows

Requisito validado nesta revisão: **Python 3.13**.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.lock.txt
.venv/Scripts/python.exe -m flask --app app create-user
.venv/Scripts/python.exe app.py
```

O comando `create-user` pergunta nome, login e senha com confirmação. Não existe usuário/senha padrão. Abra http://127.0.0.1:5000/login. Novos usuários também podem ser cadastrados pela tela Cadastro após autenticação.

Em Linux/macOS, substitua `.venv/Scripts/python.exe` por `.venv/bin/python`. Esses ambientes não foram executados nesta revisão.

`requirements.txt` preserva os requisitos diretos do projeto. `requirements.lock.txt` registra as versões completas validadas para reprodução da instalação. O inicializador `iniciar.bat` também está disponível; a criação do primeiro usuário continua sendo explícita pelo comando acima.

## Arquitetura e dados

```text
app.py                 fábrica Flask, configuração, autenticação/CSRF e CLI
models.py              modelos SQLAlchemy
routes/                blueprints e validação de entradas
pdf_generator.py       recibo PDF
static/                estilos, scripts e logo
templates/             páginas Jinja
tests/                 testes integrados com banco temporário
instance/              dados locais; nunca versionados
```

O banco padrão fica em `instance/oficina.db`, os recibos em `instance/pdfs/` e a chave de sessão em `instance/session-secret`. A chave é criada aleatoriamente na primeira execução e reutilizada. Não envie essa pasta ao GitHub.

Para um banco SQLite diferente, configure `DATABASE_URL` com uma URI SQLAlchemy de caminho absoluto. Para reutilizar uma base antiga, feche o sistema, faça backup e aponte a variável ao arquivo ou copie-o para `instance/oficina.db` **antes** de iniciar a aplicação. A revisão não apaga nem recria bancos existentes e não migra dados automaticamente.

`SECRET_KEY` permite fornecer a chave de sessão por variável de ambiente. `PORT` altera a porta local. A aplicação escuta somente em `127.0.0.1`, com debug desativado. É uma aplicação local; exposição pública exige servidor WSGI, HTTPS e configuração própria. GitHub Pages não executa Flask.

MySQL pode ser selecionado em `config.py`, com a conexão previamente criada, ou por `DATABASE_URL`. Somente SQLite foi testado nesta revisão; o relatório mensal atual usa a função SQLite `strftime`.

## Verificar

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m pip check
```

Os testes criam usuários e registros fictícios em uma pasta temporária. Não usam o banco real da oficina. Consulte `REVISAO-PUBLICACAO.md` para resultados e limitações.

## Revisão de publicação

Foram corrigidos o acesso anônimo às APIs/páginas, a chave de sessão fixa, a ausência de criação do primeiro usuário, os campos opcionais com restrição única, a validação de itens/status/datas, a escrita insegura do nome do PDF e a inserção de texto em HTML nas listagens. Formulários e chamadas JSON usam proteção CSRF.

Bancos, PDFs emitidos, ambientes virtuais e segredos não fazem parte deste repositório. O antigo script de massa com credenciais fixas não integra a versão pública. Os materiais originais permanecem preservados no diretório de origem do autor.
