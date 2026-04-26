# Documentação do Sistema: YouTube Sentiment Analysis Pipeline

Este documento detalha o funcionamento técnico e operacional da plataforma de análise de sentimento para marcas e tópicos no YouTube.

## 🏗️ Arquitetura do Sistema

O projeto utiliza uma arquitetura **Cloud-Native** baseada em microserviços e processamento assíncrono no Google Cloud Platform (GCP).

1.  **Frontend (Cloud Run Service):** Uma interface web construída em Flask (Python) que serve como painel de controle. Ele é protegido por **Identity-Aware Proxy (IAP)**, garantindo que apenas usuários autorizados acessem a ferramenta.
2.  **Armazenamento (Google Cloud Storage via FUSE):** Um bucket centralizado que atua como disco compartilhado entre todos os componentes. Ele armazena configurações, áudios, vídeos e os relatórios finais.
3.  **Backend (Cloud Run Job):** O "motor" de processamento. Ele é disparado pelo frontend e executa o pipeline pesado (crawler, download, transcrição e análise) de forma independente.
4.  **IA (Google Gemini):** Utiliza os modelos 1.5 Pro e Flash para processar milhares de comentários e sintetizar insights estratégicos.

---

## 🧭 Guia de Parâmetros de Entrada

A interface web oferece diversos campos para refinar sua análise. Aqui está o que cada um faz:

### 1. Configurações de Busca (Crawler)

*   **Termo Principal (`search_terms`):** A marca, produto ou tema que você quer analisar. (Ex: "iPhone 15 Pro").
*   **Modificadores (`search_modifiers`):** Palavras adicionais para refinar a busca. (Ex: "review", "defeito", "unboxing"). Ajuda a focar em tipos específicos de conteúdo.
*   **Máx. Vídeos (`max_results`):** O número máximo de vídeos que o sistema tentará encontrar. Mais vídeos significam uma análise mais profunda, mas consomem mais tempo e recursos.
*   **Região (ISO) (`region_code`):** Código de duas letras do país (Ex: `BR`, `US`). Filtra os resultados baseando-se na relevância regional.
*   **Ordenar por (`sort_by`):** Critério de ordenação do YouTube (Relevância, Visualizações, Engajamento ou Data).
*   **Palavras para Excluir (`exclude_keywords`):** Filtra vídeos que contenham estas palavras no título. Essencial para remover "ruído" ou temas não relacionados.
*   **Tipo de Conteúdo (`video_type`):** Escolha entre vídeos longos tradicionais, YouTube Shorts ou ambos.
*   **Publicado após (`published_after`):** Filtro de data (AAAA-MM-DD). Analise apenas tendências recentes ou lançamentos específicos.
*   **Canais (Incluir/Excluir):** Permite focar a análise em canais específicos ou ignorar canais concorrentes/irrelevantes.
*   **Mínimo de Visualizações (`min_view_count`):** Filtro de popularidade. Garante que você analise apenas vídeos que tiveram impacto real de audiência.

### 2. Configurações de IA (Análise)

*   **Modelo Síntese (Pro) (`pro_model_name`):** O modelo Gemini mais potente (ex: 1.5 Pro). Ele é responsável por ler todos os resumos e criar o relatório estratégico final, conectando os pontos e gerando insights.
*   **Modelo Batch (Flash) (`flash_model_name`):** Um modelo mais rápido e econômico (ex: 1.5 Flash). Ele processa os vídeos e comentários em lotes, resumindo o conteúdo individual de cada um.
*   **Vídeos por Lote (`batch_size`):** Define quantos vídeos a IA lê de uma vez. Aumentar este valor pode acelerar a análise, mas pode perder detalhes sutis. O padrão recomendado é 3.
*   **Formato do Relatório (`report_format`):** Escolha entre HTML (relatório interativo e visual) ou Markdown (texto puro para documentação).

---

## ⚙️ Fluxo de Execução

Ao clicar em **"Iniciar Análise"**, o sistema segue estes passos:

1.  **Geração de ID:** Um identificador único (UUID) é criado para a execução.
2.  **Configuração:** O arquivo `config.ini` é gerado no bucket dentro da pasta dessa execução.
3.  **Trigger:** O Cloud Run Job é disparado e recebe o ID da execução.
4.  **Crawl:** O sistema busca os vídeos conforme seus filtros e salva um CSV.
5.  **Download:** Os áudios/vídeos são baixados para extração de contexto adicional.
6.  **Extração:** Os comentários de cada vídeo são coletados via YouTube API.
7.  **Análise Gemini:**
    *   **Fase 1:** O modelo Flash resume grupos de vídeos e comentários.
    *   **Fase 2:** O modelo Pro lê todos os resumos e gera o **Relatório Estratégico Final**.
8.  **Finalização:** O tracker de status marca como concluído e libera o link de visualização na web.

---

## 📂 Arquivos Gerados

Dentro da pasta de execução no Bucket (`/executions/ID/`), você encontrará:
*   `*_discovered_videos.csv`: Lista de vídeos encontrados e seus metadados.
*   `*_raw_comments.csv`: Todos os comentários extraídos.
*   `*_strategic_report.html`: O seu produto final, o relatório de insights.
*   `status.json`: O rastro técnico do progresso da execução.
