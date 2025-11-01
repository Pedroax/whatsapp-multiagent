# Script para atualizar backend no servidor
ssh -o StrictHostKeyChecking=no root@138.68.13.174 "cd /root/alice-lc && git pull && systemctl restart alice-backend && systemctl status alice-backend --no-pager"
