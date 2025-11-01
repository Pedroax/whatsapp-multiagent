#!/usr/bin/env python3
"""Verifica conversas no banco"""
from supabase import create_client
import os
from dotenv import load_dotenv
import json

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

phone = "556182563956"

# Buscar conversas
print('=== CONVERSAS ===')
conversas = supabase.table('conversas').select('*').eq('phone', phone).execute()
print(f"Total: {len(conversas.data)}")
for c in conversas.data:
    print(f"  - ID: {c['id']}")
    print(f"    Status: {c.get('status')}")
    print(f"    Customer: {c.get('customer_name')}")
    print(f"    Created: {c.get('created_at')}")

# Buscar mensagens
print('\n=== MENSAGENS ===')
if conversas.data:
    conv_id = conversas.data[0]['id']
    msgs = supabase.table('mensagens').select('*').eq('conversa_id', conv_id).execute()
    print(f"Total: {len(msgs.data)}")
    for m in msgs.data[-5:]:
        print(f"  - {m['role']}: {m['content'][:50]}")
