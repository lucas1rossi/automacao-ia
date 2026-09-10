import re
import unicodedata


# ============================================================
# TAXONOMIA CANÔNICA
# ============================================================

SEGMENTOS_CANONICOS = {
    "Neurocirurgia",
    "Ortopedia",
    "Cirurgia Bucomaxilofacial",
    "Cirurgia Torácica",
    "Cirurgia Vascular",
    "Cirurgia Geral",
    "Cardiologia",
    "Oncologia",
    "Radiologia",
    "Dermatologia",
    "Fisioterapia",
    "Medicina Esportiva",
    "Urologia",
    "Ginecologia",
    "Endocrinologia",
    "Anestesiologia",
    "Hematologia",
    "Odontologia",
    "Terapia Infusional",
    "Controle de Infecção",
    "Tratamento de Feridas",
    "Nutrição Clínica",
}


# ============================================================
# SINÔNIMOS / TERMOS DA IA
# ============================================================

MAPA_SEGMENTOS = {
    # Neurocirurgia
    "neurosurgery": "Neurocirurgia",
    "neurosurgical": "Neurocirurgia",
    "neurocirurgia": "Neurocirurgia",
    "cranial": "Neurocirurgia",
    "cranio": "Neurocirurgia",
    "crânio": "Neurocirurgia",

    # Ortopedia
    "orthopedics": "Ortopedia",
    "orthopedic": "Ortopedia",
    "orthopaedic": "Ortopedia",
    "orthopaedics": "Ortopedia",
    "ortopedia": "Ortopedia",
    "coluna": "Ortopedia",

    # Bucomaxilofacial
    "maxillofacial": "Cirurgia Bucomaxilofacial",
    "maxillofacial surgery": "Cirurgia Bucomaxilofacial",
    "bucomaxilofacial": "Cirurgia Bucomaxilofacial",
    "cirurgia bucomaxilofacial": "Cirurgia Bucomaxilofacial",

    # Torácica
    "thoracic": "Cirurgia Torácica",
    "thoracic surgery": "Cirurgia Torácica",
    "toracica": "Cirurgia Torácica",
    "cirurgia toracica": "Cirurgia Torácica",

    # Cardiologia
    "cardiology": "Cardiologia",
    "cardiologia": "Cardiologia",
    "cardiovascular": "Cardiologia",
    "cardiac": "Cardiologia",

    # Oncologia
    "oncology": "Oncologia",
    "oncologia": "Oncologia",
    "oncological": "Oncologia",

    # Radiologia
    "radiology": "Radiologia",
    "radiologia": "Radiologia",
    "medical imaging": "Radiologia",

    # Dermatologia
    "dermatology": "Dermatologia",
    "dermatologia": "Dermatologia",

    # Fisioterapia
    "physiotherapy": "Fisioterapia",
    "physical therapy": "Fisioterapia",
    "fisioterapia": "Fisioterapia",

    # Medicina esportiva
    "sports medicine": "Medicina Esportiva",
    "medicina esportiva": "Medicina Esportiva",

    # Cirurgia vascular
    "vascular surgery": "Cirurgia Vascular",
    "cirurgia vascular": "Cirurgia Vascular",

    # Cirurgia geral
    "general surgery": "Cirurgia Geral",
    "cirurgia geral": "Cirurgia Geral",

    # Urologia
    "urology": "Urologia",
    "urologia": "Urologia",

    # Ginecologia
    "gynecology": "Ginecologia",
    "gynaecology": "Ginecologia",
    "ginecologia": "Ginecologia",

    # Endocrinologia
    "endocrinology": "Endocrinologia",
    "endocrinologia": "Endocrinologia",
    "diabetes": "Endocrinologia",

    # Anestesiologia
    "anesthesiology": "Anestesiologia",
    "anaesthesiology": "Anestesiologia",
    "anestesiologia": "Anestesiologia",

    # Hematologia
    "hematology": "Hematologia",
    "haematology": "Hematologia",
    "hematologia": "Hematologia",

    # Odontologia
    "dental": "Odontologia",
    "dentistry": "Odontologia",
    "odontologia": "Odontologia",

    # Terapia infusional
    "infusion therapy": "Terapia Infusional",
    "iv therapy": "Terapia Infusional",
    "terapia infusional": "Terapia Infusional",

    # Controle de infecção
    "infection control": "Controle de Infecção",
    "infection prevention": "Controle de Infecção",
    "controle de infeccao": "Controle de Infecção",

    # Feridas
    "wound care": "Tratamento de Feridas",
    "tratamento de feridas": "Tratamento de Feridas",

    # Nutrição
    "clinical nutrition": "Nutrição Clínica",
    "nutricao clinica": "Nutrição Clínica",
}


# ============================================================
# NORMALIZAÇÃO DE TEXTO
# ============================================================

def limpar_texto(texto):
    """
    Normaliza texto para comparação:
    - minúsculas
    - remoção de acentos
    - espaços normalizados
    """

    if texto is None:
        return ""

    texto = str(texto).lower().strip()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto


def contem_termo(texto, termo):
    """
    Procura um termo completo no texto.

    Evita falsos positivos como:

    fusion dentro de infusion
    """

    texto = limpar_texto(texto)
    termo = limpar_texto(termo)

    if not texto or not termo:
        return False

    padrao = (
        r"(?<![a-z0-9])"
        + re.escape(termo)
        + r"(?![a-z0-9])"
    )

    return bool(
        re.search(
            padrao,
            texto
        )
    )


def contem_algum(texto, termos):
    """
    Verifica se pelo menos um termo
    aparece corretamente no texto.
    """

    return any(
        contem_termo(
            texto,
            termo
        )
        for termo in termos
    )


def remover_duplicados(lista):
    """
    Remove duplicados mantendo
    a ordem original.
    """

    resultado = []
    vistos = set()

    for item in lista:

        if not item:
            continue

        chave = limpar_texto(
            item
        )

        if chave in vistos:
            continue

        vistos.add(
            chave
        )

        resultado.append(
            item
        )

    return resultado


# ============================================================
# NORMALIZAÇÃO DE SEGMENTOS DA IA
# ============================================================

def normalizar_segmento(segmento):
    """
    Converte a resposta livre da IA para
    uma taxonomia controlada.

    Termos não reconhecidos não entram
    automaticamente no banco.
    """

    if not segmento:
        return None

    texto = limpar_texto(
        segmento
    )

    # Verifica se já é um valor canônico.
    for canonico in SEGMENTOS_CANONICOS:

        if texto == limpar_texto(
            canonico
        ):
            return canonico

    # Procura correspondência exata
    # nos sinônimos.
    for termo, canonico in MAPA_SEGMENTOS.items():

        if texto == limpar_texto(
            termo
        ):
            return canonico

    # Depois aceita termos compostos
    # conhecidos.
    for termo, canonico in MAPA_SEGMENTOS.items():

        if contem_termo(
            texto,
            termo
        ):
            return canonico

    # Taxonomia fechada:
    # termo desconhecido não entra.
    return None


def normalizar_lista_segmentos(segmentos):
    """
    Normaliza todos os segmentos
    retornados pela IA.
    """

    resultado = []

    for segmento in segmentos or []:

        normalizado = (
            normalizar_segmento(
                segmento
            )
        )

        if normalizado:

            resultado.append(
                normalizado
            )

    return remover_duplicados(
        resultado
    )


# ============================================================
# INFERÊNCIA CONTROLADA POR PRODUTO
# ============================================================

def inferir_segmentos_produto(produto):
    """
    Faz inferência determinística usando
    apenas informações já coletadas
    do website.

    Nenhuma fonte externa é consultada.
    """

    partes = [
        getattr(
            produto,
            "nome",
            None
        ),
        getattr(
            produto,
            "descricao",
            None
        ),
        getattr(
            produto,
            "categoria",
            None
        ),
    ]

    texto = limpar_texto(
        " ".join(
            str(parte)
            for parte in partes
            if parte
        )
    )

    encontrados = []

    # --------------------------------------------------------
    # ANESTESIOLOGIA
    # Deve vir antes das regras de coluna para
    # não interpretar "spinal needle" como implante.
    # --------------------------------------------------------

    if contem_algum(
        texto,
        [
            "spinal needle",
            "epidural needle",
            "epidural",
        ]
    ):

        encontrados.append(
            "Anestesiologia"
        )

    # --------------------------------------------------------
    # COLUNA / ORTOPEDIA / NEUROCIRURGIA
    # --------------------------------------------------------

    sinais_coluna = [
        "spine implant",
        "spinal implant",
        "spinal fixation",
        "spinal fusion",
        "interbody",
        "cervical",
        "lumbar",
        "vertebral",
        "vertebra",
        "llif",
        "coluna",
    ]

    if contem_algum(
        texto,
        sinais_coluna
    ):

        encontrados.extend(
            [
                "Ortopedia",
                "Neurocirurgia",
            ]
        )

    # --------------------------------------------------------
    # NEUROCIRURGIA / CRÂNIO
    # --------------------------------------------------------

    if contem_algum(
        texto,
        [
            "cranial",
            "cranio",
            "neurosurgical",
            "neurosurgery",
        ]
    ):

        encontrados.append(
            "Neurocirurgia"
        )

    # --------------------------------------------------------
    # BUCOMAXILOFACIAL
    # --------------------------------------------------------

    if contem_algum(
        texto,
        [
            "maxillofacial",
            "maxillofacial surgery",
            "bucomaxilofacial",
        ]
    ):

        encontrados.append(
            "Cirurgia Bucomaxilofacial"
        )

    # --------------------------------------------------------
    # ODONTOLOGIA
    # --------------------------------------------------------

    if contem_algum(
        texto,
        [
            "dental",
            "dentistry",
            "odontologia",
        ]
    ):

        encontrados.append(
            "Odontologia"
        )

    # --------------------------------------------------------
    # TORÁCICA
    # --------------------------------------------------------

    if contem_algum(
        texto,
        [
            "thoracic",
            "thoracic surgery",
            "toracica",
        ]
    ):

        encontrados.append(
            "Cirurgia Torácica"
        )

    # --------------------------------------------------------
    # CARDIOLOGIA
    # --------------------------------------------------------

    if contem_algum(
        texto,
        [
            "cardiology",
            "cardiac",
            "cardiovascular",
            "coronary",
        ]
    ):

        encontrados.append(
            "Cardiologia"
        )

    # --------------------------------------------------------
    # ONCOLOGIA
    # --------------------------------------------------------

    if contem_algum(
        texto,
        [
            "oncology",
            "oncological",
            "oncologia",
            "oncologico",
        ]
    ):

        encontrados.append(
            "Oncologia"
        )

    # --------------------------------------------------------
    # ENDOCRINOLOGIA
    # --------------------------------------------------------

    if contem_algum(
        texto,
        [
            "insulin",
            "insulina",
            "diabetes",
            "insulin syringe",
        ]
    ):

        encontrados.append(
            "Endocrinologia"
        )

    # --------------------------------------------------------
    # TERAPIA INFUSIONAL
    # --------------------------------------------------------

    if contem_algum(
        texto,
        [
            "infusion therapy",
            "infusion set",
            "infusion",
            "intravenous",
            "iv cannula",
            "i.v. cannula",
            "line access",
            "line conditioning",
            "line protection",
            "flush syringe",
            "needle free valve",
            "pressure monitoring line",
        ]
    ):

        encontrados.append(
            "Terapia Infusional"
        )

    # --------------------------------------------------------
    # CONTROLE DE INFECÇÃO
    # --------------------------------------------------------

    if contem_algum(
        texto,
        [
            "chlorhexidine",
            "clorexidina",
            "chg",
            "disinfectant",
            "disinfection",
            "infection control",
            "infection prevention",
            "antiseptic",
            "antisseptico",
        ]
    ):

        encontrados.append(
            "Controle de Infecção"
        )

    # --------------------------------------------------------
    # NUTRIÇÃO CLÍNICA
    # --------------------------------------------------------

    if contem_algum(
        texto,
        [
            "enfit",
            "enteral",
            "enteral feeding",
            "enteral nutrition",
        ]
    ):

        encontrados.append(
            "Nutrição Clínica"
        )

    # --------------------------------------------------------
    # TRATAMENTO DE FERIDAS
    # --------------------------------------------------------

    if contem_algum(
        texto,
        [
            "wound care",
            "wound",
            "dressing",
            "tratamento de feridas",
            "curativo",
        ]
    ):

        encontrados.append(
            "Tratamento de Feridas"
        )

    # --------------------------------------------------------
    # UROLOGIA
    # --------------------------------------------------------

    if contem_algum(
        texto,
        [
            "urology",
            "urological",
            "circumcision",
        ]
    ):

        encontrados.append(
            "Urologia"
        )

    # --------------------------------------------------------
    # CIRURGIA GERAL
    # --------------------------------------------------------

    if contem_algum(
        texto,
        [
            "surgical instrument",
            "surgical instruments",
            "trocar",
            "ligating clip",
            "ligating clips",
        ]
    ):

        encontrados.append(
            "Cirurgia Geral"
        )

    # --------------------------------------------------------
    # RADIOLOGIA
    # --------------------------------------------------------

    if contem_algum(
        texto,
        [
            "radiology",
            "radiologia",
            "diagnostic imaging",
            "medical imaging",
        ]
    ):

        encontrados.append(
            "Radiologia"
        )

    return remover_duplicados(
        encontrados
    )


# ============================================================
# APLICAÇÃO COMPLETA
# ============================================================

def aplicar_taxonomia(empresa):
    """
    Padroniza os segmentos da empresa
    e dos produtos.

    Ordem:

    1. Normaliza segmentos encontrados pela IA;
    2. Normaliza segmentos de cada produto;
    3. Caso um produto não possua segmento,
       aplica inferência determinística;
    4. Consolida os segmentos dos produtos
       na empresa.
    """

    empresa.segmentos_medicos = (
        normalizar_lista_segmentos(
            empresa.segmentos_medicos
        )
    )

    segmentos_empresa = list(
        empresa.segmentos_medicos
    )

    for produto in empresa.produtos:

        segmentos_produto = (
            normalizar_lista_segmentos(
                produto.segmentos_medicos
            )
        )

        if not segmentos_produto:

            segmentos_produto = (
                inferir_segmentos_produto(
                    produto
                )
            )

        produto.segmentos_medicos = (
            segmentos_produto
        )

        segmentos_empresa.extend(
            segmentos_produto
        )

    empresa.segmentos_medicos = (
        remover_duplicados(
            segmentos_empresa
        )
    )

    return empresa