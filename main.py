import sys
import time
from pathlib import Path

from src.scraper import coletar_site
from src.llm_service import analisar_empresa
from src.database import criar_banco, salvar_empresa
from src.image_extractor import buscar_imagem_produto
from src.integracao import sincronizar_labd_mbo
from src.models import Empresa


# ============================================================
# CONFIGURAÇÃO DAS EMPRESAS DA PROVA
# ============================================================

EMPRESAS = [
    {
        "nome": "spmmedicare",
        "website": "https://spmmedicare.com",
        "urls": [
            "https://spmmedicare.com"
        ]
    },
    {
        "nome": "lifespine",
        "website": "http://lifespine.com.br",
        "urls": [
            "http://lifespine.com.br",
            "https://lifespine.com.br",
            "https://www.lifespine.com.br"
        ]
    },
    {
        "nome": "kontmed",
        # O domínio fornecido na prova é tentado primeiro.
        # Caso esteja indisponível, usamos o domínio
        # público funcional encontrado durante os testes.
        "website": "https://kontourmed.com",
        "urls": [
            "http://kontmed.com",
            "https://kontmed.com",
            "https://www.kontmed.com",
            "https://kontourmed.com",
            "https://www.kontourmed.com"
        ]
    },
    {
        "nome": "oncoexo",
        "website": "https://oncoexo.com.br",
        "urls": [
            "https://oncoexo.com.br",
            "https://www.oncoexo.com.br"
        ]
    },
    {
        "nome": "verarosas",
        "website": "https://www.verarosas.com.br",
        "urls": [
            "https://www.verarosas.com.br",
            "https://verarosas.com.br"
        ]
    }
]


DATA_DIR = Path("data")
RESULTADOS_DIR = DATA_DIR / "resultados"


# ============================================================
# SALVAMENTO DO JSON
# ============================================================

def salvar_json(nome_empresa, empresa):
    """
    Salva uma cópia estruturada do resultado em JSON.
    """

    RESULTADOS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    caminho = (
        RESULTADOS_DIR /
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


# ============================================================
# ENRIQUECIMENTO DAS IMAGENS
# ============================================================

def enriquecer_imagens(empresa):
    """
    Procura imagens públicas dos produtos.

    Uma falha de imagem não interrompe
    o processamento da empresa.
    """

    total = len(
        empresa.produtos
    )

    if total == 0:
        print(
            "[IMAGENS] Nenhum produto "
            "para processar."
        )

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
            f"[IMAGENS] "
            f"[{indice}/{total}] "
            f"{produto.nome}"
        )

        # Se já existe uma imagem confiável,
        # não fazemos outra requisição.
        if produto.imagem_url:

            print(
                "[IMAGENS] [OK] "
                "Produto já possui imagem."
            )

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
                    f"Imagem não encontrada "
                    f"para {produto.nome}"
                )

        except Exception as erro:

            # Uma imagem com problema
            # não derruba o pipeline.
            print(
                f"[IMAGENS] [ERRO] "
                f"{produto.nome}: {erro}"
            )

        time.sleep(
            0.3
        )

    return empresa


# ============================================================
# PROCESSAMENTO DE UMA EMPRESA
# ============================================================

def processar_empresa(item):
    """
    Pipeline completo:

    Website
        ↓
    Scraping
        ↓
    Gemini / LLM
        ↓
    Pydantic
        ↓
    Imagens
        ↓
    Banco principal
        ↓
    LABD simulada
        ↓
    MBO simulada
        ↓
    JSON
    """

    nome = item["nome"]
    website = item["website"]
    urls = item["urls"]

    print(
        "\n"
        "===================================="
    )

    print(
        f"PROCESSANDO: {nome}"
    )

    print(
        "===================================="
    )

    # --------------------------------------------------------
    # 1. LIMPEZA DO TXT ANTIGO
    # --------------------------------------------------------

    caminho_txt = (
        DATA_DIR /
        f"{nome}.txt"
    )

    # Evita analisar dados antigos caso
    # uma nova coleta falhe.
    if caminho_txt.exists():

        caminho_txt.unlink()

    # --------------------------------------------------------
    # 2. SCRAPING
    # --------------------------------------------------------

    print(
        "\n[ETAPA 1] Coleta do website"
    )

    coletar_site(
        nome_empresa=nome,
        urls=urls
    )

    if not caminho_txt.exists():

        raise RuntimeError(
            "A coleta não gerou dados "
            "para esta empresa."
        )

    if caminho_txt.stat().st_size == 0:

        raise RuntimeError(
            "O arquivo coletado está vazio."
        )

    # --------------------------------------------------------
    # 3. IA + PYDANTIC
    # --------------------------------------------------------

    print(
        "\n[ETAPA 2] "
        "Análise e classificação com IA"
    )

    empresa = analisar_empresa(
        nome_empresa=nome,
        website=website
    )

    # --------------------------------------------------------
    # 4. IMAGENS
    # --------------------------------------------------------

    print(
        "\n[ETAPA 3] "
        "Enriquecimento de imagens"
    )

    empresa = enriquecer_imagens(
        empresa
    )

    # --------------------------------------------------------
    # 5. BANCO PRINCIPAL
    # --------------------------------------------------------

    print(
        "\n[ETAPA 4] "
        "Banco estruturado"
    )

    criar_banco()

    salvar_empresa(
        empresa
    )

    # --------------------------------------------------------
    # 6. LABD E MBO
    # --------------------------------------------------------

    print(
        "\n[ETAPA 5] "
        "Integração LABD / MBO"
    )

    integracao = (
        sincronizar_labd_mbo(
            empresa
        )
    )

    # --------------------------------------------------------
    # 7. JSON
    # --------------------------------------------------------

    print(
        "\n[ETAPA 6] "
        "Persistência do resultado"
    )

    salvar_json(
        nome,
        empresa
    )

    produtos_com_imagem = sum(
        1
        for produto in empresa.produtos
        if produto.imagem_url
    )

    print(
        "\n------------------------------------"
    )

    print(
        f"[SUCESSO] {empresa.nome}"
    )

    print(
        f"Tipo: {empresa.tipo_empresa}"
    )

    print(
        f"Segmentos: "
        f"{len(empresa.segmentos_medicos)}"
    )

    print(
        f"Produtos: "
        f"{len(empresa.produtos)}"
    )

    print(
        f"Produtos com imagem: "
        f"{produtos_com_imagem}"
    )

    print(
        f"Certificações: "
        f"{len(empresa.certificacoes)}"
    )

    print(
        f"LABD: "
        f"{integracao['labd']}"
    )

    print(
        f"MBO: "
        f"{integracao['mbo']}"
    )

    print(
        "------------------------------------"
    )

    return empresa


# ============================================================
# PROCESSAMENTO DAS 5 EMPRESAS
# ============================================================

def processar_todas():
    """
    Executa o pipeline completo nas cinco
    empresas determinadas pela prova.
    """

    print(
        "\n"
        "===================================="
    )

    print(
        "LABD AI DATA AGENT"
    )

    print(
        "PROCESSAMENTO COMPLETO"
    )

    print(
        "===================================="
    )

    sucessos = []
    erros = []

    for indice, item in enumerate(
        EMPRESAS,
        start=1
    ):

        print(
            f"\nEMPRESA "
            f"{indice}/{len(EMPRESAS)}"
        )

        try:

            processar_empresa(
                item
            )

            sucessos.append(
                item["nome"]
            )

        except Exception as erro:

            print(
                f"\n[ERRO] "
                f"{item['nome']}: "
                f"{erro}"
            )

            erros.append(
                {
                    "empresa": item["nome"],
                    "erro": str(erro)
                }
            )

        # Uma empresa com erro não impede
        # o processamento das demais.
        if indice < len(EMPRESAS):

            print(
                "\n[INFO] "
                "Aguardando antes "
                "da próxima empresa..."
            )

            time.sleep(
                3
            )

    print(
        "\n"
        "===================================="
    )

    print(
        "RESUMO FINAL"
    )

    print(
        "===================================="
    )

    print(
        f"Sucessos: {len(sucessos)}"
    )

    for nome in sucessos:

        print(
            f"  [OK] {nome}"
        )

    print(
        f"\nErros: {len(erros)}"
    )

    for item in erros:

        print(
            f"  [ERRO] "
            f"{item['empresa']}: "
            f"{item['erro']}"
        )

    print(
        "\nPipeline finalizado."
    )


# ============================================================
# INTEGRAÇÃO DE RESULTADOS JÁ EXISTENTES
# ============================================================

def integrar_resultados_existentes():
    """
    Permite demonstrar LABD/MBO usando os JSONs
    já processados, sem fazer uma nova chamada
    ao Gemini.

    Útil também quando a API do modelo
    estiver temporariamente indisponível.
    """

    print(
        "\n"
        "===================================="
    )

    print(
        "INTEGRAÇÃO DE RESULTADOS EXISTENTES"
    )

    print(
        "===================================="
    )

    RESULTADOS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    arquivos = sorted(
        RESULTADOS_DIR.glob(
            "*.json"
        )
    )

    if not arquivos:

        print(
            "[AVISO] Nenhum JSON encontrado."
        )

        return

    criar_banco()

    sucessos = 0
    erros = 0

    for arquivo in arquivos:

        print(
            f"\nProcessando "
            f"{arquivo.name}"
        )

        try:

            empresa = (
                Empresa.model_validate_json(
                    arquivo.read_text(
                        encoding="utf-8"
                    )
                )
            )

            # Atualiza o banco principal.
            salvar_empresa(
                empresa
            )

            # Alimenta os bancos simulados.
            sincronizar_labd_mbo(
                empresa
            )

            print(
                f"[OK] "
                f"{empresa.nome}"
            )

            sucessos += 1

        except Exception as erro:

            print(
                f"[ERRO] "
                f"{arquivo.name}: "
                f"{erro}"
            )

            erros += 1

    print(
        "\n"
        "===================================="
    )

    print(
        f"Sucessos: {sucessos}"
    )

    print(
        f"Erros: {erros}"
    )

    print(
        "===================================="
    )


# ============================================================
# PROCESSAMENTO MANUAL DE UM DOMÍNIO
# ============================================================

def processar_dominio_manual(
    nome,
    website
):
    """
    Permite processar qualquer outro
    domínio público informado.
    """

    nome_normalizado = (
        nome
        .lower()
        .strip()
    )

    # Se for uma das empresas da prova,
    # mantém os fallbacks configurados.
    empresa_configurada = next(
        (
            item
            for item in EMPRESAS
            if item["nome"] == nome_normalizado
        ),
        None
    )

    if empresa_configurada:

        item = (
            empresa_configurada.copy()
        )

        item["website"] = website

    else:

        item = {
            "nome": nome_normalizado,
            "website": website,
            "urls": [
                website
            ]
        }

    processar_empresa(
        item
    )


# ============================================================
# AJUDA
# ============================================================

def mostrar_ajuda():

    print(
        """
LABD AI Data Agent

COMANDOS:

1. Processar as 5 empresas da prova:

   python main.py processar


2. Processar apenas uma empresa:

   python main.py empresa NOME WEBSITE

Exemplo:

   python main.py empresa lifespine http://lifespine.com.br


3. Integrar JSONs já existentes
   com LABD e MBO:

   python main.py integrar-existentes


4. Mostrar esta ajuda:

   python main.py ajuda
"""
    )


# ============================================================
# ENTRYPOINT
# ============================================================

def main():

    argumentos = (
        sys.argv[1:]
    )

    if not argumentos:

        mostrar_ajuda()

        return

    comando = (
        argumentos[0]
        .lower()
        .strip()
    )

    if comando == "processar":

        processar_todas()

    elif comando == "empresa":

        if len(argumentos) < 3:

            print(
                "[ERRO] Informe o nome "
                "e o website."
            )

            print(
                "Exemplo:"
            )

            print(
                "python main.py empresa "
                "lifespine "
                "http://lifespine.com.br"
            )

            return

        nome = argumentos[1]
        website = argumentos[2]

        processar_dominio_manual(
            nome,
            website
        )

    elif comando == "integrar-existentes":

        integrar_resultados_existentes()

    elif comando == "ajuda":

        mostrar_ajuda()

    else:

        print(
            f"[ERRO] Comando desconhecido: "
            f"{comando}"
        )

        mostrar_ajuda()


if __name__ == "__main__":
    main()