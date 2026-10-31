
import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


BANCO_TESTES = "techstore_test_db"


@pytest.fixture(scope="session")
def test_engine():
    load_dotenv()

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=BANCO_TESTES
    )

    engine = create_engine(
        database_url,
        pool_pre_ping=True
    )

    with engine.connect() as conexao:
        banco_atual = conexao.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if banco_atual != BANCO_TESTES:
            engine.dispose()
            raise RuntimeError(
                "Os testes nao estao conectados ao banco correto!"
            )

    yield engine

    engine.dispose()


@pytest.fixture
def banco_limpo(test_engine):
    with test_engine.begin() as conexao:
        banco_atual = conexao.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if banco_atual != BANCO_TESTES:
            raise RuntimeError(
                "Limpeza bloqueada: banco de dados incorreto!"
            )

        conexao.execute(
            text("""
                TRUNCATE TABLE
                    itens_pedido,
                    pedidos,
                    produtos,
                    clientes
                RESTART IDENTITY CASCADE
            """)
        )

    yield

    with test_engine.begin() as conexao:
        banco_atual = conexao.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if banco_atual != BANCO_TESTES:
            raise RuntimeError(
                "Limpeza bloqueada: banco de dados incorreto!"
            )

        conexao.execute(
            text("""
                TRUNCATE TABLE
                    itens_pedido,
                    pedidos,
                    produtos,
                    clientes
                RESTART IDENTITY CASCADE
            """)
        )


@pytest.fixture
def client(test_engine, monkeypatch):
    import app.services.produto_service as produto_service
    import app.services.cliente_service as cliente_service
    import app.services.pedido_service as pedido_service
    import app.services.auth_service as auth_service

    monkeypatch.setattr(
        produto_service,
        "engine",
        test_engine
    )

    monkeypatch.setattr(
        cliente_service,
        "engine",
        test_engine
    )

    monkeypatch.setattr(
        pedido_service,
        "engine",
        test_engine
    )

    monkeypatch.setattr(
        auth_service,
        "engine",
        test_engine
    )

    from app.main import app

    with TestClient(app) as cliente:
        yield cliente
