# AI Data Agent | Automação, IA e Engenharia de Dados

Projeto desenvolvido para aplicar conhecimentos de automação, inteligência artificial, APIs e engenharia de dados.

A aplicação recebe o site público de uma empresa, coleta informações relevantes, utiliza inteligência artificial para interpretar o conteúdo e salva os resultados de forma estruturada. O fluxo também pode ser acessado por API e automatizado com n8n.

## Destaques do projeto

- Coleta de conteúdo com Requests e BeautifulSoup;
- Uso do Selenium como alternativa para páginas dinâmicas;
- Análise e estruturação de dados com Gemini;
- Validação dos resultados com Pydantic;
- Padronização de segmentos médicos;
- Persistência em banco SQLite;
- API REST desenvolvida com FastAPI;
- Automação do fluxo com n8n;
- Tratamento de erros e novas tentativas.

## Tecnologias

`Python` · `FastAPI` · `Gemini API` · `n8n` · `SQLite` · `Pydantic` · `Requests` · `BeautifulSoup` · `Selenium` · `JSON`

## Como funciona

```text
Website público
      |
      v
Coleta de conteúdo
      |
      v
Análise com IA
      |
      v
Normalização e validação
      |
      v
Extração de produtos e imagens
      |
      v
Banco SQLite e arquivos JSON
      |
      v
API e automação com n8n
```

O sistema executa as seguintes etapas:

1. Recebe o nome e o domínio público da empresa;
2. Acessa o website e coleta o conteúdo disponível;
3. Utiliza Selenium quando a página depende de JavaScript;
4. Envia o texto coletado para o modelo de linguagem;
5. Organiza as informações em uma estrutura padronizada;
6. Valida os dados com Pydantic;
7. Normaliza os segmentos médicos identificados;
8. Procura imagens públicas relacionadas aos produtos;
9. Salva os resultados em SQLite e JSON;
10. Disponibiliza o processamento por FastAPI e n8n.

## Informações coletadas

### Empresa

- Nome;
- Descrição;
- Website;
- E-mail;
- Telefone;
- Endereço;
- Classificação da empresa.

As empresas podem ser classificadas como:

- Fabricante;
- Distribuidor;
- Prestador de Serviços;
- Não identificado.

### Produtos

- Nome;
- Descrição;
- Categoria;
- Segmento médico;
- URL da imagem;
- Página utilizada como fonte.

### Segmentos médicos

A saída da IA passa por uma taxonomia controlada para padronizar termos e pequenas variações.

Exemplos:

```text
Neurosurgical -> Neurocirurgia
Cranial -> Neurocirurgia
Maxillofacial -> Cirurgia Bucomaxilofacial
Thoracic -> Cirurgia Torácica
Dental -> Odontologia
```

### Certificações

O sistema procura menções públicas a certificações e regulamentações, como:

- ISO 13485;
- CE;
- FDA;
- ANVISA;
- MDSAP;
- GMP/BGMP.

Quando uma informação não é encontrada de forma confiável, o campo permanece vazio ou nulo. O sistema evita completar dados sem evidências no conteúdo coletado.

## Estrutura do projeto

```text
ai-data-agent/
|
├── data/
|   ├── resultados/
|   └── bancos SQLite
|
├── n8n/
|   └── workflow de automação
|
├── src/
|   ├── api.py
|   ├── database.py
|   ├── enriquecer_imagens.py
|   ├── image_extractor.py
|   ├── integracao.py
|   ├── llm_service.py
|   ├── models.py
|   ├── processar_empresas.py
|   ├── scraper.py
|   └── taxonomia.py
|
├── .env.example
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
```

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/lucas1rossi/automacao-ia.git
cd automacao-iaD
```

### 2. Criar e ativar o ambiente virtual

Windows:

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

Linux ou macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as dependências

```cmd
pip install -r requirements.txt
```

### 4. Configurar as variáveis de ambiente

Crie um arquivo `.env` com base no `.env.example`:

```env
GEMINI_API_KEY=SUA_CHAVE
LLM_PROVIDER=gemini
GEMINI_MODEL=SEU_MODELO
```

A chave é necessária apenas para novas coletas e análises com IA. Nunca publique sua chave real no GitHub.

## Execução

### Testar os resultados existentes sem chave de API

```cmd
python main.py integrar-existentes
```

Esse comando utiliza os JSONs disponíveis em `data/resultados/`, valida os dados e os sincroniza com os bancos do projeto.

### Executar o pipeline completo

Com a chave do Gemini configurada:

```cmd
python main.py processar
```

### Processar uma empresa específica

```cmd
python main.py empresa lifespine http://lifespine.com.br
```

### Exibir os comandos disponíveis

```cmd
python main.py ajuda
```

## API com FastAPI

Inicie a API com:

```cmd
uvicorn src.api:app --reload
```

Endereços locais:

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

Endpoint principal:

```text
POST /processar
```

Exemplo de entrada:

```json
{
  "nome": "lifespine",
  "website": "http://lifespine.com.br"
}
```

Exemplo simplificado de resposta:

```json
{
  "status": "sucesso",
  "resumo": {
    "produtos": 6,
    "produtos_com_imagem": 3,
    "segmentos": 2,
    "certificacoes": 0
  }
}
```

## Automação com n8n

Inicie o n8n localmente:

```cmd
npx n8n
```

Acesse `http://localhost:5678` e importe o workflow disponível na pasta `n8n/`.

Durante o teste, a FastAPI deve continuar em execução na porta `8000`.

O workflow segue este fluxo:

```text
Webhook -> HTTP Request -> FastAPI -> Validação -> Sucesso ou erro
```

## Tratamento de erros

O projeto inclui:

- Novas tentativas em falhas temporárias do provedor de IA;
- Isolamento do processamento de cada empresa;
- Continuidade do fluxo quando uma imagem não é encontrada;
- Respostas de erro estruturadas em JSON;
- Validação do resultado antes da persistência.

Uma resposta de erro da API segue este formato:

```json
{
  "status": "erro",
  "mensagem": "Descrição do erro",
  "empresa": null
}
```

## Decisões técnicas

O projeto utiliza uma arquitetura híbrida:

- Scraping tradicional para coleta;
- IA para interpretação semântica;
- Pydantic para validação estrutural;
- Regras determinísticas para normalização;
- SQLite para persistência local;
- FastAPI para disponibilização do serviço;
- n8n para automação.

Essa separação reduz a dependência da inteligência artificial. Quando uma informação não pode ser confirmada, o sistema utiliza valores vazios ou nulos em vez de inventar dados.

## Uso responsável

O projeto acessa somente informações públicas de websites corporativos. Ele não realiza autenticação, acesso a áreas privadas, quebra de mecanismos de segurança ou coleta de dados confidenciais.

## Limitações

- Sites podem apresentar indisponibilidade, timeout ou redirecionamentos;
- Algumas páginas dependem de JavaScript e exigem o fallback com Selenium;
- A qualidade do resultado depende do conteúdo público disponível;
- Nem todos os produtos possuem imagens claramente associadas;
- O provedor de IA pode apresentar limites ou indisponibilidade temporária;
- SQLite é adequado para testes locais, mas não para grandes volumes ou muitos usuários simultâneos.

## Possíveis melhorias

- Migrar o banco para PostgreSQL;
- Adicionar testes automatizados;
- Criar processamento assíncrono com filas;
- Implementar cache e controle de requisições;
- Ampliar a taxonomia médica;
- Adicionar score de confiança e revisão manual;
- Armazenar imagens em serviço de object storage;
- Criar autenticação e monitoramento da API;
- Adicionar Docker e deploy em nuvem;
- Permitir o uso de diferentes provedores de IA.

## Autor

Desenvolvido por **Lucas Ribeiro Rossi**.

[GitHub — lucas1rossi](https://github.com/lucas1rossi)
