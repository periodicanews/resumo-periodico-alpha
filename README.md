# Resumo Periódico (alpha)

Ferramenta experimental desenvolvida para gerar resumos de artigos científicos diretamente de arquivos PDF. Esses resumos são aproveitados no processo de curadoria da [newsletter Periódica](https://periodica.substack.com/).

O modelo de linguagem Claude 3.5 Haiku é utilizado em conjunto com a biblioteca de aprendizado de máquina GROBID, responsável pela extração de informações acadêmicas dos artigos.

# Metodologia

A aplicação é desenvolvida em Python (v3.11.11).

O front-end, implementado com o framework Streamlit (v1.41.1), é executado em um contêiner Docker e intermedia a comunicação com a API da Anthropic para gerar respostas por meio do modelo `claude-3-5-haiku-20241022`.

O back-end executa uma imagem do GROBID, com apenas modelos CRF, utilizados para segmentação e estruturação de documentos acadêmicos em elementos semânticos, como título, autores, afiliações, referências bibliográficas, etc. A [documentação do GROBID](https://grobid.readthedocs.io/en/latest/Grobid-docker/) também disponibiliza a versão completa (10GB), porém, para esta etapa experimental, usamos a [versão leve](https://hub.docker.com/r/lfoppiano/grobid/) (300MB).

O GROBID é uma biblioteca de aprendizado de máquina para extração, parsing e reestruturação de documentos brutos, como PDFs, convertendo-os para TEI (Text Encoding Initiative), um formato XML voltado para representação de textos acadêmicos e científicos de forma estruturada.

A integração entre o GROBID e a API da Anthropic ocorre pelo front-end com o cliente Python do GROBID (v0.0.9). O usuário anexa um artigo em PDF, que é enviado ao servidor para processamento. O GROBID converte o conteúdo para TEI/XML e retorna o documento reestruturado. Em seguida, o prompt e o código TEI/XML são enviados ao modelo de linguagem. A resposta gerada é retornada e exibida ao usuário.

A reestruturação do artigo ocorre apenas uma vez por sessão, durante a geração do resumo (primeiro prompt enviado automaticamente). O servidor não mantém o histórico de prompts nem recupera arquivos processados (PDF e TEI), embora os armazene temporariamente em diretórios organizados por data e hora.

O framework do front-end e o modelo de linguagem utilizados nesta etapa não são definitivos e fazem parte do processo de prototipação da ferramenta, permitindo a experimentação com outras arquiteturas. Para o próximo teste será desenvolvido um chatbot para o WhatsApp e testado outro LLM.
