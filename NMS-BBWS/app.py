from flask import Flask, jsonify, render_template, request
from ping3 import ping
import json
import os

app = Flask(__name__)

DATA_FILE = 'devices.json'

# Fungsi untuk membaca data dari file JSON
def load_devices():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                # Mengubah key JSON string kembali menjadi integer agar cocok dengan kode Anda
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
            except json.JSONDecodeError:
                return {}
    return {}

# Fungsi untuk menyimpan data ke file JSON
def save_devices(devices):
    with open(DATA_FILE, 'w') as f:
        json.dump(devices, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/denah3d')
def denah_3d():
    return render_template('denah3d.html')

# Endpoint untuk mengambil data atau menambah perangkat baru secara dinamis
@app.route('/api/devices', methods=['GET', 'POST'])
def handle_devices():
    devices = load_devices()
    
    if request.method == 'POST':
        data = request.json
        new_id = max(devices.keys()) + 1 if devices else 1
        
        # Mapping jenis perangkat ke ikon fontawesome yang sesuai
        type_icons = {
            "router": "fa-router",
            "ap": "fa-wifi",
            "wifi": "fa-wifi",
            "tv": "fa-tv",
            "laptop": "fa-laptop",
            "server": "fa-server"
        }
        
        dev_type = data.get("type", "wifi")
        
        devices[new_id] = {
            "name": data.get("name", f"Perangkat {new_id}"),
            "ip": data.get("ip", "192.168.1.100"),
            "band": data.get("band", "2.4 GHz"),
            "status": "ping",
            "type": dev_type,
            "icon": type_icons.get(dev_type, "fa-wifi"),
            "x": float(data.get("x", 0)),
            "z": float(data.get("z", 0))
        }
        save_devices(devices)
        return jsonify({"success": True, "id": new_id})
    
    return jsonify(devices)

# Endpoint Edit Perangkat (PUT)
@app.route('/api/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    devices = load_devices()
    if device_id not in devices:
        return jsonify({"success": False, "error": "Perangkat tidak ditemukan"}), 404
    
    data = request.json
    dev_type = data.get("type", devices[device_id].get("type", "wifi"))
    
    type_icons = {
        "router": "fa-router",
        "ap": "fa-wifi",
        "wifi": "fa-wifi",
        "tv": "fa-tv",
        "laptop": "fa-laptop",
        "server": "fa-server"
    }

    devices[device_id].update({
        "name": data.get("name", devices[device_id]["name"]),
        "ip": data.get("ip", devices[device_id]["ip"]),
        "band": data.get("band", devices[device_id]["band"]),
        "type": dev_type,
        "icon": type_icons.get(dev_type, "fa-wifi"),
        "x": float(data.get("x", devices[device_id]["x"])),
        "z": float(data.get("z", devices[device_id]["z"]))
    })
    
    save_devices(devices)
    return jsonify({"success": True})

# Endpoint Hapus Perangkat (DELETE)
@app.route('/api/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    devices = load_devices()
    if device_id in devices:
        del devices[device_id]
        save_devices(devices)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Perangkat tidak ditemukan"}), 404

@app.route('/api/status')
def get_status():
    devices = load_devices()
    status_data = {}
    for dev_id, dev in devices.items():
        if dev["status"] == "disabled":
            status_data[dev_id] = {
                "status": "disabled",
                "ip": dev["ip"],
                "latency": "-",
                "name": dev["name"],
                "band": dev["band"],
                "type": dev.get("type", "wifi")
            }
            continue
        
        if dev["status"] == "simulated_online":
            status_data[dev_id] = {
                "status": "online",
                "ip": dev["ip"],
                "latency": "2.5 ms",
                "name": dev["name"],
                "band": dev["band"],
                "type": dev.get("type", "wifi")
            }
            continue

        response = ping(dev["ip"], timeout=1)
        if response is not None:
            latency_ms = round(response * 1000, 1)
            status_data[dev_id] = {
                "status": "online",
                "ip": dev["ip"],
                "latency": f"{latency_ms} ms",
                "name": dev["name"],
                "band": dev["band"],
                "type": dev.get("type", "wifi")
            }
        else:
            status_data[dev_id] = {
                "status": "offline",
                "ip": dev["ip"],
                "latency": "-",
                "name": dev["name"],
                "band": dev["band"],
                "type": dev.get("type", "wifi")
            }
            
    return jsonify(status_data)

# Endpoint untuk memperbarui posisi perangkat di denah 3D
@app.route('/api/devices/<int:device_id>/position', methods=['PUT'])
def update_device_position(device_id):
    devices = load_devices()
    if device_id not in devices:
        return jsonify({"success": False, "error": "Perangkat tidak ditemukan"}), 404
    
    data = request.json
    if "x" in data:
        devices[device_id]["x"] = float(data["x"])
    if "z" in data:
        devices[device_id]["z"] = float(data["z"])
        
    save_devices(devices)
    return jsonify({"success": True})

if __name__ == '__main__':
    print("==================================================")
    print("Server NMS Berjalan Normal & Tersinkronisasi JSON!")
    print("==================================================")
    app.run(debug=True, port=5000)