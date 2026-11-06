import re
import json
import os
import urllib.request
from pathlib import Path

USER = 'IsabellyTubys'
PATH = Path('assets/estatisticas.svg')
TOKEN = os.environ.get('GH_TOKEN', '')


def fetch(url, accept='application/vnd.github+json'):
    headers = {'User-Agent': 'IsabellyTubys-profile-stats', 'Accept': accept}
    if TOKEN:
        headers['Authorization'] = f'Bearer {TOKEN}'
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as response:
        return response.read().decode('utf-8')


profile = json.loads(fetch(f'https://api.github.com/users/{USER}'))
repos = profile['public_repos']
followers = profile['followers']

# GitHub GraphQL provides the same contribution-calendar total shown on the profile.
# If the token cannot access it, display a dash rather than an invented zero.
contributions = '—'
try:
    query = {'query': 'query($login:String!) { user(login:$login) { contributionsCollection { contributionCalendar { totalContributions } } } }', 'variables': {'login': USER}}
    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps(query).encode('utf-8'),
        headers={'User-Agent': 'IsabellyTubys-profile-stats', 'Content-Type': 'application/json', 'Authorization': f'Bearer {TOKEN}'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        result = json.load(response)
    contributions = str(result['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions'])
except Exception as exc:
    print(f'Contribution count unavailable: {exc}')

svg = PATH.read_text(encoding='utf-8')
start = '<!-- AUTO-STATS-START -->'
end = '<!-- AUTO-STATS-END -->'
block = f'''{start}
<g font-family="monospace" font-size="20">
<text x="518" y="171" fill="#FFFFFF">Contribuições: <tspan fill="#82D9FF" font-weight="bold">{contributions}</tspan></text>
<text x="518" y="210" fill="#FFFFFF">Repositórios: <tspan fill="#FFAD66" font-weight="bold">{repos}</tspan></text>
<text x="518" y="249" fill="#FFFFFF">Seguidores: <tspan fill="#82D9FF" font-weight="bold">{followers}</tspan></text>
</g>
{end}'''
if start in svg and end in svg:
    svg = svg[:svg.index(start)] + block + svg[svg.index(end) + len(end):]
else:
    # Replace only the existing three static text lines in the right panel.
    pattern = r'<text x="518" y="169"[^>]*>.*?</text><text x="518" y="201"[^>]*>.*?</text><text x="518" y="244"[^>]*>.*?</text>'
    svg, count = re.subn(pattern, block, svg, count=1)
    if count != 1:
        raise RuntimeError('Could not locate original stats labels; no changes saved')
svg = svg.replace('Pronta para conectar métricas automáticas', 'Métricas atualizadas automaticamente')
PATH.write_text(svg, encoding='utf-8')
print(f'Updated: contributions={contributions}, repos={repos}, followers={followers}')
