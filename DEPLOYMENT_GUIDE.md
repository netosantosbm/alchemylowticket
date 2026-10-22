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

## 2. Banco de Dados Supabase (Já Configurado e Ativo! ✅)

O banco de dados já está provisionado, conectado e com as tabelas criadas no projeto Supabase `vwiplqpczlounotnzlll`.

Na sua VPS, o arquivo `/var/www/alchemylow/backend/.env` deve conter exatamente:
```env
# Conexão Supabase Pooler (Testada e Homologada)
DATABASE_URL="postgresql://postgres.vwiplqpczlounotnzlll:Ch4k%40l1440Anu@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"

# Domínio e Servidor
DOMAIN=alchemylow.shop
PORT=8000
HOST=0.0.0.0
```

---

## 3. Preparando a VPS (Ubuntu/Debian)

### 3.1. Acesso SSH à VPS:
```bash
ssh root@IP_DA_SUA_VPS
```

### 3.2. Instalar Pacotes Essenciais:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git nginx certbot python3-certbot-nginx nodejs npm rsync
```

### 3.3. Enviar os Arquivos para a VPS

**Opção A (Via Git):**
```bash
mkdir -p /var/www/alchemylow
cd /var/www/alchemylow
# Se você tiver enviado para o GitHub:
git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git .
```

**Opção B (Envio Direto do seu Mac via rsync - Sem precisar do GitHub):**
Execute este comando no terminal do seu **Mac** (substitua `IP_DA_SUA_VPS` pelo IP real):
```bash
rsync -avz --exclude 'venv' --exclude 'node_modules' --exclude '.git' "/Users/macintosh/Desktop/Geral iCloud/AlchemyTech/Plataforma LowTicket/" root@IP_DA_SUA_VPS:/var/www/alchemylow/
```

---

### 3.4. Configurar o Backend na VPS
```bash
cd /var/www/alchemylow/backend
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# Criar o arquivo .env
cat << 'EOF' > /var/www/alchemylow/backend/.env
DATABASE_URL="postgresql://postgres.vwiplqpczlounotnzlll:Ch4k%40l1440Anu@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
DOMAIN=alchemylow.shop
PORT=8000
HOST=0.0.0.0
EOF
```

### 3.5. Compilar o Frontend para Produção
```bash
cd /var/www/alchemylow/frontend
npm install
npm run build
# A pasta /var/www/alchemylow/frontend/dist será gerada automaticamente
```

### 3.6. Configurar o Serviço do Backend (Systemd)
```bash
sudo cp /var/www/alchemylow/deploy/lowticket-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lowticket-backend
sudo systemctl start lowticket-backend
sudo systemctl status lowticket-backend
```

### 3.7. Configurar o Servidor Web Nginx
```bash
sudo cp /var/www/alchemylow/deploy/nginx.conf /etc/nginx/sites-available/alchemylow.shop
sudo ln -s /etc/nginx/sites-available/alchemylow.shop /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3.8. Gerar Certificado SSL Gratuito (HTTPS)
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
