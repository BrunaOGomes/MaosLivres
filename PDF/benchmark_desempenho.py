"""
CitizenTech - MAOS LIVRES: benchmark de desempenho computacional
================================================================
Mede o DESEMPENHO DA VISAO COMPUTACIONAL do projeto, etapa por etapa:
quanto tempo cada parte do processamento leva e quantos quadros por segundo
(FPS) o sistema consegue processar.

Por que isso importa para o trabalho: um sistema de acessibilidade precisa
responder em tempo real. Se o processamento de cada quadro demorar mais que
~33 ms, o cursor fica "travado" e a pessoa nao consegue usar. Estes numeros
sao a comprovacao objetiva de que a solucao roda em tempo real num notebook
comum, sem placa de video dedicada.

O que ele mede, por quadro:
  1. captura       - tempo do cap.read() (ler o quadro da webcam)
  2. pre-proc      - flip (espelho) + conversao BGR->RGB
  3. inferencia    - detect_for_video() do MediaPipe (a parte mais pesada)
  4. pos-proc      - EAR dos dois olhos + leitura dos blendshapes
  5. total         - soma de tudo, e o FPS resultante

Tambem mede a TAXA DE DETECCAO: em quantos % dos quadros o rosto foi
encontrado. Para esse numero valer, fique na frente da camera durante o teste.

Saidas (pasta resultados/):
  - desempenho_quadros.csv  : uma linha por quadro, para auditoria
  - desempenho_resumo.csv   : media, mediana, p95 e minimo/maximo por etapa
  - grafico_latencia.png    : distribuicao do tempo total por quadro
  - grafico_etapas.png      : quanto cada etapa custa
  - grafico_fps.png         : FPS ao longo do tempo

IMPORTANTE: este script NAO move o mouse e NAO clica. Ele so le a camera e
mede. E seguro rodar a qualquer momento.

Como rodar:
    venv\\Scripts\\python.exe benchmark_desempenho.py
"""

import csv
import time
from math import dist
from pathlib import Path
from statistics import median
from urllib.request import urlretrieve

import cv2
import matplotlib
import mediapipe as mp
import numpy as np

matplotlib.use("Agg")          # salva em arquivo, sem abrir janela
import matplotlib.pyplot as plt

# ============================================================
# Configuracoes
# ============================================================
N_QUADROS = 300                # ~10 s de video a 30 FPS
AQUECIMENTO = 20               # quadros descartados (o modelo "esquenta")
CAM_INDEX = 0                  # mesmo indice do controle_sem_toque.py

MODEL_DIR = Path("models")
MODEL_NOME = "face_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"

SAIDA = Path("resultados")

# Os mesmos indices de landmark usados no controle_sem_toque.py
OLHO_A = [33, 160, 158, 133, 153, 144]
OLHO_B = [362, 385, 387, 263, 373, 380]


def eye_aspect_ratio(eye):
    """EAR do Lab12 (mesma funcao do controle_sem_toque.py), para o tempo
    medido no pos-processamento ser o tempo real da nossa aplicacao."""
    A = dist(eye[1], eye[5])
    B = dist(eye[2], eye[4])
    C = dist(eye[0], eye[3])
    return (A + B) / (2.0 * C)


def pontos_px(landmarks, indices, w, h):
    return [(landmarks[i].x * w, landmarks[i].y * h) for i in indices]


def estatisticas(valores):
    """Media, mediana, percentil 95, minimo e maximo de uma lista."""
    if not valores:
        return {"media": 0, "mediana": 0, "p95": 0, "min": 0, "max": 0}
    ordenados = sorted(valores)
    return {
        "media": sum(valores) / len(valores),
        "mediana": median(valores),
        # p95 = 95% dos quadros foram mais rapidos que isso. Mostra o pior
        # caso realista, que e o que trava a experiencia de uso.
        "p95": ordenados[int(0.95 * (len(ordenados) - 1))],
        "min": ordenados[0],
        "max": ordenados[-1],
    }


def main():
    SAIDA.mkdir(exist_ok=True)

    # --- garante o modelo ---
    MODEL_DIR.mkdir(exist_ok=True)
    caminho_modelo = MODEL_DIR / MODEL_NOME
    if not caminho_modelo.exists():
        print("Baixando o modelo (primeira execucao)...")
        urlretrieve(MODEL_URL, caminho_modelo)

    # --- abre a camera ---
    cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print(f"Nao consegui abrir a camera no indice {CAM_INDEX}.")
        print("Rode o verificar_ambiente.py para descobrir o indice correto.")
        return

    largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # --- cria o detector com as MESMAS opcoes da aplicacao ---
    opcoes = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(caminho_modelo)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
        output_face_blendshapes=True,
    )

    print(f"Resolucao da camera: {largura}x{altura}")
    print(f"Medindo {N_QUADROS} quadros (descartando {AQUECIMENTO} de aquecimento).")
    print("Fique na frente da camera para a taxa de deteccao valer.")
    print()

    registros = []
    detectados = 0
    ultimo_ts = -1

    with mp.tasks.vision.FaceLandmarker.create_from_options(opcoes) as detector:
        t_inicio_total = time.perf_counter()

        for i in range(N_QUADROS + AQUECIMENTO):
            # ---------- 1. captura ----------
            t0 = time.perf_counter()
            ok, frame = cap.read()
            t_captura = time.perf_counter() - t0
            if not ok:
                print("Falha ao ler o quadro; encerrando.")
                break

            # ---------- 2. pre-processamento ----------
            t0 = time.perf_counter()
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            t_pre = time.perf_counter() - t0

            # ---------- 3. inferencia ----------
            agora = time.perf_counter()
            ts = int((agora - t_inicio_total) * 1000)
            if ts <= ultimo_ts:
                ts = ultimo_ts + 1
            ultimo_ts = ts

            t0 = time.perf_counter()
            resultado = detector.detect_for_video(mp_image, ts)
            t_inferencia = time.perf_counter() - t0

            # ---------- 4. pos-processamento ----------
            t0 = time.perf_counter()
            achou = bool(resultado.face_landmarks)
            if achou:
                lm = resultado.face_landmarks[0]
                h, w = frame.shape[:2]
                eye_aspect_ratio(pontos_px(lm, OLHO_A, w, h))
                eye_aspect_ratio(pontos_px(lm, OLHO_B, w, h))
                if resultado.face_blendshapes:
                    {c.category_name: c.score for c in resultado.face_blendshapes[0]}
            t_pos = time.perf_counter() - t0

            # descarta os quadros de aquecimento
            if i < AQUECIMENTO:
                continue

            if achou:
                detectados += 1

            # Duas medidas DIFERENTES, e a distincao importa na analise:
            #  - processamento: o que o NOSSO codigo custa (pre + inferencia + pos).
            #  - total do ciclo: inclui o cap.read(), que FICA ESPERANDO o proximo
            #    quadro chegar da webcam. Essa espera nao e culpa do algoritmo:
            #    e o limite fisico da camera (uma webcam de 30 FPS entrega um
            #    quadro a cada 33 ms, por mais rapido que o programa seja).
            processamento = t_pre + t_inferencia + t_pos
            total = t_captura + processamento
            registros.append({
                "quadro": len(registros) + 1,
                "captura_ms": t_captura * 1000,
                "preproc_ms": t_pre * 1000,
                "inferencia_ms": t_inferencia * 1000,
                "posproc_ms": t_pos * 1000,
                "processamento_ms": processamento * 1000,
                "total_ms": total * 1000,
                "fps_ciclo": 1.0 / total if total > 0 else 0.0,
                "fps_teorico_processamento": 1.0 / processamento if processamento > 0 else 0.0,
                "rosto_detectado": int(achou),
            })

            if len(registros) % 50 == 0:
                print(f"  {len(registros)}/{N_QUADROS} quadros medidos...")

    cap.release()

    if not registros:
        print("Nenhum quadro medido.")
        return

    # ============================================================
    # CSV por quadro (auditoria / comprovacao das metricas)
    # ============================================================
    arq_quadros = SAIDA / "desempenho_quadros.csv"
    with open(arq_quadros, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(registros[0].keys()))
        w.writeheader()
        w.writerows(registros)

    # ============================================================
    # Resumo estatistico
    # ============================================================
    etapas = {
        "pre-processamento": [r["preproc_ms"] for r in registros],
        "inferencia (MediaPipe)": [r["inferencia_ms"] for r in registros],
        "pos-processamento (EAR)": [r["posproc_ms"] for r in registros],
        "PROCESSAMENTO (nosso codigo)": [r["processamento_ms"] for r in registros],
        "espera da webcam (cap.read)": [r["captura_ms"] for r in registros],
        "TOTAL do ciclo": [r["total_ms"] for r in registros],
    }
    fps_ciclo = [r["fps_ciclo"] for r in registros]
    fps_proc = [r["fps_teorico_processamento"] for r in registros]
    taxa_deteccao = 100.0 * detectados / len(registros)

    arq_resumo = SAIDA / "desempenho_resumo.csv"
    with open(arq_resumo, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["etapa", "media_ms", "mediana_ms", "p95_ms", "min_ms", "max_ms"])
        for nome, vals in etapas.items():
            e = estatisticas(vals)
            w.writerow([nome, f"{e['media']:.2f}", f"{e['mediana']:.2f}",
                        f"{e['p95']:.2f}", f"{e['min']:.2f}", f"{e['max']:.2f}"])
        e_ciclo = estatisticas(fps_ciclo)
        e_proc = estatisticas(fps_proc)
        w.writerow(["FPS real (limitado pela webcam)", f"{e_ciclo['media']:.1f}",
                    f"{e_ciclo['mediana']:.1f}", f"{e_ciclo['p95']:.1f}",
                    f"{e_ciclo['min']:.1f}", f"{e_ciclo['max']:.1f}"])
        w.writerow(["FPS que o algoritmo suportaria", f"{e_proc['media']:.1f}",
                    f"{e_proc['mediana']:.1f}", f"{e_proc['p95']:.1f}",
                    f"{e_proc['min']:.1f}", f"{e_proc['max']:.1f}"])
        w.writerow(["taxa_deteccao_%", f"{taxa_deteccao:.1f}", "", "", "", ""])
        w.writerow(["quadros_medidos", len(registros), "", "", "", ""])
        w.writerow(["resolucao", f"{largura}x{altura}", "", "", "", ""])

    # ============================================================
    # Graficos
    # ============================================================
    media_proc = sum(etapas["PROCESSAMENTO (nosso codigo)"]) / len(registros)
    media_total = sum(etapas["TOTAL do ciclo"]) / len(registros)

    # 1. distribuicao da latencia DO NOSSO PROCESSAMENTO
    plt.figure(figsize=(8, 4.5))
    plt.hist([r["processamento_ms"] for r in registros], bins=30,
             color="#2d7dd2", edgecolor="white")
    plt.axvline(media_proc, color="#d62828", linestyle="--",
                label=f"media {media_proc:.1f} ms")
    plt.axvline(33.3, color="#2a9d8f", linestyle=":",
                label="orcamento de 33,3 ms (30 FPS)")
    plt.xlabel("Tempo de processamento por quadro (ms) - sem a espera da webcam")
    plt.ylabel("Quantidade de quadros")
    plt.title("MaosLivres - latencia do processamento por quadro")
    plt.legend()
    plt.tight_layout()
    plt.savefig(SAIDA / "grafico_latencia.png", dpi=150)
    plt.close()

    # 2. custo de cada etapa (inclui a espera da webcam, para mostrar o gargalo)
    nomes = ["pre-processamento", "inferencia (MediaPipe)",
             "pos-processamento (EAR)", "espera da webcam (cap.read)"]
    medias = [sum(etapas[n]) / len(registros) for n in nomes]
    plt.figure(figsize=(9, 4.5))
    barras = plt.barh(nomes, medias, color=["#9bc1bc", "#e76f51", "#8e7dbe", "#adb5bd"])
    for barra, valor in zip(barras, medias):
        pct = 100.0 * valor / media_total
        plt.text(valor, barra.get_y() + barra.get_height() / 2,
                 f"  {valor:.1f} ms ({pct:.0f}% do ciclo)", va="center", fontsize=9)
    plt.xlabel("Tempo medio por quadro (ms)")
    plt.title("MaosLivres - onde o tempo e gasto (o gargalo e a webcam)")
    plt.xlim(0, max(medias) * 1.45)
    plt.tight_layout()
    plt.savefig(SAIDA / "grafico_etapas.png", dpi=150)
    plt.close()

    # 3. FPS ao longo do tempo: o real e o que o algoritmo suportaria
    plt.figure(figsize=(9, 4.5))
    quadros = [r["quadro"] for r in registros]
    plt.plot(quadros, fps_ciclo, color="#2d7dd2", linewidth=1,
             label="FPS real (limitado pela webcam)")
    media_ciclo = sum(fps_ciclo) / len(fps_ciclo)
    plt.axhline(media_ciclo, color="#d62828", linestyle="--",
                label=f"media real {media_ciclo:.1f} FPS")
    plt.axhline(30, color="#2a9d8f", linestyle=":", label="30 FPS (tempo real)")
    plt.xlabel("Quadro")
    plt.ylabel("FPS")
    plt.ylim(bottom=0)
    plt.title("MaosLivres - FPS ao longo da execucao")
    plt.legend(loc="lower right", fontsize=8)
    plt.tight_layout()
    plt.savefig(SAIDA / "grafico_fps.png", dpi=150)
    plt.close()

    # ============================================================
    # Resumo na tela (para colar no relatorio)
    # ============================================================
    print()
    print("=" * 64)
    print("RESUMO DO DESEMPENHO")
    print("=" * 64)
    print(f"Quadros medidos ........... {len(registros)}")
    print(f"Resolucao ................. {largura}x{altura}")
    print(f"Taxa de deteccao do rosto . {taxa_deteccao:.1f}%")
    print()
    print(f"{'etapa':<32}{'media':>9}{'mediana':>10}{'p95':>9}")
    for nome, vals in etapas.items():
        e = estatisticas(vals)
        print(f"{nome:<32}{e['media']:>7.2f}ms{e['mediana']:>8.2f}ms{e['p95']:>7.2f}ms")
    e_ciclo = estatisticas(fps_ciclo)
    e_proc = estatisticas(fps_proc)
    print()
    print(f"FPS real (com a webcam) ........... {e_ciclo['media']:.1f}")
    print(f"FPS que o algoritmo suportaria .... {e_proc['media']:.0f}")
    print()
    # O veredito correto compara o PROCESSAMENTO com o orcamento de 33,3 ms.
    # Se o processamento cabe no orcamento, o sistema acompanha a camera e a
    # unica limitacao e o hardware da webcam.
    if media_proc <= 33.3:
        print("VEREDITO: o processamento cabe no orcamento de 33,3 ms por quadro,")
        print(f"          ocupando apenas {100*media_proc/33.3:.0f}% dele. O sistema")
        print("          acompanha a camera em tempo real; o gargalo e a webcam.")
    else:
        print("VEREDITO: o processamento NAO cabe no orcamento de 33,3 ms.")
    print()
    if taxa_deteccao < 50:
        print("ATENCAO: taxa de deteccao baixa. Rode de novo SENTADO NA FRENTE da")
        print("camera: sem rosto no quadro, o tempo de inferencia fica menor que o")
        print("real e a taxa de deteccao nao vale para o relatorio.")
        print()
    print(f"Arquivos gerados em: {SAIDA.resolve()}")
    for arq in sorted(SAIDA.iterdir()):
        print(f"  - {arq.name}")


if __name__ == "__main__":
    main()
