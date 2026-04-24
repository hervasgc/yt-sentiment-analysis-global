import argparse
import sys
import os

# Add src to python path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from crawler import YouTubeBrandCrawler
from downloader import VideoDownloader
from comment_extractor import YouTubeCommentExtractor
from audio_extractor import AudioExtractor
from pipeline import CachedAnalysisPipeline

def main():
    print("\n" + "!"*60)
    print(" DISCLAIMER: This tool is for educational/research purposes only.")
    print(" Users are responsible for complying with YouTube's Terms of Service.")
    print(" By using this tool, you agree to these terms.")
    print("!"*60 + "\n")

    parser = argparse.ArgumentParser(description="Sentiment Analysis Pipeline")
    parser.add_argument('step', nargs='?', default='all', choices=['all', 'crawl', 'download', 'comments', 'audio', 'analyze'], 
                        help="The step of the pipeline to run.")
    parser.add_argument('--config', default=None, help="Path to configuration file.")
    
    args = parser.parse_args()
    
    # Check for Cloud Run Job Execution ID
    execution_id = os.environ.get("EXECUTION_ID")
    outputs_dir = os.environ.get("OUTPUTS_DIR", os.path.join(os.path.dirname(__file__), 'outputs'))
    
    if args.config:
        config_path = os.path.abspath(args.config)
        base_output_dir = None # Let components decide or use default
    elif execution_id:
        base_output_dir = os.path.join(outputs_dir, "executions", execution_id)
        config_path = os.path.join(base_output_dir, "config.ini")
        print(f"Using Cloud Run Execution Context: {base_output_dir}")
    else:
        config_path = os.path.abspath('config.ini')
        base_output_dir = None

    # Ensure config path exists
    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found.")
        return
    
    # Initialize Status Tracker if in execution mode
    tracker = None
    if execution_id and base_output_dir:
        from src.status_tracker import StatusTracker
        tracker = StatusTracker(base_output_dir)

    try:
        if args.step in ['all', 'crawl']:
            print("\n" + "="*40)
            print(" STEP 1: CRAWLING VIDEOS ")
            print("="*40)
            if tracker: tracker.update_step("crawl", "running")
            crawler = YouTubeBrandCrawler(config_path=config_path, output_dir=base_output_dir)
            crawler.run_crawler()
            if tracker: tracker.update_step("crawl", "success")
            
        if args.step in ['all', 'download']:
            print("\n" + "="*40)
            print(" STEP 2: DOWNLOADING VIDEOS ")
            print("="*40)
            if tracker: tracker.update_step("download", "running")
            downloader = VideoDownloader(config_path=config_path, output_dir=base_output_dir)
            downloader.download_videos()
            if tracker: tracker.update_step("download", "success")
            
        if args.step in ['all', 'comments']:
            print("\n" + "="*40)
            print(" STEP 3: EXTRACTING COMMENTS ")
            print("="*40)
            if tracker: tracker.update_step("comments", "running")
            extractor = YouTubeCommentExtractor(config_path=config_path, output_dir=base_output_dir)
            extractor.extract_comments()
            if tracker: tracker.update_step("comments", "success")

        if args.step == 'audio' or (args.step == 'all' and os.path.exists(config_path)):
            # Only run audio if needed (usually part of analyze or explicitly asked)
            print("\n" + "="*40)
            print(" EXTRA STEP: EXTRACTING AUDIO ")
            print("="*40)
            if tracker: tracker.update_step("audio", "running")
            extractor = AudioExtractor(config_path=config_path, output_dir=base_output_dir)
            extractor.extract_audio()
            if tracker: tracker.update_step("audio", "success")
            
        if args.step in ['all', 'analyze']:
            print("\n" + "="*40)
            print(" STEP 4: RUNNING ANALYSIS PIPELINE ")
            print("="*40)
            if tracker: tracker.update_step("analyze", "running")
            pipeline = CachedAnalysisPipeline(config_path=config_path, output_dir=base_output_dir)
            pipeline.run_pipeline()
            if tracker: tracker.update_step("analyze", "success")
            if tracker: tracker.update_step("complete", "success")
            
    except Exception as e:
        if tracker:
            # Try to identify which step failed
            for step_id, info in tracker.steps.items():
                if info["status"] == "running":
                    tracker.update_step(step_id, "error", message=str(e))
        print(f"\nAn error occurred during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


#primeito deploy com secrets criados