"""
CitizenTech - TESTE DE VALIDAÇÃO
================================
O enunciado da GS pede para "validar as principais hipóteses" e "medir o impacto".
Este script mede, com números, o quanto o controle sem toque funciona:

  - aparece UM alvo (círculo verde) por vez em posição aleatória;
  - a pessoa tem que clicar no alvo (usando o controle_sem_toque.py, só com a cabeça e os olhos);
  - o script mede o tempo até cada acerto e conta os cliques errados.

Como usar:
  1) Terminal 1: python controle_sem_toque.py   (deixe rodando)
  2) Terminal 2: python teste_validacao.py
  3) Faça o teste com o controle por rosto e, para comparar, com o mouse comum.
  Os resultados ficam no arquivo resultados_validacao.csv -> viram gráfico/slide.

Usa o EVENTO DE MOUSE do OpenCV (Lab11): cada clique chama a função mouse_click().
"""

import csv
import random
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

# ------------------ configurações ------------------
N_ALVOS = 8                    # quantos alvos por rodada
RAIO = 45                      # raio do alvo em pixels
LARGURA, ALTURA = 860, 500     # tamanho da janela de teste
ARQUIVO_CSV = Path("resultados_validacao.csv")
JANELA = "Teste de validacao"


class Teste:
    """Guarda o estado do teste e decide o que cada clique significa."""

    def __init__(self, n_alvos=N_ALVOS):
        """Prepara uma rodada: zera os contadores e sorteia o primeiro alvo."""
        self.n_alvos = n_alvos
        self.acertos = 0
        self.erros = 0
        self.tempos = []                 # tempo (s) de cada acerto
        self.alvo = None
        self.inicio_alvo = None
        self.inicio_total = None
        self.terminou = False
        self.novo_alvo(time.perf_counter())

    def novo_alvo(self, agora):
        """Sorteia a posição do próximo alvo, a pelo menos 200 pixels do anterior.
        A distância mínima evita que dois alvos saiam quase no mesmo lugar, o que
        deixaria o tempo medido artificialmente curto."""
        anterior = self.alvo
        while True:                      # sorteia posição longe do alvo anterior
            x = random.randint(RAIO + 10, LARGURA - RAIO - 10)
            y = random.randint(RAIO + 60, ALTURA - RAIO - 10)
            if anterior is None or np.hypot(x - anterior[0], y - anterior[1]) > 200:
                break
        self.alvo = (x, y)
        self.inicio_alvo = agora
        if self.inicio_total is None:
            self.inicio_total = agora

    def clicar(self, x, y, agora):
        """Chamado a cada clique. Acertou o alvo? Errou?"""
        if self.terminou:
            return
        distancia = np.hypot(x - self.alvo[0], y - self.alvo[1])
        if distancia <= RAIO:
            self.acertos += 1
            self.tempos.append(agora - self.inicio_alvo)
            if self.acertos >= self.n_alvos:
                self.terminou = True
                self.fim_total = agora
            else:
                self.novo_alvo(agora)
        else:
            self.erros += 1

    def taxa_acerto(self):
        """Porcentagem de cliques que acertaram o alvo: acertos / total de cliques."""
        total = self.acertos + self.erros
        return 100.0 * self.acertos / total if total else 0.0

    def tempo_medio(self):
        """Média de segundos que a pessoa levou para acertar cada alvo."""
        return float(np.mean(self.tempos)) if self.tempos else 0.0


teste = None   # criado em main()


def mouse_click(event, x, y, flags, param):
    """Callback do Lab11: só nos interessa o clique esquerdo."""
    if event == cv2.EVENT_LBUTTONDOWN and teste is not None:
        teste.clicar(x, y, time.perf_counter())


def desenhar(t):
    """Monta a imagem da janela de teste e devolve pronta para o cv2.imshow.
    Durante a rodada: o alvo verde e o painel com alvo atual, erros e tempo.
    Ao terminar: o resumo com acertos, taxa de acerto e tempos."""
    tela = np.full((ALTURA, LARGURA, 3), 30, dtype="uint8")
    if not t.terminou:
        cv2.circle(tela, t.alvo, RAIO, (0, 200, 0), -1)
        cv2.circle(tela, t.alvo, RAIO, (255, 255, 255), 2)
        cv2.circle(tela, t.alvo, 6, (255, 255, 255), -1)
        decorrido = time.perf_counter() - t.inicio_total
        cv2.putText(tela, f"Alvo {t.acertos + 1}/{t.n_alvos}   Erros: {t.erros}   Tempo: {decorrido:4.1f}s",
                    (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    else:
        total = t.fim_total - t.inicio_total
        linhas = [
            "TESTE CONCLUIDO!",
            f"Acertos: {t.acertos}   Erros: {t.erros}",
            f"Taxa de acerto: {t.taxa_acerto():.0f}%",
            f"Tempo medio por alvo: {t.tempo_medio():.1f} s",
            f"Tempo total: {total:.1f} s",
            "Pressione ESC para salvar e sair",
        ]
        for i, linha in enumerate(linhas):
            cv2.putText(tela, linha, (60, 110 + i * 55), cv2.FONT_HERSHEY_SIMPLEX,
                        1.0 if i == 0 else 0.85, (0, 255, 255) if i == 0 else (255, 255, 255), 2)
    return tela


def salvar_csv(t, participante, modo):
    """Acrescenta uma linha de resultado ao resultados_validacao.csv.
    Abre em modo 'a' (append) para não apagar as rodadas anteriores, e escreve
    o cabeçalho só se o arquivo ainda não existir."""
    novo = not ARQUIVO_CSV.exists()
    with open(ARQUIVO_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if novo:
            w.writerow(["data", "participante", "modo", "alvos", "acertos", "erros",
                        "taxa_acerto_%", "tempo_medio_s", "tempo_total_s"])
        total = t.fim_total - t.inicio_total
        w.writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), participante, modo, t.n_alvos,
                    t.acertos, t.erros, f"{t.taxa_acerto():.1f}", f"{t.tempo_medio():.2f}", f"{total:.2f}"])
    print(f"Resultado salvo em {ARQUIVO_CSV}")


def main():
    """Programa principal do teste:
      1. pergunta o nome do participante e o modo (rosto ou mouse);
      2. cria a rodada e registra o callback de clique do mouse (Lab11);
      3. fica redesenhando a janela até a pessoa apertar ESC;
      4. ao sair, salva no CSV se o teste foi concluído.
    """
    global teste
    participante = input("Nome do participante: ").strip() or "anonimo"
    modo = input("Modo (rosto / mouse): ").strip().lower() or "rosto"
    input("Aperte ENTER para iniciar (o primeiro alvo aparece na hora)...")

    teste = Teste()

    cv2.namedWindow(JANELA)
    cv2.moveWindow(JANELA, 40, 40)
    cv2.setMouseCallback(JANELA, mouse_click)

    while True:
        cv2.imshow(JANELA, desenhar(teste))
        if cv2.waitKey(30) & 0xFF == 27:      # ESC
            break

    cv2.destroyAllWindows()
    if teste.terminou:
        salvar_csv(teste, participante, modo)
    else:
        print("Teste interrompido, nada foi salvo.")


if __name__ == "__main__":
    main()
