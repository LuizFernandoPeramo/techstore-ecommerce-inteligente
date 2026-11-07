
from fastapi import APIRouter, Depends, status

from app.core.permissions import exigir_administrador
from app.schemas.produto import Produto, ProdutoCadastro
from app.services import produto_service


router = APIRouter(
    prefix="/produtos",
    tags=["Produtos"]
)


@router.get("", response_model=list[Produto])
def listar_produtos():
    return produto_service.listar_produtos()


@router.get("/{produto_id}", response_model=Produto)
def consultar_produto(produto_id: int):
    return produto_service.consultar_produto(produto_id)


@router.post(
    "",
    response_model=Produto,
    status_code=status.HTTP_201_CREATED
)
def cadastrar_produto(
    produto: ProdutoCadastro,
    administrador: dict = Depends(exigir_administrador)
):
    return produto_service.cadastrar_produto(produto)


@router.put("/{produto_id}", response_model=Produto)
def atualizar_produto(
    produto_id: int,
    produto: ProdutoCadastro,
    administrador: dict = Depends(exigir_administrador)
):
    return produto_service.atualizar_produto(
        produto_id,
        produto
    )


@router.delete("/{produto_id}")
def excluir_produto(
    produto_id: int,
    administrador: dict = Depends(exigir_administrador)
):
    return produto_service.excluir_produto(produto_id)
