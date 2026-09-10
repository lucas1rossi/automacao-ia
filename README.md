# LABD AI Data Agent

Prova Técnica – Estágio em Estratégia de Adoção de IA, Data Engineering & Automação.

Este projeto implementa um agente automatizado para coleta, análise, classificação e estruturação de informações públicas de empresas do setor médico-hospitalar.

A solução utiliza scraping, inteligência artificial, validação de dados, banco relacional, API e automação com n8n.

---

## Objetivo

O sistema recebe um domínio corporativo público e executa automaticamente as seguintes etapas:

1. Acessa o website da empresa;
2. Coleta informações públicas relevantes;
3. Analisa o conteúdo utilizando um modelo de linguagem;
4. Classifica a empresa;
5. Identifica produtos, segmentos médicos e certificações;
6. Valida os dados estruturados;
7. Enriquece os produtos com imagens públicas;
8. Salva os dados em banco SQLite;
9. Simula o envio das informações para os sistemas LABD e MBO;
10. Disponibiliza o processamento por API;
11. Permite automação através do n8n.

---

## Teste rápido sem chave de API

É possível testar a camada de validação, persistência e integração sem configurar uma chave do Gemini.

Use:

```cmd
python main.py integrar-existentes
```

Esse comando utiliza os JSONs já disponíveis em:

```text
data/resultados/
```

Os dados são carregados, validados com Pydantic e sincronizados com:

```text
data/labd.db
data/labd_simulado.db
data/mbo_simulado.db
```

Assim, o avaliador consegue testar as camadas de banco e integração mesmo sem possuir uma chave de API.

Importante: esse modo não substitui a inteligência artificial. Os JSONs utilizados foram gerados previamente pelo pipeline completo com IA.

O fluxo desse modo é:

```text
JSON previamente processado
        |
        v
Pydantic
        |
        v
Banco principal
        |
        +-------------------+
        |                   |
        v                   v
LABD simulada           MBO simulada
```

Para executar uma nova coleta e nova análise semântica de um website, é necessária uma chave válida do Gemini.

---

## Empresas utilizadas

A prova técnica utiliza os seguintes domínios:

- https://spmmedicare.com
- http://lifespine.com.br
- http://kontmed.com
- https://oncoexo.com.br
- https://www.verarosas.com.br

Durante os testes, alguns websites apresentaram indisponibilidade, limitações de conteúdo ou comportamento diferente entre HTTP e HTTPS.

No caso do domínio Kontmed, o sistema tenta primeiro os endereços fornecidos e variações públicas disponíveis.

Foi também utilizado fallback para um domínio público funcional encontrado durante os testes quando o domínio original não respondeu adequadamente.

Essa situação é tratada como limitação conhecida e deve ser revisada antes de uso em ambiente de produção.

---

## Arquitetura

Fluxo principal:

```text
Website público
      |
      v
Scraper Python
Requests + BeautifulSoup
      |
      | fallback
      v
Selenium
      |
      v
Texto não estruturado
      |
      v
Gemini / LLM
      |
      v
Normalização
      |
      v
Validação Pydantic
      |
      v
Taxonomia médica
      |
      v
Extração de imagens
      |
      v
Banco principal SQLite
      |
      +-------------------+
      |                   |
      v                   v
LABD simulada         MBO simulada
      |
      v
JSON estruturado
```

Fluxo externo de automação:

```text
Webhook n8n
    |
    v
HTTP Request
    |
    v
FastAPI
    |
    v
Pipeline Python
    |
    v
Gemini
    |
    v
SQLite / LABD / MBO
    |
    v
IF n8n
   / \
  /   \
OK    ERRO
```

---

## Tecnologias utilizadas

### Python

Responsável pelo crawler, processamento, regras de negócio, banco de dados, integrações e API.

### Requests

Utilizado para acesso HTTP aos websites públicos.

### BeautifulSoup

Utilizado para leitura e extração de conteúdo HTML.

### Selenium

Utilizado como fallback para páginas que dependem de JavaScript ou não retornam conteúdo suficiente através de Requests.

### Gemini API

Modelo de linguagem utilizado para transformar texto não estruturado em dados estruturados.

A IA é utilizada principalmente para:

- identificar dados institucionais;
- classificar a empresa;
- identificar segmentos médicos;
- identificar produtos;
- identificar certificações;
- interpretar conteúdo não estruturado.

A IA não é utilizada para todas as etapas do sistema. O projeto adota uma arquitetura híbrida, combinando regras determinísticas e interpretação semântica.

### Pydantic

Responsável pela validação da estrutura retornada pelo modelo de linguagem.

### Taxonomia determinística

Após a saída da IA, segmentos médicos são normalizados para uma taxonomia controlada.

Também existe inferência determinística baseada nos dados já coletados dos produtos quando nenhum segmento foi identificado.

### SQLite

Banco de dados utilizado pela aplicação.

SQLite foi escolhido pela simplicidade de execução da prova de conceito e por não exigir infraestrutura externa.

### FastAPI

Expõe o pipeline através de API REST.

### n8n

Responsável pela orquestração externa do processo através de webhook e chamadas HTTP.

---

## Estrutura do projeto

```text
projeto-labd-entrega/
|
├── data/
|   ├── resultados/
|   ├── labd.db
|   ├── labd_simulado.db
|   └── mbo_simulado.db
|
├── n8n/
|   └── workflow_labd_ai_pipeline.json
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

---

## Dados coletados

O agente busca automaticamente:

### Dados institucionais

- nome;
- descrição;
- website;
- e-mail;
- telefone;
- endereço.

Caso uma informação não seja encontrada de forma confiável no conteúdo público coletado, o sistema mantém o campo como vazio ou nulo.

---

## Classificação da empresa

A empresa é classificada automaticamente em uma das seguintes categorias:

- Fabricante;
- Distribuidor;
- Prestador de Serviços;
- Não identificado.

Existe uma etapa de normalização para pequenas variações na resposta do LLM.

Exemplos:

```text
Manufacturer -> Fabricante
distribuidora -> Distribuidor
service provider -> Prestador de Serviços
valor desconhecido -> Não identificado
```

Isso evita que pequenas variações textuais interrompam o pipeline.

---

## Segmentação médica

O sistema identifica especialidades e segmentos médicos relacionados à empresa e aos seus produtos.

A saída da IA passa por uma taxonomia controlada para padronizar termos em português.

Exemplos de normalização:

```text
Neurosurgical -> Neurocirurgia
Cranial -> Neurocirurgia
Maxillofacial -> Cirurgia Bucomaxilofacial
Thoracic -> Cirurgia Torácica
Dental -> Odontologia
```

Também são utilizados segmentos como:

- Neurocirurgia;
- Ortopedia;
- Cardiologia;
- Oncologia;
- Radiologia;
- Odontologia;
- Urologia;
- Anestesiologia;
- Terapia Infusional;
- Controle de Infecção;
- Nutrição Clínica;
- Cirurgia Geral;
- Cirurgia Torácica;
- Cirurgia Bucomaxilofacial.

Quando não há evidência suficiente, o sistema mantém a lista vazia em vez de inventar informações.

---

## Produtos

Para cada produto podem ser armazenados:

- nome;
- descrição;
- categoria;
- URL da imagem;
- segmento médico;
- página utilizada como fonte.

A extração das imagens é feita de maneira determinística e separada da IA.

O sistema procura páginas relacionadas ao produto e tenta identificar imagens através de:

- `og:image`;
- tags `<img>`;
- `src`;
- `data-src`;
- `srcset`.

Imagens como logos, favicons e arquivos claramente irrelevantes são filtrados quando possível.

---

## Certificações e compliance

O agente identifica menções públicas a certificações e regulamentações como:

- ISO 13485;
- CE;
- FDA;
- ANVISA;
- MDSAP;
- GMP/BGMP;
- outras certificações mencionadas no website.

A ausência de uma certificação no resultado não significa que a empresa não a possua.

Significa apenas que ela não foi identificada no conteúdo público coletado.

---

## Banco de dados

O banco principal é:

```text
data/labd.db
```

A estrutura utiliza tabelas relacionadas para reduzir duplicação de dados.

Entre as entidades existentes estão:

- empresas;
- produtos;
- segmentos;
- relacionamento empresa-segmento;
- relacionamento produto-segmento;
- certificações;
- fontes.

Essa estrutura permite relacionamento entre empresas, produtos e segmentos médicos.

---

## Simulação LABD e MBO

Além do banco estruturado principal, foram criados dois bancos independentes para simular a alimentação dos sistemas internos da LABD e da MBO.

### LABD

```text
data/labd_simulado.db
```

Recebe principalmente:

- dados institucionais;
- contato;
- classificação;
- certificações.

### MBO

```text
data/mbo_simulado.db
```

Recebe principalmente:

- empresa;
- classificação;
- segmentos médicos;
- produtos.

Isso simula a etapa de integração automática após a validação dos dados coletados.

---

## Tratamento de erros

O projeto possui tratamento de falhas em diferentes etapas.

### Retry da IA

Caso o Gemini retorne erro temporário de disponibilidade, como HTTP 503, o sistema realiza novas tentativas automaticamente.

### Isolamento por empresa

Uma empresa com erro não interrompe obrigatoriamente o processamento das demais empresas do lote.

### Imagens

Uma falha ao encontrar uma imagem não interrompe o restante do pipeline.

### API

Erros são retornados em formato estruturado:

```json
{
    "status": "erro",
    "mensagem": "Descrição do erro",
    "empresa": null
}
```

Isso permite que o n8n trate o resultado através do nó IF.

---

## Configuração

### 1. Criar ambiente virtual

Windows:

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 2. Instalar dependências

```cmd
pip install -r requirements.txt
```

---

### 3. Configurar variáveis de ambiente

O repositório não inclui a chave real da API.

Use o arquivo:

```text
.env.example
```

como referência.

Crie uma cópia chamada:

```text
.env
```

Exemplo:

```env
GEMINI_API_KEY=SUA_CHAVE
LLM_PROVIDER=gemini
GEMINI_MODEL=SEU_MODELO
```

A chave do Gemini é necessária apenas para novas coletas e novas análises com IA.

Para testar os resultados já processados sem chave, use:

```cmd
python main.py integrar-existentes
```

Nunca publique ou envie a chave real da API.

---

## Execução

### Opção 1 - Testar sem chave de API

Este é o modo mais rápido para validar o projeto sem depender do provedor de IA.

```cmd
python main.py integrar-existentes
```

Esse comando utiliza os resultados existentes em:

```text
data/resultados/
```

e sincroniza os dados com:

```text
data/labd.db
data/labd_simulado.db
data/mbo_simulado.db
```

Resultado esperado:

```text
Sucessos: 5
Erros: 0
```

---

### Opção 2 - Processar todas as empresas com IA

Com uma chave Gemini configurada:

```cmd
python main.py processar
```

Esse comando executa o pipeline completo das empresas configuradas:

```text
website
-> scraping
-> IA
-> validação
-> taxonomia
-> imagens
-> banco
-> LABD
-> MBO
-> JSON
```

---

### Opção 3 - Processar uma empresa específica

Exemplo:

```cmd
python main.py empresa lifespine http://lifespine.com.br
```

---

### Ajuda

```cmd
python main.py ajuda
```

---

## FastAPI

Para iniciar a API:

```cmd
uvicorn src.api:app --reload
```

A API ficará disponível em:

```text
http://127.0.0.1:8000
```

Documentação Swagger:

```text
http://127.0.0.1:8000/docs
```

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

Exemplo de resposta bem-sucedida:

```json
{
    "status": "sucesso",
    "integracao": {
        "labd": "sincronizado",
        "mbo": "sincronizado"
    },
    "resumo": {
        "produtos": 6,
        "produtos_com_imagem": 3,
        "segmentos": 2,
        "certificacoes": 0
    }
}
```

---

## n8n

Para iniciar o n8n localmente:

```cmd
npx n8n
```

Depois acesse:

```text
http://localhost:5678
```

O workflow exportado está disponível em:

```text
n8n/workflow_labd_ai_pipeline.json
```

O workflow pode ser importado no n8n.

Fluxo:

```text
Webhook
   |
   v
HTTP Request
   |
   v
FastAPI
   |
   v
IF
  / \
 /   \
Sucesso Erro
```

Endpoint utilizado pelo webhook:

```text
POST /webhook/labd-processar
```

Durante a execução local, a FastAPI precisa estar disponível na porta `8000`.

---

## Exemplo de teste via n8n

Com FastAPI e n8n em execução:

```cmd
curl -X POST http://localhost:5678/webhook/labd-processar -H "Content-Type: application/json" -d "{\"nome\":\"lifespine\",\"website\":\"http://lifespine.com.br\"}"
```

Exemplo de resposta:

```json
{
    "status": "sucesso",
    "integracao": {
        "labd": "sincronizado",
        "mbo": "sincronizado"
    }
}
```

Caso o provedor de IA esteja temporariamente indisponível, o workflow pode retornar:

```json
{
    "status": "erro",
    "mensagem": "503 UNAVAILABLE..."
}
```

Esse comportamento é tratado pelo fluxo de erro do n8n.

---

## Uso ético dos dados

O sistema foi desenvolvido exclusivamente para acessar informações públicas disponíveis nos websites corporativos fornecidos.

Não são realizadas:

- invasões;
- tentativas de autenticação;
- bypass de sistemas;
- scraping de áreas privadas;
- obtenção indevida de dados;
- coleta de informações confidenciais.

O objetivo do projeto é exclusivamente demonstrar coleta e estruturação de dados públicos.

---

## Limitações

O projeto possui algumas limitações conhecidas.

### Disponibilidade dos websites

Alguns domínios podem apresentar:

- timeout;
- indisponibilidade;
- redirecionamentos;
- páginas removidas;
- conteúdo carregado dinamicamente.

### Disponibilidade da IA

O provedor de IA pode apresentar erros temporários de alta demanda, como HTTP 503.

Por esse motivo foi implementada lógica de retry e tratamento controlado de erro.

### Segmentação médica

A qualidade inicial da segmentação depende das informações públicas presentes nos websites.

Para aumentar a consistência, foi adicionada uma taxonomia determinística após a etapa de IA.

Mesmo assim, quando não há evidência suficiente, alguns segmentos podem permanecer vazios.

### Imagens

Nem todos os produtos possuem imagens claramente associadas nos websites.

Nesta prova de conceito, o sistema armazena principalmente a URL pública da imagem identificada.

Em produção, uma possível evolução seria baixar os arquivos e armazená-los em object storage, como AWS S3, Azure Blob Storage ou solução equivalente.

### Scraping

O crawler atualmente prioriza páginas consideradas relevantes e possui limite de navegação para evitar requisições excessivas.

### Banco

SQLite atende à prova de conceito e facilita a execução local.

Em um ambiente de produção ou com maior volume de dados, seria recomendável migrar para PostgreSQL, MySQL ou banco gerenciado em cloud.

---

## Escalabilidade

Apesar da implementação local utilizar SQLite, a arquitetura foi separada em módulos independentes:

```text
scraping
IA
validação
taxonomia
imagens
persistência
integração
API
automação
```

Essa separação permite substituir componentes sem reconstruir todo o sistema.

Em produção, a solução poderia utilizar:

```text
n8n
  |
  v
API em cloud
  |
  v
fila de processamento
  |
  +------------+
  |            |
workers      workers
  |            |
  v            v
LLM          scraping
  |
  v
PostgreSQL
  |
  +----------------+
  |                |
  v                v
LABD              MBO
```

---

## Decisões de arquitetura

O modelo de linguagem não é utilizado para todas as etapas.

Foi adotada uma arquitetura híbrida:

- scraping tradicional para coleta;
- LLM para interpretação semântica;
- normalização para consistência da classificação;
- Pydantic para validação estrutural;
- taxonomia determinística para segmentos médicos;
- extração determinística para imagens;
- SQLite para persistência;
- FastAPI para integração;
- n8n para automação.

Essa separação reduz dependência da IA e diminui o risco de alucinação.

Quando uma informação não pode ser comprovada a partir do conteúdo coletado, o sistema utiliza valores vazios ou nulos em vez de inventar dados.

---

## Resultados atuais

A solução foi testada com os cinco domínios previstos na prova.

Os resultados processados estão disponíveis em:

```text
data/resultados/
```

Foram armazenados dados estruturados das seguintes empresas:

```text
SPM Medicare
Life Spine
Kontmed / fallback público utilizado durante os testes
Oncoexo
Vera Rosas Regulatory Affairs
```

Também foram gerados:

```text
data/labd.db
data/labd_simulado.db
data/mbo_simulado.db
```

O pipeline foi testado através da FastAPI e do n8n, incluindo:

- caminho de sucesso;
- integração LABD;
- integração MBO;
- caminho de erro quando o provedor Gemini retorna indisponibilidade temporária.

---

## Melhorias futuras

Em uma versão de produção, algumas evoluções possíveis seriam:

- PostgreSQL ou banco em nuvem;
- migrations de banco;
- índices adicionais;
- processamento assíncrono;
- filas de tarefas;
- cache;
- controle de rate limit;
- leitura de `sitemap.xml`;
- análise de `robots.txt`;
- chunking para websites muito grandes;
- taxonomia médica ampliada;
- armazenamento do valor bruto e normalizado dos segmentos;
- normalização multilíngue;
- score de confiança;
- fila de revisão manual;
- armazenamento real das imagens;
- object storage;
- logs centralizados;
- dashboard administrativo;
- autenticação da API;
- deploy em cloud;
- monitoramento;
- notificações automáticas;
- execução agendada;
- testes automatizados;
- suporte a múltiplos provedores de LLM;
- containerização com Docker.

---

## Observação sobre o provedor de IA

O projeto utiliza Gemini como provedor de LLM nesta prova de conceito.

A arquitetura pode ser evoluída para suportar múltiplos provedores no futuro, como:

- Gemini;
- Claude;
- OpenAI;
- modelos locais.

A variável:

```text
LLM_PROVIDER
```

já está documentada no `.env.example` como referência para essa evolução arquitetural.

Na implementação atual, o pipeline utiliza Gemini.

---

## Resultado final

A solução demonstra um pipeline completo de Data Engineering, inteligência artificial e automação:

```text
Coleta
  |
  v
Estruturação
  |
  v
IA
  |
  v
Validação
  |
  v
Taxonomia
  |
  v
Enriquecimento
  |
  v
Persistência
  |
  v
Integração LABD/MBO
  |
  v
Automação n8n
```

O projeto foi desenvolvido como prova de conceito e pode ser expandido para processar um volume maior de empresas utilizando infraestrutura distribuída, filas, banco de dados em nuvem e múltiplos provedores de inteligência artificial.