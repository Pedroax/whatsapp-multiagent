"""
Teste da nova tool consultar_prazos_pagamento

Execute com: python test_consultar_prazos.py
"""
import asyncio
from alice.tools import consultar_prazos_pagamento


async def test_consultar_prazos():
    """Testa a consulta de prazos de pagamento"""

    print("=" * 60)
    print("TESTE: Consultar Prazos de Pagamento")
    print("=" * 60)

    # Teste 1: Pedido pequeno
    print("\n[TESTE 1] Pedido: 3 baterias, R$ 680,00")
    print("-" * 60)

    resultado = await consultar_prazos_pagamento(
        quantidade_total=3,
        valor_total=680.0
    )

    print(f"\nSucesso: {resultado.get('sucesso')}")

    if resultado.get('sucesso'):
        print(f"Total de prazos: {resultado.get('total_prazos')}")
        print("\nPrazos disponíveis:")

        for prazo in resultado.get('prazos', []):
            print(f"  - Código: {prazo['codigo']}")
            print(f"    Condição: {prazo['condicao']}")
            print(f"    Prazo: {prazo['prazo']}")
            print()

        print("Mensagem formatada para o cliente:")
        print(resultado.get('mensagem_formatada'))
    else:
        print(f"Erro: {resultado.get('erro')}")

    print("\n" + "=" * 60)
    print("FIM DOS TESTES")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_consultar_prazos())
