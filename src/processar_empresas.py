import json
import time
from pathlib import Path

from src.llm_service import analisar_empresa
from src.database import criar_banco, salvar_empresa


EMPRESAS = [
    {
        "nome": "spmmedicare",
        "website": "https://spmmedicare.com"
    },
    {
        "nome": "lifespine",
        "website": "http://lifespine.com.br"
    },
    {
        "nome": "kontmed",
        # Domínio funcional encontrado pelo fallback
        "website": "https://kontourmed.com"
    },
    {
        "nome": "oncoexo",
        "website": "https://oncoexo.com.br"
    },
    {
        "nome": "verarosas",
        "website": "https://www.verarosas.com.br"
    }
]


PASTA_RESULTADOS = Path("data/resultados")


def salvar_json(nome_empresa, empresa):
    """
    Salva também uma cópia em JSON para facilitar
    auditoria, demonstração e debugging.
    """

    PASTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True
    )

    caminho = (
        PASTA_RESULTADOS /
        f"{nome_empresa}.json"
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


def main():

    print(
        "\n===================================="
    )
    print(
        "PIPELINE LABD - PROCESSAMENTO"
    )
    print(
        "====================================\n"
    )

    criar_banco()

    sucessos = []
    erros = []

    for indice, item in enumerate(
        EMPRESAS,
        start=1
    ):

        nome = item["nome"]
        website = item["website"]

        print(
            f"\n[{indice}/{len(EMPRESAS)}] "
            f"Processando {nome}"
        )

        try:
            # TXT -> Gemini -> Pydantic
            empresa = analisar_empresa(
                nome_empresa=nome,
                website=website
            )

            # Salva JSON estruturado
            salvar_json(
                nome,
                empresa
            )

            # Salva no SQLite
            salvar_empresa(
                empresa
            )

            sucessos.append(nome)

            print(
                f"[SUCESSO] {nome} concluída."
            )

        except Exception as erro:

            print(
                f"[ERRO] Não foi possível "
                f"processar {nome}: {erro}"
            )

            erros.append(
                {
                    "empresa": nome,
                    "erro": str(erro)
                }
            )

        # Pequeno intervalo entre APIs
        # para evitar chamadas consecutivas demais
        if indice < len(EMPRESAS):

            print(
                "[INFO] Aguardando 3 segundos..."
            )

            time.sleep(3)

    print(
        "\n===================================="
    )

    print(
        "RESUMO DO PROCESSAMENTO"
    )

    print(
        "===================================="
    )

    print(
        f"Sucessos: {len(sucessos)}"
    )

    for nome in sucessos:
        print(f"  [OK] {nome}")

    print(
        f"\nErros: {len(erros)}"
    )

    for erro in erros:
        print(
            f"  [ERRO] {erro['empresa']}: "
            f"{erro['erro']}"
        )

    print(
        "\nPipeline finalizado."
    )


if __name__ == "__main__":
    main()