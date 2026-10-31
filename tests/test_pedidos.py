
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
    banco_limpo
):
    resposta_cliente = client.post(
        "/clientes",
        json={
            "nome": "Paulo Roberto",
            "email": "paulo.roberto@exemplo.com",
            "telefone": "11955554444",
            "cpf": "44455566677"
        }
    )

    assert resposta_cliente.status_code == 201
    cliente_id = resposta_cliente.json()["id"]

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
        f"/clientes/{cliente_id}"
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

def test_consultar_pedido(client, banco_limpo):
    resposta_cliente = client.post(
        "/clientes",
        json={
            "nome": "Juliana Martins",
            "email": "juliana.pedidos@exemplo.com",
            "telefone": "11988887777",
            "cpf": "55566677788"
        }
    )

    assert resposta_cliente.status_code == 201
    cliente_id = resposta_cliente.json()["id"]

    resposta_produto = client.post(
        "/produtos",
        json={
            "nome": "Mouse Gamer",
            "categoria": "Perifericos",
            "preco": "149.90",
            "estoque": 10
        }
    )

    assert resposta_produto.status_code == 201
    produto_id = resposta_produto.json()["id"]

    resposta_cadastro = client.post(
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

    assert resposta_cadastro.status_code == 201
    pedido_id = resposta_cadastro.json()["id"]

    resposta_consulta = client.get(f"/pedidos/{pedido_id}")

    assert resposta_consulta.status_code == 200

    dados = resposta_consulta.json()

    assert dados["id"] == pedido_id
    assert dados["cliente_id"] == cliente_id
    assert dados["cliente_nome"] == "Juliana Martins"
    assert dados["status"] == "pendente"
    assert Decimal(str(dados["valor_total"])) == Decimal("299.80")
    assert len(dados["itens"]) == 1

    item = dados["itens"][0]

    assert item["produto_id"] == produto_id
    assert item["nome"] == "Mouse Gamer"
    assert item["quantidade"] == 2
    assert Decimal(str(item["preco_unitario"])) == Decimal("149.90")
    assert Decimal(str(item["subtotal"])) == Decimal("299.80")


def test_consultar_pedido_inexistente(client, banco_limpo):
    resposta = client.get("/pedidos/99999")

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Pedido nao encontrado"


def test_listar_pedidos(client, banco_limpo):
    resposta_cliente = client.post(
        "/clientes",
        json={
            "nome": "Ricardo Oliveira",
            "email": "ricardo.lista@exemplo.com",
            "telefone": "11977776666",
            "cpf": "66677788899"
        }
    )

    assert resposta_cliente.status_code == 201
    cliente_id = resposta_cliente.json()["id"]

    resposta_produto = client.post(
        "/produtos",
        json={
            "nome": "Teclado Mecanico",
            "categoria": "Perifericos",
            "preco": "250.00",
            "estoque": 10
        }
    )

    assert resposta_produto.status_code == 201
    produto_id = resposta_produto.json()["id"]

    pedidos_criados = []

    for quantidade in [1, 2]:
        resposta = client.post(
            "/pedidos",
            json={
                "cliente_id": cliente_id,
                "itens": [
                    {
                        "produto_id": produto_id,
                        "quantidade": quantidade
                    }
                ]
            }
        )

        assert resposta.status_code == 201
        pedidos_criados.append(resposta.json()["id"])

    resposta_listagem = client.get("/pedidos")

    assert resposta_listagem.status_code == 200

    dados = resposta_listagem.json()

    assert isinstance(dados, list)
    assert len(dados) == 2

    ids_retornados = [pedido["id"] for pedido in dados]

    assert ids_retornados == list(reversed(pedidos_criados))

    for pedido in dados:
        assert pedido["cliente_id"] == cliente_id
        assert pedido["cliente_nome"] == "Ricardo Oliveira"
        assert pedido["status"] == "pendente"

    assert Decimal(str(dados[0]["valor_total"])) == Decimal("500.00")
    assert Decimal(str(dados[1]["valor_total"])) == Decimal("250.00")

def test_cancelar_pedido_e_devolver_estoque(
    client,
    test_engine,
    banco_limpo
):
    resposta_cliente = client.post(
        "/clientes",
        json={
            "nome": "Patricia Almeida",
            "email": "patricia.cancelamento@exemplo.com",
            "telefone": "11966665555",
            "cpf": "77788899900"
        }
    )

    assert resposta_cliente.status_code == 201
    cliente_id = resposta_cliente.json()["id"]

    resposta_produto = client.post(
        "/produtos",
        json={
            "nome": "Headset Gamer",
            "categoria": "Perifericos",
            "preco": "199.90",
            "estoque": 10
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
                    "quantidade": 3
                }
            ]
        }
    )

    assert resposta_pedido.status_code == 201
    pedido_id = resposta_pedido.json()["id"]

    with test_engine.connect() as conexao:
        estoque_apos_compra = conexao.execute(
            text("""
                SELECT estoque
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        ).scalar_one()

    assert estoque_apos_compra == 7

    resposta_cancelamento = client.patch(
        f"/pedidos/{pedido_id}/status",
        json={"status": "cancelado"}
    )

    assert resposta_cancelamento.status_code == 200

    dados = resposta_cancelamento.json()

    assert dados["id"] == pedido_id
    assert dados["status"] == "cancelado"
    assert dados["mensagem"] == (
        "Status do pedido atualizado com sucesso"
    )

    with test_engine.connect() as conexao:
        estoque_apos_cancelamento = conexao.execute(
            text("""
                SELECT estoque
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        ).scalar_one()

        status_banco = conexao.execute(
            text("""
                SELECT status
                FROM pedidos
                WHERE id = :pedido_id
            """),
            {"pedido_id": pedido_id}
        ).scalar_one()

    assert estoque_apos_cancelamento == 10
    assert status_banco == "cancelado"

    resposta_segundo_cancelamento = client.patch(
        f"/pedidos/{pedido_id}/status",
        json={"status": "cancelado"}
    )

    assert resposta_segundo_cancelamento.status_code == 409

    with test_engine.connect() as conexao:
        estoque_final = conexao.execute(
            text("""
                SELECT estoque
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        ).scalar_one()

    assert estoque_final == 10

def test_fluxo_completo_status_pedido(
    client,
    test_engine,
    banco_limpo
):
    resposta_cliente = client.post(
        "/clientes",
        json={
            "nome": "Marcelo Ferreira",
            "email": "marcelo.status@exemplo.com",
            "telefone": "11955554444",
            "cpf": "88899900011"
        }
    )

    assert resposta_cliente.status_code == 201
    cliente_id = resposta_cliente.json()["id"]

    resposta_produto = client.post(
        "/produtos",
        json={
            "nome": "Notebook Lenovo",
            "categoria": "Computadores",
            "preco": "3499.90",
            "estoque": 5
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
                    "quantidade": 1
                }
            ]
        }
    )

    assert resposta_pedido.status_code == 201

    pedido_id = resposta_pedido.json()["id"]
    assert resposta_pedido.json()["status"] == "pendente"

    for novo_status in ["pago", "enviado", "entregue"]:
        resposta = client.patch(
            f"/pedidos/{pedido_id}/status",
            json={"status": novo_status}
        )

        assert resposta.status_code == 200
        assert resposta.json()["id"] == pedido_id
        assert resposta.json()["status"] == novo_status

    resposta_consulta = client.get(f"/pedidos/{pedido_id}")

    assert resposta_consulta.status_code == 200
    assert resposta_consulta.json()["status"] == "entregue"

    resposta_alteracao_invalida = client.patch(
        f"/pedidos/{pedido_id}/status",
        json={"status": "cancelado"}
    )

    assert resposta_alteracao_invalida.status_code == 409

    assert resposta_alteracao_invalida.json()["detail"] == (
        "Nao e permitido alterar o pedido "
        "de 'entregue' para 'cancelado'"
    )

    with test_engine.connect() as conexao:
        pedido_banco = conexao.execute(
            text("""
                SELECT status, valor_total
                FROM pedidos
                WHERE id = :pedido_id
            """),
            {"pedido_id": pedido_id}
        ).mappings().one()

        estoque_final = conexao.execute(
            text("""
                SELECT estoque
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        ).scalar_one()

    assert pedido_banco["status"] == "entregue"
    assert pedido_banco["valor_total"] == Decimal("3499.90")
    assert estoque_final == 4

def test_impedir_transicoes_invalidas_pedido(
    client,
    test_engine,
    banco_limpo
):
    resposta_cliente = client.post(
        "/clientes",
        json={
            "nome": "Roberto Martins",
            "email": "roberto.status@exemplo.com",
            "telefone": "11944443333",
            "cpf": "99900011122"
        }
    )

    assert resposta_cliente.status_code == 201
    cliente_id = resposta_cliente.json()["id"]

    resposta_produto = client.post(
        "/produtos",
        json={
            "nome": "Monitor Full HD",
            "categoria": "Monitores",
            "preco": "899.90",
            "estoque": 10
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
                    "quantidade": 2
                }
            ]
        }
    )

    assert resposta_pedido.status_code == 201
    pedido_id = resposta_pedido.json()["id"]

    for status_invalido in ["enviado", "entregue"]:
        resposta = client.patch(
            f"/pedidos/{pedido_id}/status",
            json={"status": status_invalido}
        )

        assert resposta.status_code == 409
        assert resposta.json()["detail"] == (
            "Nao e permitido alterar o pedido "
            f"de 'pendente' para '{status_invalido}'"
        )

    resposta_pagamento = client.patch(
        f"/pedidos/{pedido_id}/status",
        json={"status": "pago"}
    )

    assert resposta_pagamento.status_code == 200

    resposta_voltar_pendente = client.patch(
        f"/pedidos/{pedido_id}/status",
        json={"status": "pendente"}
    )

    assert resposta_voltar_pendente.status_code == 409

    resposta_entrega_direta = client.patch(
        f"/pedidos/{pedido_id}/status",
        json={"status": "entregue"}
    )

    assert resposta_entrega_direta.status_code == 409

    with test_engine.connect() as conexao:
        pedido_banco = conexao.execute(
            text("""
                SELECT status, valor_total
                FROM pedidos
                WHERE id = :pedido_id
            """),
            {"pedido_id": pedido_id}
        ).mappings().one()

        estoque_final = conexao.execute(
            text("""
                SELECT estoque
                FROM produtos
                WHERE id = :produto_id
            """),
            {"produto_id": produto_id}
        ).scalar_one()

    assert pedido_banco["status"] == "pago"
    assert pedido_banco["valor_total"] == Decimal("1799.80")
    assert estoque_final == 8
