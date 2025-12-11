import os
import time
import shutil
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allows Express (on Laptop) to communicate with this RPi

# --- CONFIGURATION ---
# Set to True since you are running on the actual RPi with a scanner
USE_REAL_SCANNER = True 

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. INPUT: Source for simulation (Only needed if USE_REAL_SCANNER is False)
TEST_SOURCE_FOLDER = os.path.join(BASE_DIR, "scans")
TEST_IMAGE_SOURCE = os.path.join(TEST_SOURCE_FOLDER, "test_scan.jpg")

# 2. OUTPUT: Where we save the result on the RPi
# Note: This creates the folder structure INSIDE the RPi
SCAN_FOLDER = os.path.abspath(os.path.join(BASE_DIR, "scanned_output"))

# --- SAFETY CHECKS ---
print(f"--- PATH CONFIGURATION ---")
print(f"Mode: {'REAL SCANNER' if USE_REAL_SCANNER else 'SIMULATION'}")
print(f"Output Will Be Saved To (On RPi): {SCAN_FOLDER}")
print(f"--------------------------")

# Ensure the output directory exists
if not os.path.exists(SCAN_FOLDER):
    print("Creating output folder on RPi...")
    os.makedirs(SCAN_FOLDER)

# Ensure the input directory exists (for organization)
if not os.path.exists(TEST_SOURCE_FOLDER):
    os.makedirs(TEST_SOURCE_FOLDER)

# --- ROUTES ---

@app.route('/scan', methods=['POST'])
def perform_scan():
    filename = f"scan_{int(time.time())}.jpg"
    destination_path = os.path.join(SCAN_FOLDER, filename)

    try:
        if USE_REAL_SCANNER:
            # === OPTION A: REAL RASPBERRY PI SCANNER ===
            print("Initializing SANE scanner...")
            import sane 
            
            try:
                sane.init()
                devices = sane.get_devices()
                if not devices:
                    print("No scanner found via SANE.")
                    return jsonify({"success": False, "error": "No scanner found. Check USB connection."})
                
                print(f"Using device: {devices[0][0]}")
                dev = sane.open(devices[0][0])
                dev.mode = 'Color'
                dev.resolution = 300
                
                dev.start()
                img = dev.snap() # .snap() is often more stable than .scan() for PIL images
                img.save(destination_path)
                dev.close()
                print("Scan saved successfully.")

            except Exception as e:
                print(f"SANE Error: {e}")
                return jsonify({"success": False, "error": f"Scanner Error: {str(e)}"})
            
        else:
            # === OPTION B: LAPTOP SIMULATION (MOCK) ===
            print("Simulating scan...")
            time.sleep(2) 
            
            if os.path.exists(TEST_IMAGE_SOURCE):
                shutil.copy(TEST_IMAGE_SOURCE, destination_path)
            else:
                return jsonify({
                    "success": False, 
                    "error": f"Setup Error: File not found at {TEST_IMAGE_SOURCE}"
                })

        # === SUCCESS RESPONSE ===
        # We return the filename so the frontend knows what was created.
        return jsonify({
            "success": True, 
            "message": "Scan completed successfully",
            "filename": filename,
            "url": f"http://192.168.100.39:5000/download/{filename}" # Helper link
        })

    except Exception as e:
        print(f"Error during scan: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# NEW ROUTE: Allow the laptop to download the image
@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(SCAN_FOLDER, filename)

if __name__ == '__main__':
    # HOST must be 0.0.0.0 to allow connection from Laptop
    app.run(host='0.0.0.0', port=5000, debug=True)