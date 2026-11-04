"""Gera assets/stats.svg com as estatísticas do perfil, no tema Pompompurin (creme e caramelo).

Roda no GitHub Actions (.github/workflows/stats.yml) uma vez por dia, usando o
GITHUB_TOKEN do próprio workflow. Localmente:

    GITHUB_TOKEN=... python scripts/gerar_stats.py RATZogun
"""
import json
import os
import sys
import urllib.request
from html import escape
from pathlib import Path

CONSULTA = """
query($login: String!) {
  user(login: $login) {
    name
    createdAt
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar { totalContributions }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""

CORES = ["#B5713D", "#E0A458", "#F2C14E", "#8B4A2B", "#D9B46E", "#C99A6B"]


def consultar(login, token):
    corpo = json.dumps({"query": CONSULTA, "variables": {"login": login}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=corpo, headers={
        "Authorization": f"bearer {token}", "Content-Type": "application/json",
        "User-Agent": "gerar-stats"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        dados = json.load(resp)
    if "errors" in dados:
        raise SystemExit(f"Erro da API: {dados['errors']}")
    return dados["data"]["user"]


def linguagens(repos, limite=6):
    total = {}
    for repo in repos:
        for aresta in repo["languages"]["edges"]:
            nome = aresta["node"]["name"]
            total[nome] = total.get(nome, 0) + aresta["size"]
    soma = sum(total.values()) or 1
    ordenadas = sorted(total.items(), key=lambda kv: -kv[1])[:limite]
    return [(nome, 100 * tam / soma) for nome, tam in ordenadas]


def pudim(x, y, escala=1.0):
    return (f'<g transform="translate({x} {y}) scale({escala})">'
            '<ellipse cx="0" cy="22" rx="34" ry="7" fill="#FFFFFF" stroke="#5A3328" stroke-width="3"/>'
            '<path d="M-24 20 L-18 -10 Q0 -16 18 -10 L24 20 Z" fill="#FCE38A" stroke="#5A3328" '
            'stroke-width="3" stroke-linejoin="round"/>'
            '<path d="M-18 -10 Q0 -16 18 -10 L19.5 -2 Q12 6 6 -1 Q0 7 -6 -1 Q-12 6 -19.5 -2 Z" '
            'fill="#B5713D" stroke="#5A3328" stroke-width="3" stroke-linejoin="round"/>'
            '<circle cx="0" cy="-17" r="5" fill="#E2483D" stroke="#5A3328" stroke-width="2.5"/></g>')


def coracao(x, y, cor):
    return (f'<path transform="translate({x} {y}) scale(.75)" fill="{cor}" '
            'd="M0 7 C-10 -3 -13 -10 -7 -14 C-3 -16 0 -13 0 -10 C0 -13 3 -16 7 -14 C13 -10 10 -3 0 7Z"/>')


def gerar_svg(u):
    cc = u["contributionsCollection"]
    repos = u["repositories"]["nodes"]
    itens = [
        ("Contribuições no último ano", cc["contributionCalendar"]["totalContributions"]),
        ("Commits no último ano", cc["totalCommitContributions"]),
        ("Pull requests", cc["totalPullRequestContributions"]),
        ("Issues", cc["totalIssueContributions"]),
        ("Repositórios públicos", u["repositories"]["totalCount"]),
        ("Estrelas recebidas", sum(r["stargazerCount"] for r in repos)),
    ]
    langs = linguagens(repos)

    linhas = []
    for i, (rotulo, valor) in enumerate(itens):
        y = 92 + i * 32
        linhas.append(
            f'{coracao(42, y - 5, CORES[i % len(CORES)])}'
            f'<text x="60" y="{y}" class="rotulo">{escape(rotulo)}</text>'
            f'<text x="380" y="{y}" class="valor" text-anchor="end">{valor}</text>')

    barra, legenda, x = [], [], 430
    largura_total = 410
    for i, (nome, pct) in enumerate(langs):
        w = largura_total * pct / 100
        barra.append(f'<rect x="{x:.1f}" y="84" width="{max(w, 2):.1f}" height="14" fill="{CORES[i % len(CORES)]}"/>')
        x += w
        coluna, linha = i % 2, i // 2
        lx, ly = 430 + coluna * 210, 132 + linha * 34
        legenda.append(
            f'<circle cx="{lx + 7}" cy="{ly - 5}" r="7" fill="{CORES[i % len(CORES)]}"/>'
            f'<text x="{lx + 22}" y="{ly}" class="rotulo">{escape(nome)} '
            f'<tspan class="pct">{pct:.1f}%</tspan></text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 300" width="880" height="300" role="img" aria-label="Estatísticas do GitHub de {escape(u["name"] or "")}">
  <style>
    text {{ font-family: 'Segoe UI', 'Trebuchet MS', 'Helvetica Neue', Arial, sans-serif; }}
    .titulo {{ font-size: 21px; font-weight: 800; fill: #5A3328; }}
    .rotulo {{ font-size: 15px; fill: #6B4226; }}
    .valor {{ font-size: 16px; font-weight: 800; fill: #A0602E; }}
    .pct {{ fill: #A0602E; font-weight: 600; }}
    .nota {{ font-size: 11px; fill: #8B6A4A; }}
  </style>
  <defs>
    <pattern id="bolinhas" width="26" height="26" patternUnits="userSpaceOnUse">
      <circle cx="5" cy="5" r="2.2" fill="#FFFFFF" opacity=".7"/>
    </pattern>
    <clipPath id="arredonda"><rect x="430" y="84" width="410" height="14" rx="7"/></clipPath>
  </defs>
  <rect x="1" y="1" width="878" height="298" rx="20" fill="#FFF9DC" stroke="#E8C97A" stroke-width="2"/>
  <rect x="1" y="1" width="878" height="298" rx="20" fill="url(#bolinhas)"/>
  <line x1="405" y1="40" x2="405" y2="270" stroke="#E8C97A" stroke-width="2" stroke-dasharray="1 8" stroke-linecap="round"/>
  {pudim(52, 38, .55)}
  <text x="76" y="47" class="titulo">Estatísticas no GitHub</text>
  {pudim(452, 38, .55)}
  <text x="476" y="47" class="titulo">Linguagens mais usadas</text>
  {''.join(linhas)}
  <rect x="430" y="84" width="410" height="14" rx="7" fill="#F6E7B8"/>
  <g clip-path="url(#arredonda)">{''.join(barra)}</g>
  {''.join(legenda)}
  <text x="846" y="282" class="nota" text-anchor="end">atualizado diariamente pelo GitHub Actions</text>
</svg>
'''


def main():
    login = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_REPOSITORY_OWNER", "RATZogun")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Defina GITHUB_TOKEN.")
    destino = Path(__file__).resolve().parent.parent / "assets" / "stats.svg"
    destino.write_text(gerar_svg(consultar(login, token)), encoding="utf-8")
    print(f"Gerado {destino}")


if __name__ == "__main__":
    main()
