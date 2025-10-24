# 🚀 Deploy em VPS - Alice Multiagente

## 1. Requisitos da VPS

```bash
- Ubuntu 20.04+ ou Debian 11+
- 2GB RAM mínimo (4GB recomendado)
- 20GB disco
- Python 3.11+
- Node.js 18+
- Nginx
- PM2
```

## 2. Preparar VPS

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Instalar Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Instalar Nginx
sudo apt install nginx -y

# Instalar PM2
sudo npm install -g pm2

# Instalar Certbot (SSL)
sudo apt install certbot python3-certbot-nginx -y
```

## 3. Clonar Projeto

```bash
# Criar diretório
cd /var/www
sudo mkdir alice-lc
sudo chown $USER:$USER alice-lc
cd alice-lc

# Clonar (ou fazer upload via FTP/SCP)
git clone <seu-repositorio>.git .
```

## 4. Configurar Backend

```bash
# Criar ambiente virtual Python
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
nano .env
```

**Arquivo .env:**
```env
# LLM Configuration
ANTHROPIC_API_KEY=sua-chave-aqui
OPENAI_API_KEY=sua-chave-aqui

# WhatsApp Evolution API
EVOLUTION_API_URL=https://whatsapp.seudominio.com
EVOLUTION_API_KEY=sua-chave-aqui
EVOLUTION_INSTANCE_NAME=nome-instancia

# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_KEY=sua-chave-service-role

# Application
DEBUG=false
LOG_LEVEL=INFO
DEBOUNCE_SECONDS=5.0
```

**Iniciar backend com PM2:**
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Iniciar com PM2
pm2 start "python main.py" --name alice-backend

# Salvar configuração PM2
pm2 save
pm2 startup
```

## 5. Configurar Frontend

```bash
cd frontend-multiagente

# Instalar dependências
npm install

# Configurar URL da API
nano src/lib/api.ts
# Mudar: http://localhost:8000 → https://api.seudominio.com

# Build para produção
npm run build

# Servir build com PM2
pm2 serve dist 3000 --spa --name alice-frontend

# Salvar
pm2 save
```

## 6. Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/alice
```

**Arquivo nginx:**
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

**Ativar site:**
```bash
sudo ln -s /etc/nginx/sites-available/alice /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 7. Configurar DNS

No seu provedor de domínio (Cloudflare, Hostinger, etc.):

```
Tipo  | Nome | Valor
------|------|-------
A     | api  | IP_DA_VPS
A     | app  | IP_DA_VPS
```

## 8. Gerar SSL (HTTPS)

```bash
# Gerar certificados SSL
sudo certbot --nginx -d api.seudominio.com -d app.seudominio.com

# Renovação automática
sudo certbot renew --dry-run
```

## 9. Configurar Webhook Evolution API

```bash
# URL do webhook
https://api.seudominio.com/webhook/evolution
```

No painel da Evolution API:
1. Acessar sua instância
2. Configurar webhook
3. URL: `https://api.seudominio.com/webhook/evolution`
4. Events: `messages.upsert`

## 10. Verificar Status

```bash
# Ver logs backend
pm2 logs alice-backend

# Ver logs frontend
pm2 logs alice-frontend

# Ver status
pm2 status

# Reiniciar
pm2 restart alice-backend
pm2 restart alice-frontend
```

## 11. Migração de Cliente

### Se cliente já tem VPS:

```bash
# 1. Exportar código
git push origin main

# 2. Na VPS do cliente
git clone <repositorio>
# Seguir passos 4-10

# 3. Migrar dados do Supabase (se necessário)
# Exportar SQL → Importar no novo projeto

# 4. Atualizar webhook Evolution API
# Apontar para novo domínio
```

### Se cliente usa mesma VPS:

```bash
# Criar subdiretório
cd /var/www
mkdir alice-cliente2
cd alice-cliente2

# Clonar projeto
git clone <repositorio> .

# Usar portas diferentes
# Backend: 8001
# Frontend: 3001

# Configurar nginx para cliente2.com
```

## 12. Backup Automático

```bash
# Criar script de backup
nano /var/www/alice-lc/backup.sh
```

**Script:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/alice"

# Criar diretório
mkdir -p $BACKUP_DIR

# Backup código
tar -czf $BACKUP_DIR/codigo_$DATE.tar.gz /var/www/alice-lc

# Backup .env
cp /var/www/alice-lc/.env $BACKUP_DIR/env_$DATE.bak

# Limpar backups antigos (manter últimos 7 dias)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup concluído: $DATE"
```

**Agendar backup diário:**
```bash
chmod +x backup.sh
crontab -e

# Adicionar linha:
0 3 * * * /var/www/alice-lc/backup.sh
```

## 13. Monitoramento

```bash
# Instalar htop
sudo apt install htop -y

# Ver recursos
htop

# Ver logs nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Ver logs PM2
pm2 logs --lines 100
```

## 14. Troubleshooting

### Backend não inicia:
```bash
# Ver logs
pm2 logs alice-backend

# Verificar .env
cat .env

# Testar manualmente
source venv/bin/activate
python main.py
```

### Frontend não carrega:
```bash
# Rebuild
cd frontend-multiagente
npm run build
pm2 restart alice-frontend
```

### Nginx erro 502:
```bash
# Verificar backend rodando
pm2 status

# Ver logs nginx
sudo tail -f /var/log/nginx/error.log
```

### SSL não funciona:
```bash
# Renovar certificado
sudo certbot renew

# Verificar nginx
sudo nginx -t
sudo systemctl restart nginx
```

## 15. Segurança

```bash
# Firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable

# Fail2ban
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
```

## 16. Atualização

```bash
# Backup antes
./backup.sh

# Atualizar código
git pull origin main

# Reinstalar dependências
source venv/bin/activate
pip install -r requirements.txt

cd frontend-multiagente
npm install
npm run build

# Reiniciar
pm2 restart alice-backend
pm2 restart alice-frontend
```

---

## ✅ Checklist Deploy

- [ ] VPS preparada (Python, Node, Nginx, PM2)
- [ ] Projeto clonado em /var/www/alice-lc
- [ ] .env configurado com credenciais corretas
- [ ] Backend rodando com PM2
- [ ] Frontend buildado e servido
- [ ] Nginx configurado
- [ ] DNS apontando para VPS
- [ ] SSL gerado com certbot
- [ ] Webhook Evolution API configurado
- [ ] Backup automático agendado
- [ ] Firewall configurado

---

**🎯 URLs Finais:**

- Frontend: `https://app.seudominio.com`
- Backend API: `https://api.seudominio.com`
- Webhook: `https://api.seudominio.com/webhook/evolution`
