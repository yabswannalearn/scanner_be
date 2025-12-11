from flask import Flask, jsonify, send_from_directory
import subprocess
import os
import datetime

app = Flask(__name__)

# --- CONFIGURATION ---
# This directory will hold images on the Pi until your PC downloads them
SCAN_FOLDER = os.path.join(os.getcwd(), "scanned_images")

# Safety: Ensure the folder exists
if not os.path.exists(SCAN_FOLDER):
    os.makedirs(SCAN_FOLDER)

@app.route('/scan', methods=['POST'])
def scan():
    """
    Handles the POST request from your Node.js service.
    1. Generates a filename.
    2. Runs the scanimage command.
    3. Returns JSON with status 'success' and the filename.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scan_{timestamp}.png"
    filepath = os.path.join(SCAN_FOLDER, filename)

    # Command adjusted for your scanner capabilities 
    # (Removed --mode Color as per previous hardware checks)
    command = [
        "scanimage", 
        "--resolution", "300", 
        "--mode", "Color" 
        "--format=png"
    ]

    try:
        print(f"Starting scan: {filename}...")
        
        # Open file to write the scanner output directly
        with open(filepath, "wb") as image_file:
            subprocess.run(command, stdout=image_file, check=True)

        print(f"Scan saved to {filepath}")

        # Returns the JSON structure your Node.js code checks for
        return jsonify({
            "status": "success",
            "message": "Scan completed",
            "filename": filename
        })

    except subprocess.CalledProcessError as e:
        print(f"Scanner Error: {e}")
        return jsonify({
            "status": "error",
            "message": "Scanner hardware failed to respond."
        }), 500
    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/images/<path:filename>', methods=['GET'])
def get_image(filename):
    """
    Serves the image file to your Node.js 'downloadFile' function.
    """
    try:
        return send_from_directory(SCAN_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "File not found"}), 404

if __name__ == '__main__':
    # '0.0.0.0' is required to make the server accessible from your PC
    # Port 5000 matches your Node.js FLASK_BASE_URL
    print(f"Server running. Saving scans to: {SCAN_FOLDER}")
    app.run(host='0.0.0.0', port=5000)