#!/usr/bin/env python3
"""
Discover Consent — Nightly Session Cleanup
Run via cron at 3am daily.

For sessions with opt_in=True, extracts anonymous question-by-question
counts before deleting. No individual answers are retained.
"""

import os
import json
import time
import base64

SESSIONS_DIR    = '/var/www/discoverconsent/sessions'
AGGREGATES_FILE = '/var/www/discoverconsent/aggregates.json'
SESSION_TTL     = 7 * 24 * 3600  # Must match api.py
TOTAL_QUESTIONS = 46


def decode_answers(encoded: str) -> list:
    """Decode a base64url answer string into a list of Y/M/N/U chars."""
    try:
        b64 = encoded.replace('-', '+').replace('_', '/')
        pad = b64 + '==' [:(4 - len(b64) % 4) % 4]
        return list(base64.b64decode(pad).decode('ascii'))
    except Exception:
        return []


def load_aggregates() -> dict:
    if os.path.exists(AGGREGATES_FILE):
        try:
            with open(AGGREGATES_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        'total_sessions': 0,
        'total_participants': 0,
        'questions': [{'yes': 0, 'maybe': 0, 'no': 0} for _ in range(TOTAL_QUESTIONS)]
    }


def save_aggregates(agg: dict):
    with open(AGGREGATES_FILE, 'w') as f:
        json.dump(agg, f, indent=2)


def extract_aggregates(session_data: dict, agg: dict):
    """Add this session's counts to the running aggregate."""
    answers_list = session_data.get('answers', [])
    if len(answers_list) < 2:
        return  # Need at least 2 participants to be meaningful

    agg['total_sessions']     += 1
    agg['total_participants'] += len(answers_list)

    for encoded in answers_list:
        chars = decode_answers(encoded)
        for i, c in enumerate(chars[:TOTAL_QUESTIONS]):
            if c == 'Y':
                agg['questions'][i]['yes']   += 1
            elif c == 'M':
                agg['questions'][i]['maybe'] += 1
            elif c == 'N':
                agg['questions'][i]['no']    += 1


def main():
    now     = time.time()
    agg     = load_aggregates()
    changed = False

    try:
        session_files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith('.json')]
    except OSError:
        return

    for fname in session_files:
        path = os.path.join(SESSIONS_DIR, fname)
        try:
            if now - os.path.getmtime(path) < SESSION_TTL:
                continue  # Not expired yet

            # Load session
            with open(path) as f:
                data = json.load(f)

            # Extract aggregates if user opted in and session has data
            if data.get('opt_in') and len(data.get('answers', [])) >= 2:
                extract_aggregates(data, agg)
                changed = True

            os.remove(path)

        except (OSError, json.JSONDecodeError, ValueError):
            # Try to delete even if we can't read it
            try:
                os.remove(path)
            except OSError:
                pass

    if changed:
        save_aggregates(agg)
        print(f"Aggregates updated: {agg['total_sessions']} sessions, "
              f"{agg['total_participants']} participants")


if __name__ == '__main__':
    main()
