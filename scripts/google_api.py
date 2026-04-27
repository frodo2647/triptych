#!/usr/bin/env python3
"""Google Workspace API integration for Triptych.

Handles OAuth2 auth and read/write for Google Docs and Sheets.
Claude can read and edit documents while the user has them open —
changes appear in real-time via Google's OT sync.

Usage:
    python scripts/google_api.py auth                        # OAuth login (opens browser)
    python scripts/google_api.py status                      # Check auth status
    python scripts/google_api.py logout                      # Remove stored tokens
    python scripts/google_api.py doc-read <doc_id>           # Read a Google Doc
    python scripts/google_api.py doc-write <doc_id> <json>   # Write to a Google Doc
    python scripts/google_api.py sheet-read <sheet_id> [range]  # Read cells
    python scripts/google_api.py sheet-write <sheet_id> <range> <json>  # Write cells
    python scripts/google_api.py resolve <url>               # Extract doc/sheet ID from URL
"""

import sys
import os
import json
import re
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / 'workspace' / 'config'
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

CREDENTIALS_FILE = CONFIG_DIR / 'google_credentials.json'
TOKEN_FILE = CONFIG_DIR / 'google_token.json'

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
]


# ── Auth ──────────────────────────────────────────────────────

def get_credentials():
    """Load or refresh OAuth2 credentials. Returns None if not authenticated."""
    if not TOKEN_FILE.exists():
        return None

    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())
        except Exception:
            return None

    if creds and creds.valid:
        return creds
    return None


def authenticate():
    """Run the OAuth2 flow (opens browser for consent)."""
    if not CREDENTIALS_FILE.exists():
        return {
            'error': 'No credentials file found',
            'detail': f'Place your Google OAuth credentials at: {CREDENTIALS_FILE}',
            'setup': (
                '1. Go to https://console.cloud.google.com/apis/credentials\n'
                '2. Create an OAuth 2.0 Client ID (type: Desktop app)\n'
                '3. Download the JSON and save it as:\n'
                f'   {CREDENTIALS_FILE}'
            ),
        }

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE), SCOPES
        )
        # Opens browser, runs local server for redirect
        creds = flow.run_local_server(port=0, open_browser=True)
        TOKEN_FILE.write_text(creds.to_json())
        return {'ok': True, 'message': 'Authenticated successfully'}
    except Exception as e:
        return {'error': f'Auth failed: {e}'}


def get_status():
    """Check authentication status."""
    if not CREDENTIALS_FILE.exists():
        return {'authenticated': False, 'reason': 'no_credentials_file'}
    creds = get_credentials()
    if creds:
        return {'authenticated': True}
    if TOKEN_FILE.exists():
        return {'authenticated': False, 'reason': 'token_expired'}
    return {'authenticated': False, 'reason': 'not_logged_in'}


def logout():
    """Remove stored tokens."""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
    return {'ok': True}


# ── URL parsing ───────────────────────────────────────────────

def resolve_url(url):
    """Extract document/sheet ID and type from a Google URL."""
    # Google Docs: https://docs.google.com/document/d/{ID}/edit
    m = re.search(r'docs\.google\.com/document/d/([a-zA-Z0-9_-]+)', url)
    if m:
        return {'type': 'doc', 'id': m.group(1)}

    # Google Sheets: https://docs.google.com/spreadsheets/d/{ID}/edit
    m = re.search(r'docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)', url)
    if m:
        return {'type': 'sheet', 'id': m.group(1)}

    return {'error': f'Could not parse Google URL: {url}'}


# ── Google Docs ───────────────────────────────────────────────

def doc_read(doc_id):
    """Read a Google Doc. Returns structured content."""
    creds = get_credentials()
    if not creds:
        return {'error': 'Not authenticated. Run: python scripts/google_api.py auth'}

    service = build('docs', 'v1', credentials=creds)
    doc = service.documents().get(documentId=doc_id).execute()

    title = doc.get('title', '')
    revision_id = doc.get('revisionId', '')

    # Extract text content from the document body
    body = doc.get('body', {})
    content = body.get('content', [])

    paragraphs = []
    for element in content:
        if 'paragraph' not in element:
            continue
        para = element['paragraph']
        text = ''
        for elem in para.get('elements', []):
            text_run = elem.get('textRun', {})
            text += text_run.get('content', '')

        style = para.get('paragraphStyle', {}).get('namedStyleType', 'NORMAL_TEXT')
        paragraphs.append({
            'text': text,
            'style': style,
            'startIndex': element.get('startIndex', 0),
            'endIndex': element.get('endIndex', 0),
        })

    # Also extract plain text
    plain_text = ''.join(p['text'] for p in paragraphs)

    return {
        'ok': True,
        'title': title,
        'revisionId': revision_id,
        'documentId': doc_id,
        'paragraphs': paragraphs,
        'text': plain_text,
        'wordCount': len(plain_text.split()) if plain_text.strip() else 0,
    }


def doc_write(doc_id, operations_json):
    """Write to a Google Doc using batchUpdate.

    operations_json is a JSON string containing a list of operations:
    [
        {"insertText": {"location": {"index": 1}, "text": "Hello\\n"}},
        {"replaceAllText": {"containsText": {"text": "old"}, "replaceText": "new"}},
        {"deleteContentRange": {"range": {"startIndex": 10, "endIndex": 20}}}
    ]
    """
    creds = get_credentials()
    if not creds:
        return {'error': 'Not authenticated'}

    try:
        operations = json.loads(operations_json) if isinstance(operations_json, str) else operations_json
    except json.JSONDecodeError as e:
        return {'error': f'Invalid JSON: {e}'}

    service = build('docs', 'v1', credentials=creds)
    result = service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': operations}
    ).execute()

    return {
        'ok': True,
        'documentId': doc_id,
        'replies': result.get('replies', []),
        'writeControl': result.get('writeControl', {}),
    }


# ── Google Sheets ─────────────────────────────────────────────

def sheet_read(sheet_id, cell_range='Sheet1'):
    """Read cells from a Google Sheet."""
    creds = get_credentials()
    if not creds:
        return {'error': 'Not authenticated'}

    service = build('sheets', 'v4', credentials=creds)
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=cell_range,
    ).execute()

    values = result.get('values', [])
    return {
        'ok': True,
        'spreadsheetId': sheet_id,
        'range': result.get('range', cell_range),
        'values': values,
        'rows': len(values),
        'cols': max((len(r) for r in values), default=0),
    }


def sheet_write(sheet_id, cell_range, values_json):
    """Write cells to a Google Sheet.

    values_json is a JSON string containing a 2D array:
    [["A1", "B1"], ["A2", "B2"]]
    """
    creds = get_credentials()
    if not creds:
        return {'error': 'Not authenticated'}

    try:
        values = json.loads(values_json) if isinstance(values_json, str) else values_json
    except json.JSONDecodeError as e:
        return {'error': f'Invalid JSON: {e}'}

    service = build('sheets', 'v4', credentials=creds)
    result = service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=cell_range,
        valueInputOption='USER_ENTERED',
        body={'values': values},
    ).execute()

    return {
        'ok': True,
        'spreadsheetId': sheet_id,
        'updatedRange': result.get('updatedRange', ''),
        'updatedRows': result.get('updatedRows', 0),
        'updatedCols': result.get('updatedColumns', 0),
        'updatedCells': result.get('updatedCells', 0),
    }


def sheet_info(sheet_id):
    """Get spreadsheet metadata (sheet names, etc.)."""
    creds = get_credentials()
    if not creds:
        return {'error': 'Not authenticated'}

    service = build('sheets', 'v4', credentials=creds)
    result = service.spreadsheets().get(
        spreadsheetId=sheet_id,
        fields='properties.title,sheets.properties',
    ).execute()

    sheets = []
    for s in result.get('sheets', []):
        props = s.get('properties', {})
        sheets.append({
            'id': props.get('sheetId'),
            'title': props.get('title'),
            'rows': props.get('gridProperties', {}).get('rowCount'),
            'cols': props.get('gridProperties', {}).get('columnCount'),
        })

    return {
        'ok': True,
        'spreadsheetId': sheet_id,
        'title': result.get('properties', {}).get('title', ''),
        'sheets': sheets,
    }


# ── CLI ───────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: google_api.py <command> [args...]'}))
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'auth':
        print(json.dumps(authenticate(), indent=2))
    elif cmd == 'status':
        print(json.dumps(get_status(), indent=2))
    elif cmd == 'logout':
        print(json.dumps(logout()))
    elif cmd == 'resolve' and len(sys.argv) >= 3:
        print(json.dumps(resolve_url(sys.argv[2])))
    elif cmd == 'doc-read' and len(sys.argv) >= 3:
        print(json.dumps(doc_read(sys.argv[2]), indent=2))
    elif cmd == 'doc-write' and len(sys.argv) >= 4:
        print(json.dumps(doc_write(sys.argv[2], sys.argv[3])))
    elif cmd == 'sheet-read' and len(sys.argv) >= 3:
        cell_range = sys.argv[3] if len(sys.argv) >= 4 else 'Sheet1'
        print(json.dumps(sheet_read(sys.argv[2], cell_range), indent=2))
    elif cmd == 'sheet-write' and len(sys.argv) >= 5:
        print(json.dumps(sheet_write(sys.argv[2], sys.argv[3], sys.argv[4])))
    elif cmd == 'sheet-info' and len(sys.argv) >= 3:
        print(json.dumps(sheet_info(sys.argv[2]), indent=2))
    else:
        print(json.dumps({'error': f'Unknown command or missing args: {cmd}'}))
        sys.exit(1)


if __name__ == '__main__':
    main()
