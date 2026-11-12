"""
CitizenTech - MAOS LIVRES: analise dos resultados de validacao
===============================================================
Le o resultados_validacao.csv (gerado pelo teste_validacao.py) e produz os
indicadores de desempenho e os graficos que entram no relatorio.

Indicadores calculados:
  - taxa de acerto (%)      : acertos / total de cliques
  - tempo medio por alvo (s): quanto a pessoa leva para acertar cada alvo
  - desvio padrao           : o quanto os participantes variaram entre si
  - custo relativo          : quantas vezes o modo rosto e mais lento que o mouse

Por que comparar com o mouse: o mouse NAO e a meta, e a REFERENCIA. Para quem
nao pode usar o mouse, o que importa e o controle por rosto ser possivel e
preciso. A comparacao serve para dimensionar o custo de interacao.

Saidas (pasta resultados/):
  - grafico_taxa_acerto.png     : taxa de acerto por modo
  - grafico_tempo_alvo.png      : tempo medio por alvo, por modo
  - grafico_por_participante.png: comparacao rosto x mouse por participante
  - validacao_resumo.csv        : a tabela de indicadores para o relatorio

Como rodar (depois de coletar os dados com o validar.bat):
    venv\\Scripts\\python.exe analise_resultados.py
"""

import csv
from pathlib import Path
from statistics import mean, pstdev

import matplotlib

matplotlib.use("Agg")          # salva em arquivo, sem abrir janela
import matplotlib.pyplot as plt

ARQUIVO_CSV = Path("resultados_validacao.csv")
SAIDA = Path("resultados")

CORES = {"rosto": "#2d7dd2", "mouse": "#adb5bd"}


def carregar():
    """Le o CSV e converte os campos numericos. Devolve lista de dicionarios."""
    if not ARQUIVO_CSV.exists():
        return []
    linhas = []
    # utf-8-sig remove o BOM, caso o CSV tenha sido aberto e salvo no Excel ou
    # no PowerShell: sem isso, a primeira coluna viria com um caractere invisivel
    # no nome e o cabecalho "data" nao seria reconhecido.
    with open(ARQUIVO_CSV, encoding="utf-8-sig") as f:
        for linha in csv.DictReader(f):
            try:
                linhas.append({
                    "data": linha["data"],
                    # normaliza o nome: "Ana", "ana " e "ANA" sao a MESMA pessoa.
                    # Sem isso, uma diferenca de maiuscula contaria dois participantes
                    # e inflaria o N da amostra no relatorio.
                    "participante": linha["participante"].strip().lower(),
                    "modo": linha["modo"].strip().lower(),
                    "alvos": int(linha["alvos"]),
                    "acertos": int(linha["acertos"]),
                    "erros": int(linha["erros"]),
                    "taxa": float(linha["taxa_acerto_%"]),
                    "tempo_medio": float(linha["tempo_medio_s"]),
                    "tempo_total": float(linha["tempo_total_s"]),
                })
            except (KeyError, ValueError) as erro:
                print(f"  (linha ignorada, formato inesperado: {erro})")
    return linhas


def resumo_por_modo(dados):
    """Agrupa por modo (rosto / mouse) e calcula os indicadores."""
    modos = {}
    for modo in ("rosto", "mouse"):
        grupo = [d for d in dados if d["modo"] == modo]
        if not grupo:
            continue
        taxas = [d["taxa"] for d in grupo]
        tempos = [d["tempo_medio"] for d in grupo]
        modos[modo] = {
            "rodadas": len(grupo),
            "participantes": len({d["participante"] for d in grupo}),
            "taxa_media": mean(taxas),
            # pstdev exige 2+ amostras; com 1 rodada o desvio e 0 por definicao
            "taxa_desvio": pstdev(taxas) if len(taxas) > 1 else 0.0,
            "tempo_medio": mean(tempos),
            "tempo_desvio": pstdev(tempos) if len(tempos) > 1 else 0.0,
            "acertos": sum(d["acertos"] for d in grupo),
            "erros": sum(d["erros"] for d in grupo),
        }
    return modos


def grafico_barras(modos, campo, desvio, titulo, rotulo_y, arquivo, formato="{:.1f}"):
    """Grafico de barras por modo, com barra de erro (desvio padrao)."""
    nomes = list(modos.keys())
    valores = [modos[m][campo] for m in nomes]
    erros = [modos[m][desvio] for m in nomes]
    plt.figure(figsize=(6, 4.5))
    barras = plt.bar(nomes, valores, yerr=erros, capsize=8,
                     color=[CORES.get(n, "#888") for n in nomes], width=0.55)
    for barra, valor in zip(barras, valores):
        plt.text(barra.get_x() + barra.get_width() / 2,
                 barra.get_height(), formato.format(valor),
                 ha="center", va="bottom", fontweight="bold")
    plt.ylabel(rotulo_y)
    plt.title(titulo)
    plt.ylim(0, max(v + e for v, e in zip(valores, erros)) * 1.25)
    plt.tight_layout()
    plt.savefig(SAIDA / arquivo, dpi=150)
    plt.close()


def grafico_participantes(dados):
    """Barras agrupadas: cada participante com seu tempo nos dois modos."""
    nomes = sorted({d["participante"] for d in dados})
    if not nomes:
        return
    rosto, mouse = [], []
    for nome in nomes:
        r = [d["tempo_medio"] for d in dados if d["participante"] == nome and d["modo"] == "rosto"]
        m = [d["tempo_medio"] for d in dados if d["participante"] == nome and d["modo"] == "mouse"]
        rosto.append(mean(r) if r else 0.0)
        mouse.append(mean(m) if m else 0.0)

    x = range(len(nomes))
    largura = 0.38
    plt.figure(figsize=(max(6, 1.4 * len(nomes)), 4.5))
    plt.bar([i - largura / 2 for i in x], rosto, largura,
            label="rosto", color=CORES["rosto"])
    plt.bar([i + largura / 2 for i in x], mouse, largura,
            label="mouse", color=CORES["mouse"])
    plt.xticks(list(x), nomes, rotation=20, ha="right")
    plt.ylabel("Tempo medio por alvo (s)")
    plt.title("MaosLivres - tempo por alvo, participante a participante")
    plt.legend()
    plt.tight_layout()
    plt.savefig(SAIDA / "grafico_por_participante.png", dpi=150)
    plt.close()


def main():
    SAIDA.mkdir(exist_ok=True)
    dados = carregar()

    if not dados:
        print("=" * 64)
        print("Nenhum dado encontrado.")
        print("=" * 64)
        print(f"O arquivo {ARQUIVO_CSV} nao existe ou esta vazio.")
        print()
        print("Para gerar os dados:")
        print("  1. rode o iniciar.bat numa janela (controle por rosto);")
        print("  2. rode o validar.bat em outra janela;")
        print("  3. faca o teste no modo 'rosto' e depois no modo 'mouse';")
        print("  4. repita com 3 a 5 pessoas;")
        print("  5. rode este script de novo.")
        print()
        print("IMPORTANTE: nao invente numeros. O relatorio precisa dos dados reais.")
        return

    modos = resumo_por_modo(dados)

    # ---------- tabela de indicadores ----------
    arq = SAIDA / "validacao_resumo.csv"
    with open(arq, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["modo", "rodadas", "participantes", "taxa_acerto_media_%",
                    "taxa_desvio", "tempo_medio_por_alvo_s", "tempo_desvio",
                    "acertos_totais", "erros_totais"])
        for modo, m in modos.items():
            w.writerow([modo, m["rodadas"], m["participantes"],
                        f"{m['taxa_media']:.1f}", f"{m['taxa_desvio']:.1f}",
                        f"{m['tempo_medio']:.2f}", f"{m['tempo_desvio']:.2f}",
                        m["acertos"], m["erros"]])

    # ---------- graficos ----------
    grafico_barras(modos, "taxa_media", "taxa_desvio",
                   "MaosLivres - taxa de acerto por modo",
                   "Taxa de acerto (%)", "grafico_taxa_acerto.png", "{:.1f}%")
    grafico_barras(modos, "tempo_medio", "tempo_desvio",
                   "MaosLivres - tempo medio por alvo",
                   "Tempo por alvo (s)", "grafico_tempo_alvo.png", "{:.2f}s")
    grafico_participantes(dados)

    # ---------- resumo na tela ----------
    print("=" * 64)
    print("INDICADORES DE VALIDACAO")
    print("=" * 64)
    print(f"Rodadas registradas: {len(dados)}")
    print()
    print(f"{'modo':<8}{'rodadas':>9}{'pessoas':>9}{'acerto':>10}{'tempo/alvo':>13}")
    for modo, m in modos.items():
        print(f"{modo:<8}{m['rodadas']:>9}{m['participantes']:>9}"
              f"{m['taxa_media']:>9.1f}%{m['tempo_medio']:>11.2f}s")

    if "rosto" in modos and "mouse" in modos:
        r, m = modos["rosto"], modos["mouse"]
        if m["tempo_medio"] > 0:
            print()
            print(f"Custo relativo: o controle por rosto levou "
                  f"{r['tempo_medio'] / m['tempo_medio']:.1f}x o tempo do mouse.")
        print(f"Diferenca de acerto: {r['taxa_media'] - m['taxa_media']:+.1f} "
              f"pontos percentuais em relacao ao mouse.")

    n_pessoas = max((m["participantes"] for m in modos.values()), default=0)
    if n_pessoas < 3:
        print()
        print(f"ATENCAO: so {n_pessoas} participante(s). O enunciado pede analise")
        print("critica: com menos de 3 pessoas nao da para falar de tendencia.")
        print("Declare o N real no relatorio e trate como estudo exploratorio.")

    print()
    print(f"Arquivos gerados em: {SAIDA.resolve()}")
    for a in sorted(SAIDA.glob("*validacao*")) + sorted(SAIDA.glob("grafico_t*")) + sorted(SAIDA.glob("grafico_p*")):
        print(f"  - {a.name}")


if __name__ == "__main__":
    main()
