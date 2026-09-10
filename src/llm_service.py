import os
import json
import time
import unicodedata
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError

from src.models import Empresa
from src.taxonomia import aplicar_taxonomia


load_dotenv()

PASTA_DADOS = Path("data")


# ============================================================
# LEITURA DOS DADOS COLETADOS
# ============================================================

def ler_texto_empresa(
    nome_empresa: str
) -> str:
    """
    Lê o arquivo de texto bruto
    gerado pelo scraper.
    """

    caminho = (
        PASTA_DADOS
        / f"{nome_empresa}.txt"
    )

    if not caminho.exists():

        raise FileNotFoundError(
            f"Arquivo não encontrado: "
            f"{caminho}"
        )

    texto = caminho.read_text(
        encoding="utf-8"
    )

    if not texto.strip():

        raise ValueError(
            f"O arquivo {caminho} "
            f"está vazio."
        )

    return texto


# ============================================================
# PROMPT
# ============================================================

def montar_prompt(
    texto_site: str,
    website: str
) -> str:
    """
    Monta o prompt utilizado
    para extração estruturada.
    """

    return f"""
Você é um agente especializado em extração e estruturação
de dados públicos de empresas do setor médico-hospitalar.

Analise SOMENTE o conteúdo fornecido abaixo.

REGRAS IMPORTANTES:

- Não invente informações.
- Não utilize conhecimento externo.
- Utilize somente informações presentes no conteúdo coletado.
- Quando não encontrar um campo individual, use null.
- Quando não encontrar itens de uma lista, use [].
- Não presuma certificações.
- Não presuma especialidades médicas sem evidência.
- Não transforme marcas citadas em produtos automaticamente.
- Extraia apenas produtos claramente mencionados.
- Preserve URLs quando disponíveis.
- Não invente endereço, telefone ou e-mail.
- Não invente certificações.
- Não invente produtos.
- Não invente URLs de imagens.

CLASSIFICAÇÃO DA EMPRESA:

Classifique exclusivamente em uma destas categorias:

- Fabricante
- Distribuidor
- Prestador de Serviços
- Não identificado

SEGMENTAÇÃO MÉDICA:

Identifique especialidades ou segmentos médicos relacionados
aos produtos ou serviços da empresa.

Exemplos:

- Cardiologia
- Neurocirurgia
- Ortopedia
- Oncologia
- Radiologia
- Dermatologia
- Fisioterapia
- Medicina Esportiva
- Odontologia
- Urologia
- Anestesiologia

Caso não exista evidência suficiente, retorne [].

DADOS DA EMPRESA:

Extraia:

- nome
- descrição institucional
- website
- email
- telefone
- endereço
- tipo da empresa
- segmentos médicos
- certificações
- produtos
- fontes utilizadas

DADOS DOS PRODUTOS:

Para cada produto:

- nome
- descrição
- categoria
- imagem_url
- segmentos_medicos
- fonte_url

WEBSITE PRINCIPAL:

{website}

Retorne SOMENTE JSON válido com esta estrutura:

{{
    "nome": "string",
    "descricao": null,
    "website": "{website}",
    "email": null,
    "telefone": null,
    "endereco": null,
    "tipo_empresa": "Não identificado",
    "segmentos_medicos": [],
    "certificacoes": [],
    "produtos": [
        {{
            "nome": "string",
            "descricao": null,
            "categoria": null,
            "imagem_url": null,
            "segmentos_medicos": [],
            "fonte_url": null
        }}
    ],
    "fontes": [],
    "observacoes": null
}}

CONTEÚDO DO WEBSITE:

----------------------------------------

{texto_site}

----------------------------------------
"""


# ============================================================
# NORMALIZAÇÃO DE TEXTO
# ============================================================

def normalizar_texto(
    texto
) -> str:
    """
    Normaliza texto para comparações simples.
    """

    if texto is None:
        return ""

    texto = str(
        texto
    ).strip().lower()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(
            caractere
        )
    )

    return texto


# ============================================================
# NORMALIZAÇÃO DO TIPO DE EMPRESA
# ============================================================

def normalizar_tipo_empresa(
    dados: dict
) -> dict:
    """
    Garante que tipo_empresa sempre
    pertença ao enum aceito pelo Pydantic.

    Isso evita que pequenas variações
    da resposta do LLM interrompam
    todo o processamento.
    """

    valor = dados.get(
        "tipo_empresa"
    )

    texto = normalizar_texto(
        valor
    )

    mapa = {
        "fabricante":
            "Fabricante",

        "manufacturer":
            "Fabricante",

        "manufacturing":
            "Fabricante",

        "distribuidor":
            "Distribuidor",

        "distribuidora":
            "Distribuidor",

        "distributor":
            "Distribuidor",

        "prestador de servicos":
            "Prestador de Serviços",

        "prestadora de servicos":
            "Prestador de Serviços",

        "prestador de serviço":
            "Prestador de Serviços",

        "service provider":
            "Prestador de Serviços",

        "services provider":
            "Prestador de Serviços",

        "nao identificado":
            "Não identificado",

        "not identified":
            "Não identificado",

        "unknown":
            "Não identificado",

        "":
            "Não identificado",
    }

    tipo_normalizado = mapa.get(
        texto,
        "Não identificado"
    )

    dados["tipo_empresa"] = (
        tipo_normalizado
    )

    return dados


# ============================================================
# GEMINI
# ============================================================

def analisar_com_gemini(
    texto_site: str,
    website: str
) -> dict:
    """
    Envia o conteúdo coletado para o Gemini.

    Possui retry automático para
    indisponibilidade temporária,
    como HTTP 503.
    """

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    modelo = os.getenv(
        "GEMINI_MODEL"
    )

    if not api_key:

        raise ValueError(
            "GEMINI_API_KEY não encontrada "
            "no arquivo .env"
        )

    if not modelo:

        raise ValueError(
            "GEMINI_MODEL não encontrado "
            "no arquivo .env"
        )

    client = genai.Client(
        api_key=api_key
    )

    prompt = montar_prompt(
        texto_site,
        website
    )

    print(
        f"[IA] Enviando "
        f"{len(texto_site)} caracteres "
        f"para o Gemini..."
    )

    resposta = None

    # ========================================================
    # RETRY
    # ========================================================

    for tentativa in range(
        1,
        4
    ):

        try:

            print(
                f"[IA] Tentativa "
                f"{tentativa}/3..."
            )

            resposta = (
                client.models.generate_content(
                    model=modelo,
                    contents=prompt,
                    config=(
                        types.GenerateContentConfig(
                            response_mime_type=(
                                "application/json"
                            )
                        )
                    )
                )
            )

            # Funcionou.
            break

        except ServerError as erro:

            codigo = getattr(
                erro,
                "code",
                None
            )

            if codigo == 503:

                if tentativa == 3:

                    print(
                        "[ERRO] Gemini continuou "
                        "indisponível após "
                        "3 tentativas."
                    )

                    raise

                espera = (
                    tentativa * 5
                )

                print(
                    "[IA] Gemini temporariamente "
                    "indisponível. "
                    f"Nova tentativa em "
                    f"{espera} segundos..."
                )

                time.sleep(
                    espera
                )

            else:

                # Outros erros devem ser
                # propagados para o tratamento
                # superior.
                raise

    if resposta is None:

        raise ValueError(
            "Não foi possível obter "
            "resposta do Gemini."
        )

    if not resposta.text:

        raise ValueError(
            "Gemini retornou "
            "uma resposta vazia."
        )

    # ========================================================
    # JSON
    # ========================================================

    try:

        dados = json.loads(
            resposta.text
        )

    except json.JSONDecodeError as erro:

        print(
            "\n[ERRO] Resposta recebida "
            "do Gemini:\n"
        )

        print(
            resposta.text
        )

        raise ValueError(
            "Gemini não retornou "
            "JSON válido."
        ) from erro

    if not isinstance(
        dados,
        dict
    ):

        raise ValueError(
            "Gemini não retornou "
            "um objeto JSON válido."
        )

    return dados


# ============================================================
# VALIDAÇÃO
# ============================================================

def validar_resultado(
    dados: dict
) -> Empresa:
    """
    Fluxo:

    JSON da IA
        ↓
    normalização do tipo
        ↓
    Pydantic
        ↓
    taxonomia médica
    """

    # --------------------------------------------------------
    # 1. TIPO DA EMPRESA
    # --------------------------------------------------------

    dados = (
        normalizar_tipo_empresa(
            dados
        )
    )

    # --------------------------------------------------------
    # 2. PYDANTIC
    # --------------------------------------------------------

    empresa = (
        Empresa.model_validate(
            dados
        )
    )

    # --------------------------------------------------------
    # 3. TAXONOMIA MÉDICA
    # --------------------------------------------------------

    empresa = aplicar_taxonomia(
        empresa
    )

    return empresa


# ============================================================
# PIPELINE DA CAMADA DE IA
# ============================================================

def analisar_empresa(
    nome_empresa: str,
    website: str
) -> Empresa:
    """
    Pipeline da camada de inteligência:

    TXT coletado
        ↓
    Gemini
        ↓
    JSON
        ↓
    normalização
        ↓
    Pydantic
        ↓
    taxonomia médica
        ↓
    Empresa validada
    """

    texto = ler_texto_empresa(
        nome_empresa
    )

    dados = analisar_com_gemini(
        texto,
        website
    )

    empresa = validar_resultado(
        dados
    )

    print(
        "[IA] Dados estruturados "
        "e validados com sucesso."
    )

    print(
        "[TAXONOMIA] Segmentos médicos "
        "normalizados."
    )

    return empresa