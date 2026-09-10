import json
import sqlite3
from datetime import datetime
from pathlib import Path

from src.models import Empresa


DATA_DIR = Path("data")

LABD_DB = DATA_DIR / "labd_simulado.db"
MBO_DB = DATA_DIR / "mbo_simulado.db"


def criar_bancos_integracao():
    """
    Cria dois bancos SQLite independentes para simular
    os sistemas internos da LABD e da MBO.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Banco simulado LABD
    with sqlite3.connect(LABD_DB) as conexao:
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS empresas_labd (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                website TEXT NOT NULL UNIQUE,
                descricao TEXT,
                email TEXT,
                telefone TEXT,
                endereco TEXT,
                tipo_empresa TEXT,
                certificacoes_json TEXT,
                atualizado_em TEXT NOT NULL
            )
            """
        )

    # Banco simulado MBO
    with sqlite3.connect(MBO_DB) as conexao:
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS perfis_mbo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                website TEXT NOT NULL UNIQUE,
                tipo_empresa TEXT,
                segmentos_medicos_json TEXT,
                produtos_json TEXT,
                atualizado_em TEXT NOT NULL
            )
            """
        )


def enviar_para_labd(empresa: Empresa):
    """
    Simula o envio dos dados institucionais e regulatórios
    para o sistema interno da LABD.
    """

    atualizado_em = datetime.now().isoformat(
        timespec="seconds"
    )

    with sqlite3.connect(LABD_DB) as conexao:
        conexao.execute(
            """
            INSERT INTO empresas_labd (
                nome,
                website,
                descricao,
                email,
                telefone,
                endereco,
                tipo_empresa,
                certificacoes_json,
                atualizado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(website)
            DO UPDATE SET
                nome = excluded.nome,
                descricao = excluded.descricao,
                email = excluded.email,
                telefone = excluded.telefone,
                endereco = excluded.endereco,
                tipo_empresa = excluded.tipo_empresa,
                certificacoes_json = excluded.certificacoes_json,
                atualizado_em = excluded.atualizado_em
            """,
            (
                empresa.nome,
                empresa.website,
                empresa.descricao,
                empresa.email,
                empresa.telefone,
                empresa.endereco,
                empresa.tipo_empresa,
                json.dumps(
                    empresa.certificacoes,
                    ensure_ascii=False
                ),
                atualizado_em
            )
        )

    print(
        "[LABD] Empresa sincronizada com sucesso."
    )


def enviar_para_mbo(empresa: Empresa):
    """
    Simula o envio dos dados usados pela plataforma MBO,
    incluindo classificação, segmentos e produtos.
    """

    atualizado_em = datetime.now().isoformat(
        timespec="seconds"
    )

    produtos = [
        produto.model_dump()
        for produto in empresa.produtos
    ]

    with sqlite3.connect(MBO_DB) as conexao:
        conexao.execute(
            """
            INSERT INTO perfis_mbo (
                nome,
                website,
                tipo_empresa,
                segmentos_medicos_json,
                produtos_json,
                atualizado_em
            )
            VALUES (?, ?, ?, ?, ?, ?)

            ON CONFLICT(website)
            DO UPDATE SET
                nome = excluded.nome,
                tipo_empresa = excluded.tipo_empresa,
                segmentos_medicos_json = excluded.segmentos_medicos_json,
                produtos_json = excluded.produtos_json,
                atualizado_em = excluded.atualizado_em
            """,
            (
                empresa.nome,
                empresa.website,
                empresa.tipo_empresa,
                json.dumps(
                    empresa.segmentos_medicos,
                    ensure_ascii=False
                ),
                json.dumps(
                    produtos,
                    ensure_ascii=False
                ),
                atualizado_em
            )
        )

    print(
        "[MBO] Empresa sincronizada com sucesso."
    )


def sincronizar_labd_mbo(
    empresa: Empresa
):
    """
    Executa a integração simulada com os dois sistemas.
    """

    criar_bancos_integracao()

    enviar_para_labd(
        empresa
    )

    enviar_para_mbo(
        empresa
    )

    return {
        "labd": "sincronizado",
        "mbo": "sincronizado"
    }