# YouTube Sentiment Analysis & Presentation Generator

(THIS IS NOT AN OFFICIAL GOOGLE TOOL)

This project performs a comprehensive sentiment analysis of a brand on YouTube using Google's Gemini AI. It crawls for relevant videos, extracts comments, analyzes sentiment, and generates both a strategic report (HTML) and a full presentation deck (Images & PDF).

It now features a user-friendly **Streamlit web interface** and uses parallel processing for faster execution.

## ⚠️ Disclaimer

**Please read this carefully before using this tool.**

1.  **Terms of Service Compliance:** This tool automates interactions with YouTube. Users are strictly responsible for ensuring their usage complies with [YouTube's Terms of Service](https://www.youtube.com/t/terms).
2.  **Rate Limiting:** Aggressive scraping can lead to IP bans or account restrictions. This tool is intended for personal research and analysis, not for high-volume data harvesting.

## Features

-   **Web UI**: Run the entire pipeline from a clean Streamlit interface.
-   **No Downloads Required**: Uses Gemini's direct video understanding capabilities via URLs.
-   **Parallel Processing**: Analyzes video batches in parallel to save time.
-   **Automatic Presentation**: Generates full slides with text using Gemini's image generation (Nano Banana).
-   **Export Options**: Download reports as HTML and presentations as PDF.
-   **Customization**: Set target language and provide custom context to guide the AI analysis.

## Project Structure

-   **`app.py`**: The Streamlit web application.
-   **`main.py`**: The CLI entry point for running steps manually.
-   **`src/`**: Core Python scripts for crawling, analysis, and generation.
-   **`templates/`**: HTML templates for reports and text prompts for Gemini.
-   **`outputs/`**: Generated data (CSVs, reports, slides, PDFs).
-   **`config.ini`**: Configuration file for search terms, models, and limits.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd sentiment-analysis
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    -   Copy `.env.example` to `.env`:
        ```bash
        cp .env.example .env
        ```
    -   Open `.env` and add your YouTube API key (Gemini key is hardcoded in this version for convenience):
        ```env
        YOUTUBE_API_KEY=your_youtube_api_key
        ```

## Usage

### Option A: Streamlit Web Interface (Recommended)
Run the following command to start the local web server:
```bash
streamlit run app.py
```
Open your browser at the provided URL (usually `http://localhost:8501`) to configure and run the pipeline.

### Option B: Command Line Interface (CLI)
You can run the entire pipeline or individual steps using `main.py`.

#### Run the Full Pipeline
This will crawl videos, extract comments, run the analysis, and generate the presentation.
```bash
python main.py all
```

#### Run Individual Steps
1.  **Crawl Videos:**
    ```bash
    python main.py crawl
    ```
2.  **Extract Comments:**
    ```bash
    python main.py comments
    ```
3.  **Run Analysis:** Generates the strategic report.
    ```bash
    python main.py analyze
    ```
4.  **Generate Slides:** Generates the presentation images and PDF.
    ```bash
    python main.py slides
    ```

## Outputs

All outputs are saved in the `outputs/<brand_name>/` directory:
-   `*_discovered_videos.csv`: List of videos found.
-   `*_raw_comments.csv`: Extracted comments.
-   `*_strategic_report.html`: The final analysis report.
-   `*_deck.html`: Interactive presentation viewer.
-   `*_presentation.pdf`: Combined slides in PDF format.
