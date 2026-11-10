
from decimal import Decimal

import pytest
from sqlalchemy import text


SENHA_TESTE = "TechStore@2026"


def criar_cliente(client, numero):
    resposta = client.post(
        "/clientes",
        json={
            "nome": f"Cliente Pagamento {numero}",
            "email": f"pagamento{numero}@exemplo.com",
            "telefone": "11999998888",
            "cpf": f"{numero:011d}",
            "senha": SENHA_TESTE
        }
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def autenticar(client, cliente):
    resposta = client.post(
        "/auth/login",
        json={
            "email": cliente["email"],
            "senha": SENHA_TESTE
        }
    )
    assert resposta.status_code == 200, resposta.text
    return {
        "Authorization": f"Bearer {resposta.json()['access_token']}"
    }


def promover_administrador(test_engine, cliente_id):
    with test_engine.begin() as conexao:
        banco = conexao.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if banco != "techstore_test_db":
            raise RuntimeError("Banco de testes incorreto")

        resultado = conexao.execute(
            text("""
                UPDATE clientes
                SET perfil = 'admin'
                WHERE id = :cliente_id
                RETURNING id
            """),
            {"cliente_id": cliente_id}
        )
        assert resultado.scalar_one() == cliente_id


@pytest.fixture
def contexto_pagamentos(client, test_engine, banco_limpo):
    cliente = criar_cliente(client, 201)
    outro_cliente = criar_cliente(client, 202)
    administrador = criar_cliente(client, 203)

    promover_administrador(test_engine, administrador["id"])

    headers_cliente = autenticar(client, cliente)
    headers_outro = autenticar(client, outro_cliente)
    headers_admin = autenticar(client, administrador)

    resposta_produto = client.post(
        "/produtos",
        json={
            "nome": "Produto Teste Pagamento",
            "categoria": "Eletronicos",
            "preco": "150.00",
            "estoque": 20
        },
        headers=headers_admin
    )
    assert resposta_produto.status_code == 201, resposta_produto.text

    resposta_pedido = client.post(
        "/pedidos",
        json={
            "cliente_id": cliente["id"],
            "itens": [
                {
                    "produto_id": resposta_produto.json()["id"],
                    "quantidade": 2
                }
            ]
        },
        headers=headers_cliente
    )
    assert resposta_pedido.status_code == 201, resposta_pedido.text

    return {
        "cliente": cliente,
        "outro_cliente": outro_cliente,
        "administrador": administrador,
        "headers_cliente": headers_cliente,
        "headers_outro": headers_outro,
        "headers_admin": headers_admin,
        "pedido": resposta_pedido.json(),
        "engine": test_engine
    }


def criar_pagamento(client, contexto, metodo="pix"):
    resposta = client.post(
        "/pagamentos",
        headers=contexto["headers_cliente"],
        json={
            "pedido_id": contexto["pedido"]["id"],
            "metodo": metodo
        }
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def consultar_status(test_engine, tabela, registro_id):
    if tabela not in {"pedidos", "pagamentos"}:
        raise ValueError("Tabela invalida")

    with test_engine.connect() as conexao:
        return conexao.execute(
            text(f"""
                SELECT status
                FROM {tabela}
                WHERE id = :id
            """),
            {"id": registro_id}
        ).scalar_one()


@pytest.mark.parametrize("metodo", ["pix", "cartao", "boleto"])
def test_criar_pagamento_pendente(
    client,
    contexto_pagamentos,
    metodo
):
    dados = contexto_pagamentos

    pagamento = criar_pagamento(client, dados, metodo)

    assert pagamento["pedido_id"] == dados["pedido"]["id"]
    assert pagamento["metodo"] == metodo
    assert pagamento["status"] == "pendente"
    assert Decimal(str(pagamento["valor"])) == Decimal("300.00")

    assert consultar_status(
        dados["engine"],
        "pedidos",
        dados["pedido"]["id"]
    ) == "pendente"


def test_pagamento_exige_autenticacao(client, contexto_pagamentos):
    resposta = client.post(
        "/pagamentos",
        json={
            "pedido_id": contexto_pagamentos["pedido"]["id"],
            "metodo": "pix"
        }
    )
    assert resposta.status_code == 401


def test_pagamento_rejeita_metodo_invalido(
    client,
    contexto_pagamentos
):
    resposta = client.post(
        "/pagamentos",
        headers=contexto_pagamentos["headers_cliente"],
        json={
            "pedido_id": contexto_pagamentos["pedido"]["id"],
            "metodo": "dinheiro"
        }
    )
    assert resposta.status_code == 422


def test_pagamento_rejeita_pedido_inexistente(
    client,
    contexto_pagamentos
):
    resposta = client.post(
        "/pagamentos",
        headers=contexto_pagamentos["headers_cliente"],
        json={
            "pedido_id": 999999,
            "metodo": "pix"
        }
    )
    assert resposta.status_code == 404


def test_cliente_nao_paga_pedido_de_outro(
    client,
    contexto_pagamentos
):
    resposta = client.post(
        "/pagamentos",
        headers=contexto_pagamentos["headers_outro"],
        json={
            "pedido_id": contexto_pagamentos["pedido"]["id"],
            "metodo": "pix"
        }
    )
    assert resposta.status_code == 403


def test_pagamento_duplicado(client, contexto_pagamentos):
    criar_pagamento(client, contexto_pagamentos)

    resposta = client.post(
        "/pagamentos",
        headers=contexto_pagamentos["headers_cliente"],
        json={
            "pedido_id": contexto_pagamentos["pedido"]["id"],
            "metodo": "cartao"
        }
    )
    assert resposta.status_code == 409


def test_cliente_nao_pode_simular(
    client,
    contexto_pagamentos,
    monkeypatch
):
    monkeypatch.setenv("APP_ENV", "testing")
    pagamento = criar_pagamento(client, contexto_pagamentos)

    resposta = client.post(
        f"/pagamentos/{pagamento['id']}/simular",
        headers=contexto_pagamentos["headers_cliente"],
        json={"resultado": "aprovado"}
    )
    assert resposta.status_code == 403


def test_simulacao_exige_autenticacao(
    client,
    contexto_pagamentos
):
    pagamento = criar_pagamento(client, contexto_pagamentos)

    resposta = client.post(
        f"/pagamentos/{pagamento['id']}/simular",
        json={"resultado": "aprovado"}
    )
    assert resposta.status_code == 401


def test_aprovar_pagamento(
    client,
    contexto_pagamentos,
    monkeypatch
):
    monkeypatch.setenv("APP_ENV", "testing")
    dados = contexto_pagamentos
    pagamento = criar_pagamento(client, dados)

    resposta = client.post(
        f"/pagamentos/{pagamento['id']}/simular",
        headers=dados["headers_admin"],
        json={"resultado": "aprovado"}
    )

    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["status"] == "aprovado"

    assert consultar_status(
        dados["engine"],
        "pagamentos",
        pagamento["id"]
    ) == "aprovado"

    assert consultar_status(
        dados["engine"],
        "pedidos",
        dados["pedido"]["id"]
    ) == "pago"


def test_recusar_pagamento(
    client,
    contexto_pagamentos,
    monkeypatch
):
    monkeypatch.setenv("APP_ENV", "testing")
    dados = contexto_pagamentos
    pagamento = criar_pagamento(client, dados)

    resposta = client.post(
        f"/pagamentos/{pagamento['id']}/simular",
        headers=dados["headers_admin"],
        json={"resultado": "recusado"}
    )

    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["status"] == "recusado"

    assert consultar_status(
        dados["engine"],
        "pagamentos",
        pagamento["id"]
    ) == "recusado"

    assert consultar_status(
        dados["engine"],
        "pedidos",
        dados["pedido"]["id"]
    ) == "pendente"


def test_permite_nova_tentativa_apos_recusa(
    client,
    contexto_pagamentos,
    monkeypatch
):
    monkeypatch.setenv("APP_ENV", "testing")
    dados = contexto_pagamentos
    primeiro = criar_pagamento(client, dados)

    resposta = client.post(
        f"/pagamentos/{primeiro['id']}/simular",
        headers=dados["headers_admin"],
        json={"resultado": "recusado"}
    )
    assert resposta.status_code == 200

    segundo = criar_pagamento(client, dados, "cartao")

    assert segundo["id"] != primeiro["id"]
    assert segundo["status"] == "pendente"


def test_nao_processa_pagamento_duas_vezes(
    client,
    contexto_pagamentos,
    monkeypatch
):
    monkeypatch.setenv("APP_ENV", "testing")
    dados = contexto_pagamentos
    pagamento = criar_pagamento(client, dados)

    primeira = client.post(
        f"/pagamentos/{pagamento['id']}/simular",
        headers=dados["headers_admin"],
        json={"resultado": "aprovado"}
    )
    assert primeira.status_code == 200

    segunda = client.post(
        f"/pagamentos/{pagamento['id']}/simular",
        headers=dados["headers_admin"],
        json={"resultado": "aprovado"}
    )
    assert segunda.status_code == 409


@pytest.mark.parametrize(
    "ambiente",
    ["production", "staging", ""]
)
def test_simulacao_bloqueada_fora_ambiente_permitido(
    client,
    contexto_pagamentos,
    monkeypatch,
    ambiente
):
    monkeypatch.setenv("APP_ENV", ambiente)
    dados = contexto_pagamentos
    pagamento = criar_pagamento(client, dados)

    resposta = client.post(
        f"/pagamentos/{pagamento['id']}/simular",
        headers=dados["headers_admin"],
        json={"resultado": "aprovado"}
    )

    assert resposta.status_code == 403
    assert consultar_status(
        dados["engine"],
        "pagamentos",
        pagamento["id"]
    ) == "pendente"


def test_rollback_quando_atualizacao_pedido_falha(
    client,
    contexto_pagamentos,
    monkeypatch
):
    monkeypatch.setenv("APP_ENV", "testing")
    dados = contexto_pagamentos
    pagamento = criar_pagamento(client, dados)

    with dados["engine"].begin() as conexao:
        conexao.execute(
            text("""
                CREATE OR REPLACE FUNCTION
                bloquear_aprovacao_pedido_teste()
                RETURNS trigger
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    IF NEW.status = 'pago' THEN
                        RAISE EXCEPTION
                        'Falha simulada na atualizacao do pedido';
                    END IF;
                    RETURN NEW;
                END;
                $$
            """)
        )
        conexao.execute(
            text("""
                CREATE TRIGGER bloquear_aprovacao_pedido_teste
                BEFORE UPDATE ON pedidos
                FOR EACH ROW
                EXECUTE FUNCTION bloquear_aprovacao_pedido_teste()
            """)
        )

    try:
        resposta = client.post(
            f"/pagamentos/{pagamento['id']}/simular",
            headers=dados["headers_admin"],
            json={"resultado": "aprovado"}
        )

        assert resposta.status_code == 500

        assert consultar_status(
            dados["engine"],
            "pagamentos",
            pagamento["id"]
        ) == "pendente"

        assert consultar_status(
            dados["engine"],
            "pedidos",
            dados["pedido"]["id"]
        ) == "pendente"

    finally:
        with dados["engine"].begin() as conexao:
            conexao.execute(
                text("""
                    DROP TRIGGER IF EXISTS
                    bloquear_aprovacao_pedido_teste
                    ON pedidos
                """)
            )
            conexao.execute(
                text("""
                    DROP FUNCTION IF EXISTS
                    bloquear_aprovacao_pedido_teste()
                """)
            )
