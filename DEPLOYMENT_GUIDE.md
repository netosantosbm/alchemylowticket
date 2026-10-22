# 🌐 Guia de Deploy em Produção: VPS + Domínio alchemylow.shop + Supabase

Este guia documenta o passo a passo exato para colocar a **Plataforma LowTicket** no ar quando concluirmos o desenvolvimento das etapas.

---

## 1. Configurar Apontamento de DNS na HostGator

No painel do cliente da HostGator (Gerenciador de DNS do domínio `alchemylow.shop`):

1. **Registro A (Principal):**
   - Nome/Host: `@` (ou deixar em branco)
   - Tipo: `A`
   - Destino/Valor: `IP_DA_SUA_VPS` (ex: `142.93.xxx.xxx`)
   - TTL: 3600 (1 hora)
2. **Registro CNAME ou A (Subdomínio www):**
   - Nome/Host: `www`
   - Tipo: `CNAME` (apontando para `alchemylow.shop`) ou `A` (apontando para `IP_DA_SUA_VPS`)
   - TTL: 3600

> ⏳ *A propagação do DNS leva de 15 minutos a algumas horas.*

---

## 2. Configurar o Banco de Dados no Supabase

1. Crie uma conta gratuita em [supabase.com](https://supabase.com).
2. Clique em **"New Project"**, dê o nome (ex: `alchemy-lowticket`), defina uma senha forte para o banco e selecione a região **São Paulo (sa-east-1)**.
3. No painel do projeto Supabase:
   - Vá em **Project Settings** (ícone de engrenagem) ➔ **Database**.
   - Role até a seção **Connection String** e selecione a aba **URI**.
   - Copie a URL. Se for usar o Connection Pooler (porta 6543, recomendada para VPS):
     ```
     postgresql://postgres.[PROJECT-REF]:[SUA-SENHA]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres?sslmode=require
     ```
4. Na sua VPS (ou no arquivo `backend/.env`), adicione:
   ```env
   DATABASE_URL="postgresql://postgres.[PROJECT-REF]:[SUA-SENHA]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
   ```
5. **Zero Migração Manual:** Quando o FastAPI iniciar na VPS pela primeira vez, o SQLAlchemy criará automaticamente todas as tabelas (`market_trends`, `products`, `orders`) no Supabase!

---

## 3. Preparando a VPS (Ubuntu/Debian)

Acesse a VPS via terminal SSH:
```bash
ssh root@IP_DA_SUA_VPS
```

Instale os pacotes necessários:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git nginx certbot python3-certbot-nginx nodejs npm
```

### 3.1. Clonar ou Enviar o Projeto para `/var/www/alchemylow`
```bash
mkdir -p /var/www/alchemylow
cd /var/www/alchemylow
# Se usar Git:
# git clone <URL_DO_SEU_REPOSITORIO> .
```

### 3.2. Configurar o Backend
```bash
cd /var/www/alchemylow/backend
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# Crie o arquivo .env com a URL do Supabase
nano .env
# Cole o conteúdo com DATABASE_URL e salve (CTRL+O, ENTER, CTRL+X)
```

### 3.3. Compilar o Frontend para Produção
```bash
cd /var/www/alchemylow/frontend
npm install
npm run build
# A pasta /var/www/alchemylow/frontend/dist será gerada automaticamente
```

### 3.4. Configurar o Serviço do Backend (Systemd)
```bash
sudo cp /var/www/alchemylow/deploy/lowticket-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lowticket-backend
sudo systemctl start lowticket-backend
sudo systemctl status lowticket-backend
```

### 3.5. Configurar o Servidor Web Nginx
```bash
sudo cp /var/www/alchemylow/deploy/nginx.conf /etc/nginx/sites-available/alchemylow.shop
sudo ln -s /etc/nginx/sites-available/alchemylow.shop /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3.6. Gerar Certificado SSL Gratuito (HTTPS)
```bash
sudo certbot --nginx -d alchemylow.shop -d www.alchemylow.shop
```
O Certbot configurará o HTTPS automaticamente com renovação automática.

---

## 4. URL de Webhook para as Plataformas

Assim que o domínio estiver no ar com SSL, configure nas suas contas:

- **Kiwify:** Painel ➔ Configurações ➔ Webhooks ➔ Inserir:
  `https://alchemylow.shop/api/webhooks/order`
- **Hotmart:** Ferramentas ➔ Webhooks (API e Notificações) ➔ Inserir:
  `https://alchemylow.shop/api/webhooks/order`
- **Eduzz:** Painel ➔ Avançado ➔ Webhooks ➔ Inserir:
  `https://alchemylow.shop/api/webhooks/order`
