"""Script de teste para a tool consultar_baterias"""
import asyncio
import sys
import os

# Configurar encoding UTF-8 no Windows
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

from loguru import logger
from alice.tools import consultar_baterias


async def test_consultar_baterias():
    """Testa a tool consultar_baterias com casos reais"""

    print("=" * 70)
    print("TESTE DA TOOL CONSULTAR_BATERIAS")
    print("=" * 70)
    print()

    # Casos de teste
    casos_teste = [
        {
            "nome": "1 produto com sucata - Empresa 1",
            "query": "CLP-60 VD:20|SIM|EMP:1"
        },
        {
            "nome": "1 produto sem sucata - Empresa 1",
            "query": "CLP-60 VD:10|NAO|EMP:1"
        },
        {
            "nome": "Múltiplos produtos com sucata - Empresa 1",
            "query": "CLP-60 VD:15,CL-45 VD:5|SIM|EMP:1"
        },
        {
            "nome": "1 produto com sucata - Empresa 2",
            "query": "CLP-60 VD:30|SIM|EMP:2"
        }
    ]

    for caso in casos_teste:
        print(f"\n{'='*70}")
        print(f"TESTANDO: {caso['nome']}")
        print(f"Query: {caso['query']}")
        print('='*70)

        try:
            # Chamar a tool
            resultado = await consultar_baterias.ainvoke({"query": caso['query']})

            print(f"\n✅ RESPOSTA:")
            print(f"  • Sucesso: {resultado.get('sucesso')}")

            if resultado.get('sucesso'):
                print(f"  • Valor Total: R$ {resultado.get('valor_total_geral')}")
                print(f"\n📊 PRODUTOS:")
                for prod in resultado.get('produtos', []):
                    if prod.get('sucesso'):
                        print(f"  ✓ {prod['codigo']}: {prod['quantidade']}x R$ {prod['valor_unitario']} = R$ {prod['valor_total']}")
                    else:
                        print(f"  ✗ {prod['codigo']}: ERRO - {prod.get('erro')}")

                print(f"\n💬 MENSAGEM FORMATADA:")
                print(resultado.get('mensagem_formatada', ''))

                print(f"\n🔍 DEBUG:")
                debug = resultado.get('debug', {})
                print(f"  • Empresa: {debug.get('empresa_solicitada')}")
                print(f"  • Sucata: {debug.get('criterios', {}).get('sucata')}")
                print(f"  • Processados: {debug.get('processados_com_sucesso')}/{debug.get('total_produtos')}")

                print(f"\n✅ TESTE PASSOU")
            else:
                print(f"\n❌ ERRO: {resultado.get('erro')}")

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

    # Executar testes
    asyncio.run(test_consultar_baterias())

    print("\n" + "=" * 70)
    print("✅ TODOS OS TESTES CONCLUÍDOS")
    print("=" * 70)
