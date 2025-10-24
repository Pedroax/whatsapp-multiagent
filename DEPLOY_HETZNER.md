# 🚀 Deploy Alice na Hetzner Cloud

## 1. Criar Servidor na Hetzner

### 1.1 Via Dashboard:

1. **Acesse**: https://console.hetzner.cloud
2. **Create Server**
3. **Escolher:**
   - Location: `Nuremberg` (melhor para Brasil)
   - Image: `Ubuntu 22.04`
   - Type: `CPX21` (4GB RAM) ou `CPX31` (8GB RAM)
   - Networking: `IPv4 + IPv6`
   - SSH Key: Adicionar sua chave pública
   - Firewall: Criar novo (regras abaixo)

### 1.2 Firewall Rules:

```
Regra          | Porta | Protocolo | Origem
---------------|-------|-----------|--------
SSH            | 22    | TCP       | 0.0.0.0/0
HTTP           | 80    | TCP       | 0.0.0.0/0
HTTPS          | 443   | TCP       | 0.0.0.0/0
```

### 1.3 Criar Servidor:

```bash
# Preço mensal: ~€5,83 (CPX21) ou ~€11,16 (CPX31)
# Click em "CREATE & BUY NOW"
```

---

## 2. Acessar Servidor

```bash
# Via SSH (copiar IP do dashboard)
ssh root@SEU_IP_HETZNER

# Primeira vez vai pedir para aceitar fingerprint
# Digite: yes
```

---

## 3. Configuração Inicial do Servidor

```bash
# Atualizar sistema
apt update && apt upgrade -y

# Criar usuário não-root
adduser alice
usermod -aG sudo alice

# Copiar chave SSH para novo usuário
rsync --archive --chown=alice:alice ~/.ssh /home/alice

# Sair e reconectar como alice
exit
ssh alice@SEU_IP_HETZNER
```

---

## 4. Instalar Dependências

```bash
# Python 3.11
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y

# Node.js 18 LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Nginx
sudo apt install nginx -y

# PM2 (Process Manager)
sudo npm install -g pm2

# Git
sudo apt install git -y

# Certbot (SSL)
sudo apt install certbot python3-certbot-nginx -y

# Build essentials
sudo apt install build-essential -y
```

---

## 5. Clonar Projeto

```bash
# Criar diretório
sudo mkdir -p /var/www/alice
sudo chown alice:alice /var/www/alice
cd /var/www/alice

# Clonar (substitua pela sua URL)
git clone https://github.com/seu-usuario/alice-lc.git .

# OU fazer upload via SCP do seu PC:
# scp -r "C:\Users\Desktop\OneDrive\Área de Trabalho\alice-lc\*" alice@SEU_IP:/var/www/alice/
```

---

## 6. Configurar Backend

```bash
cd /var/www/alice

# Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Criar .env
nano .env
```

**Arquivo .env:**
```env
# LLM Configuration
ANTHROPIC_API_KEY=sua-chave
OPENAI_API_KEY=sua-chave

# WhatsApp Evolution API
EVOLUTION_API_URL=https://evolutionv2.dev.automatexia.com.br
EVOLUTION_API_KEY=sua-chave
EVOLUTION_INSTANCE_NAME=sua-instancia

# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_KEY=sua-service-key

# Application
DEBUG=false
LOG_LEVEL=INFO
DEBOUNCE_SECONDS=5.0
```

**Testar backend:**
```bash
source venv/bin/activate
python main.py
# Deve iniciar sem erros
# Ctrl+C para parar
```

**Iniciar com PM2:**
```bash
# Criar script de inicialização
nano start-backend.sh
```

**Conteúdo do start-backend.sh:**
```bash
#!/bin/bash
cd /var/www/alice
source venv/bin/activate
exec python main.py
```

```bash
# Tornar executável
chmod +x start-backend.sh

# Iniciar com PM2
pm2 start start-backend.sh --name alice-backend --interpreter bash

# Configurar para iniciar automaticamente
pm2 save
pm2 startup systemd
# Copiar e executar o comando que aparecer
```

---

## 7. Configurar Frontend

```bash
cd /var/www/alice/frontend-multiagente

# Instalar dependências
npm install

# Atualizar URL da API
nano src/hooks/useAuth.ts
# Mudar: http://localhost:8000 → https://api.seudominio.com

nano src/components/ContactInfo.tsx
# Mudar: http://localhost:8000 → https://api.seudominio.com

# Build
npm run build

# Iniciar com PM2
pm2 serve dist 3000 --spa --name alice-frontend

# Salvar
pm2 save
```

---

## 8. Configurar Nginx

```bash
# Criar configuração
sudo nano /etc/nginx/sites-available/alice
```

**Configuração inicial (HTTP):**
```nginx
# Backend API
server {
    listen 80;
    server_name api.seudominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout maior para LLM
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}

# Frontend
server {
    listen 80;
    server_name app.seudominio.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**Ativar:**
```bash
# Criar link simbólico
sudo ln -s /etc/nginx/sites-available/alice /etc/nginx/sites-enabled/

# Remover default
sudo rm /etc/nginx/sites-enabled/default

# Testar configuração
sudo nginx -t

# Reiniciar
sudo systemctl restart nginx
```

---

## 9. Configurar DNS

No seu provedor de domínio (Registro.br, Hostinger, Cloudflare):

```
Tipo  | Nome | Valor              | TTL
------|------|--------------------|-----
A     | api  | IP_HETZNER         | 3600
A     | app  | IP_HETZNER         | 3600
```

**Aguardar propagação DNS (5-30 minutos)**

Testar:
```bash
ping api.seudominio.com
ping app.seudominio.com
```

---

## 10. Gerar SSL (HTTPS)

```bash
# Aguardar DNS propagar antes!

# Gerar certificados
sudo certbot --nginx -d api.seudominio.com -d app.seudominio.com

# Responder perguntas:
# Email: seu@email.com
# Termos: Y
# Compartilhar email: N
# Redirect HTTP → HTTPS: Y (opção 2)

# Testar renovação automática
sudo certbot renew --dry-run
```

---

## 11. Configurar Webhook Evolution API

1. **Acessar Evolution API**: https://evolutionv2.dev.automatexia.com.br
2. **Sua instância** → **Webhooks**
3. **URL**: `https://api.seudominio.com/webhook/evolution`
4. **Events**: `messages.upsert`
5. **Salvar**

---

## 12. Testar Sistema

```bash
# Ver logs backend
pm2 logs alice-backend

# Ver logs frontend
pm2 logs alice-frontend

# Status dos processos
pm2 status

# Reiniciar se necessário
pm2 restart alice-backend
pm2 restart alice-frontend
```

**Acessar no navegador:**
- Frontend: `https://app.seudominio.com`
- API: `https://api.seudominio.com/docs` (Swagger)

---

## 13. Backup Automático

```bash
# Criar script
nano /var/www/alice/backup.sh
```

**Script:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/alice/backups"

mkdir -p $BACKUP_DIR

# Backup código
tar -czf $BACKUP_DIR/alice_$DATE.tar.gz /var/www/alice --exclude='node_modules' --exclude='venv' --exclude='.git'

# Backup .env
cp /var/www/alice/.env $BACKUP_DIR/env_$DATE.bak

# Limpar backups antigos (manter 7 dias)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "✅ Backup concluído: $DATE"
```

```bash
chmod +x /var/www/alice/backup.sh

# Agendar backup diário 3h da manhã
crontab -e
# Adicionar:
0 3 * * * /var/www/alice/backup.sh >> /var/log/alice-backup.log 2>&1
```

---

## 14. Monitoramento

```bash
# Ver recursos do servidor
htop

# Ver logs nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Ver todos os logs PM2
pm2 logs --lines 200

# Monitorar em tempo real
pm2 monit
```

---

## 15. Hetzner Cloud Firewall (Extra Segurança)

No dashboard Hetzner:

1. **Firewalls** → **Create Firewall**
2. **Regras Inbound:**
```
Nome     | Protocolo | Porta | Origem
---------|-----------|-------|----------
SSH      | TCP       | 22    | 0.0.0.0/0
HTTP     | TCP       | 80    | 0.0.0.0/0
HTTPS    | TCP       | 443   | 0.0.0.0/0
```
3. **Apply to Resources** → Seu servidor

---

## 16. Habilitar Backups Hetzner (Opcional)

No dashboard:
- **Server** → **Backups**
- **Enable backups** (~20% do preço mensal)
- Backups automáticos semanais
- Restauração com 1 click

---

## 17. Custo Mensal Estimado

```
Item                    | Preço/mês
------------------------|----------
Hetzner CPX21 (4GB)    | €5,83 (~R$ 35)
Backups Hetzner        | €1,17 (~R$ 7)
Domínio (.com.br)      | R$ 40/ano (R$ 3/mês)
------------------------|----------
TOTAL                  | ~R$ 45/mês
```

**Se usar CPX31 (8GB):** ~R$ 75/mês

---

## 18. Comandos Úteis

```bash
# Reiniciar tudo
pm2 restart all

# Parar tudo
pm2 stop all

# Ver logs em tempo real
pm2 logs --lines 100

# Atualizar código
cd /var/www/alice
git pull
pm2 restart all

# Verificar espaço em disco
df -h

# Verificar memória
free -h

# Processos rodando
pm2 status
```

---

## 19. Troubleshooting

### SSL não funciona:
```bash
# Verificar DNS propagou
nslookup api.seudominio.com

# Verificar nginx
sudo nginx -t

# Renovar SSL manualmente
sudo certbot renew --force-renewal
```

### Backend não inicia:
```bash
pm2 logs alice-backend --lines 50
# Ver erro específico

# Testar manualmente
cd /var/www/alice
source venv/bin/activate
python main.py
```

### Porta 80/443 ocupada:
```bash
# Ver o que está usando
sudo lsof -i :80
sudo lsof -i :443

# Parar apache2 se estiver rodando
sudo systemctl stop apache2
sudo systemctl disable apache2
```

---

## ✅ Checklist Final

- [ ] Servidor Hetzner criado (CPX21 ou CPX31)
- [ ] Firewall configurado (22, 80, 443)
- [ ] SSH funcionando
- [ ] Dependências instaladas
- [ ] Projeto clonado em /var/www/alice
- [ ] .env configurado
- [ ] Backend rodando com PM2
- [ ] Frontend buildado e rodando
- [ ] Nginx configurado
- [ ] DNS propagado
- [ ] SSL gerado (certbot)
- [ ] Webhook Evolution configurado
- [ ] Backup automático agendado
- [ ] Sistema testado e funcionando

---

## 🎯 URLs Finais

- **Frontend**: https://app.seudominio.com
- **API**: https://api.seudominio.com
- **Docs API**: https://api.seudominio.com/docs
- **Webhook**: https://api.seudominio.com/webhook/evolution

---

## 📞 Suporte Hetzner

- **Docs**: https://docs.hetzner.com
- **Status**: https://status.hetzner.com
- **Ticket**: Via dashboard
- **Community**: https://community.hetzner.com

---

**🚀 Pronto para produção na Hetzner!**
