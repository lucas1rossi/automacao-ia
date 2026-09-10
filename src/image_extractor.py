import re
import unicodedata
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


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
        print(
            f"    [ERRO IMAGEM] Não consegui acessar "
            f"{url}: {erro}"
        )

        return None, None


def normalizar_texto(texto):
    """
    Remove acentos e caracteres especiais para
    facilitar comparação entre produto, URL e links.
    """

    if not texto:
        return ""

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = texto.lower()

    texto = re.sub(
        r"[^a-z0-9]+",
        " ",
        texto
    )

    return " ".join(
        texto.split()
    )


def tokens_produto(nome):
    """
    Obtém palavras relevantes do nome do produto.
    """

    ignorar = {
        "de",
        "da",
        "do",
        "das",
        "dos",
        "para",
        "com",
        "the",
        "and",
        "of",
        "system"
    }

    return [
        token
        for token in normalizar_texto(nome).split()
        if len(token) >= 3 and token not in ignorar
    ]


def mesmo_dominio(url1, url2):
    dominio1 = (
        urlparse(url1)
        .netloc
        .lower()
        .replace("www.", "")
    )

    dominio2 = (
        urlparse(url2)
        .netloc
        .lower()
        .replace("www.", "")
    )

    return dominio1 == dominio2


def pontuar_link(
    url,
    texto_link,
    nome_produto
):
    """
    Mede o quanto um link parece apontar
    para determinado produto.
    """

    tokens = tokens_produto(
        nome_produto
    )

    alvo = normalizar_texto(
        f"{url} {texto_link}"
    )

    pontos = 0

    for token in tokens:
        if token in alvo:
            pontos += 3

    url_lower = url.lower()

    if "/product/" in url_lower:
        pontos += 3

    if "/produto/" in url_lower:
        pontos += 3

    if "/products/" in url_lower:
        pontos += 1

    if "/produtos/" in url_lower:
        pontos += 1

    return pontos


def localizar_pagina_produto(
    nome_produto,
    fonte_url,
    website
):
    """
    Tenta descobrir a página mais específica
    do produto.

    Primeiro usa fonte_url.
    Depois procura links relacionados ao produto.
    """

    urls_para_buscar = []

    if fonte_url:
        urls_para_buscar.append(
            fonte_url
        )

    if website not in urls_para_buscar:
        urls_para_buscar.append(
            website
        )

    melhor_url = fonte_url or website
    melhor_pontuacao = 0

    for pagina in urls_para_buscar:

        html, url_final = baixar_html(
            pagina
        )

        if html is None:
            continue

        # Se a própria URL já parece muito relacionada
        # ao produto, podemos utilizá-la diretamente.
        pontuacao_pagina = pontuar_link(
            url_final,
            "",
            nome_produto
        )

        if pontuacao_pagina > melhor_pontuacao:
            melhor_pontuacao = pontuacao_pagina
            melhor_url = url_final

        sopa = BeautifulSoup(
            html,
            "html.parser"
        )

        for tag in sopa.find_all(
            "a",
            href=True
        ):

            href = tag.get(
                "href"
            )

            url_completa = urljoin(
                url_final,
                href
            )

            if not mesmo_dominio(
                website,
                url_completa
            ):
                continue

            texto_link = tag.get_text(
                separator=" ",
                strip=True
            )

            pontos = pontuar_link(
                url_completa,
                texto_link,
                nome_produto
            )

            if pontos > melhor_pontuacao:

                melhor_pontuacao = pontos
                melhor_url = url_completa

    return melhor_url


def obter_url_img(tag, url_base):
    """
    Obtém URL de imagem considerando
    carregamento normal e lazy loading.
    """

    atributos = [
        "src",
        "data-src",
        "data-lazy-src",
        "data-original"
    ]

    for atributo in atributos:

        valor = tag.get(
            atributo
        )

        if valor and not valor.startswith(
            "data:"
        ):
            return urljoin(
                url_base,
                valor
            )

    srcset = tag.get(
        "srcset"
    )

    if srcset:

        itens = srcset.split(",")

        if itens:

            ultimo = itens[-1].strip()

            valor = ultimo.split()[0]

            return urljoin(
                url_base,
                valor
            )

    return None


def imagem_valida(url):
    if not url:
        return False

    url_lower = url.lower()

    ignorar = [
        "logo",
        "favicon",
        "icon",
        "avatar",
        "placeholder",
        "loading.gif"
    ]

    for termo in ignorar:
        if termo in url_lower:
            return False

    if url_lower.endswith(
        ".svg"
    ):
        return False

    return True


def extrair_imagem_da_pagina(
    url,
    nome_produto
):
    """
    Tenta localizar a imagem principal
    relacionada ao produto.
    """

    html, url_final = baixar_html(
        url
    )

    if html is None:
        return None

    sopa = BeautifulSoup(
        html,
        "html.parser"
    )

    candidatos = []

    # 1. Imagem OpenGraph.
    # Em páginas de produto costuma apontar
    # para a imagem principal.
    og_image = sopa.find(
        "meta",
        attrs={
            "property": "og:image"
        }
    )

    if og_image:

        conteudo = og_image.get(
            "content"
        )

        if conteudo:

            url_imagem = urljoin(
                url_final,
                conteudo
            )

            if imagem_valida(
                url_imagem
            ):
                candidatos.append(
                    (
                        5,
                        url_imagem
                    )
                )

    tokens = tokens_produto(
        nome_produto
    )

    # 2. Analisa imagens presentes na página.
    for imagem in sopa.find_all(
        "img"
    ):

        url_imagem = obter_url_img(
            imagem,
            url_final
        )

        if not imagem_valida(
            url_imagem
        ):
            continue

        alt = imagem.get(
            "alt",
            ""
        )

        title = imagem.get(
            "title",
            ""
        )

        classes = " ".join(
            imagem.get(
                "class",
                []
            )
        )

        contexto = normalizar_texto(
            f"{alt} {title} {classes} {url_imagem}"
        )

        pontos = 0

        for token in tokens:
            if token in contexto:
                pontos += 4

        contexto_lower = contexto.lower()

        if "product" in contexto_lower:
            pontos += 2

        if "produto" in contexto_lower:
            pontos += 2

        if "gallery" in contexto_lower:
            pontos += 2

        if "woocommerce" in contexto_lower:
            pontos += 2

        candidatos.append(
            (
                pontos,
                url_imagem
            )
        )

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return candidatos[0][1]


def buscar_imagem_produto(
    nome_produto,
    fonte_url,
    website
):
    """
    Pipeline:

    produto
      ↓
    localizar página
      ↓
    extrair imagem
    """

    pagina = localizar_pagina_produto(
        nome_produto=nome_produto,
        fonte_url=fonte_url,
        website=website
    )

    if not pagina:
        return None, None

    imagem = extrair_imagem_da_pagina(
        pagina,
        nome_produto
    )

    return imagem, pagina