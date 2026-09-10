import os
import sqlite3

from src.models import Empresa


CAMINHO_BANCO = "data/labd.db"


def conectar():
    """
    Cria conexão com o banco SQLite.
    """
    os.makedirs("data", exist_ok=True)

    conexao = sqlite3.connect(CAMINHO_BANCO)

    # Ativa relacionamentos com chaves estrangeiras
    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


def criar_banco():
    """
    Cria todas as tabelas necessárias.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            website TEXT NOT NULL UNIQUE,
            email TEXT,
            telefone TEXT,
            endereco TEXT,
            tipo_empresa TEXT NOT NULL,
            observacoes TEXT
        );


        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            descricao TEXT,
            categoria TEXT,
            imagem_url TEXT,
            fonte_url TEXT,

            FOREIGN KEY (empresa_id)
                REFERENCES empresas(id)
                ON DELETE CASCADE
        );


        CREATE TABLE IF NOT EXISTS segmentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        );


        CREATE TABLE IF NOT EXISTS empresa_segmentos (
            empresa_id INTEGER NOT NULL,
            segmento_id INTEGER NOT NULL,

            PRIMARY KEY (
                empresa_id,
                segmento_id
            ),

            FOREIGN KEY (empresa_id)
                REFERENCES empresas(id)
                ON DELETE CASCADE,

            FOREIGN KEY (segmento_id)
                REFERENCES segmentos(id)
                ON DELETE CASCADE
        );


        CREATE TABLE IF NOT EXISTS produto_segmentos (
            produto_id INTEGER NOT NULL,
            segmento_id INTEGER NOT NULL,

            PRIMARY KEY (
                produto_id,
                segmento_id
            ),

            FOREIGN KEY (produto_id)
                REFERENCES produtos(id)
                ON DELETE CASCADE,

            FOREIGN KEY (segmento_id)
                REFERENCES segmentos(id)
                ON DELETE CASCADE
        );


        CREATE TABLE IF NOT EXISTS certificacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            nome TEXT NOT NULL,

            FOREIGN KEY (empresa_id)
                REFERENCES empresas(id)
                ON DELETE CASCADE
        );


        CREATE TABLE IF NOT EXISTS fontes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            url TEXT NOT NULL,

            FOREIGN KEY (empresa_id)
                REFERENCES empresas(id)
                ON DELETE CASCADE
        );
        """
    )

    conexao.commit()
    conexao.close()

    print(f"[OK] Banco criado em {CAMINHO_BANCO}")


def obter_segmento_id(cursor, nome):
    """
    Retorna o ID de um segmento.
    Se não existir, cria automaticamente.
    """

    cursor.execute(
        """
        INSERT OR IGNORE INTO segmentos (nome)
        VALUES (?)
        """,
        (nome,)
    )

    cursor.execute(
        """
        SELECT id
        FROM segmentos
        WHERE nome = ?
        """,
        (nome,)
    )

    resultado = cursor.fetchone()

    return resultado[0]


def salvar_empresa(empresa: Empresa):
    """
    Salva uma Empresa validada pelo Pydantic
    dentro do SQLite.
    """

    conexao = conectar()
    cursor = conexao.cursor()

    # Empresa
    cursor.execute(
        """
        INSERT INTO empresas (
            nome,
            descricao,
            website,
            email,
            telefone,
            endereco,
            tipo_empresa,
            observacoes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(website)
        DO UPDATE SET

            nome = excluded.nome,
            descricao = excluded.descricao,
            email = excluded.email,
            telefone = excluded.telefone,
            endereco = excluded.endereco,
            tipo_empresa = excluded.tipo_empresa,
            observacoes = excluded.observacoes
        """,
        (
            empresa.nome,
            empresa.descricao,
            empresa.website,
            empresa.email,
            empresa.telefone,
            empresa.endereco,
            empresa.tipo_empresa,
            empresa.observacoes
        )
    )

    cursor.execute(
        """
        SELECT id
        FROM empresas
        WHERE website = ?
        """,
        (empresa.website,)
    )

    empresa_id = cursor.fetchone()[0]

    # Limpa informações relacionadas antes de atualizar.
    # Assim os testes não acumulam dados duplicados.
    cursor.execute(
        "DELETE FROM produtos WHERE empresa_id = ?",
        (empresa_id,)
    )

    cursor.execute(
        "DELETE FROM empresa_segmentos WHERE empresa_id = ?",
        (empresa_id,)
    )

    cursor.execute(
        "DELETE FROM certificacoes WHERE empresa_id = ?",
        (empresa_id,)
    )

    cursor.execute(
        "DELETE FROM fontes WHERE empresa_id = ?",
        (empresa_id,)
    )

    # Segmentos da empresa
    for segmento in empresa.segmentos_medicos:

        segmento_id = obter_segmento_id(
            cursor,
            segmento
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO empresa_segmentos (
                empresa_id,
                segmento_id
            )
            VALUES (?, ?)
            """,
            (
                empresa_id,
                segmento_id
            )
        )

    # Certificações
    for certificacao in empresa.certificacoes:

        cursor.execute(
            """
            INSERT INTO certificacoes (
                empresa_id,
                nome
            )
            VALUES (?, ?)
            """,
            (
                empresa_id,
                certificacao
            )
        )

    # Fontes
    for fonte in empresa.fontes:

        cursor.execute(
            """
            INSERT INTO fontes (
                empresa_id,
                url
            )
            VALUES (?, ?)
            """,
            (
                empresa_id,
                fonte
            )
        )

    # Produtos
    for produto in empresa.produtos:

        cursor.execute(
            """
            INSERT INTO produtos (
                empresa_id,
                nome,
                descricao,
                categoria,
                imagem_url,
                fonte_url
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                empresa_id,
                produto.nome,
                produto.descricao,
                produto.categoria,
                produto.imagem_url,
                produto.fonte_url
            )
        )

        produto_id = cursor.lastrowid

        for segmento in produto.segmentos_medicos:

            segmento_id = obter_segmento_id(
                cursor,
                segmento
            )

            cursor.execute(
                """
                INSERT OR IGNORE INTO produto_segmentos (
                    produto_id,
                    segmento_id
                )
                VALUES (?, ?)
                """,
                (
                    produto_id,
                    segmento_id
                )
            )

    conexao.commit()
    conexao.close()

    print(
        f"[OK] Empresa '{empresa.nome}' "
        f"salva no banco."
    )