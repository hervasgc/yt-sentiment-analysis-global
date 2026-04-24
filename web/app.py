import os
import uuid
import configparser
from flask import Flask, render_template, request, jsonify, redirect, url_for
from google.cloud import run_v2

app = Flask(__name__)

# Cloud Run Job name to trigger
JOB_NAME = os.environ.get("CLOUD_RUN_JOB_NAME", "yt-analyzer-job")
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
REGION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")

# The path where GCS is mounted via FUSE, or local outputs if testing
OUTPUTS_DIR = os.environ.get("OUTPUTS_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs'))
os.makedirs(OUTPUTS_DIR, exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    # Extract user email from IAP header if present
    user_email = request.headers.get("X-Goog-Authenticated-User-Email", "Local User")
    
    # Strip the prefix if present (IAP sends "accounts.google.com:user@example.com")
    if ":" in user_email:
        user_email = user_email.split(":")[1]
        
    return render_template('index.html', user_email=user_email)

@app.route('/analyze', methods=['POST'])
def start_analysis():
    # Extract user email from IAP header if present
    user_email = request.headers.get("X-Goog-Authenticated-User-Email", "Local User")
    if ":" in user_email:
        user_email = user_email.split(":")[1]

    # Form extraction
    search_terms = request.form.get('search_terms')
    search_modifiers = request.form.get('search_modifiers', '')
    max_results = request.form.get('max_results', '10')
    video_type = request.form.get('video_type', 'both')
    region_code = request.form.get('region_code', 'BR')
    exclude_keywords = request.form.get('exclude_keywords', '')
    published_after = request.form.get('published_after', '')
    include_channels = request.form.get('include_channels', '')
    exclude_channels = request.form.get('exclude_channels', '')
    min_view_count = request.form.get('min_view_count', '10000')
    sort_by = request.form.get('sort_by', 'relevance')
    
    pro_model_name = request.form.get('pro_model_name', 'gemini-1.5-pro')
    flash_model_name = request.form.get('flash_model_name', 'gemini-1.5-flash')
    batch_size = request.form.get('batch_size', '3')
    report_format = request.form.get('report_format', 'html')
    
    if not search_terms:
        return jsonify({"error": "Search terms are required"}), 400
        
    # Generate a unique execution ID
    execution_id = str(uuid.uuid4())
    
    # Create execution-specific config directory
    exec_dir = os.path.join(OUTPUTS_DIR, "executions", execution_id)
    os.makedirs(exec_dir, exist_ok=True)
    
    # Load the base config.ini as a raw text template to preserve comments and formatting
    # Inside Docker, the project root is /app
    base_config_path = '/app/config.ini'
    if not os.path.exists(base_config_path):
        # Fallback for local testing outside Docker
        base_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.ini')
    
    if os.path.exists(base_config_path):
        with open(base_config_path, 'r', encoding='utf-8') as f:
            config_text = f.read()
        
        # Replace specific values using simple string replacement or regex
        import re
        def replace_value(text, key, new_value):
            # Regex to match key = value and replace it, keeping comments on the SAME line if any
            # But usually we just want to replace the whole line for these specific settings
            pattern = rf'^{key}\s*=.*$'
            return re.sub(pattern, f'{key} = {new_value}', text, flags=re.MULTILINE)

        # Crawler replacements
        config_text = replace_value(config_text, 'search_terms', search_terms)
        config_text = replace_value(config_text, 'search_modifiers', search_modifiers)
        config_text = replace_value(config_text, 'max_results', max_results)
        config_text = replace_value(config_text, 'video_type', video_type)
        config_text = replace_value(config_text, 'region_code', region_code)
        config_text = replace_value(config_text, 'exclude_keywords', exclude_keywords)
        config_text = replace_value(config_text, 'published_after', published_after)
        config_text = replace_value(config_text, 'include_channels', include_channels)
        config_text = replace_value(config_text, 'exclude_channels', exclude_channels)
        config_text = replace_value(config_text, 'min_view_count', min_view_count)
        config_text = replace_value(config_text, 'sort_by', sort_by)
        
        # Analysis replacements
        config_text = replace_value(config_text, 'pro_model_name', pro_model_name)
        config_text = replace_value(config_text, 'flash_model_name', flash_model_name)
        config_text = replace_value(config_text, 'batch_size', batch_size)
        config_text = replace_value(config_text, 'report_format', report_format)
        
        config_path = os.path.join(exec_dir, 'config.ini')
        with open(config_path, 'w', encoding='utf-8') as configfile:
            configfile.write(config_text)
    else:
        # Fallback to configparser if template is missing
        config = configparser.ConfigParser()
        # ... (keep existing fallback logic)
        config['Crawler'] = {
            'search_terms': search_terms,
            'search_modifiers': search_modifiers,
            'max_results': max_results,
            'video_type': video_type,
            'region_code': region_code,
            'exclude_keywords': exclude_keywords,
            'published_after': published_after,
            'include_channels': include_channels,
            'exclude_channels': exclude_channels,
            'min_view_count': min_view_count,
            'sort_by': sort_by
        }
        config['AudioExtractor'] = {'audio_folder_name': 'audio'}
        config['Analysis'] = {
            'pro_model_name': pro_model_name,
            'flash_model_name': flash_model_name,
            'batch_size': batch_size,
            'report_format': report_format,
            'pro_prompt_template_path': 'templates/prompts/topic_analysis.txt',
            'flash_prompt_template_path': 'templates/prompts/topic_flash.txt'
        }
        config_path = os.path.join(exec_dir, 'config.ini')
        with open(config_path, 'w') as configfile:
            config.write(configfile)
        
    # Trigger the Cloud Run Job
    try:
        if not PROJECT_ID:
            print("Warning: GOOGLE_CLOUD_PROJECT not set, skipping job trigger (local dev)")
            return jsonify({
                "message": "Analysis configuration saved (local dev mode).", 
                "execution_id": execution_id
            })
            
        client = run_v2.JobsClient()
        job_path = client.job_path(PROJECT_ID, REGION, JOB_NAME)
        
        # We pass the execution ID as an environment variable override
        request_pb = run_v2.RunJobRequest(
            name=job_path,
            overrides={
                "container_overrides": [
                    {
                        "env": [
                            {"name": "EXECUTION_ID", "value": execution_id},
                            {"name": "USER_EMAIL", "value": user_email}
                        ]
                    }
                ]
            }
        )
        
        operation = client.run_job(request=request_pb)
        # We don't wait for the operation to complete, we return immediately
        
        return jsonify({
            "message": "Análise iniciada com sucesso na nuvem!", 
            "execution_id": execution_id,
            "operation_id": operation.operation.name
        })
        
    except Exception as e:
        import traceback
        return jsonify({"error": f"Falha ao iniciar o job: {str(e)}", "traceback": traceback.format_exc()}), 500

@app.route('/status/<execution_id>', methods=['GET'])
def get_status(execution_id):
    exec_dir = os.path.join(OUTPUTS_DIR, "executions", execution_id)
    if not os.path.exists(exec_dir):
        return jsonify({"error": "Execution not found"}), 404
    
    from src.status_tracker import StatusTracker
    status = StatusTracker.get_status(exec_dir)
    
    if not status:
        return jsonify({"status": "starting", "steps": {}})
    
    # Check if complete to provide the report filename
    if status['steps'].get('complete', {}).get('status') == 'success':
        # Look for the HTML file in the outputs directory
        # The file is usually search_terms_strategic_report.html
        import glob
        html_files = glob.glob(os.path.join(exec_dir, "*_report.html"))
        if html_files:
            status['report_url'] = f"/report/{execution_id}"

    return jsonify(status)

@app.route('/report/<execution_id>')
def serve_report(execution_id):
    exec_dir = os.path.join(OUTPUTS_DIR, "executions", execution_id)
    import glob
    html_files = glob.glob(os.path.join(exec_dir, "*_report.html"))
    if not html_files:
        return "Relatório não encontrado", 404
    
    from flask import send_file
    return send_file(html_files[0])

if __name__ == '__main__':
    # Cloud Run provides the PORT environment variable
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
