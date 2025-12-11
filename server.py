import os
import datetime
import subprocess
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)

# --- CONFIGURATION (FIX 1: Absolute Path) ---
# We use os.getcwd() to get the full path to the folder on the SD card
BASE_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'scanned_images')

# Create the folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- ROUTES ---
@app.route('/')
def home():
    return "Scanner System is Online. Use /scan to trigger."

@app.route('/scan', methods=['POST', 'GET'])
def scan_document():
    # 1. Generate Filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Note: Switching to PNG is often safer for text, but JPG is fine if you prefer
    filename = f"scan_{timestamp}.jpg"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # 2. Define Command (FIX 2: Removing 'shell=True' for safety)
    # Note: I removed '--mode Color' because your logs showed it wasn't supported.
    # If your scanner definitely supports it, you can add it back.
    command = [
        "scanimage",
        "--format=jpeg",
        "--resolution", "300"
    ]

    try:
        print(f"Scanning to: {filepath}")
        
        # 3. Execute Scan safely
        # We write directly to the file handle. This ensures the file is
        # closed and fully saved before the code moves on.
        with open(filepath, "wb") as f:
            subprocess.run(command, stdout=f, check=True)

        # 4. Return Success
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
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "System error",
            "debug_error": str(e)
        }), 500

@app.route('/images/<path:filename>')  # FIX 3: allow paths if needed
def get_image(filename):
    # This serves the file from the absolute path defined above
    try:
        print(f"Sending file: {filename}")
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "File not found on SD card"}), 404

if __name__ == '__main__':
    # Ensure this port matches your Node.js config (5000)
    print(f"Starting server. Saving images to: {UPLOAD_FOLDER}")
    app.run(host='0.0.0.0', port=5000, debug=True)