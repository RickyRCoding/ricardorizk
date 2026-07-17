import json
import os
from flask import Flask, render_template, send_from_directory

app = Flask(__name__, template_folder='templates', static_folder='static')

# Production Configurations
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production-135792468')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')

@app.route('/')
def index():
    data_path = os.path.join(os.path.dirname(__file__), 'data.json')
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            portfolio_data = json.load(f)
    except FileNotFoundError:
        portfolio_data = {}
    return render_template('index.html', data=portfolio_data)

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Running locally for testing
    port = int(os.environ.get('PORT', 5001))
    debug_mode = app.config['DEBUG']
    print(f"Starting server on http://0.0.0.0:{port} (Debug: {debug_mode})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
