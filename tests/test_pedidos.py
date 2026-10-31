
from decimal import Decimal

from sqlalchemy import text


def test_cadastrar_pedido_e_atualizar_estoque(
    client,
    test_engine,
    banco_limpo
):
    resposta_cliente = client.post(
        "/clientes",
        json={
            "nome": "Mariana Oliveira",
            "email": "mariana.pedidos@exemplo.com",
            "telefone": "11987654321",
            "cpf": "12345678901"
        }
    )

    assert resposta_cliente.status_code == 201
    cliente_id = resposta_cliente.json()["id"]

    resposta_produto_1 = client.post(
        "/produtos",
        json={
            "nome": "Mouse Logitech M170",
            "categoria": "Perifericos",
            "preco": "89.90",
            "estoque": 20
        }
    )

    resposta_produto_2 = client.post(
        "/produtos",
        json={
            "nome": "Teclado Redragon",
            "categoria": "Perifericos",
            "preco": "199.90",
            "estoque": 15
        }
    )

    assert resposta_produto_1.status_code == 201
    assert resposta_produto_2.status_code == 201

    produto_1_id = resposta_produto_1.json()["id"]
    produto_2_id = resposta_produto_2.json()["id"]

    resposta_pedido = client.post(
        "/pedidos",
        json={
            "cliente_id": cliente_id,
            "itens": [
                {
                    "produto_id": produto_1_id,
                    "quantidade": 2
                },
                {
                    "produto_id": produto_2_id,
                    "quantidade": 1
                }
            ]
        }
    )

    assert resposta_pedido.status_code == 201

    dados = resposta_pedido.json()

    assert dados["id"] > 0
    assert dados["cliente_id"] == cliente_id
    assert dados["status"] == "pendente"
    assert Decimal(str(dados["valor_total"])) == Decimal("379.70")
    assert len(dados["itens"]) == 2

    itens_por_produto = {
        item["produto_id"]: item
        for item in dados["itens"]
    }

    assert itens_por_produto[produto_1_id]["quantidade"] == 2
    assert itens_por_produto[produto_2_id]["quantidade"] == 1

    assert Decimal(
        str(itens_por_produto[produto_1_id]["subtotal"])
    ) == Decimal("179.80")

    assert Decimal(
        str(itens_por_produto[produto_2_id]["subtotal"])
    ) == Decimal("199.90")

    pedido_id = dados["id"]

    with test_engine.connect() as conexao:
        pedido_banco = conexao.execute(
            text("""
                SELECT id, cliente_id, status, valor_total
                FROM pedidos
                WHERE id = :pedido_id
            """),
            {"pedido_id": pedido_id}
        ).mappings().first()

        itens_banco = conexao.execute(
            text("""
                SELECT produto_id, quantidade, preco_unitario, subtotal
                FROM itens_pedido
                WHERE pedido_id = :pedido_id
                ORDER BY produto_id
            """),
            {"pedido_id": pedido_id}
        ).mappings().all()

        produtos_banco = conexao.execute(
            text("""
                SELECT id, estoque
                FROM produtos
                WHERE id IN (:produto_1_id, :produto_2_id)
            """),
            {
                "produto_1_id": produto_1_id,
                "produto_2_id": produto_2_id
            }
        ).mappings().all()

    assert pedido_banco is not None
    assert pedido_banco["cliente_id"] == cliente_id
    assert pedido_banco["status"] == "pendente"
    assert pedido_banco["valor_total"] == Decimal("379.70")

    assert len(itens_banco) == 2

    itens_registrados = {
        item["produto_id"]: item
        for item in itens_banco
    }

    assert itens_registrados[produto_1_id]["quantidade"] == 2
    assert itens_registrados[produto_1_id]["preco_unitario"] == Decimal("89.90")
    assert itens_registrados[produto_1_id]["subtotal"] == Decimal("179.80")

    assert itens_registrados[produto_2_id]["quantidade"] == 1
    assert itens_registrados[produto_2_id]["preco_unitario"] == Decimal("199.90")
    assert itens_registrados[produto_2_id]["subtotal"] == Decimal("199.90")

    estoques = {
        produto["id"]: produto["estoque"]
        for produto in produtos_banco
    }

    assert estoques[produto_1_id] == 18
    assert estoques[produto_2_id] == 14


def test_pedido_com_estoque_insuficiente(
    client,
    test_engine,
    banco_limpo
):
    resposta_cliente = client.post(
        "/clientes",
        json={
            "nome": "Carlos Almeida",
            "email": "carlos.pedidos@exemplo.com",
            "telefone": "11999998888",
            "cpf": "98765432100"
        }
    )

    assert resposta_cliente.status_code == 201
    cliente_id = resposta_cliente.json()["id"]

    resposta_produto = client.post(
        "/produtos",
        json={
            "nome": "Monitor Samsung",
            "categoria": "Monitores",
            "preco": "899.90",
            "estoque": 3
        }
    )

    assert resposta_produto.status_code == 201
    produto_id = resposta_produto.json()["id"]

    resposta_pedido = client.post(
        "/pedidos",
        json={
            "cliente_id": cliente_id,
            "itens": [
                {
                    "produto_id": produto_id,
                    "quantidade": 5
                }
            ]
        }
    )

    assert resposta_pedido.status_code == 409

    assert resposta_pedido.json()["detail"] == (
        f"Estoque insuficiente para o produto {produto_id}"
    )

    with test_engine.connect() as conexao:
        estoque_atual = conexao.execute(
            text("""
                SELECT estoque
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        ).scalar_one()

        quantidade_pedidos = conexao.execute(
            text("""
                SELECT COUNT(*)
                FROM pedidos
                WHERE cliente_id = :cliente_id
            """),
            {"cliente_id": cliente_id}
        ).scalar_one()

        quantidade_itens = conexao.execute(
            text("""
                SELECT COUNT(*)
                FROM itens_pedido
            """)
        ).scalar_one()

    assert estoque_atual == 3
    assert quantidade_pedidos == 0
    assert quantidade_itens == 0


def test_pedido_com_produto_inexistente(
    client,
    test_engine,
    banco_limpo
):
    resposta_cliente = client.post(
        "/clientes",
        json={
            "nome": "Fernanda Lima",
            "email": "fernanda.pedidos@exemplo.com",
            "telefone": "11988887777",
            "cpf": "22233344455"
        }
    )

    assert resposta_cliente.status_code == 201
    cliente_id = resposta_cliente.json()["id"]

    produto_id_inexistente = 99999

    resposta_pedido = client.post(
        "/pedidos",
        json={
            "cliente_id": cliente_id,
            "itens": [
                {
                    "produto_id": produto_id_inexistente,
                    "quantidade": 1
                }
            ]
        }
    )

    assert resposta_pedido.status_code == 404

    assert resposta_pedido.json()["detail"] == (
        f"Produto {produto_id_inexistente} nao encontrado ou inativo"
    )

    with test_engine.connect() as conexao:
        quantidade_pedidos = conexao.execute(
            text("SELECT COUNT(*) FROM pedidos")
        ).scalar_one()

        quantidade_itens = conexao.execute(
            text("SELECT COUNT(*) FROM itens_pedido")
        ).scalar_one()

    assert quantidade_pedidos == 0
    assert quantidade_itens == 0


def test_pedido_com_produto_inativo(
    client,
    test_engine,
    banco_limpo
):
    resposta_cliente = client.post(
        "/clientes",
        json={
            "nome": "Ricardo Mendes",
            "email": "ricardo.pedidos@exemplo.com",
            "telefone": "11977776666",
            "cpf": "33344455566"
        }
    )

    assert resposta_cliente.status_code == 201
    cliente_id = resposta_cliente.json()["id"]

    resposta_produto = client.post(
        "/produtos",
        json={
            "nome": "Webcam Full HD",
            "categoria": "Acessorios",
            "preco": "159.90",
            "estoque": 10
        }
    )

    assert resposta_produto.status_code == 201
    produto_id = resposta_produto.json()["id"]

    resposta_exclusao = client.delete(
        f"/produtos/{produto_id}"
    )

    assert resposta_exclusao.status_code == 200

    resposta_pedido = client.post(
        "/pedidos",
        json={
            "cliente_id": cliente_id,
            "itens": [
                {
                    "produto_id": produto_id,
                    "quantidade": 2
                }
            ]
        }
    )

    assert resposta_pedido.status_code == 404

    assert resposta_pedido.json()["detail"] == (
        f"Produto {produto_id} nao encontrado ou inativo"
    )

    with test_engine.connect() as conexao:
        produto_banco = conexao.execute(
            text("""
                SELECT estoque, ativo
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        ).mappings().one()

        quantidade_pedidos = conexao.execute(
            text("SELECT COUNT(*) FROM pedidos")
        ).scalar_one()

        quantidade_itens = conexao.execute(
            text("SELECT COUNT(*) FROM itens_pedido")
        ).scalar_one()

    assert produto_banco["ativo"] is False
    assert produto_banco["estoque"] == 10
    assert quantidade_pedidos == 0
    assert quantidade_itens == 0

def test_pedido_com_cliente_inexistente(
    client,
    test_engine,
    banco_limpo
):
    resposta_produto = client.post(
        "/produtos",
        json={
            "nome": "Mouse Sem Fio",
            "categoria": "Perifericos",
            "preco": "79.90",
            "estoque": 10
        }
    )

    assert resposta_produto.status_code == 201
    produto_id = resposta_produto.json()["id"]

    resposta_pedido = client.post(
        "/pedidos",
        json={
            "cliente_id": 99999,
            "itens": [
                {
                    "produto_id": produto_id,
                    "quantidade": 2
                }
            ]
        }
    )

    assert resposta_pedido.status_code == 404
    assert resposta_pedido.json()["detail"] == (
        "Cliente nao encontrado ou inativo"
    )

    with test_engine.connect() as conexao:
        estoque = conexao.execute(
            text("""
                SELECT estoque
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        ).scalar_one()

        quantidade_pedidos = conexao.execute(
            text("SELECT COUNT(*) FROM pedidos")
        ).scalar_one()

        quantidade_itens = conexao.execute(
            text("SELECT COUNT(*) FROM itens_pedido")
        ).scalar_one()

    assert estoque == 10
    assert quantidade_pedidos == 0
    assert quantidade_itens == 0



def test_pedido_com_cliente_inativo(
    client,
    test_engine,
    banco_limpo,
    cliente_autenticado
):
    senha = "TechStore@2026"
    email = "paulo.roberto@exemplo.com"

    resposta_cliente = client.post(
        "/clientes",
        json={
            "nome": "Paulo Roberto",
            "email": email,
            "telefone": "11955554444",
            "cpf": "44455566677",
            "senha": senha
        }
    )

    assert resposta_cliente.status_code == 201
    cliente_id = resposta_cliente.json()["id"]

    headers = cliente_autenticado(email, senha)

    resposta_produto = client.post(
        "/produtos",
        json={
            "nome": "Teclado USB",
            "categoria": "Perifericos",
            "preco": "99.90",
            "estoque": 8
        }
    )

    assert resposta_produto.status_code == 201
    produto_id = resposta_produto.json()["id"]

    resposta_exclusao = client.delete(
        f"/clientes/{cliente_id}",
        headers=headers
    )

    assert resposta_exclusao.status_code == 200

    resposta_pedido = client.post(
        "/pedidos",
        json={
            "cliente_id": cliente_id,
            "itens": [
                {
                    "produto_id": produto_id,
                    "quantidade": 3
                }
            ]
        }
    )

    assert resposta_pedido.status_code == 404
    assert resposta_pedido.json()["detail"] == (
        "Cliente nao encontrado ou inativo"
    )

    with test_engine.connect() as conexao:
        cliente_banco = conexao.execute(
            text("""
                SELECT ativo
                FROM clientes
                WHERE id = :cliente_id
            """),
            {"cliente_id": cliente_id}
        ).scalar_one()

        estoque = conexao.execute(
            text("""
                SELECT estoque
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        ).scalar_one()

        quantidade_pedidos = conexao.execute(
            text("SELECT COUNT(*) FROM pedidos")
        ).scalar_one()

        quantidade_itens = conexao.execute(
            text("SELECT COUNT(*) FROM itens_pedido")
        ).scalar_one()

    assert cliente_banco is False
    assert estoque == 8
    assert quantidade_pedidos == 0
    assert quantidade_itens == 0
