import os
import datetime
import subprocess
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)

# --- CONFIGURATION ---
# 1. Get the absolute path to the folder on the SD card
BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'scanned_images')

# 2. Create the folder if it doesn't exist (Safety Principle)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- ROUTES ---
@app.route('/')
def home():
    return "Scanner System is Online. Use /scan to trigger."

@app.route('/scan', methods=['POST', 'GET'])
def scan_document():
    # --- TIMESTAMP LOGIC (Ensures "Latest" Scan) ---
    # We create a unique name based on the exact second.
    # The PC receives this filename and asks for it specifically.
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scan_{timestamp}.jpg"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # --- SCAN COMMAND ---
    # Added '--mode Color' as requested.
    command = [
        "scanimage",
        "--format=png",
        "--mode", "Color", 
        "--resolution", "300"
    ]

    try:
        print(f"Scanning new file: {filename}")
        
        # Execute Scan: Write output directly to file to prevent empty files
        with open(filepath, "wb") as f:
            subprocess.run(command, stdout=f, check=True)

        print(f"Saved successfully: {filepath}")

        # Return the UNIQUE filename so the PC knows exactly what to download
        return jsonify({
            "status": "success",
            "message": "Scan completed",
            "filename": filename
        })

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return jsonify({
            "status": "error",
            "message": "Scanner failed. It might not support 'Color' mode or is disconnected.",
            "debug_error": str(e)
        }), 500
    except Exception as e:
        print(f"System Error: {e}")
        return jsonify({
            "status": "error",
            "message": "Internal Server Error",
            "debug_error": str(e)
        }), 500

@app.route('/images/<path:filename>')
def get_image(filename):
    """
    Serves the specific image requested by the PC.
    Because the PC requests the 'filename' it just received from /scan,
    it is guaranteed to get the latest image.
    """
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "File not found"}), 404

if __name__ == '__main__':
    print(f"Server Online. Images will be saved to: {UPLOAD_FOLDER}")
    app.run(host='0.0.0.0', port=5000, debug=True)