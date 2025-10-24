"""Script de teste para a tool enviar_pedido"""
import asyncio
import sys
import os

# Configurar encoding UTF-8 no Windows
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

from loguru import logger
from alice.tools import enviar_pedido


async def test_enviar_pedido():
    """Testa a tool enviar_pedido com múltiplos formatos"""

    print("=" * 70)
    print("TESTE DA TOOL ENVIAR_PEDIDO")
    print("=" * 70)
    print()

    # Casos de teste com diferentes formatos de produtos
    casos_teste = [
        {
            "nome": "Produtos como ARRAY (formato padrão)",
            "pedido": {
                "codigo_cliente": 1,
                "codigo_empresa": 1,
                "produtos": [
                    {
                        "nome_produto": "CLP-60 VD",
                        "quantidade": 20,
                        "valor_unitario": 269.08
                    }
                ],
                "base_troca": 1,
                "tipo_pagamento": 2,
                "forma_pagamento": 5,
                "prazo_pedido": "30/45/60",
                "prazo_sucata": "no ato"
            }
        },
        {
            "nome": "Produtos como OBJETO ÚNICO (IA envia dict)",
            "pedido": {
                "codigo_cliente": 1,
                "codigo_empresa": 1,
                "produtos": {  # OBJETO ao invés de ARRAY
                    "codigo_produto": "CL-45 VD",  # Testando campo alternativo
                    "quantidade": 10,
                    "valor_unitario": 243.98
                },
                "base_troca": 0,
                "tipo_pagamento": 1,
                "forma_pagamento": 4,
                "prazo_pedido": "AVISTA"
            }
        },
        {
            "nome": "Múltiplos produtos com sucata",
            "pedido": {
                "codigo_cliente": 1,
                "codigo_empresa": 1,
                "produtos": [
                    {
                        "codigo": "CLP-60 VD",  # Testando outro campo alternativo
                        "quantidade": 15,
                        "valor_unitario": 269.08
                    },
                    {
                        "nome": "CL-45 VD",  # Testando mais um campo alternativo
                        "quantidade": 5,
                        "valor_unitario": 243.98
                    }
                ],
                "base_troca": 1,
                "tipo_pagamento": 2,
                "forma_pagamento": 5,
                "prazo_pedido": "30/45 DD",
                "prazo_sucata": "30 DD"
            }
        },
        {
            "nome": "Produtos como STRING JSON (edge case)",
            "pedido": {
                "codigo_cliente": 2,
                "codigo_empresa": 2,
                "produtos": '[{"nome_produto": "CLP-60 VD", "quantidade": 30, "valor_unitario": 269.08}]',  # STRING
                "base_troca": 1,
                "tipo_pagamento": 2,
                "forma_pagamento": 5,
                "prazo_pedido": "30/45/60",
                "prazo_sucata": "imediato"
            }
        }
    ]

    for caso in casos_teste:
        print(f"\n{'='*70}")
        print(f"TESTANDO: {caso['nome']}")
        print('='*70)

        try:
            # Chamar a tool
            resultado = await enviar_pedido.ainvoke({"pedido_json": caso['pedido']})

            print(f"\n✅ RESPOSTA:")
            print(f"  • Sucesso: {resultado.get('sucesso')}")

            if resultado.get('sucesso'):
                print(f"  • Número do Pedido: #{resultado.get('numero_pedido')}")
                print(f"  • Status: {resultado.get('status_pedido')}")
                print(f"\n💬 MENSAGEM:")
                print(f"  {resultado.get('mensagem')}")
                print(f"\n✅ TESTE PASSOU")
            else:
                print(f"\n❌ ERRO: {resultado.get('erro')}")
                if 'dados_recebidos' in resultado:
                    print(f"\n📋 Debug - Dados recebidos:")
                    import json
                    print(json.dumps(resultado['dados_recebidos'], indent=2, ensure_ascii=False))

        except Exception as e:
            print(f"\n❌ ERRO NO TESTE: {str(e)}")
            import traceback
            traceback.print_exc()

        print()


if __name__ == "__main__":
    # Configurar logger
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )

    print("\n⚠️  ATENÇÃO: Este teste fará requisições REAIS à API!")
    print("Pressione Ctrl+C para cancelar ou Enter para continuar...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nTeste cancelado.")
        sys.exit(0)

    # Executar testes
    asyncio.run(test_enviar_pedido())

    print("\n" + "=" * 70)
    print("✅ TODOS OS TESTES CONCLUÍDOS")
    print("=" * 70)
