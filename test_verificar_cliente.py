"""Script de teste para a tool verificar_cliente"""
import asyncio
import sys
import os

# Configurar encoding UTF-8 no Windows
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

from loguru import logger
from alice.tools import verificar_cliente


async def test_verificar_cliente():
    """Testa a tool verificar_cliente com CNPJ real"""

    print("=" * 60)
    print("TESTE DA TOOL VERIFICAR_CLIENTE")
    print("=" * 60)
    print()

    # CNPJ de teste (do exemplo fornecido)
    cnpj_teste = "09547508000189"

    print(f"📋 Testando com CNPJ: {cnpj_teste}")
    print()

    try:
        # Chamar a tool usando ainvoke
        resultado = await verificar_cliente.ainvoke({"cnpj": cnpj_teste})

        print("✅ RESPOSTA DA TOOL:")
        print("-" * 60)

        # Exibir campos importantes
        print(f"Sucesso: {resultado.get('sucesso')}")
        print(f"Cliente Encontrado: {resultado.get('cliente_encontrado')}")
        print()

        if resultado.get('cliente_encontrado'):
            print("📊 DADOS DO CLIENTE:")
            print(f"  • Código Cliente: {resultado.get('codigo_cliente')}")
            print(f"  • Código Empresa: {resultado.get('codigo_empresa')}")
            print(f"  • Nome da Loja: {resultado.get('nome_loja')}")
            print(f"  • Documento: {resultado.get('documento')}")
            print(f"  • Endereço: {resultado.get('endereco_completo')}")
            print(f"  • Telefone: {resultado.get('telefone')}")
            print(f"  • Email: {resultado.get('email')}")
            print()
            print("💬 MENSAGEM PARA IA:")
            print(f"  {resultado.get('mensagem_para_ia')}")
            print()
            print("✅ TESTE PASSOU - Cliente verificado com sucesso!")
        else:
            print("⚠️ Cliente não encontrado")
            if 'erro' in resultado:
                print(f"Erro: {resultado['erro']}")

        print("-" * 60)
        print()

        # Exibir JSON completo para debug
        print("🔍 JSON COMPLETO DA RESPOSTA:")
        import json
        print(json.dumps(resultado, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def test_cnpj_invalido():
    """Testa com CNPJ inválido"""

    print()
    print("=" * 60)
    print("TESTE COM CNPJ INVÁLIDO")
    print("=" * 60)
    print()

    cnpj_invalido = "123"
    print(f"📋 Testando com CNPJ inválido: {cnpj_invalido}")
    print()

    resultado = await verificar_cliente.ainvoke({"cnpj": cnpj_invalido})

    if not resultado.get('sucesso'):
        print(f"✅ Validação funcionou: {resultado.get('erro')}")
    else:
        print("❌ ERRO: Deveria ter rejeitado CNPJ inválido")


async def test_cnpj_formatado():
    """Testa com CNPJ formatado (deve limpar automaticamente)"""

    print()
    print("=" * 60)
    print("TESTE COM CNPJ FORMATADO")
    print("=" * 60)
    print()

    cnpj_formatado = "09.547.508/0001-89"
    print(f"📋 Testando com CNPJ formatado: {cnpj_formatado}")
    print()

    resultado = await verificar_cliente.ainvoke({"cnpj": cnpj_formatado})

    if resultado.get('sucesso') and resultado.get('cliente_encontrado'):
        print("✅ Limpeza automática funcionou!")
        print(f"   Cliente encontrado: {resultado.get('nome_loja')}")
    else:
        print(f"⚠️ Resultado: {resultado}")


if __name__ == "__main__":
    # Configurar logger
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="DEBUG"
    )

    # Executar testes
    asyncio.run(test_verificar_cliente())
    asyncio.run(test_cnpj_invalido())
    asyncio.run(test_cnpj_formatado())

    print()
    print("=" * 60)
    print("✅ TODOS OS TESTES CONCLUÍDOS")
    print("=" * 60)
