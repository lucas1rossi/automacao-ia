import os
import re
import time
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


EMPRESAS = [
    {
        "nome": "spmmedicare",
        "urls": [
            "https://spmmedicare.com"
        ]
    },
    {
        "nome": "lifespine",
        "urls": [
            "http://lifespine.com.br",
            "https://lifespine.com.br",
            "https://www.lifespine.com.br"
        ]
    },
    {
        "nome": "kontmed",
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
        "urls": [
            "https://oncoexo.com.br",
            "https://www.oncoexo.com.br"
        ]
    },
    {
        "nome": "verarosas",
        "urls": [
            "https://www.verarosas.com.br",
            "https://verarosas.com.br"
        ]
    },
]


PASTA_SAIDA = "data"

LIMIAR_TEXTO_CURTO = 1500

PALAVRAS_RELEVANTES = [
    "about",
    "sobre",
    "empresa",
    "quem-somos",
    "who-we-are",
    "products",
    "produtos",
    "product",
    "services",
    "servicos",
    "service",
    "contact",
    "contato",
    "certification",
    "certificacoes",
    "quality",
    "qualidade",
]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def baixar_html(url):
    try:
        resposta = requests.get(
            url,
            headers=HEADERS,
            timeout=15,
            allow_redirects=True
        )

        resposta.raise_for_status()

        return resposta.text, resposta.url

    except requests.exceptions.RequestException as erro:
        print(f"  [ERRO] {url}: {erro}")
        return None, None


def baixar_html_com_selenium(url):
    """
    Usa Selenium como plano B quando requests
    encontra pouco conteúdo.
    """

    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = None

    try:
        print(f"  [SELENIUM] Abrindo {url}")

        driver = webdriver.Chrome(options=options)

        driver.set_page_load_timeout(30)

        driver.get(url)

        # Espera JavaScript carregar
        time.sleep(5)

        return driver.page_source

    except Exception as erro:
        print(f"  [ERRO SELENIUM] {erro}")
        return None

    finally:
        if driver:
            driver.quit()


def encontrar_url_funcional(urls):
    """
    Testa as URLs disponíveis até encontrar
    uma que responda corretamente.
    """

    for url in urls:

        print(f"  Tentando: {url}")

        html, url_final = baixar_html(url)

        if html:
            print(f"  [OK] URL funcional: {url_final}")
            return html, url_final

    return None, None


def limpar_texto(html):
    sopa = BeautifulSoup(html, "html.parser")

    for tag in sopa([
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "noscript"
    ]):
        tag.decompose()

    texto = sopa.get_text(separator="\n")

    texto = re.sub(r"[ \t]+", " ", texto)

    texto = re.sub(
        r"\n\s*\n+",
        "\n\n",
        texto
    )

    return texto.strip()


def normalizar_url(url):
    """
    Remove parâmetros e âncoras para evitar
    visitar a mesma página repetidamente.
    """

    parsed = urlparse(url)

    return parsed._replace(
        query="",
        fragment=""
    ).geturl().rstrip("/")


def mesmo_dominio(url_base, url_nova):
    dominio_base = (
        urlparse(url_base)
        .netloc
        .replace("www.", "")
    )

    dominio_novo = (
        urlparse(url_nova)
        .netloc
        .replace("www.", "")
    )

    return dominio_base == dominio_novo


def encontrar_links_relevantes(html, url_base):
    """
    Procura páginas relacionadas a:
    produtos, empresa, contato, serviços,
    certificações etc.
    """

    sopa = BeautifulSoup(html, "html.parser")

    links = set()

    for tag in sopa.find_all("a", href=True):

        href = tag["href"]

        url_completa = urljoin(
            url_base,
            href
        )

        url_completa = normalizar_url(
            url_completa
        )

        if not url_completa.startswith(
            ("http://", "https://")
        ):
            continue

        if not mesmo_dominio(
            url_base,
            url_completa
        ):
            continue

        if normalizar_url(url_completa) == normalizar_url(url_base):
            continue

        texto_link = tag.get_text(
            separator=" ",
            strip=True
        ).lower()

        url_lower = url_completa.lower()

        for palavra in PALAVRAS_RELEVANTES:

            if (
                palavra in texto_link
                or palavra in url_lower
            ):
                links.add(url_completa)
                break

    return list(links)


def salvar_texto(nome_empresa, texto):

    os.makedirs(
        PASTA_SAIDA,
        exist_ok=True
    )

    caminho = os.path.join(
        PASTA_SAIDA,
        f"{nome_empresa}.txt"
    )

    with open(
        caminho,
        "w",
        encoding="utf-8"
    ) as arquivo:

        arquivo.write(texto)

    print(
        f"  [OK] Salvo em {caminho} "
        f"({len(texto)} caracteres)"
    )


def coletar_site(nome_empresa, urls):

    print(f"\nProcessando {nome_empresa}")

    html_home, url_base = encontrar_url_funcional(
        urls
    )

    if html_home is None:

        print(
            f"  [FALHA] Nenhuma URL funcionou "
            f"para {nome_empresa}"
        )

        return

    textos = []

    texto_home = limpar_texto(
        html_home
    )

    textos.append(
        f"""
=============================
PÁGINA: {url_base}
=============================

{texto_home}
"""
    )

    links = encontrar_links_relevantes(
        html_home,
        url_base
    )

    print(
        f"  Links relevantes encontrados: "
        f"{len(links)}"
    )

    # Limita quantidade de páginas
    links = links[:12]

    for link in links:

        print(f"  Visitando: {link}")

        html, url_final = baixar_html(
            link
        )

        if html is None:
            continue

        texto = limpar_texto(
            html
        )

        if len(texto) < 50:
            continue

        textos.append(
            f"""
=============================
PÁGINA: {url_final}
=============================

{texto}
"""
        )

    texto_completo = "\n".join(
        textos
    )

    # Fallback com Selenium
    if len(texto_completo) < LIMIAR_TEXTO_CURTO:

        print(
            f"  [AVISO] Texto total curto "
            f"({len(texto_completo)} caracteres). "
            f"Tentando Selenium..."
        )

        html_selenium = baixar_html_com_selenium(
            url_base
        )

        if html_selenium:

            texto_selenium = limpar_texto(
                html_selenium
            )

            print(
                f"  Selenium encontrou "
                f"{len(texto_selenium)} caracteres"
            )

            # Só adiciona se Selenium trouxe
            # mais conteúdo que a homepage normal
            if len(texto_selenium) > len(texto_home):

                textos.append(
                    f"""
=============================
PÁGINA VIA SELENIUM: {url_base}
=============================

{texto_selenium}
"""
                )

                texto_completo = "\n".join(
                    textos
                )

                print(
                    f"  [OK] Conteúdo via Selenium "
                    f"adicionado. Total: "
                    f"{len(texto_completo)} caracteres"
                )

            else:

                print(
                    "  [AVISO] Selenium não encontrou "
                    "conteúdo adicional relevante."
                )

    salvar_texto(
        nome_empresa,
        texto_completo
    )


def main():

    print(
        "Iniciando coleta avançada...\n"
    )

    for empresa in EMPRESAS:

        coletar_site(
            empresa["nome"],
            empresa["urls"]
        )

    print(
        "\nColeta finalizada."
    )


if __name__ == "__main__":
    main()