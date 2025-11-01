# Deploy frontend to production server
ssh -o StrictHostKeyChecking=no root@138.68.13.174 "cd /root/alice-lc && git pull && rm -rf /var/www/alice-lc/* && unzip -o frontend-dist.zip -d /var/www/alice-lc && chown -R www-data:www-data /var/www/alice-lc && ls -lah /var/www/alice-lc/assets/ | head -5"
