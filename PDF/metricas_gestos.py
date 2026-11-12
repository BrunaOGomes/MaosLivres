"""
CitizenTech - MAOS LIVRES: metricas de deteccao dos gestos
===========================================================
Mede, no rosto real da pessoa, os VALORES NUMERICOS que o sistema usa para
decidir que um gesto aconteceu. E a comprovacao quantitativa dos limiares.

O que e medido, quadro a quadro:
  EAR olho A e B   : abertura da palpebra (altura / largura do olho)
  mouthPucker      : quanto os labios estao em bico (0 a 1)
  sobrancelha      : media de browInnerUp + browOuterUpLeft + browOuterUpRight
  nariz x, y       : posicao normalizada da ponta do nariz (0 a 1)

Saidas (pasta resultados/):
  metricas_gestos.csv        : uma linha por quadro
  metricas_gestos_resumo.csv : limiares calibrados e estatisticas por gesto
  grafico_ear.png            : EAR no tempo, com o limiar de olho fechado
  grafico_blendshapes.png    : sobrancelha e beijinho no tempo, com limiares
  grafico_nariz.png          : trajetoria do nariz e o alcance usado

NAO move o mouse e NAO clica. Usa a camera e mostra uma janela de previa.

Como rodar:
    venv\\Scripts\\python.exe metricas_gestos.py

Roteiro durante a gravacao (o programa avisa na tela a cada etapa):
  0-3 s   : calibracao. Rosto RELAXADO, olhos abertos, boca fechada.
  3-13 s  : olhos abertos, so olhando a tela (linha de base)
  13-23 s : pisque naturalmente varias vezes
  23-33 s : feche os dois olhos por ~1 s e abra, repita (gesto de clique)
  33-43 s : levante as sobrancelhas, mantenha ~1 s, repita
  43-53 s : faca biquinho, mantenha ~1,5 s, repita
  53-63 s : mova a cabeca nos 4 cantos da tela
"""

import csv
import time
from math import dist
from pathlib import Path
from statistics import mean, median, pstdev
from urllib.request import urlretrieve

import cv2
import matplotlib
import mediapipe as mp
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- as MESMAS constantes do controle_sem_toque.py ----
CAM_INDEX = 0
CALIB_SEGUNDOS = 3.0
EAR_FATOR = 0.70
WINK_MARGEM = 1.10
SOBRANCELHA_DELTA = 0.35
BEIJO_DELTA = 0.45
CLIQUE_SEG = 0.5
CLIQUE_MAX_SEG = 3.0
GANHO_X, GANHO_Y = 5.0, 6.0

OLHO_A = [33, 160, 158, 133, 153, 144]
OLHO_B = [362, 385, 387, 263, 373, 380]
NARIZ = 1

MODEL_DIR = Path("models")
MODEL_NOME = "face_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
SAIDA = Path("resultados")

# Roteiro: (segundo_inicial, instrucao mostrada na tela)
ROTEIRO = [
    (0, "CALIBRANDO - rosto relaxado, olhos abertos, boca fechada"),
    (3, "ETAPA 1/5 - apenas olhe a tela (linha de base)"),
    (13, "ETAPA 2/5 - pisque naturalmente varias vezes"),
    (23, "ETAPA 3/5 - feche os 2 olhos ~1s e abra, repita"),
    (33, "ETAPA 4/5 - levante as sobrancelhas ~1s, repita"),
    (43, "ETAPA 5/5 - faca biquinho ~1,5s, repita"),
    (53, "EXTRA - mova a cabeca nos 4 cantos da tela"),
    (63, "FIM - gerando os graficos..."),
]
DURACAO = 63.0


def eye_aspect_ratio(eye):
    """EAR: (altura1 + altura2) / (2 * largura). Mesma funcao da aplicacao."""
    A = dist(eye[1], eye[5])
    B = dist(eye[2], eye[4])
    C = dist(eye[0], eye[3])
    return (A + B) / (2.0 * C)


def pontos_px(landmarks, indices, w, h):
    return [(landmarks[i].x * w, landmarks[i].y * h) for i in indices]


def instrucao(t):
    atual = ROTEIRO[0][1]
    for inicio, texto in ROTEIRO:
        if t >= inicio:
            atual = texto
    return atual


def estat(v):
    if not v:
        return {"media": 0, "mediana": 0, "sd": 0, "min": 0, "max": 0}
    return {"media": mean(v), "mediana": median(v),
            "sd": pstdev(v) if len(v) > 1 else 0.0, "min": min(v), "max": max(v)}


def main():
    SAIDA.mkdir(exist_ok=True)
    MODEL_DIR.mkdir(exist_ok=True)
    modelo = MODEL_DIR / MODEL_NOME
    if not modelo.exists():
        print("Baixando o modelo...")
        urlretrieve(MODEL_URL, modelo)

    cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print(f"Nao consegui abrir a camera no indice {CAM_INDEX}.")
        return

    opcoes = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(modelo)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
        output_face_blendshapes=True,
    )

    registros = []
    calib = {"ear_a": [], "ear_b": [], "sobr": [], "beijo": [], "nx": [], "ny": []}
    limiares = {}
    ultimo_ts = -1

    print("Siga as instrucoes na janela. ESC encerra antes do fim.")
    janela = "Metricas de gestos - MaosLivres"
    cv2.namedWindow(janela, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(janela, 760, 570)

    with mp.tasks.vision.FaceLandmarker.create_from_options(opcoes) as det:
        t0 = time.perf_counter()
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            t = time.perf_counter() - t0
            if t > DURACAO:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts = int(t * 1000)
            if ts <= ultimo_ts:
                ts = ultimo_ts + 1
            ultimo_ts = ts

            res = det.detect_for_video(img, ts)

            if res.face_landmarks:
                lm = res.face_landmarks[0]
                ear_a = eye_aspect_ratio(pontos_px(lm, OLHO_A, w, h))
                ear_b = eye_aspect_ratio(pontos_px(lm, OLHO_B, w, h))
                nariz = lm[NARIZ]

                sobr = beijo = 0.0
                if res.face_blendshapes:
                    b = {c.category_name: c.score for c in res.face_blendshapes[0]}
                    sobr = (b.get("browInnerUp", 0) + b.get("browOuterUpLeft", 0)
                            + b.get("browOuterUpRight", 0)) / 3.0
                    beijo = b.get("mouthPucker", 0.0)

                if t < CALIB_SEGUNDOS:
                    calib["ear_a"].append(ear_a)
                    calib["ear_b"].append(ear_b)
                    calib["sobr"].append(sobr)
                    calib["beijo"].append(beijo)
                    calib["nx"].append(nariz.x)
                    calib["ny"].append(nariz.y)
                else:
                    if not limiares:
                        limiares = {
                            "ear_a_repouso": float(np.median(calib["ear_a"])),
                            "ear_b_repouso": float(np.median(calib["ear_b"])),
                            "ear_a_limiar": float(np.median(calib["ear_a"])) * EAR_FATOR,
                            "ear_b_limiar": float(np.median(calib["ear_b"])) * EAR_FATOR,
                            "sobr_repouso": float(np.median(calib["sobr"])),
                            "sobr_limiar": float(np.median(calib["sobr"])) + SOBRANCELHA_DELTA,
                            "beijo_repouso": float(np.median(calib["beijo"])),
                            "beijo_limiar": float(np.median(calib["beijo"])) + BEIJO_DELTA,
                            "nariz_centro_x": float(np.median(calib["nx"])),
                            "nariz_centro_y": float(np.median(calib["ny"])),
                        }
                        print("\nLimiares calibrados:")
                        for k, v in limiares.items():
                            print(f"  {k:<18} {v:.4f}")

                    registros.append({
                        "t_s": round(t, 3),
                        "ear_a": round(ear_a, 5),
                        "ear_b": round(ear_b, 5),
                        # % da abertura normal da palpebra daquela pessoa
                        "ear_a_pct_repouso": round(100 * ear_a / limiares["ear_a_repouso"], 2),
                        "ear_b_pct_repouso": round(100 * ear_b / limiares["ear_b_repouso"], 2),
                        "olho_a_fechado": int(ear_a < limiares["ear_a_limiar"]),
                        "olho_b_fechado": int(ear_b < limiares["ear_b_limiar"]),
                        "sobrancelha": round(sobr, 5),
                        "sobrancelha_ativa": int(sobr > limiares["sobr_limiar"]),
                        "beijo": round(beijo, 5),
                        "beijo_ativo": int(beijo > limiares["beijo_limiar"]),
                        "nariz_x": round(nariz.x, 5),
                        "nariz_y": round(nariz.y, 5),
                        "etapa": instrucao(t),
                    })

                # feedback visual
                cor_a = (0, 0, 255) if limiares and ear_a < limiares["ear_a_limiar"] else (0, 255, 0)
                cor_b = (0, 0, 255) if limiares and ear_b < limiares["ear_b_limiar"] else (0, 255, 0)
                for pts, cor in ((pontos_px(lm, OLHO_A, w, h), cor_a),
                                 (pontos_px(lm, OLHO_B, w, h), cor_b)):
                    cv2.drawContours(frame, [cv2.convexHull(np.array(pts, dtype=np.int32))], -1, cor, 1)
                cv2.putText(frame, f"EAR A {ear_a:.3f}  B {ear_b:.3f}", (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 2)
                cv2.putText(frame, f"sobr {sobr:.2f}   beijo {beijo:.2f}", (10, 95),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 2)
            else:
                cv2.putText(frame, "Rosto nao detectado", (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            cv2.putText(frame, instrucao(t), (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
            cv2.putText(frame, instrucao(t), (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"{t:4.1f}s / {DURACAO:.0f}s", (10, 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow(janela, frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

    cap.release()
    cv2.destroyAllWindows()

    if not registros or not limiares:
        print("\nNao foi possivel medir: o rosto precisa estar visivel na camera.")
        return

    # ---------------- CSV por quadro ----------------
    with open(SAIDA / "metricas_gestos.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(registros[0].keys()))
        wr.writeheader()
        wr.writerows(registros)

    # ---------------- resumo ----------------
    ear_a = [r["ear_a"] for r in registros]
    ear_b = [r["ear_b"] for r in registros]
    sobr = [r["sobrancelha"] for r in registros]
    beijo = [r["beijo"] for r in registros]

    aberto_a = [r["ear_a"] for r in registros if not r["olho_a_fechado"]]
    fechado_a = [r["ear_a"] for r in registros if r["olho_a_fechado"]]
    sobr_ativo = [r["sobrancelha"] for r in registros if r["sobrancelha_ativa"]]
    beijo_ativo = [r["beijo"] for r in registros if r["beijo_ativo"]]

    with open(SAIDA / "metricas_gestos_resumo.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["metrica", "valor"])
        for k, v in limiares.items():
            wr.writerow([k, f"{v:.4f}"])
        wr.writerow(["quadros_analisados", len(registros)])
        wr.writerow(["EAR_FATOR (limiar = % do repouso)", EAR_FATOR])
        wr.writerow(["SOBRANCELHA_DELTA", SOBRANCELHA_DELTA])
        wr.writerow(["BEIJO_DELTA", BEIJO_DELTA])
        wr.writerow([])
        wr.writerow(["grupo", "n", "media", "mediana", "desvio", "min", "max"])
        for nome, v in (("EAR A (todos)", ear_a), ("EAR A (olho aberto)", aberto_a),
                        ("EAR A (olho fechado)", fechado_a), ("EAR B (todos)", ear_b),
                        ("sobrancelha (todos)", sobr), ("sobrancelha (ativa)", sobr_ativo),
                        ("beijo (todos)", beijo), ("beijo (ativo)", beijo_ativo)):
            e = estat(v)
            wr.writerow([nome, len(v), f"{e['media']:.4f}", f"{e['mediana']:.4f}",
                         f"{e['sd']:.4f}", f"{e['min']:.4f}", f"{e['max']:.4f}"])
        wr.writerow([])
        wr.writerow(["% quadros olho A fechado",
                     f"{100*sum(r['olho_a_fechado'] for r in registros)/len(registros):.1f}"])
        wr.writerow(["% quadros sobrancelha ativa",
                     f"{100*sum(r['sobrancelha_ativa'] for r in registros)/len(registros):.1f}"])
        wr.writerow(["% quadros beijo ativo",
                     f"{100*sum(r['beijo_ativo'] for r in registros)/len(registros):.1f}"])

    # ---------------- graficos ----------------
    t = [r["t_s"] for r in registros]

    plt.figure(figsize=(11, 4.8))
    plt.plot(t, ear_a, color="#2d7dd2", linewidth=0.9, label="EAR olho A")
    plt.plot(t, ear_b, color="#8e7dbe", linewidth=0.9, alpha=0.7, label="EAR olho B")
    plt.axhline(limiares["ear_a_repouso"], color="#2a9d8f", linestyle="-", linewidth=1,
                label=f"repouso A = {limiares['ear_a_repouso']:.3f} (100%)")
    plt.axhline(limiares["ear_a_limiar"], color="#d62828", linestyle="--", linewidth=1.3,
                label=f"limiar A = {limiares['ear_a_limiar']:.3f} (70% do repouso)")
    plt.xlabel("Tempo (s)")
    plt.ylabel("EAR (altura / largura do olho)")
    plt.title("MaosLivres - abertura da palpebra e o limiar de olho fechado")
    plt.legend(fontsize=8, loc="upper right")
    plt.tight_layout()
    plt.savefig(SAIDA / "grafico_ear.png", dpi=150)
    plt.close()

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True)
    a1.plot(t, sobr, color="#f4a261", linewidth=1)
    a1.axhline(limiares["sobr_repouso"], color="#2a9d8f", linewidth=1,
               label=f"repouso = {limiares['sobr_repouso']:.3f}")
    a1.axhline(limiares["sobr_limiar"], color="#d62828", linestyle="--", linewidth=1.3,
               label=f"limiar = repouso + {SOBRANCELHA_DELTA} = {limiares['sobr_limiar']:.3f}")
    a1.set_ylabel("sobrancelha (0 a 1)")
    a1.set_title("MaosLivres - blendshapes dos gestos e seus limiares")
    a1.legend(fontsize=8)

    a2.plot(t, beijo, color="#c77dff", linewidth=1)
    a2.axhline(limiares["beijo_repouso"], color="#2a9d8f", linewidth=1,
               label=f"repouso = {limiares['beijo_repouso']:.3f}")
    a2.axhline(limiares["beijo_limiar"], color="#d62828", linestyle="--", linewidth=1.3,
               label=f"limiar = repouso + {BEIJO_DELTA} = {limiares['beijo_limiar']:.3f}")
    a2.set_ylabel("beijinho / mouthPucker")
    a2.set_xlabel("Tempo (s)")
    a2.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(SAIDA / "grafico_blendshapes.png", dpi=150)
    plt.close()

    nx = [r["nariz_x"] for r in registros]
    ny = [r["nariz_y"] for r in registros]
    plt.figure(figsize=(6.5, 5.5))
    plt.scatter(nx, ny, s=5, c=t, cmap="viridis")
    plt.colorbar(label="tempo (s)")
    plt.scatter([limiares["nariz_centro_x"]], [limiares["nariz_centro_y"]],
                marker="+", s=260, c="red", linewidths=2, label="centro calibrado")
    plt.gca().invert_yaxis()
    plt.xlabel("nariz x (0 a 1 da largura da imagem)")
    plt.ylabel("nariz y (0 a 1 da altura da imagem)")
    plt.title("MaosLivres - deslocamento do nariz usado para mover o cursor")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(SAIDA / "grafico_nariz.png", dpi=150)
    plt.close()

    # ---------------- resumo na tela ----------------
    amp_x = max(nx) - min(nx)
    amp_y = max(ny) - min(ny)
    print()
    print("=" * 66)
    print("METRICAS DE DETECCAO DOS GESTOS")
    print("=" * 66)
    print(f"Quadros analisados ................ {len(registros)}")
    print()
    print("OLHOS (EAR = altura / largura da palpebra)")
    print(f"  EAR em repouso, olho A .......... {limiares['ear_a_repouso']:.4f}")
    print(f"  EAR em repouso, olho B .......... {limiares['ear_b_repouso']:.4f}")
    print(f"  Limiar de fechado (70%) A ....... {limiares['ear_a_limiar']:.4f}")
    print(f"  Limiar de fechado (70%) B ....... {limiares['ear_b_limiar']:.4f}")
    if fechado_a:
        print(f"  EAR medio com olho fechado ...... {mean(fechado_a):.4f} "
              f"({100*mean(fechado_a)/limiares['ear_a_repouso']:.0f}% do repouso)")
    if aberto_a:
        print(f"  EAR medio com olho aberto ....... {mean(aberto_a):.4f} "
              f"({100*mean(aberto_a)/limiares['ear_a_repouso']:.0f}% do repouso)")
    print(f"  Quadros com olho A fechado ...... "
          f"{100*sum(r['olho_a_fechado'] for r in registros)/len(registros):.1f}%")
    print()
    print("SOBRANCELHA (blendshape, 0 a 1)")
    print(f"  Repouso ......................... {limiares['sobr_repouso']:.4f}")
    print(f"  Limiar (repouso + {SOBRANCELHA_DELTA}) ......... {limiares['sobr_limiar']:.4f}")
    if sobr_ativo:
        print(f"  Media quando ativa .............. {mean(sobr_ativo):.4f}")
    print(f"  Pico observado .................. {max(sobr):.4f}")
    print()
    print("BEIJINHO (mouthPucker, 0 a 1)")
    print(f"  Repouso ......................... {limiares['beijo_repouso']:.4f}")
    print(f"  Limiar (repouso + {BEIJO_DELTA}) ......... {limiares['beijo_limiar']:.4f}")
    if beijo_ativo:
        print(f"  Media quando ativo .............. {mean(beijo_ativo):.4f}")
    print(f"  Pico observado .................. {max(beijo):.4f}")
    print()
    print("NARIZ (controle do cursor)")
    print(f"  Centro calibrado ................ "
          f"x={limiares['nariz_centro_x']:.4f}  y={limiares['nariz_centro_y']:.4f}")
    print(f"  Amplitude usada ................. "
          f"x={amp_x:.4f} ({100*amp_x:.1f}% da largura)  y={amp_y:.4f} ({100*amp_y:.1f}% da altura)")
    print(f"  Ganho aplicado .................. X={GANHO_X}  Y={GANHO_Y}")
    print(f"  Deslocamento de cabeca para cruzar a tela: "
          f"x={100/GANHO_X:.0f}%  y={100/GANHO_Y:.0f}% da imagem")
    print()
    print(f"Arquivos em: {SAIDA.resolve()}")
    for a in ("metricas_gestos.csv", "metricas_gestos_resumo.csv",
              "grafico_ear.png", "grafico_blendshapes.png", "grafico_nariz.png"):
        print(f"  - {a}")


if __name__ == "__main__":
    main()
