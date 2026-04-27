"""Tests for scripts/google_api.py — Google Workspace API integration."""

import sys
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT = str(PROJECT_ROOT / 'scripts' / 'google_api.py')


# ── URL Resolution Tests ──────────────────────────────────────

class TestResolveUrl:
    """Test Google URL parsing."""

    def test_google_doc_url(self):
        from scripts.google_api import resolve_url
        result = resolve_url('https://docs.google.com/document/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ/edit')
        assert result['type'] == 'doc'
        assert result['id'] == '1aBcDeFgHiJkLmNoPqRsTuVwXyZ'

    def test_google_sheet_url(self):
        from scripts.google_api import resolve_url
        result = resolve_url('https://docs.google.com/spreadsheets/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ/edit#gid=0')
        assert result['type'] == 'sheet'
        assert result['id'] == '1aBcDeFgHiJkLmNoPqRsTuVwXyZ'

    def test_google_doc_with_params(self):
        from scripts.google_api import resolve_url
        result = resolve_url('https://docs.google.com/document/d/abc123_-XYZ/edit?usp=sharing')
        assert result['type'] == 'doc'
        assert result['id'] == 'abc123_-XYZ'

    def test_invalid_url(self):
        from scripts.google_api import resolve_url
        result = resolve_url('https://example.com/not-google')
        assert 'error' in result

    def test_partial_url(self):
        from scripts.google_api import resolve_url
        result = resolve_url('docs.google.com/document/d/myDocId123/edit')
        assert result['type'] == 'doc'
        assert result['id'] == 'myDocId123'


# ── Auth Status Tests ─────────────────────────────────────────

class TestAuthStatus:
    """Test authentication status checks."""

    def test_status_no_credentials_file(self, tmp_path):
        from scripts import google_api
        orig_creds = google_api.CREDENTIALS_FILE
        orig_token = google_api.TOKEN_FILE
        google_api.CREDENTIALS_FILE = tmp_path / 'nonexistent.json'
        google_api.TOKEN_FILE = tmp_path / 'token.json'
        try:
            result = google_api.get_status()
            assert result['authenticated'] is False
            assert result['reason'] == 'no_credentials_file'
        finally:
            google_api.CREDENTIALS_FILE = orig_creds
            google_api.TOKEN_FILE = orig_token

    def test_status_no_token(self, tmp_path):
        from scripts import google_api
        orig_creds = google_api.CREDENTIALS_FILE
        orig_token = google_api.TOKEN_FILE
        # Create a fake credentials file
        creds_file = tmp_path / 'creds.json'
        creds_file.write_text('{"installed": {}}')
        google_api.CREDENTIALS_FILE = creds_file
        google_api.TOKEN_FILE = tmp_path / 'token.json'
        try:
            result = google_api.get_status()
            assert result['authenticated'] is False
            assert result['reason'] == 'not_logged_in'
        finally:
            google_api.CREDENTIALS_FILE = orig_creds
            google_api.TOKEN_FILE = orig_token

    def test_logout(self, tmp_path):
        from scripts import google_api
        orig_token = google_api.TOKEN_FILE
        token_file = tmp_path / 'token.json'
        token_file.write_text('{"token": "test"}')
        google_api.TOKEN_FILE = token_file
        try:
            result = google_api.logout()
            assert result['ok'] is True
            assert not token_file.exists()
        finally:
            google_api.TOKEN_FILE = orig_token

    def test_logout_no_token(self, tmp_path):
        from scripts import google_api
        orig_token = google_api.TOKEN_FILE
        google_api.TOKEN_FILE = tmp_path / 'nonexistent.json'
        try:
            result = google_api.logout()
            assert result['ok'] is True
        finally:
            google_api.TOKEN_FILE = orig_token


# ── Auth Flow Tests (mocked) ─────────────────────────────────

class TestAuthenticate:
    """Test OAuth flow with mocked dependencies."""

    def test_auth_no_credentials_file(self, tmp_path):
        from scripts import google_api
        orig = google_api.CREDENTIALS_FILE
        google_api.CREDENTIALS_FILE = tmp_path / 'nonexistent.json'
        try:
            result = google_api.authenticate()
            assert 'error' in result
            assert 'credentials' in result['error'].lower()
            assert 'setup' in result
        finally:
            google_api.CREDENTIALS_FILE = orig


# ── CLI Integration Tests ─────────────────────────────────────

class TestCLI:
    """Test command-line interface."""

    def test_status_command(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, 'status'],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert 'authenticated' in data

    def test_resolve_doc_url(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, 'resolve',
             'https://docs.google.com/document/d/testDoc123/edit'],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data['type'] == 'doc'
        assert data['id'] == 'testDoc123'

    def test_resolve_sheet_url(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, 'resolve',
             'https://docs.google.com/spreadsheets/d/testSheet456/edit'],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data['type'] == 'sheet'
        assert data['id'] == 'testSheet456'

    def test_unknown_command(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, 'nonexistent'],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 1

    def test_doc_read_not_authenticated(self):
        """doc-read should return error when not authenticated."""
        result = subprocess.run(
            [sys.executable, SCRIPT, 'doc-read', 'fake-doc-id'],
            capture_output=True, text=True, timeout=10,
        )
        data = json.loads(result.stdout)
        # Should return an auth error (not crash)
        assert 'error' in data

    def test_sheet_read_not_authenticated(self):
        """sheet-read should return error when not authenticated."""
        result = subprocess.run(
            [sys.executable, SCRIPT, 'sheet-read', 'fake-sheet-id', 'A1:B2'],
            capture_output=True, text=True, timeout=10,
        )
        data = json.loads(result.stdout)
        assert 'error' in data


# ── Mocked API Tests ──────────────────────────────────────────

class TestDocRead:
    """Test doc reading with mocked Google API."""

    @patch('scripts.google_api.get_credentials')
    @patch('scripts.google_api.build')
    def test_doc_read_returns_structured_content(self, mock_build, mock_creds):
        from scripts.google_api import doc_read

        mock_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.documents().get().execute.return_value = {
            'title': 'Test Doc',
            'revisionId': 'rev123',
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [{'textRun': {'content': 'Hello World\n'}}],
                            'paragraphStyle': {'namedStyleType': 'HEADING_1'},
                        },
                        'startIndex': 1,
                        'endIndex': 13,
                    },
                    {
                        'paragraph': {
                            'elements': [{'textRun': {'content': 'Some body text.\n'}}],
                            'paragraphStyle': {'namedStyleType': 'NORMAL_TEXT'},
                        },
                        'startIndex': 13,
                        'endIndex': 29,
                    },
                ]
            }
        }

        result = doc_read('test-doc-id')
        assert result['ok'] is True
        assert result['title'] == 'Test Doc'
        assert result['revisionId'] == 'rev123'
        assert len(result['paragraphs']) == 2
        assert result['paragraphs'][0]['text'] == 'Hello World\n'
        assert result['paragraphs'][0]['style'] == 'HEADING_1'
        assert 'Hello World' in result['text']
        assert result['wordCount'] >= 2


class TestSheetRead:
    """Test sheet reading with mocked Google API."""

    @patch('scripts.google_api.get_credentials')
    @patch('scripts.google_api.build')
    def test_sheet_read_returns_values(self, mock_build, mock_creds):
        from scripts.google_api import sheet_read

        mock_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.return_value = {
            'range': 'Sheet1!A1:B2',
            'values': [['Name', 'Age'], ['Alice', '30']],
        }

        result = sheet_read('test-sheet-id', 'A1:B2')
        assert result['ok'] is True
        assert result['values'] == [['Name', 'Age'], ['Alice', '30']]
        assert result['rows'] == 2
        assert result['cols'] == 2


class TestDocWrite:
    """Test doc writing with mocked Google API."""

    @patch('scripts.google_api.get_credentials')
    @patch('scripts.google_api.build')
    def test_doc_write_sends_operations(self, mock_build, mock_creds):
        from scripts.google_api import doc_write

        mock_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.documents().batchUpdate().execute.return_value = {
            'replies': [{}],
            'writeControl': {'requiredRevisionId': 'rev456'},
        }

        ops = [{'insertText': {'location': {'index': 1}, 'text': 'New text\n'}}]
        result = doc_write('test-doc-id', json.dumps(ops))
        assert result['ok'] is True
        assert result['documentId'] == 'test-doc-id'


class TestSheetWrite:
    """Test sheet writing with mocked Google API."""

    @patch('scripts.google_api.get_credentials')
    @patch('scripts.google_api.build')
    def test_sheet_write_sends_values(self, mock_build, mock_creds):
        from scripts.google_api import sheet_write

        mock_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.spreadsheets().values().update().execute.return_value = {
            'updatedRange': 'Sheet1!A1:B2',
            'updatedRows': 2,
            'updatedColumns': 2,
            'updatedCells': 4,
        }

        values = [['X', 'Y'], [1, 2]]
        result = sheet_write('test-sheet-id', 'A1:B2', json.dumps(values))
        assert result['ok'] is True
        assert result['updatedCells'] == 4
