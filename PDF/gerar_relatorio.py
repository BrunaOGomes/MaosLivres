"""
CitizenTech - MAOS LIVRES: gerador do relatorio final
======================================================
Transforma o RELATORIO_FINAL.md em UM UNICO arquivo HTML autocontido, com os
graficos embutidos dentro do proprio arquivo (base64). Isso resolve dois
problemas de entrega:

  1. e um arquivo so: nao tem como esquecer de anexar as imagens;
  2. abre em qualquer navegador e vira PDF com Ctrl+P -> "Salvar como PDF".

As figuras sao inseridas automaticamente nos pontos onde o Markdown tem uma
linha comecando com "*Figura N - `caminho`". Se o grafico ainda nao existir,
entra um aviso visivel no lugar, em vez de uma imagem quebrada.

Como rodar:
    venv\\Scripts\\python.exe gerar_relatorio.py

Depois: abra RELATORIO_FINAL.html, confira, e use Ctrl+P -> Salvar como PDF.
"""

import base64
import csv
import re
from datetime import datetime
from pathlib import Path

import markdown

AQUI = Path(__file__).resolve().parent      # pasta PDF/
RAIZ = AQUI.parent                          # raiz do projeto


def achar(relativo) -> Path:
    """Procura o arquivo na pasta do script e depois na raiz do projeto.
    Assim o script funciona rodando de dentro de PDF/ ou da raiz."""
    for base in (AQUI, RAIZ):
        caminho = base / relativo
        if caminho.exists():
            return caminho
    return AQUI / relativo


ENTRADA = achar("RELATORIO_FINAL.md")
SAIDA = AQUI / "RELATORIO_FINAL.html"

CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body {
  font-family: "Segoe UI", Calibri, Arial, sans-serif;
  font-size: 10.8pt; line-height: 1.55; color: #1a1a1a;
  max-width: 900px; margin: 0 auto; padding: 28px 24px 60px;
}
h1 { font-size: 22pt; color: #10365c; margin: 0 0 4px; line-height: 1.2; }
h2 {
  font-size: 15pt; color: #10365c; margin: 30px 0 10px;
  border-bottom: 2px solid #d6e2ef; padding-bottom: 5px; page-break-after: avoid;
}
h3 { font-size: 12.5pt; color: #1d5a8f; margin: 20px 0 7px; page-break-after: avoid; }
h4 { font-size: 11pt; color: #2b2b2b; margin: 15px 0 6px; page-break-after: avoid; }
p { margin: 8px 0; text-align: justify; }
table {
  border-collapse: collapse; width: 100%; margin: 12px 0 16px;
  font-size: 9.6pt; page-break-inside: avoid;
}
th {
  background: #10365c; color: #fff; text-align: left;
  padding: 7px 9px; font-weight: 600;
}
td { padding: 6px 9px; border-bottom: 1px solid #e3e9ef; vertical-align: top; }
tr:nth-child(even) td { background: #f7f9fc; }
code {
  background: #eef2f7; padding: 1px 5px; border-radius: 3px;
  font-family: Consolas, "Courier New", monospace; font-size: 9.3pt; color: #0b3d62;
}
pre {
  background: #f5f7fa; border: 1px solid #dde4ec; border-left: 4px solid #10365c;
  padding: 11px 13px; overflow-x: auto; page-break-inside: avoid; border-radius: 3px;
}
pre code { background: none; padding: 0; font-size: 9pt; color: #1a1a1a; }
blockquote {
  border-left: 4px solid #2d7dd2; background: #f2f7fc;
  margin: 14px 0; padding: 10px 16px; font-style: italic;
}
hr { border: none; border-top: 1px solid #dde4ec; margin: 26px 0; }
ul, ol { margin: 8px 0 8px 22px; }
li { margin: 4px 0; }
strong { color: #0b2d4d; }
figure {
  margin: 18px 0; text-align: center; page-break-inside: avoid;
  background: #fbfcfd; border: 1px solid #e3e9ef; border-radius: 4px; padding: 12px;
}
figure img { max-width: 100%; height: auto; }
figcaption {
  font-size: 9pt; color: #4a5a6a; margin-top: 8px;
  font-style: italic; text-align: center;
}
.faltando {
  border: 2px dashed #e07a5f; background: #fdf3f0; color: #a33b1e;
  padding: 14px; border-radius: 4px; font-size: 9.5pt; text-align: left;
}
.rodape {
  margin-top: 40px; padding-top: 12px; border-top: 1px solid #dde4ec;
  font-size: 8.6pt; color: #6b7a89; text-align: center;
}
@media print { body { padding: 0; } .naoimprimir { display: none; } }
.naoimprimir {
  background: #fff8e1; border: 1px solid #f0c36d; border-radius: 4px;
  padding: 12px 16px; margin-bottom: 24px; font-size: 9.6pt;
}
"""

# Reconhece: *Figura 1 - `resultados/arquivo.png`: legenda.*
PADRAO_FIGURA = re.compile(
    r"^\*(Figura\s+\d+)\s*[—–-]\s*`([^`]+)`\s*:?\s*(.*?)\*\s*$",
    re.MULTILINE,
)


def imagem_base64(caminho: Path) -> str:
    """Le a imagem e devolve o conteudo como data URI, para embutir no HTML."""
    dados = base64.b64encode(caminho.read_bytes()).decode("ascii")
    tipo = "jpeg" if caminho.suffix.lower() in (".jpg", ".jpeg") else "png"
    return f"data:image/{tipo};base64,{dados}"


CSV_GESTOS = achar("resultados/metricas_gestos_resumo.csv")
MARCADOR_GESTOS = "<!-- TABELA_METRICAS_GESTOS -->"

# Como cada chave do CSV aparece no relatorio: (chave, rotulo, casas decimais)
ROTULOS_GESTOS = [
    ("ear_a_repouso", "EAR de repouso, olho esquerdo da tela", 4),
    ("ear_b_repouso", "EAR de repouso, olho direito da tela", 4),
    ("ear_a_limiar", "Limiar de olho fechado, esquerdo (70% do repouso)", 4),
    ("ear_b_limiar", "Limiar de olho fechado, direito (70% do repouso)", 4),
    ("sobr_repouso", "Coeficiente de sobrancelha em repouso", 4),
    ("sobr_limiar", "Limiar de sobrancelha (repouso + 0,35)", 4),
    ("beijo_repouso", "`mouthPucker` em repouso", 4),
    ("beijo_limiar", "Limiar de beijinho (repouso + 0,45)", 4),
    ("nariz_centro_x", "Centro calibrado do nariz, eixo X", 4),
    ("nariz_centro_y", "Centro calibrado do nariz, eixo Y", 4),
    ("quadros_analisados", "Quadros analisados", 0),
]


def tabela_metricas_gestos():
    """Monta a tabela da secao 3.3 a partir do CSV gerado pelo metricas_gestos.py.
    Devolve (markdown_da_tabela, encontrou_dados)."""
    if not CSV_GESTOS.exists():
        return (
            "> **Tabela ainda nao gerada.** Rode `venv\\Scripts\\python.exe "
            "metricas_gestos.py` e depois `venv\\Scripts\\python.exe gerar_relatorio.py`.",
            False,
        )

    valores, grupos = {}, {}
    with open(CSV_GESTOS, encoding="utf-8-sig") as f:
        for linha in csv.reader(f):
            if len(linha) == 2 and linha[0] and linha[1]:
                valores[linha[0]] = linha[1]
            # linhas de grupo: nome, n, media, mediana, desvio, min, max
            elif len(linha) == 7 and linha[0] not in ("grupo", ""):
                grupos[linha[0]] = linha

    linhas = ["| Métrica | Valor medido |", "|---|---|"]
    for chave, rotulo, casas in ROTULOS_GESTOS:
        if chave in valores:
            try:
                v = float(valores[chave])
                txt = f"{v:.{casas}f}" if casas else f"{int(v)}"
            except ValueError:
                txt = valores[chave]
            linhas.append(f"| {rotulo} | {txt} |")

    # EAR medio com olho fechado, e quanto isso representa do repouso
    fechado = grupos.get("EAR A (olho fechado)")
    aberto = grupos.get("EAR A (olho aberto)")
    repouso = valores.get("ear_a_repouso")
    if fechado and repouso and float(fechado[1]) > 0:
        pct = 100 * float(fechado[2]) / float(repouso)
        linhas.append(f"| EAR médio com o olho fechado | {float(fechado[2]):.4f} "
                      f"({pct:.0f}% do repouso) |")
    if aberto and repouso and float(aberto[1]) > 0:
        pct = 100 * float(aberto[2]) / float(repouso)
        linhas.append(f"| EAR médio com o olho aberto | {float(aberto[2]):.4f} "
                      f"({pct:.0f}% do repouso) |")

    sobr_ativa = grupos.get("sobrancelha (ativa)")
    if sobr_ativa and float(sobr_ativa[1]) > 0:
        linhas.append(f"| Sobrancelha, média quando o gesto está ativo | {float(sobr_ativa[2]):.4f} |")
    sobr_todos = grupos.get("sobrancelha (todos)")
    if sobr_todos:
        linhas.append(f"| Sobrancelha, pico observado | {float(sobr_todos[6]):.4f} |")

    beijo_ativo = grupos.get("beijo (ativo)")
    if beijo_ativo and float(beijo_ativo[1]) > 0:
        linhas.append(f"| Beijinho, média quando o gesto está ativo | {float(beijo_ativo[2]):.4f} |")
    beijo_todos = grupos.get("beijo (todos)")
    if beijo_todos:
        linhas.append(f"| Beijinho, pico observado | {float(beijo_todos[6]):.4f} |")

    for chave, rotulo in (("% quadros olho A fechado", "Quadros com o olho esquerdo fechado"),
                          ("% quadros sobrancelha ativa", "Quadros com sobrancelha ativa"),
                          ("% quadros beijo ativo", "Quadros com beijinho ativo")):
        if chave in valores:
            linhas.append(f"| {rotulo} | {valores[chave]}% |")

    return "\n".join(linhas), True


def main():
    if not ENTRADA.exists():
        print(f"Nao achei o {ENTRADA}.")
        return

    texto = ENTRADA.read_text(encoding="utf-8")

    tabela, tem_gestos = tabela_metricas_gestos()
    texto = texto.replace(MARCADOR_GESTOS, tabela)
    embutidas, faltando = [], []

    def trocar(m):
        rotulo, caminho, legenda = m.group(1), m.group(2).strip(), m.group(3).strip()
        arquivo = achar(caminho)
        if arquivo.exists():
            embutidas.append(caminho)
            return (f'<figure><img src="{imagem_base64(arquivo)}" alt="{rotulo}">'
                    f'<figcaption><strong>{rotulo}</strong> — {legenda}</figcaption></figure>')
        faltando.append(caminho)
        return (f'<figure><div class="faltando"><strong>{rotulo} ainda nao gerada.</strong><br>'
                f'Arquivo esperado: <code>{caminho}</code><br>'
                f'Rode o script correspondente e gere o relatorio de novo.</div>'
                f'<figcaption><strong>{rotulo}</strong> — {legenda}</figcaption></figure>')

    corpo_md = PADRAO_FIGURA.sub(trocar, texto)

    corpo = markdown.markdown(
        corpo_md,
        extensions=["tables", "fenced_code", "sane_lists", "md_in_html"],
    )

    agora = datetime.now().strftime("%d/%m/%Y as %H:%M")
    aviso = ""
    if faltando:
        itens = "".join(f"<li><code>{c}</code></li>" for c in faltando)
        aviso = ('<div class="naoimprimir"><strong>Antes de gerar o PDF:</strong> '
                 f'{len(faltando)} figura(s) ainda nao existe(m):<ul>{itens}</ul>'
                 'Este aviso nao aparece na impressao, mas os espacos das figuras sim.</div>')

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>MaosLivres - Relatorio | Global Solution FIAP 2026.2</title>
<style>{CSS}</style>
</head>
<body>
{aviso}
{corpo}
<div class="rodape">
MaosLivres — CitizenTech | Global Solution FIAP 2026.2<br>
Documento gerado automaticamente a partir de RELATORIO_FINAL.md em {agora}
</div>
</body>
</html>
"""
    SAIDA.write_text(html, encoding="utf-8")

    print("=" * 62)
    print("RELATORIO GERADO")
    print("=" * 62)
    print(f"Arquivo .......... {SAIDA.resolve()}")
    print(f"Tamanho .......... {SAIDA.stat().st_size / 1024:.0f} KB")
    print(f"Tabela 3.3 ....... {'preenchida com os dados medidos' if tem_gestos else 'VAZIA (rode metricas_gestos.py)'}")
    print(f"Figuras embutidas  {len(embutidas)}")
    for c in embutidas:
        print(f"  OK   {c}")
    if faltando:
        print(f"Figuras faltando   {len(faltando)}")
        for c in faltando:
            print(f"  FALTA {c}")
        print()
        print("Para completar:")
        if any("metricas" in c or "ear" in c or "blendshape" in c or "nariz" in c for c in faltando):
            print("  venv\\Scripts\\python.exe metricas_gestos.py")
        if any("desempenho" in c or "latencia" in c or "fps" in c or "etapas" in c for c in faltando):
            print("  venv\\Scripts\\python.exe benchmark_desempenho.py")
        if any("acerto" in c or "tempo_alvo" in c or "participante" in c for c in faltando):
            print("  venv\\Scripts\\python.exe analise_resultados.py")
    print()
    print("Para virar PDF: abra o HTML no navegador, Ctrl+P, 'Salvar como PDF'.")
    print("Marque 'Graficos de fundo' nas opcoes, para as tabelas sairem coloridas.")


if __name__ == "__main__":
    main()
