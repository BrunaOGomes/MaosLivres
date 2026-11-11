"""
CitizenTech - MÃOS LIVRES (controle do notebook sem usar os braços)
===================================================================
Global Solution FIAP 2026.2

Público: pessoas sem braços (amputação, ausência congênita, paralisia) ou
sem função nos membros superiores, que precisam usar o notebook.

Solução: a webcam do notebook vira mouse, usando só a CABEÇA e o ROSTO.

  Mover a cabeça (ponta do nariz) ......... move o cursor
  Fechar os 2 olhos entre 0,5 s e 3,0 s
        e abrir ........................... CLIQUE
        (mais de 3,0 s = nada: dá para descansar os olhos)
        (no modo rolagem: cabeça p/ cima = sobe a página, p/ baixo = desce)
  LEVANTAR AS SOBRANCELHAS por 0,7 s ...... liga/desliga ARRASTAR (segura o botão do mouse)
  BEIJINHO (bico) por 1,0 s ............... PAUSA/RETOMA tudo (para conversar sem mexer no cursor)

  O olho DIREITO não tem função: fechar só ele não faz nada.

Teclas (para quem for AJUDAR a configurar, com a janela da câmera em foco):
     P = pausar/retomar | C = recalibrar | ESC = sair

Segurança: jogue o mouse físico no canto superior esquerdo da tela
para abortar (fail-safe do pyautogui) ou use Ctrl+C no terminal.

Baseado nos labs:
  Lab13 (MediaPipe Tasks: FaceLandmarker, modo VIDEO)
  Lab12 (eye_aspect_ratio = EAR, convexHull dos olhos)
  Lab11 (eventos de mouse - usado no teste_validacao.py)
  Lab01 (loop de captura de vídeo com OpenCV)
"""

import time
from math import dist
from pathlib import Path
from urllib.request import urlretrieve

import cv2
import numpy as np
import mediapipe as mp
import pyautogui

# ============================================================
# 1. CONFIGURAÇÕES (ajuste aqui sem mexer no resto do código)
# ============================================================
CAM_INDEX = 0                 # 0 = webcam do notebook (se não abrir, teste 1)
MODEL_DIR = Path("models")    # mesma pasta "models" usada na aula 13

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
MODEL_NOME = "face_landmarker.task"

CALIB_SEGUNDOS = 3.0          # tempo de calibração (olhar para a tela, olhos abertos)
EAR_FATOR = 0.70              # olho "fechado" = EAR abaixo de 70% do EAR normal da pessoa
WINK_MARGEM = 1.10            # no wink, o outro olho precisa ficar bem aberto

GANHO_X = 5.0                 # sensibilidade horizontal da cabeça (maior = cursor mais rápido)
GANHO_Y = 6.0                 # sensibilidade vertical
SUAVIZACAO = 0.25             # 0 a 1: menor = cursor mais "pesado" e estável

CLIQUE_SEG = 0.5              # olhos fechados por pelo menos isso = clique (ao abrir)
CLIQUE_MAX_SEG = 3.0          # fechados por mais que isso = ignora (descanso/cansaço)
WINK_ESQUERDO_SEG = 0.6       # olho esquerdo fechado = liga/desliga rolagem

ROLAGEM_ZONA = 0.03           # folga (parte da altura da imagem) sem rolar
ROLAGEM_GANHO = 600           # velocidade de rolagem

# Gestos do rosto (usam os "blendshapes" do MediaPipe, números de 0 a 1).
# O gesto vale quando o valor passa do valor em REPOUSO (medido na calibração) + DELTA.
SOBRANCELHA_DELTA, SOBRANCELHA_SEG = 0.35, 0.7  # sobrancelhas -> arrastar
BEIJO_DELTA, BEIJO_SEG = 0.45, 1.0            # beijinho -> pausa

JANELA = "CitizenTech - Maos Livres"
JANELA_LARGURA, JANELA_ALTURA = 420, 315   # tamanho da prévia da câmera
JANELA_SEMPRE_NO_TOPO = True

# Índices dos landmarks do Face Mesh (478 pontos). Mesma ordem do dlib da aula 12:
# [canto, cima1, cima2, canto, baixo2, baixo1]  ->  eye[0..5]
OLHO_A = [33, 160, 158, 133, 153, 144]    # olho que aparece à ESQUERDA da tela (seu olho esquerdo)
OLHO_B = [362, 385, 387, 263, 373, 380]   # olho que aparece à DIREITA da tela (seu olho direito)
NARIZ = 1                                  # ponta do nariz

# ============================================================
# 2. FUNÇÕES AUXILIARES
# ============================================================


def baixar_modelo():
    """Baixa o arquivo .task na primeira execução (igual ao Lab13)."""
    MODEL_DIR.mkdir(exist_ok=True)
    destino = MODEL_DIR / MODEL_NOME
    if not destino.exists():
        print(f"Baixando {MODEL_NOME}...")
        urlretrieve(MODEL_URL, destino)


def ler_gestos(resultado):
    """Lê os 'blendshapes' do rosto (0 a 1) e devolve só os 2 que usamos:
       sobrancelha = sobrancelhas levantadas | beijo = lábios em bico.
       Se o modelo não trouxer, devolve None."""
    if not resultado.face_blendshapes:
        return None
    b = {c.category_name: c.score for c in resultado.face_blendshapes[0]}
    sobr = (b.get("browInnerUp", 0) + b.get("browOuterUpLeft", 0) + b.get("browOuterUpRight", 0)) / 3.0
    return {"sobrancelha": sobr, "beijo": b.get("mouthPucker", 0.0)}


def eye_aspect_ratio(eye):
    """EAR do Lab12: razão entre a altura e a largura do olho.
    Olho aberto ~0,25-0,35; olho fechado -> perto de 0."""
    A = dist(eye[1], eye[5])   # distância vertical 1
    B = dist(eye[2], eye[4])   # distância vertical 2
    C = dist(eye[0], eye[3])   # distância horizontal
    return (A + B) / (2.0 * C)


def pontos_px(landmarks, indices, w, h):
    """Converte landmarks normalizados (0 a 1) em pixels (x*largura, y*altura)."""
    return [(landmarks[i].x * w, landmarks[i].y * h) for i in indices]


def limitar(valor, minimo=0.0, maximo=1.0):
    """Prende um valor entre um mínimo e um máximo (padrão: entre 0 e 1).
    Usado na posição do cursor, para a cabeça nunca mandá-lo fora da tela."""
    return max(minimo, min(maximo, valor))


class GatilhoPorTempo:
    """Dispara UMA vez quando uma condição fica verdadeira por 'tempo_minimo'.
    Separa uma piscada natural (~0,2 s) de um gesto intencional."""

    def __init__(self, tempo_minimo):
        """tempo_minimo: quantos segundos o gesto precisa ser mantido."""
        self.tempo_minimo = tempo_minimo
        self.inicio = None        # instante em que a condição começou
        self.disparou = False     # evita disparar de novo sem soltar o gesto

    def atualizar(self, ativo, agora):
        """Chamada uma vez por quadro. Devolve True no quadro EXATO em que o
        gesto completa o tempo mínimo; nos outros quadros devolve False."""
        if not ativo:                      # condição acabou: zera tudo
            self.inicio = None
            self.disparou = False
            return False
        if self.inicio is None:            # condição acabou de começar
            self.inicio = agora
        if not self.disparou and agora - self.inicio >= self.tempo_minimo:
            self.disparou = True           # só dispara uma vez por "fechada"
            return True
        return False

    def progresso(self, agora):
        """Devolve de 0,0 a 1,0: o quanto o gesto já foi mantido.
        É o que enche as barrinhas coloridas na janela da câmera."""
        if self.inicio is None:
            return 0.0
        if self.disparou:
            return 1.0
        return min((agora - self.inicio) / self.tempo_minimo, 1.0)


class GestoPorDuracao:
    """Olhos fechados: o CLIQUE é executado quando a pessoa ABRE os olhos.
        0,5 a 3,0 s -> 'clique' | menos ou mais que isso -> nada
    O limite de cima deixa a pessoa descansar os olhos sem clicar sem querer."""

    def __init__(self, t_clique, t_max):
        """t_clique: tempo mínimo para valer clique. t_max: acima disso, ignora."""
        self.t_clique, self.t_max = t_clique, t_max
        self.inicio = None        # instante em que os olhos se fecharam

    def atualizar(self, fechado, agora):
        """Chamada uma vez por quadro. Devolve 'clique' no quadro em que a pessoa
        ABRE os olhos, se a duração estiver na faixa válida. Senão, devolve None."""
        if fechado:
            if self.inicio is None:
                self.inicio = agora
            return None
        if self.inicio is None:
            return None
        duracao = agora - self.inicio      # olhos acabaram de abrir
        self.inicio = None
        if duracao > self.t_max:
            return None
        if duracao >= self.t_clique:
            return "clique"
        return None

    def cancelar(self):
        """Perdeu o rosto no meio do gesto: descarta sem clicar."""
        self.inicio = None

    def duracao(self, agora):
        """Há quantos segundos os olhos estão fechados (0 se estiverem abertos).
        Alimenta a barra que muda de cor, para a pessoa saber quando soltar."""
        return 0.0 if self.inicio is None else agora - self.inicio


class CursorSuave:
    """Média móvel exponencial: o cursor 'persegue' o alvo em vez de pular.
    Isso remove o tremor natural da cabeça e do detector."""

    def __init__(self, largura, altura, alpha):
        """Começa no centro da tela. alpha (0 a 1) é o quanto o cursor anda em
        direção ao alvo por quadro: menor = mais estável, maior = mais rápido."""
        self.x, self.y, self.alpha = largura / 2, altura / 2, alpha

    def mover(self, alvo_x, alvo_y):
        """Dá um passo na direção do alvo e devolve a posição em pixels inteiros.
        Fórmula: x_novo = x + alpha * (alvo - x)  (média móvel exponencial)."""
        self.x += self.alpha * (alvo_x - self.x)
        self.y += self.alpha * (alvo_y - self.y)
        return int(self.x), int(self.y)


class Calibracao:
    """Mede, nos primeiros segundos, como É o rosto "normal" da pessoa:
    EAR com olhos abertos (cada rosto é diferente) e posição neutra do nariz."""

    def __init__(self):
        """Toda a inicialização fica em reiniciar(), para a tecla C poder
        recalibrar chamando o mesmo código, sem criar outro objeto."""
        self.reiniciar()

    def reiniciar(self):
        """Zera tudo e começa uma calibração nova (é o que a tecla C faz)."""
        self.inicio = None
        self.ear_a, self.ear_b, self.nx, self.ny = [], [], [], []
        self.g_sobr, self.g_beijo = [], []
        self.base_sobr = self.base_beijo = 0.0
        self.pronta = False
        self.limiar_a = self.limiar_b = 0.2
        self.centro_x = self.centro_y = 0.5

    def coletar(self, ear_a, ear_b, nariz_x, nariz_y, agora, gestos=None):
        """Guarda as medidas de um quadro. Quando completa CALIB_SEGUNDOS,
        calcula as medianas, define os limiares e marca 'pronta = True'.
        Usamos MEDIANA e não média porque ela ignora as piscadas que
        acontecerem durante a calibração (valores extremos não puxam o meio)."""
        if self.inicio is None:
            self.inicio = agora
        self.ear_a.append(ear_a)
        self.ear_b.append(ear_b)
        self.nx.append(nariz_x)
        self.ny.append(nariz_y)
        if gestos:
            self.g_sobr.append(gestos["sobrancelha"])
            self.g_beijo.append(gestos["beijo"])
        if agora - self.inicio >= CALIB_SEGUNDOS:
            # mediana ignora as piscadas que acontecerem durante a calibração
            self.limiar_a = float(np.median(self.ear_a)) * EAR_FATOR
            self.limiar_b = float(np.median(self.ear_b)) * EAR_FATOR
            self.centro_x = float(np.median(self.nx))
            self.centro_y = float(np.median(self.ny))
            if self.g_sobr:      # valores de REPOUSO (rosto relaxado, boca fechada)
                self.base_sobr = float(np.median(self.g_sobr))
                self.base_beijo = float(np.median(self.g_beijo))
            self.pronta = True
            print(f"Calibrado! limiar olho A={self.limiar_a:.3f} | olho B={self.limiar_b:.3f}")

    def progresso(self, agora):
        """De 0,0 a 1,0: o quanto da calibração já passou (enche a barra na tela)."""
        if self.inicio is None:
            return 0.0
        return min((agora - self.inicio) / CALIB_SEGUNDOS, 1.0)

    def reancorar(self, nariz_x, nariz_y, cursor_x, cursor_y, tela_w, tela_h):
        """Depois da rolagem, faz a posição ATUAL da cabeça corresponder à posição
        ATUAL do cursor (senão o cursor 'saltaria' pela tela)."""
        nx_atual = (cursor_x - 1) / (tela_w - 3)
        ny_atual = (cursor_y - 1) / (tela_h - 3)
        self.centro_x = nariz_x - (nx_atual - 0.5) / GANHO_X
        self.centro_y = nariz_y - (ny_atual - 0.5) / GANHO_Y


# ---------- funções de desenho (feedback visual na tela) ----------

def escrever(frame, texto, pos, cor=(255, 255, 255), escala=0.5):
    """Escreve texto na imagem DUAS vezes: primeiro grosso em preto (contorno),
    depois fino na cor. Sem o contorno, o texto desaparece em fundo claro."""
    cv2.putText(frame, texto, pos, cv2.FONT_HERSHEY_SIMPLEX, escala, (0, 0, 0), 3)   # contorno
    cv2.putText(frame, texto, pos, cv2.FONT_HERSHEY_SIMPLEX, escala, cor, 1)


def barra(frame, progresso, pos, tamanho=(150, 12), cor=(0, 255, 255)):
    """Desenha uma barra de progresso (0,0 a 1,0): um retângulo vazio de contorno
    branco e, dentro, um retângulo preenchido proporcional ao progresso.
    É o retorno visual que mostra à pessoa que o gesto está sendo reconhecido."""
    x, y = pos
    largura, altura = tamanho
    cv2.rectangle(frame, (x, y), (x + largura, y + altura), (255, 255, 255), 1)
    cv2.rectangle(frame, (x, y), (x + int(largura * progresso), y + altura), cor, -1)


def barra_duracao(frame, duracao, pos, tamanho=(200, 14)):
    """Barra de 0 a CLIQUE_MAX_SEG com marcas em 'clique' e 'duplo'.
    Amarela = ainda curto | verde = abrir agora faz CLIQUE | azul = faz DUPLO CLIQUE."""
    x, y = pos
    largura, altura = tamanho
    if duracao >= CLIQUE_SEG:
        cor = (0, 220, 0)
    else:
        cor = (0, 220, 255)
    cv2.rectangle(frame, (x, y), (x + largura, y + altura), (255, 255, 255), 1)
    cv2.rectangle(frame, (x, y), (x + int(largura * min(duracao / CLIQUE_MAX_SEG, 1.0)), y + altura), cor, -1)
    mx = x + int(largura * CLIQUE_SEG / CLIQUE_MAX_SEG)
    cv2.line(frame, (mx, y - 3), (mx, y + altura + 3), (255, 255, 255), 1)


def desenhar_olho(frame, pontos, fechado):
    """convexHull do Lab12: contorno do olho (verde = aberto, vermelho = fechado)."""
    contorno = cv2.convexHull(np.array(pontos, dtype=np.int32))
    cor = (0, 0, 255) if fechado else (0, 255, 0)
    cv2.drawContours(frame, [contorno], -1, cor, 1)


# ============================================================
# 3. PROGRAMA PRINCIPAL
# ============================================================

def main():
    """Programa principal. Faz, nesta ordem:

    PREPARAÇÃO
      1. baixa o modelo (só na primeira execução);
      2. configura o pyautogui (fail-safe ligado, sem atraso entre comandos);
      3. abre a webcam com CAP_DSHOW (backend do Windows, abre mais rápido);
      4. cria o FaceLandmarker em modo VIDEO (quadro a quadro com timestamp);
      5. posiciona a janelinha de prévia no canto superior direito.

    LOOP (repete para cada quadro da câmera, até ESC)
      6. lê o quadro, espelha (flip) e converte BGR -> RGB para o MediaPipe;
      7. detecta o rosto e calcula EAR dos dois olhos, nariz e blendshapes;
      8. se ainda está calibrando, só coleta e mostra a barra;
      9. se já calibrou, avalia os gestos e manda os comandos ao pyautogui;
     10. desenha o retorno visual e lê as teclas de atalho (P, C, ESC).

    ENCERRAMENTO
     11. solta o botão do mouse se estava arrastando, libera a câmera
         e fecha as janelas.
    """
    baixar_modelo()

    pyautogui.FAILSAFE = True   # canto superior esquerdo = abortar
    pyautogui.PAUSE = 0         # sem atraso entre comandos (cursor fluido)
    tela_w, tela_h = pyautogui.size()

    # --- câmera (Lab01) ---
    cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)   # CAP_DSHOW abre mais rápido no Windows
    if not cap.isOpened():
        cap = cv2.VideoCapture(CAM_INDEX)
    if not cap.isOpened():
        print("Não foi possível abrir a câmera. Troque CAM_INDEX no topo do arquivo.")
        return

    # --- atalhos da API atual do MediaPipe (Lab13) ---
    BaseOptions = mp.tasks.BaseOptions
    RunningMode = mp.tasks.vision.RunningMode
    FaceLandmarker = mp.tasks.vision.FaceLandmarker
    FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions

    face_options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_DIR / MODEL_NOME)),
        running_mode=RunningMode.VIDEO,   # vídeo/webcam quadro a quadro com timestamp
        num_faces=1,
        output_face_blendshapes=True,     # números de 0 a 1 para boca, sobrancelhas etc.
    )

    # --- janela da prévia (canto superior direito, abaixo da barra de título) ---
    cv2.namedWindow(JANELA, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(JANELA, JANELA_LARGURA, JANELA_ALTURA)
    cv2.moveWindow(JANELA, tela_w - JANELA_LARGURA - 10, 45)
    if JANELA_SEMPRE_NO_TOPO:
        try:
            cv2.setWindowProperty(JANELA, cv2.WND_PROP_TOPMOST, 1)
        except Exception:     # versões antigas do OpenCV não têm essa opção
            pass

    # --- estado do programa ---
    pausado = False
    modo_rolagem = False
    ref_rolagem_y = 0.5           # altura do nariz quando a rolagem foi ligada
    arrastando = False
    calibrado_antes = False
    calib = Calibracao()
    cursor = CursorSuave(tela_w, tela_h, SUAVIZACAO)
    gesto_clique = GestoPorDuracao(CLIQUE_SEG, CLIQUE_MAX_SEG)
    wink_esq = GatilhoPorTempo(WINK_ESQUERDO_SEG)
    g_sobr = GatilhoPorTempo(SOBRANCELHA_SEG)
    g_beijo = GatilhoPorTempo(BEIJO_SEG)
    aviso = ""            # última ação (ex.: "CLIQUE!") mostrada na tela
    aviso_ate = 0.0
    ultimo_ts = -1

    with FaceLandmarker.create_from_options(face_options) as face_lm:

        t0 = time.perf_counter()

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Não foi possível capturar o vídeo")
                break

            frame = cv2.flip(frame, 1)      # espelho: mover a cabeça p/ direita = cursor p/ direita
            h, w, _ = frame.shape
            agora = time.perf_counter()

            # MediaPipe espera RGB (OpenCV usa BGR) -> converte, como no Lab01/Lab13
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            # timestamp em ms, sempre crescente (exigência do modo VIDEO)
            ts = int((agora - t0) * 1000)
            if ts <= ultimo_ts:
                ts = ultimo_ts + 1
            ultimo_ts = ts

            resultado = face_lm.detect_for_video(mp_image, ts)

            if modo_rolagem:
                escrever(frame, "MODO ROLAGEM (olho esq. fechado = sair)", (10, 20), (0, 200, 255))
            else:
                escrever(frame, "MODO CURSOR" + ("  [PAUSADO]" if pausado else "") + ("  [ARRASTANDO]" if arrastando else ""), (10, 20), (0, 255, 255))

            if resultado.face_landmarks:
                lm = resultado.face_landmarks[0]

                olho_a = pontos_px(lm, OLHO_A, w, h)
                olho_b = pontos_px(lm, OLHO_B, w, h)
                ear_a = eye_aspect_ratio(olho_a)
                ear_b = eye_aspect_ratio(olho_b)
                nariz = lm[NARIZ]
                gestos = ler_gestos(resultado)
                cv2.circle(frame, (int(nariz.x * w), int(nariz.y * h)), 5, (255, 0, 0), -1)

                if not calib.pronta:
                    # ---- fase de calibração ----
                    calib.coletar(ear_a, ear_b, nariz.x, nariz.y, agora, gestos)
                    escrever(frame, "CALIBRANDO: olhe para a tela", (10, 42), (0, 200, 255))
                    escrever(frame, "olhos abertos, boca fechada, rosto relaxado", (10, 62), (0, 200, 255))
                    barra(frame, calib.progresso(agora), (10, 72), (200, 12), (0, 200, 255))
                    desenhar_olho(frame, olho_a, False)
                    desenhar_olho(frame, olho_b, False)
                else:
                    calibrado_antes = True

                    # ---- gestos do rosto (sobrancelhas, beijinho) ----
                    sobr_ativa = beijo_ativo = False
                    if gestos:
                        sobr_ativa = gestos["sobrancelha"] > calib.base_sobr + SOBRANCELHA_DELTA
                        beijo_ativo = gestos["beijo"] > calib.base_beijo + BEIJO_DELTA

                    # beijinho = pausa/retoma (vale mesmo pausado, senão não dá para voltar)
                    if g_beijo.atualizar(beijo_ativo, agora):
                        pausado = not pausado
                        if pausado and arrastando:
                            pyautogui.mouseUp()
                            arrastando = False
                        if not pausado:      # retomou: cabeça e cursor voltam a "casar"
                            px, py = pyautogui.position()
                            cursor.x, cursor.y = px, py
                            calib.reancorar(nariz.x, nariz.y, px, py, tela_w, tela_h)
                        aviso, aviso_ate = ("PAUSADO" if pausado else "RETOMADO"), agora + 1.0

                    # sobrancelhas = liga/desliga arrastar (segura/solta o botão do mouse)
                    if g_sobr.atualizar(sobr_ativa, agora) and not pausado:
                        if arrastando:
                            pyautogui.mouseUp()
                        else:
                            pyautogui.mouseDown()
                        arrastando = not arrastando
                        aviso, aviso_ate = ("ARRASTANDO: mova a cabeca" if arrastando else "SOLTOU"), agora + 1.0

                    # o cursor congela durante os gestos do rosto, para a cabeça não
                    # arrastar o cursor enquanto a pessoa faz a expressão
                    gesto_rosto_ativo = sobr_ativa or beijo_ativo

                    fechado_a = ear_a < calib.limiar_a
                    fechado_b = ear_b < calib.limiar_b
                    ambos_fechados = fechado_a and fechado_b
                    # wink: só UM olho fechado e o outro bem aberto.
                    # O olho direito não tem função: fechar só ele não faz nada.
                    wink_esquerdo = fechado_a and ear_b > calib.limiar_b * WINK_MARGEM

                    desenhar_olho(frame, olho_a, fechado_a)
                    desenhar_olho(frame, olho_b, fechado_b)

                    # barras dos gestos do rosto (enchem enquanto o gesto é mantido)
                    for i, (nome, gatilho, cor) in enumerate((("Sobr.", g_sobr, (255, 150, 0)),
                                                              ("Beijo", g_beijo, (200, 120, 255)))):
                        escrever(frame, nome, (250, 45 + i * 25), (255, 255, 255), 0.45)
                        barra(frame, gatilho.progresso(agora), (305, 34 + i * 25), (110, 11), cor)

                    if modo_rolagem:
                        # cabeça para cima/baixo em relação ao ponto onde a rolagem foi ligada
                        desvio = nariz.y - ref_rolagem_y
                        if abs(desvio) > ROLAGEM_ZONA and not pausado and not (fechado_a or fechado_b or gesto_rosto_ativo):
                            passo = int(-(desvio - np.sign(desvio) * ROLAGEM_ZONA) * ROLAGEM_GANHO)
                            if passo != 0:
                                pyautogui.scroll(passo)
                        escrever(frame, "cabeca p/ cima = sobe | p/ baixo = desce", (10, 42), (0, 200, 255))
                    else:
                        # cursor só se move com os olhos abertos (evita "escorregar" ao piscar)
                        if not (fechado_a or fechado_b or gesto_rosto_ativo):
                            nx = limitar(0.5 + (nariz.x - calib.centro_x) * GANHO_X)
                            ny = limitar(0.5 + (nariz.y - calib.centro_y) * GANHO_Y)
                            cx, cy = cursor.mover(nx * (tela_w - 3) + 1, ny * (tela_h - 3) + 1)
                            if not pausado:
                                pyautogui.moveTo(cx, cy)

                        # clique / duplo clique: decidido ao ABRIR os olhos
                        acao = gesto_clique.atualizar(ambos_fechados, agora)
                        if acao == "clique" and not pausado:
                            pyautogui.click()
                            aviso, aviso_ate = "CLIQUE!", agora + 0.8

                        escrever(frame, f"EAR A:{ear_a:.2f} B:{ear_b:.2f}", (10, 42))
                        escrever(frame, "Clique", (10, 68))
                        barra_duracao(frame, gesto_clique.duracao(agora), (70, 57))

                    # wink esquerdo liga/desliga a rolagem (vale nos dois modos)
                    if wink_esq.atualizar(wink_esquerdo, agora):
                        modo_rolagem = not modo_rolagem
                        gesto_clique.cancelar()
                        if modo_rolagem:
                            ref_rolagem_y = nariz.y
                            aviso = "ROLAGEM LIGADA"
                        else:
                            calib.reancorar(nariz.x, nariz.y, cursor.x, cursor.y, tela_w, tela_h)
                            aviso = "ROLAGEM DESLIGADA"
                        aviso_ate = agora + 1.0
            else:
                gesto_clique.cancelar()
                wink_esq.atualizar(False, agora)
                escrever(frame, "Rosto nao detectado", (10, 42), (0, 0, 255))

            if agora < aviso_ate:
                escrever(frame, aviso, (10, h - 15), (0, 255, 0), 0.8)
            escrever(frame, "P pausa | C recalibrar | ESC sair", (10, h - 45), (255, 255, 255), 0.4)

            cv2.imshow(JANELA, frame)

            # ---- teclas de atalho (para quem ajuda a configurar) ----
            tecla = cv2.waitKey(1) & 0xFF
            if tecla == 27:                         # ESC
                break
            elif tecla in (ord("p"), ord("P")):
                pausado = not pausado
                if pausado and arrastando:
                    pyautogui.mouseUp()
                    arrastando = False
            elif tecla in (ord("c"), ord("C")):
                calib.reiniciar()
                modo_rolagem = False
                calibrado_antes = False
                if arrastando:
                    pyautogui.mouseUp()
                    arrastando = False

    if arrastando:
        pyautogui.mouseUp()      # nunca deixa o botão do mouse preso ao sair
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
