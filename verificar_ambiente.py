"""
CitizenTech - MAOS LIVRES: verificacao do ambiente
==================================================
Script de diagnostico. Ele NAO move o mouse e NAO clica: so confere se o
computador tem tudo o que o controle_sem_toque.py precisa para funcionar.

Como rodar (com o venv ativado):
    python verificar_ambiente.py

O que ele confere:
    1. versoes das bibliotecas (cv2, mediapipe, pyautogui, numpy)
    2. quais indices de camera abrem (0, 1, 2, 3) e a resolucao de cada um
    3. download do modelo models/face_landmarker.task
    4. se o FaceLandmarker carrega em modo VIDEO sem erro
    5. a resolucao da tela
No final imprime um resumo com OK ou FALHOU por item.
"""

from pathlib import Path
from urllib.request import urlretrieve

# Pasta e URL do modelo: os mesmos valores usados no controle_sem_toque.py
MODEL_DIR = Path("models")
MODEL_NOME = "face_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"

INDICES_CAMERA = [0, 1, 2, 3]

# Guarda o resultado de cada etapa para o resumo do final
resumo = {}
cameras_ok = []


def titulo(texto):
    """Imprime um cabecalho simples para separar as etapas na tela."""
    print()
    print("=" * 60)
    print(texto)
    print("=" * 60)


# ------------------------------------------------------------
# 1. Bibliotecas e versoes
# ------------------------------------------------------------
titulo("1. Bibliotecas e versoes")
try:
    import cv2
    import mediapipe as mp
    import numpy as np
    import pyautogui

    print(f"opencv-python (cv2) : {cv2.__version__}")
    print(f"mediapipe           : {mp.__version__}")
    print(f"pyautogui           : {pyautogui.__version__}")
    print(f"numpy               : {np.__version__}")
    resumo["Bibliotecas importadas"] = "OK"
except Exception as erro:
    print(f"Erro ao importar as bibliotecas: {erro}")
    resumo["Bibliotecas importadas"] = "FALHOU"
    # Sem as bibliotecas nao da para continuar
    raise SystemExit("Instale as dependencias com: pip install -r requirements.txt")


# ------------------------------------------------------------
# 2. Cameras disponiveis
# ------------------------------------------------------------
titulo("2. Cameras (testando os indices 0, 1, 2 e 3)")
for indice in INDICES_CAMERA:
    # CAP_DSHOW e o backend DirectShow do Windows: abre a webcam mais rapido
    cap = cv2.VideoCapture(indice, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print(f"indice {indice}: nao abriu")
        cap.release()
        continue
    ret, frame = cap.read()      # tenta ler um unico quadro
    if ret and frame is not None:
        altura, largura = frame.shape[:2]
        print(f"indice {indice}: FUNCIONA - resolucao {largura}x{altura}")
        cameras_ok.append((indice, largura, altura))
    else:
        print(f"indice {indice}: abriu, mas nao devolveu quadro")
    cap.release()

if cameras_ok:
    resumo["Camera encontrada"] = f"OK (indice {cameras_ok[0][0]})"
else:
    resumo["Camera encontrada"] = "FALHOU (nenhuma camera respondeu)"


# ------------------------------------------------------------
# 3. Download do modelo
# ------------------------------------------------------------
titulo("3. Modelo face_landmarker.task")
destino = MODEL_DIR / MODEL_NOME
try:
    MODEL_DIR.mkdir(exist_ok=True)
    if destino.exists():
        print(f"Modelo ja existe em {destino}")
    else:
        print("Baixando o modelo (so acontece na primeira vez)...")
        urlretrieve(MODEL_URL, destino)
        print("Download concluido.")
    tamanho_mb = destino.stat().st_size / (1024 * 1024)
    print(f"Tamanho do arquivo: {tamanho_mb:.1f} MB")
    resumo["Modelo baixado"] = "OK"
except Exception as erro:
    print(f"Erro ao baixar o modelo: {erro}")
    resumo["Modelo baixado"] = "FALHOU"


# ------------------------------------------------------------
# 4. Carregar o FaceLandmarker em modo VIDEO
# ------------------------------------------------------------
titulo("4. Carregando o FaceLandmarker (modo VIDEO)")
try:
    BaseOptions = mp.tasks.BaseOptions
    RunningMode = mp.tasks.vision.RunningMode
    FaceLandmarker = mp.tasks.vision.FaceLandmarker
    FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions

    opcoes = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(destino)),
        running_mode=RunningMode.VIDEO,
        num_faces=1,
        output_face_blendshapes=True,
    )
    # O "with" abre e fecha o modelo: se chegar ao fim, esta tudo certo
    with FaceLandmarker.create_from_options(opcoes) as _detector:
        print("Modelo carregado com sucesso (running_mode=VIDEO, num_faces=1,")
        print("output_face_blendshapes=True).")
    resumo["FaceLandmarker carrega"] = "OK"
except Exception as erro:
    print(f"Erro ao carregar o modelo: {erro}")
    resumo["FaceLandmarker carrega"] = "FALHOU"


# ------------------------------------------------------------
# 5. Resolucao da tela
# ------------------------------------------------------------
titulo("5. Resolucao da tela")
try:
    tela = pyautogui.size()      # so consulta o tamanho, nao mexe no cursor
    print(f"Tela: {tela.width}x{tela.height}")
    resumo["Resolucao da tela"] = f"OK ({tela.width}x{tela.height})"
except Exception as erro:
    print(f"Erro ao consultar a tela: {erro}")
    resumo["Resolucao da tela"] = "FALHOU"


# ------------------------------------------------------------
# Resumo final
# ------------------------------------------------------------
titulo("RESUMO")
for item, estado in resumo.items():
    print(f"{item:.<32} {estado}")

if cameras_ok and cameras_ok[0][0] != 0:
    print()
    print(f"ATENCAO: a camera que funcionou foi o indice {cameras_ok[0][0]}, nao o 0.")
    print(f"Troque CAM_INDEX = 0 por CAM_INDEX = {cameras_ok[0][0]} no topo do controle_sem_toque.py.")

if all(estado.startswith("OK") for estado in resumo.values()):
    print()
    print("Tudo pronto. Voce pode rodar o iniciar.bat.")
else:
    print()
    print("Algum item FALHOU: veja a mensagem de erro da etapa correspondente.")
