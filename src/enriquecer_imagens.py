import json
import time
from pathlib import Path

from src.image_extractor import buscar_imagem_produto
from src.models import Empresa
from src.database import criar_banco, salvar_empresa


PASTA_RESULTADOS = Path(
    "data/resultados"
)


def processar_arquivo(
    caminho
):
    print(
        "\n===================================="
    )

    print(
        f"EMPRESA: {caminho.stem}"
    )

    print(
        "===================================="
    )

    dados = json.loads(
        caminho.read_text(
            encoding="utf-8"
        )
    )

    website = dados.get(
        "website"
    )

    produtos = dados.get(
        "produtos",
        []
    )

    if not produtos:

        print(
            "[INFO] Empresa não possui "
            "produtos identificados."
        )

        return

    total = len(
        produtos
    )

    encontrados = 0

    for indice, produto in enumerate(
        produtos,
        start=1
    ):

        nome = produto.get(
            "nome"
        )

        fonte_url = produto.get(
            "fonte_url"
        )

        print(
            f"\n[{indice}/{total}] "
            f"{nome}"
        )

        # Se já possui imagem,
        # não faz nova requisição.
        if produto.get(
            "imagem_url"
        ):

            print(
                "  [OK] Produto já possui imagem."
            )

            encontrados += 1
            continue

        imagem, pagina = buscar_imagem_produto(
            nome_produto=nome,
            fonte_url=fonte_url,
            website=website
        )

        if imagem:

            produto[
                "imagem_url"
            ] = imagem

            # Se descobrimos uma página mais específica,
            # também melhoramos a fonte do produto.
            if pagina:

                produto[
                    "fonte_url"
                ] = pagina

            encontrados += 1

            print(
                f"  [OK] Imagem encontrada:"
            )

            print(
                f"       {imagem}"
            )

        else:

            print(
                "  [AVISO] Nenhuma imagem "
                "confiável encontrada."
            )

        # Evita disparar muitas requisições
        # em sequência.
        time.sleep(
            0.3
        )

    # Salva novamente o JSON
    caminho.write_text(
        json.dumps(
            dados,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print(
        f"\n[RESULTADO] {encontrados}/{total} "
        f"produtos com imagem."
    )

    # Valida novamente com Pydantic.
    empresa = Empresa.model_validate(
        dados
    )

    # Atualiza SQLite com as novas imagens.
    salvar_empresa(
        empresa
    )

    print(
        "[OK] JSON e banco atualizados."
    )


def main():

    print(
        "\n===================================="
    )

    print(
        "ENRIQUECIMENTO DE IMAGENS"
    )

    print(
        "===================================="
    )

    criar_banco()

    arquivos = sorted(
        PASTA_RESULTADOS.glob(
            "*.json"
        )
    )

    for arquivo in arquivos:

        try:

            processar_arquivo(
                arquivo
            )

        except Exception as erro:

            print(
                f"[ERRO] {arquivo.name}: "
                f"{erro}"
            )

    print(
        "\n===================================="
    )

    print(
        "ENRIQUECIMENTO FINALIZADO"
    )

    print(
        "===================================="
    )


if __name__ == "__main__":
    main()