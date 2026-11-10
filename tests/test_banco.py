
from sqlalchemy import text


def test_conexao_banco_testes(test_engine):
    with test_engine.connect() as conexao:
        resultado = conexao.execute(
            text("SELECT current_database()")
        )

        banco_atual = resultado.scalar_one()

        assert banco_atual == "techstore_test_db"


def test_tabelas_banco_testes(test_engine):
    with test_engine.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
        )

        tabelas = [
            linha[0]
            for linha in resultado.fetchall()
        ]

        tabelas_esperadas = [
            "carrinhos",
            "clientes",
            "itens_carrinho",
            "itens_pedido",
            "pagamentos",
            "pedidos",
            "produtos"
        ]

        assert tabelas == tabelas_esperadas
