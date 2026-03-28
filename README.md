# Monitoramento — API (Django)

## Deploy no Render (Web Service)

Use estes valores no painel do **Web Service** (aba **Settings**).

**Importante:** no campo **Build Command**, cole o texto **completo** abaixo. Não use reticências (`...` ou `…`) nem resuma o comando — se aparecer `pip install …` no log, o deploy vai falhar. O arquivo `RENDER_BUILD_COMMAND.txt` na raiz do repo tem a mesma linha para copiar.

### Build Command

**Recomendado** (usa o script do repositório):

```bash
chmod +x build.sh && ./build.sh
```

**Alternativa** (equivalente, sem `build.sh`):

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py ensure_superuser
```

### Start Command

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --graceful-timeout 30
```

(O `Procfile` do repositório já inclui `--timeout 120` para importação Excel demorar sem o worker ser morto.)

### Campos comuns

| Campo | Valor |
|--------|--------|
| **Root Directory** | *(vazio — raiz do repositório)* |
| **Branch** | `main` |
| **Runtime** | Python 3 |

### Variáveis de ambiente (mínimo)

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | Internal Database URL do Postgres no Render (ou vincule o banco ao serviço) |
| `SECRET_KEY` | Chave secreta forte (não commite) |
| `DEBUG` | `false` |
| `ALLOWED_HOSTS` | Ex.: `monitoramento-backend-api.onrender.com` (o hostname do **seu** serviço) |
| `RENDER` | `true` |

Com frontend em outro domínio, defina também `CORS_ALLOWED_ORIGINS` e `CSRF_TRUSTED_ORIGINS`.

### Admin sem Shell (opcional)

Se não tiver acesso ao Shell do Render, defina **só no primeiro deploy** (depois remova do painel):

- `BOOTSTRAP_SUPERUSER_USERNAME` — usuário do admin
- `BOOTSTRAP_SUPERUSER_PASSWORD` — senha forte
- `BOOTSTRAP_SUPERUSER_EMAIL` — opcional

O comando `ensure_superuser` roda no final do `build.sh` e só cria o usuário se **ainda não existir nenhum** usuário no banco.

### Versão do Python

O projeto segue **Python 3.12 ou superior**; no **cPanel** use **3.13.11** quando for a única opção.

- `runtime.txt` e `.python-version` fixam **3.13.11** para documentação e ferramentas (pyenv, alguns hosts).
- Localmente: `pyenv install 3.13.11` (ou instale 3.13 pelo instalador oficial) e ative antes do `pip install`.

Não é necessário alterar código Django só por causa do 3.13 — mantenha `requirements.txt` atualizado.

### cPanel (Python 3.13.11)

1. No cPanel, crie o **Python App** com interpretador **3.13.11** e aponte a raiz para a pasta do repositório (onde está `manage.py`).
2. No **virtualenv** do app: `pip install -r requirements.txt`
3. Rode `collectstatic`, `migrate` e (opcional) `ensure_superuser` como no `build.sh`, via **Terminal** ou script de deploy.
4. **Banco:** este projeto usa **PostgreSQL** (`psycopg`). Se o cPanel só oferecer **MySQL**, será preciso outro plano/host com Postgres ou adaptar o backend — não basta trocar só a versão do Python.

### Desenvolvimento local

Copie `.env.example` para `.env`, suba o Postgres ou deixe `DATABASE_URL` vazio para SQLite, e:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
