from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from src.scraper import coletar_site
from src.llm_service import analisar_empresa
from src.database import criar_banco, salvar_empresa
from src.image_extractor import buscar_imagem_produto
from src.integracao import sincronizar_labd_mbo


app = FastAPI(
    title="LABD AI Data Agent",
    description=(
        "API para coleta, classificação, enriquecimento "
        "e estruturação de dados públicos de empresas "
        "do setor médico-hospitalar."
    ),
    version="1.0.0"
)


PASTA_RESULTADOS = Path(
    "data/resultados"
)


class RequisicaoEmpresa(
    BaseModel
):
    nome: str
    website: str


@app.get("/")
def inicio():
    return {
        "status": "online",
        "servico": "LABD AI Data Agent"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


def enriquecer_imagens(
    empresa
):
    """
    Procura imagens dos produtos depois
    da análise semântica feita pelo Gemini.
    """

    total = len(
        empresa.produtos
    )

    if total == 0:
        return empresa

    print(
        f"[IMAGENS] Procurando imagens "
        f"para {total} produtos..."
    )

    for indice, produto in enumerate(
        empresa.produtos,
        start=1
    ):

        print(
            f"[IMAGENS] [{indice}/{total}] "
            f"{produto.nome}"
        )

        # Não refaz a busca caso o produto
        # já possua uma imagem.
        if produto.imagem_url:
            continue

        try:

            imagem, pagina = (
                buscar_imagem_produto(
                    nome_produto=produto.nome,
                    fonte_url=produto.fonte_url,
                    website=empresa.website
                )
            )

            if imagem:

                produto.imagem_url = imagem

                if pagina:
                    produto.fonte_url = pagina

                print(
                    f"[IMAGENS] [OK] "
                    f"{produto.nome}"
                )

            else:

                print(
                    f"[IMAGENS] [AVISO] "
                    f"Imagem não identificada "
                    f"para {produto.nome}"
                )

        except Exception as erro:

            # Uma imagem com problema
            # não interrompe o pipeline.
            print(
                f"[IMAGENS] [ERRO] "
                f"{produto.nome}: {erro}"
            )

    return empresa


def salvar_json(
    nome,
    empresa
):
    """
    Mantém uma cópia estruturada do resultado
    para auditoria e demonstração.
    """

    PASTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True
    )

    caminho = (
        PASTA_RESULTADOS
        / f"{nome}.json"
    )

    caminho.write_text(
        empresa.model_dump_json(
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        f"[OK] JSON salvo em {caminho}"
    )


@app.post("/processar")
def processar_empresa(
    requisicao: RequisicaoEmpresa
):

    try:

        nome = (
            requisicao.nome
            .lower()
            .strip()
        )

        website = (
            requisicao.website
            .strip()
        )

        print(
            "\n===================================="
        )

        print(
            f"[API] Processando: {nome}"
        )

        print(
            f"[API] Website: {website}"
        )

        print(
            "===================================="
        )

        # -------------------------------------
        # 1. COLETA DE DADOS
        # -------------------------------------

        coletar_site(
            nome_empresa=nome,
            urls=[
                website
            ]
        )

        # -------------------------------------
        # 2. ANÁLISE COM IA + PYDANTIC
        # -------------------------------------

        empresa = analisar_empresa(
            nome_empresa=nome,
            website=website
        )

        # -------------------------------------
        # 3. ENRIQUECIMENTO DAS IMAGENS
        # -------------------------------------

        empresa = enriquecer_imagens(
            empresa
        )

        # -------------------------------------
        # 4. BANCO PRINCIPAL ESTRUTURADO
        # -------------------------------------

        criar_banco()

        salvar_empresa(
            empresa
        )

        # -------------------------------------
        # 5. INTEGRAÇÃO LABD E MBO
        # -------------------------------------

        integracao = (
            sincronizar_labd_mbo(
                empresa
            )
        )

        # -------------------------------------
        # 6. JSON PARA AUDITORIA
        # -------------------------------------

        salvar_json(
            nome,
            empresa
        )

        # -------------------------------------
        # 7. RESUMO DA EXECUÇÃO
        # -------------------------------------

        produtos_com_imagem = sum(
            1
            for produto in empresa.produtos
            if produto.imagem_url
        )

        # -------------------------------------
        # 8. RESPOSTA PARA O N8N
        # -------------------------------------

        return {
            "status": "sucesso",

            "integracao": {
                "labd": integracao["labd"],
                "mbo": integracao["mbo"]
            },

            "resumo": {
                "produtos": len(
                    empresa.produtos
                ),

                "produtos_com_imagem": (
                    produtos_com_imagem
                ),

                "segmentos": len(
                    empresa.segmentos_medicos
                ),

                "certificacoes": len(
                    empresa.certificacoes
                )
            },

            "empresa": (
                empresa.model_dump()
            )
        }

    except Exception as erro:

        print(
            f"[ERRO API] {erro}"
        )

        return {
            "status": "erro",
            "mensagem": str(
                erro
            ),
            "empresa": None
        }