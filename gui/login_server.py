import os
import sys
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import logging
from gevent import pywsgi

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import config_util

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'login_secret_key'
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route('/')
@app.route('/login')
def login_page_redirect():
    # Redirect to the main frontend application to ensure UI consistency
    return redirect("http://localhost:3000")

@app.route('/api/login', methods=['POST'])
def login_api():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'status': 'error', 'message': 'Invalid JSON body'}), 400

        username = data.get('username') or data.get('email')
        password = data.get('password')
        
        print(f"Login attempt: username={username}, password={password}")
        
        # Simple dummy check
        if username == 'zxhy' and password == '12345678':
            session['user_id'] = username
            return jsonify({'status': 'success', 'message': 'Login successful'})
        
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'Internal Server Error: {str(e)}'}), 500

@app.route('/api/login/phone', methods=['POST'])
def login_phone():
    data = request.get_json()
    phone = data.get('phone')
    code = data.get('code')
    
    # TODO: Implement actual phone verification logic
    # For now, accept any code '123456' for testing
    if code == '123456':
        session['user_id'] = phone
        return jsonify({'status': 'success', 'message': 'Login successful', 'redirect': 'http://localhost:5000/home'})
    
    return jsonify({'status': 'error', 'message': 'Invalid verification code'}), 401

@app.route('/api/login/wechat/qrcode', methods=['GET'])
def get_wechat_qrcode():
    # TODO: Implement WeChat QRCode generation
    return jsonify({'status': 'success', 'qrcode_url': '/static/images/mock_qrcode.png', 'uuid': 'mock_uuid'})

@app.route('/api/login/wechat/check', methods=['GET'])
def check_wechat_login():
    uuid = request.args.get('uuid')
    # TODO: Implement WeChat login status check
    return jsonify({'status': 'waiting'})

if __name__ == '__main__':
    print("Login Server starting on port 3002...")
    server = pywsgi.WSGIServer(('0.0.0.0', 3002), app)
    server.serve_forever()

def start():
    from threading import Thread
    print("Login Server starting on port 3002...")
    def run():
        server = pywsgi.WSGIServer(('0.0.0.0', 3002), app)
        server.serve_forever()
    t = Thread(target=run)
    t.daemon = True
    t.start()
