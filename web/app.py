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
    user_email = request.headers.get("X-Goog-Authenticated-User-Email", "Local User")
    
    search_terms = request.form.get('search_terms')
    max_results = request.form.get('max_results', '10')
    video_type = request.form.get('video_type', 'both')
    
    if not search_terms:
        return jsonify({"error": "Search terms are required"}), 400
        
    # Generate a unique execution ID
    execution_id = str(uuid.uuid4())
    
    # Create execution-specific config directory
    exec_dir = os.path.join(OUTPUTS_DIR, "executions", execution_id)
    os.makedirs(exec_dir, exist_ok=True)
    
    # Save parameters to a config.ini for this specific execution
    config = configparser.ConfigParser()
    config['Crawler'] = {
        'search_terms': search_terms,
        'max_results': max_results,
        'video_type': video_type
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
            "message": "Analysis job started successfully!", 
            "execution_id": execution_id,
            "operation_id": operation.operation.name
        })
        
    except Exception as e:
        import traceback
        return jsonify({"error": f"Failed to start job: {str(e)}", "traceback": traceback.format_exc()}), 500

if __name__ == '__main__':
    # Cloud Run provides the PORT environment variable
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
