"""Command helpers for querying workspace addons from the terminal."""

import json
import urllib.request
import urllib.error


def query_workspace(command, params=None, timeout=2.0, port=3000):
    """Send a command to the workspace addon and wait for a response.

    Args:
        command: Command name (e.g. 'get-selection', 'get-content')
        params: Optional dict of parameters
        timeout: Timeout in seconds
        port: Server port (default 3000)

    Returns:
        Response data dict from the workspace addon
    """
    body = json.dumps({
        'command': command,
        'params': params or {},
        'timeout': int(timeout * 1000),
    }).encode('utf-8')

    req = urllib.request.Request(
        f'http://localhost:{port}/api/workspace/command',
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout + 1) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result.get('data', result)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        raise RuntimeError(f'Command failed ({e.code}): {error_body}')
    except urllib.error.URLError as e:
        raise RuntimeError(f'Cannot reach server: {e.reason}')
