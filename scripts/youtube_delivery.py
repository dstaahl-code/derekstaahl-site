"""Limited dashboard video delivery. Standard library; no database credentials."""
import json
import os
import re
import uuid
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENDPOINT = 'https://dashboard.derekstaahl.com/.netlify/functions/data-api'
TOKEN = re.compile(r'^genai_agent_([0-9a-f-]{36})\.[A-Za-z0-9_-]{43}$')

class DeliveryError(RuntimeError):
    pass

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def _credential():
    token = os.environ.get('YOUTUBE_AGENT_TOKEN', '')
    match = TOKEN.fullmatch(token)
    if not match or match[1] != os.environ.get('YOUTUBE_AGENT_ID'):
        raise DeliveryError('Set the original YouTube agent ID and token in GitHub Actions secrets/variables.')
    return token, match[1]

def request(operation, params, key=None):
    token, _ = _credential()
    headers = {'Authorization': 'Bearer '+token, 'Content-Type': 'application/json'}
    if key:
        headers['Idempotency-Key'] = key
    body = json.dumps({'requests': [{'id': 'video', 'operation': operation, 'params': params}]}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers=headers, method='POST')
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=20) as response:
            data = json.loads(response.read(256*1024).decode())
    except Exception as exc:
        raise DeliveryError('Dashboard request failed or its response was lost. Resume only the original saved delivery; do not change its request keys.') from exc
    result = data.get('results', {}).get('video', {})
    if data.get('warning') or result.get('warning') or result.get('status') != 'ok':
        raise DeliveryError('Dashboard refused or could not confirm this operation. Review its saved delivery and Change history before retrying.')
    expiry = data.get('tokenExpiresAt')
    if expiry:
        try:
            days = (datetime.fromisoformat(expiry.replace('Z','+00:00'))-datetime.now(timezone.utc)).total_seconds()/86400
            if days < 21:
                print('::warning::YouTube agent token expires within 21 days. Replace it between runs after resolving pending deliveries.')
        except ValueError:
            raise DeliveryError('Invalid token expiry response')
    return result

def _write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
    return path

def validate_fields(fields):
    if not isinstance(fields, dict) or not set(fields) <= {'Title','YouTube ID','Air Date','Description','AZFamily URL'} or not all(k in fields for k in ['Title','YouTube ID','Air Date']):
        raise DeliveryError('Invalid saved video fields')
    if not isinstance(fields['Title'], str) or not fields['Title'].strip() or len(fields['Title']) > 1000 or not isinstance(fields['YouTube ID'], str) or not re.fullmatch(r'[A-Za-z0-9_-]{11}', fields['YouTube ID']):
        raise DeliveryError('Invalid video title or ID')
    try:
        if datetime.strptime(fields['Air Date'], '%Y-%m-%d').strftime('%Y-%m-%d') != fields['Air Date']:
            raise ValueError()
    except (TypeError, ValueError):
        raise DeliveryError('Invalid video air date')
    if 'Description' in fields and (not isinstance(fields['Description'], str) or len(fields['Description']) > 50000):
        raise DeliveryError('Invalid description')
    if 'AZFamily URL' in fields:
        if not isinstance(fields['AZFamily URL'], str) or len(fields['AZFamily URL']) > 4000:
            raise DeliveryError('Invalid article URL')
        url = urllib.parse.urlsplit(fields['AZFamily URL'])
        if url.scheme != 'https' or url.hostname not in ('azfamily.com','www.azfamily.com') or url.username or url.password:
            raise DeliveryError('Invalid article URL')
    encoded = json.dumps({'requests':[{'id':'video','operation':'youtubeVideos.create','params':{'fields':fields,'dry_run':False}}]}).encode()
    if len(encoded) > 32768:
        raise DeliveryError('Video request exceeds the dashboard byte limit')

def prepare(episodes_with_urls, path, run_id, call=request):
    _, agent = _credential()
    listing = call('youtubeVideos.list', {})['data']['records']
    seen = {r['fields'].get('YouTube ID') for r in listing}
    requests = []
    for ep, article in episodes_with_urls:
        video_id = ep['youtubeId']
        if video_id in seen:
            continue
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id):
            raise DeliveryError('Invalid YouTube video ID')
        fields = {'Title': ep['title'], 'YouTube ID': video_id, 'Air Date': ep['date']}
        if ep.get('description'):
            fields['Description'] = ep['description']
        if article:
            fields['AZFamily URL'] = article
        validate_fields(fields)
        requests.append({'key': str(uuid.uuid4()), 'operation': 'youtubeVideos.create', 'params': {'fields': fields, 'dry_run': False}})
        seen.add(video_id)
    if len(requests) > 100:
        raise DeliveryError('Review an unexpectedly large video import before delivery')
    box = {'version': 1, 'agentId': agent, 'runId': str(run_id), 'requests': requests}
    _write(path, box)
    print(f'Prepared {len(requests)} video requests; archive this file before delivery.')
    return box

def load(path, expected_run):
    path = Path(path)
    if path.stat().st_size > 1024*1024:
        raise DeliveryError('Delivery file exceeds limit')
    box = json.loads(path.read_text())
    _, agent = _credential()
    if set(box) != {'version','agentId','runId','requests'} or box['version'] != 1 or box['agentId'] != agent or box['runId'] != str(expected_run):
        raise DeliveryError('Use the original delivery file and original agent identity')
    if not isinstance(box['requests'], list) or len(box['requests']) > 100:
        raise DeliveryError('Invalid delivery request list')
    keys = set()
    for op in box['requests']:
        if set(op) != {'key','operation','params'} or op['operation'] != 'youtubeVideos.create' or uuid.UUID(op['key']).version != 4 or op['key'] in keys:
            raise DeliveryError('Invalid original request key')
        keys.add(op['key'])
        if set(op['params']) != {'fields','dry_run'} or op['params']['dry_run'] is not False:
            raise DeliveryError('Invalid saved video request')
        fields = op['params']['fields']
        validate_fields(fields)
    return box

def deliver(path, expected_run, receipts, call=request):
    box = load(path, expected_run)
    results = []
    for op in box['requests']:
        result = call(op['operation'], op['params'], op['key'])
        if result.get('status') != 'ok' or result.get('warning'):
            raise DeliveryError('Unconfirmed save; stop and review before another operation')
        results.append({'key': op['key'], 'recordId': result['data']['id'], 'unchanged': result.get('unchanged', False)})
    _write(receipts, {'runId': box['runId'], 'agentId': box['agentId'], 'results': results})
    print(f'Confirmed {len(results)} original video requests. No research email or deployment was run.')
    return results
