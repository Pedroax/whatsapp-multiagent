"""Script de teste para a tool buscar_baterias"""
import asyncio
import sys
import os

# Configurar encoding UTF-8 no Windows
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

from loguru import logger
from alice.tools import buscar_baterias


async def test_buscar_baterias():
    """Testa a tool buscar_baterias com exemplos reais"""

    print("=" * 70)
    print("TESTE DA TOOL BUSCAR_BATERIAS")
    print("=" * 70)
    print()

    # Casos de teste baseados nas interações reais dos clientes
    casos_teste = [
        "60ah",
        "selada de 60",
        "60 cral prime",
        "100",
        "bateria de 50 cral",
        "75ah 24 meses",
    ]

    for termo in casos_teste:
        print(f"\n{'='*70}")
        print(f"TESTANDO: '{termo}'")
        print('='*70)

        try:
            # Chamar a tool
            resultado = await buscar_baterias.ainvoke({"termo": termo})

            print(f"\n✅ RESPOSTA:")
            print(f"  • Sucesso: {resultado.get('sucesso')}")
            print(f"  • Baterias Encontradas: {resultado.get('baterias_encontradas', False)}")
            print(f"  • Total: {resultado.get('total', 0)}")

            if resultado.get('baterias_encontradas'):
                print(f"\n📊 CRITÉRIOS IDENTIFICADOS:")
                criterios = resultado.get('criterios', {})
                for key, value in criterios.items():
                    print(f"  • {key}: {value}")

                print(f"\n📋 RESULTADOS:")
                resultado_texto = resultado.get('resultado', '')
                for linha in resultado_texto.split('\n'):
                    if linha.strip():
                        print(f"  {linha}")

                print(f"\n✅ TESTE PASSOU - {resultado.get('total')} baterias encontradas")
            else:
                if resultado.get('sucesso'):
                    print(f"\n⚠️ Nenhuma bateria encontrada")
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
    asyncio.run(test_buscar_baterias())

    print("\n" + "=" * 70)
    print("✅ TODOS OS TESTES CONCLUÍDOS")
    print("=" * 70)
