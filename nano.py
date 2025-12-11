import os
import datetime
import subprocess
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'scanned_images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- ROUTES ---
@app.route('/')
def home():
    return "Scanner System is Online. Use /scan to trigger."

@app.route('/scan', methods=['GET', 'POST'])
def scan_document():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scan_{timestamp}.jpg"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Command to scan with 300 DPI resolution
    command = f"scanimage --format=jpeg --resolution 300 > {filepath}"

    try:
        subprocess.run(command, shell=True, check=True)
        return jsonify({
            "status": "success",
            "message": "Scan completed",
            "file_saved_at": filepath,
            "filename": filename
        })
    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "error",
            "message": "Scanning failed. Check USB connection.",
            "debug_error": str(e)
        }), 500

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    print(f"Starting server at http://192.168.100.39:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)