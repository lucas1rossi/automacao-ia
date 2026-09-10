from typing import Optional, Literal
from pydantic import BaseModel, Field


TipoEmpresa = Literal[
    "Fabricante",
    "Distribuidor",
    "Prestador de Serviços",
    "Não identificado"
]


class Produto(BaseModel):
    nome: str

    descricao: Optional[str] = None

    categoria: Optional[str] = None

    imagem_url: Optional[str] = None

    segmentos_medicos: list[str] = Field(
        default_factory=list
    )

    fonte_url: Optional[str] = None


class Empresa(BaseModel):
    nome: str

    descricao: Optional[str] = None

    website: str

    email: Optional[str] = None

    telefone: Optional[str] = None

    endereco: Optional[str] = None

    tipo_empresa: TipoEmpresa = "Não identificado"

    segmentos_medicos: list[str] = Field(
        default_factory=list
    )

    certificacoes: list[str] = Field(
        default_factory=list
    )

    produtos: list[Produto] = Field(
        default_factory=list
    )

    fontes: list[str] = Field(
        default_factory=list
    )

    observacoes: Optional[str] = None