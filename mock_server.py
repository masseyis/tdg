#!/usr/bin/env python3
"""Simple mock server for testing"""

from flask import Flask, jsonify, request
import json

app = Flask(__name__)

@app.route('/', methods=['GET'])
def list_versions():
    return jsonify({"version": "v2", "status": "current"}), 200

@app.route('/v2', methods=['GET'])
def get_version():
    return jsonify({"version": "v2.0", "description": "Current version"}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    print("🚀 Starting mock server on http://localhost:9999")
    app.run(host='0.0.0.0', port=9999, debug=True)
