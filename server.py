from flask import Flask, jsonify, send_from_directory
import subprocess
import os
import datetime

app = Flask(__name__)

# --- CONFIGURATION ---
# This directory will hold images on the Pi until your PC downloads them
SCAN_FOLDER = os.path.join(os.getcwd(), "scanned_images")

# Safety Principle: Ensure the folder exists to prevent file errors
if not os.path.exists(SCAN_FOLDER):
    os.makedirs(SCAN_FOLDER)

@app.route('/scan', methods=['POST'])
def scan():
    """
    Triggered by PC. 
    1. Generates a unique filename.
    2. Runs the hardware scan command.
    3. Saves the file locally.
    4. Responds with JSON success.
    """
    # Generate unique filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scan_{timestamp}.png"
    filepath = os.path.join(SCAN_FOLDER, filename)

    # Command adjusted based on your hardware (Removed --mode Color)
    command = [
        "scanimage", 
        "--resolution", "300", 
        "mode", "Color",
        "--format=png"
    ]

    try:
        print(f"Starting scan for {filename}...")
        
        # Execute scan and redirect output to file
        with open(filepath, "wb") as image_file:
            subprocess.run(command, stdout=image_file, check=True)

        print(f"Success: Saved to {filepath}")

        # Return success JSON to Node.js
        return jsonify({
            "status": "success",
            "message": "Scan completed successfully",
            "filename": filename
        })

    except subprocess.CalledProcessError as e:
        print(f"Scanner Hardware Error: {e}")
        return jsonify({
            "status": "error",
            "message": "Scanner failed to capture image. Check USB connection."
        }), 500
    except Exception as e:
        print(f"System Error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/images/<path:filename>', methods=['GET'])
def get_image(filename):
    """
    Serves the image file so the PC can download it via Axios.
    """
    try:
        return send_from_directory(SCAN_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "File not found"}), 404

if __name__ == '__main__':
    # '0.0.0.0' exposes the server to the local network (PC can see it)
    print(f"Scanner Server Online on port 5000...")
    print(f"Saving images to: {SCAN_FOLDER}")
    app.run(host='0.0.0.0', port=5000)