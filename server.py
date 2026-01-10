import os
import datetime
import subprocess
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS 

app = Flask(__name__)

# --- CONFIGURATION ---
BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'scanned_images')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- CORS: ALLOW EVERYONE ---
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/')
def home():
    return "Scanner Online. Storage Cleanup Enabled."

# --- ROUTE 1: TRIGGER THE SCAN ---
@app.route('/scan', methods=['POST', 'GET'])
def scan_document():
    # ---------------------------------------------------------
    # FEATURE UPDATE: STORAGE CLEANUP
    # Delete all previous files before starting a new scan
    # ---------------------------------------------------------
    try:
        print("--- CLEANING UP OLD IMAGES ---")
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                os.unlink(file_path) # Deletes the file
    except Exception as e:
        print(f"Cleanup Error: {e}") 
    # ---------------------------------------------------------

    # 1. Create unique filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scan_{timestamp}.png"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    print(f"--- STARTING SCAN: {filename} ---")
    
    # 2. Run the hardware command
    command = ["scanimage", "--format=png", "--mode", "Color", "--resolution", "300"]
    
    try:
        # Save output directly to file
        with open(filepath, "wb") as f:
            subprocess.run(command, stdout=f, check=True)
        
        print(f"--- SAVED: {filepath} ---")

        # 3. Construct the Full URL (Critical for your React App)
        # We use request.host_url to automatically detect the RPi's IP
        host_url = request.host_url.rstrip('/')
        file_url = f"{host_url}/images/{filename}"

        # 4. Return filename AND URL
        return jsonify({
            "status": "success",
            "message": "Scan completed",
            "filename": filename,
            "url": file_url  # React needs this to fetch the image
        })

    except Exception as e:
        print(f"SCAN ERROR: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

# --- ROUTE 2: DOWNLOAD THE IMAGE ---
@app.route('/images/<path:filename>', methods=['GET'])
def get_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # 0.0.0.0 is crucial. It means "Listen to the outside world"
    print(f"Server starting on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
