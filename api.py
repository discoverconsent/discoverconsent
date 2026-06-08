#!/usr/bin/env python3
"""
Discover Consent — Session API
Stores anonymous encoded answer strings in JSON files.
No accounts, no emails, no identifying data of any kind.
Sessions auto-expire after 48 hours.
"""

import os
import json
import time
import random
import string
from flask import Flask, request, jsonify

app = Flask(__name__)

SESSIONS_DIR = '/var/www/discoverconsent/sessions'
SESSION_TTL  = 7 * 24 * 3600  # 7 days in seconds
MAX_PARTICIPANTS = 10
CODE_LEN = 6

VALID_CODE_CHARS    = set(string.ascii_uppercase + string.digits)
VALID_ENCODED_CHARS = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')

os.makedirs(SESSIONS_DIR, exist_ok=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def session_path(code: str) -> str:
    return os.path.join(SESSIONS_DIR, f'{code}.json')

def is_valid_code(code: str) -> bool:
    return (
        isinstance(code, str)
        and len(code) == CODE_LEN
        and all(c in VALID_CODE_CHARS for c in code)
    )

def is_valid_encoded(enc: str) -> bool:
    return (
        isinstance(enc, str)
        and 20 <= len(enc) <= 200
        and all(c in VALID_ENCODED_CHARS for c in enc)
    )

def cleanup_old_sessions():
    """Remove session files older than SESSION_TTL. Called on create."""
    now = time.time()
    try:
        for fname in os.listdir(SESSIONS_DIR):
            if not fname.endswith('.json'):
                continue
            path = os.path.join(SESSIONS_DIR, fname)
            try:
                if os.path.getmtime(path) < now - SESSION_TTL:
                    os.remove(path)
            except OSError:
                pass
    except OSError:
        pass

def load_session(code: str):
    """Return session dict or None if missing/expired."""
    path = session_path(code)
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        # Treat file as expired if TTL exceeded
        if time.time() - data.get('created', 0) > SESSION_TTL:
            try:
                os.remove(path)
            except OSError:
                pass
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None

def save_session(data: dict):
    path = session_path(data['code'])
    with open(path, 'w') as f:
        json.dump(data, f)


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/api/session/create', methods=['POST'])
def create_session():
    cleanup_old_sessions()
    chars = string.ascii_uppercase + string.digits
    for _ in range(30):
        code = ''.join(random.choices(chars, k=CODE_LEN))
        if not os.path.exists(session_path(code)):
            body   = request.get_json(silent=True) or {}
            opt_in = bool(body.get('opt_in', False))
            data   = {
                'code': code,
                'created': time.time(),
                'answers': [],
                'opt_in': opt_in
            }
            save_session(data)
            return jsonify({'code': code})
    return jsonify({'error': 'Could not generate session code'}), 500


@app.route('/api/session/<code>', methods=['GET'])
def get_session(code):
    if not is_valid_code(code):
        return jsonify({'error': 'Invalid session code'}), 400
    data = load_session(code)
    if data is None:
        return jsonify({'error': 'Session not found or expired'}), 404
    age = time.time() - data['created']
    return jsonify({
        'code': code,
        'count': len(data['answers']),
        'answers': data['answers'],
        'expires_in': max(0, int(SESSION_TTL - age))
    })


@app.route('/api/session/<code>/submit', methods=['POST'])
def submit_to_session(code):
    if not is_valid_code(code):
        return jsonify({'error': 'Invalid session code'}), 400
    data = load_session(code)
    if data is None:
        return jsonify({'error': 'Session not found or expired'}), 404
    if len(data['answers']) >= MAX_PARTICIPANTS:
        return jsonify({'error': f'Session is full (max {MAX_PARTICIPANTS})'}), 400

    body    = request.get_json(silent=True) or {}
    encoded = str(body.get('encoded', '')).strip()
    if not is_valid_encoded(encoded):
        return jsonify({'error': 'Invalid answer data'}), 400

    data['answers'].append(encoded)
    save_session(data)
    return jsonify({'ok': True, 'count': len(data['answers'])})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3001, debug=False)
