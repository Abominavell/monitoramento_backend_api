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
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

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

### Desenvolvimento local

Copie `.env.example` para `.env`, suba o Postgres ou deixe `DATABASE_URL` vazio para SQLite, e:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
