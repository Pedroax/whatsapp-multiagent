# Script para corrigir nginx e preservar /api/ no proxy
ssh -o StrictHostKeyChecking=no root@138.68.13.174 @'
cat > /etc/nginx/sites-available/alice-lc << 'EOF'
server {
    listen 80;
    server_name lcbaterias.automatexia.com.br 138.68.13.174;

    # Frontend
    location / {
        root /var/www/alice-lc;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # Backend API - preserva /api/ na URL
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Backend webhook
    location /webhook/ {
        proxy_pass http://127.0.0.1:8000/webhook/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF
nginx -t && systemctl reload nginx
'@
