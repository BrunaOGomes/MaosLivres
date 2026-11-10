# MãosLivres (CitizenTech) — Passo a passo

Controle do notebook **sem usar os braços**, só com cabeça e rosto. Este guia explica **o que cada parte do código faz e por quê**, para vocês defenderem o projeto se o professor perguntar.

Arquivos: `controle_sem_toque.py` (aplicação), `teste_validacao.py` (mede a eficácia), `verificar_ambiente.py` (diagnóstico da instalação), `MaosLivres_Pitch.pptx` (slides), `pitch_e_gravacao.md` (roteiro e gravação).

---

## 1. O que o projeto faz

| Gesto da pessoa | O que acontece | Técnica |
|---|---|---|
| Mover a cabeça | Cursor acompanha a ponta do nariz | Landmark 1 do MediaPipe + suavização |
| Fechar os 2 olhos e abrir (0,5 a 3,0 s) | **Clique** | EAR (Lab12) + duração |
| Fechar só o olho **esquerdo** por 0,6 s | Liga/desliga **modo rolagem** (cabeça p/ cima sobe, p/ baixo desce) | wink + posição do nariz |
| **Levantar as sobrancelhas** por 0,7 s | Liga/desliga **arrastar** (segura o botão do mouse; levantar de novo solta) | Blendshapes `browInnerUp` + `browOuterUp` |
| **Beijinho** (bico) por 1,0 s | **Pausa/retoma** tudo (para conversar sem mexer o cursor) | Blendshape `mouthPucker` |

O olho **direito** não tem função: fechar só ele não faz nada.

**Por que só rosto?** Para quem não tem braços, o modo "mão" não serve. Removemos esse modo e investimos em tudo que o rosto consegue fazer: mover, clicar, rolar, arrastar e pausar.

**Por que o projeto não digita texto?** Ver a seção 7: é uma limitação do Windows que nós investigamos e documentamos, não um esquecimento. Essa é uma pergunta provável do professor, e a resposta está pronta lá.

**Fluxo de cada quadro da câmera:**

```
Webcam → flip (espelho) → BGR→RGB → MediaPipe FaceLandmarker (478 pontos)
      → EAR dos olhos + posição do nariz + blendshapes
      → calibração individual → suavização
      → PyAutoGUI: move / clica / rola / arrasta
```

---

## 2. Instalação (Windows, Python 3.12.10)

No **PowerShell**, na pasta do projeto:

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe verificar_ambiente.py
```

Depois basta usar os atalhos **`iniciar.bat`** (roda o sistema) e **`validar.bat`** (roda o teste de validação).

O `verificar_ambiente.py` confere as versões das bibliotecas, testa os índices de câmera 0 a 3, baixa o `face_landmarker.task` para a pasta `models/` e confirma que o modelo carrega. Ele **não mexe no mouse**, então é seguro rodar a qualquer momento. **Não precisa instalar dlib** (seção 3).

Versões fixadas em `requirements.txt`: mediapipe 1.2.2, opencv-python 5.0.0.93, pyautogui 0.9.54, numpy 2.5.4.

---

## 3. dlib × MediaPipe: o `shape_predictor_68_face_landmarks.dat`

O professor disse que podem usar o dlib se souberem explicar. Explicação, caso ele pergunte:

- O `.dat` é um arquivo de **pesos treinados** (conjunto de árvores de regressão em cascata, método de Kazemi e Sullivan, 2014). Ele **não acha o rosto**: quem acha é o `dlib.get_frontal_face_detector()` (HOG + SVM). O `.dat` recebe a imagem e o retângulo do rosto e devolve **68 pontos (x, y)**.
- **Por que não usamos:** (1) instalar o dlib no Windows exige CMake e Visual Studio C++ e costuma falhar no Python 3.12; (2) o `.dat` é grande e precisa baixar à parte; (3) o MediaPipe dá 478 pontos 3D, mais estável, com `pip install` simples (foi o que o professor sugeriu); (4) segundo a documentação da dlib, o modelo de 68 pontos foi treinado num dataset com restrição de uso comercial, e a ideia aqui é virar um produto de impacto (MediaPipe é Apache 2.0).
- **O que aproveitamos do Lab12:** a função `eye_aspect_ratio()` e a ordem dos 6 pontos do olho são **idênticas**. Só mudou a origem dos pontos. Boa frase para o pitch técnico: *"reaproveitamos o EAR do Lab12 sobre os landmarks do MediaPipe"*.

---

## 4. O código, bloco por bloco

### Bloco 1 — Configurações
Constantes agrupadas no topo (sensibilidade, tempos de clique etc.). Tabela de ajustes na seção 6.

### Bloco 2 — Funções auxiliares

**`eye_aspect_ratio(eye)`** (do Lab12)

```
        p2   p3
   p1              p4        EAR = ( |p2-p6| + |p3-p5| ) / ( 2 · |p1-p4| )
        p6   p5
```
Altura do olho dividida pela largura. Aberto ≈ 0,25–0,35; fechado ≈ 0. Dividir pela largura torna o valor independente da distância até a câmera.

**`pontos_px()`** — os landmarks vêm normalizados (0 a 1); multiplicamos x pela largura e y pela altura (igual ao que o Lab13 faz com os keypoints).

**`limitar()`** — prende um valor entre 0 e 1, para a posição calculada do cursor nunca sair da tela.

**`GatilhoPorTempo`** — dispara **uma vez** quando uma condição dura o tempo mínimo (usado no wink esquerdo, nas sobrancelhas e no beijinho). É o que separa piscada natural (~0,1–0,4 s) de gesto intencional. O método `progresso()` alimenta as barrinhas na tela.

**`GestoPorDuracao`** — para os dois olhos fechados. A ação é decidida **quando a pessoa abre os olhos**, pela duração: 0,5–3,0 s = clique; menos que 0,5 s = piscada natural (ignora); mais de 3,0 s = ignora (descanso/cansaço). Se o rosto sair da câmera no meio do gesto, `cancelar()` descarta sem clicar.

**`CursorSuave`** — média móvel exponencial: `x_novo = x + alpha·(alvo − x)`. Tira o tremor natural da cabeça e do detector.

**`Calibracao`** — nos 3 primeiros segundos mede o EAR com olhos abertos de **cada olho**, a posição neutra do nariz e o valor de repouso dos blendshapes. O limiar de "fechado" vira 70% do EAR normal da pessoa (mediana, para ignorar piscadas). Isso torna o sistema **inclusivo**: ele se adapta ao rosto, não o contrário. `reancorar()` é usada ao sair da rolagem e ao retomar da pausa (ver abaixo).

### Bloco 2b — Gestos do rosto (blendshapes)
Além dos 478 pontos, o `FaceLandmarker` pode devolver **52 "blendshapes"**: números de 0 a 1 dizendo o quanto cada expressão está ativa (`mouthPucker` = bico, `browInnerUp` = sobrancelhas levantadas...). Basta ligar `output_face_blendshapes=True` nas opções (Lab13). A função `ler_gestos()` pega só os 2 que usamos: sobrancelha (média de `browInnerUp`, `browOuterUpLeft` e `browOuterUpRight`) e beijo (`mouthPucker`).

**Por que calibrar também esses?** Cada rosto tem um valor de repouso diferente. Na calibração medimos a **mediana de repouso** e o gesto só vale quando o valor passa de `repouso + DELTA`. Mesma ideia do EAR.

**Como evitamos disparos falsos?** (1) tempo mínimo de 0,7 a 1,0 s: uma fala ou um sorriso passam rápido; (2) escolhemos gestos que quase não aparecem ao falar (sobrancelhas, bico); (3) o **beijinho pausa tudo**, então dá para conversar à vontade; (4) durante qualquer um desses gestos o **cursor congela**, porque a cabeça mexe junto.

**Arrastar:** o primeiro gesto de sobrancelhas chama `pyautogui.mouseDown()` (segura o botão); depois, movendo a cabeça, a janela/seleção acompanha; o segundo gesto chama `mouseUp()`. Ao pausar, recalibrar ou sair, o programa **solta o botão sozinho** para nunca deixá-lo preso.

**Ao retomar da pausa**, o programa reancora a cabeça na posição atual do cursor (`reancorar`), para o cursor não saltar.

### Bloco 3 — Desenho
`barra_duracao()` mostra uma barra que **muda de cor**: amarela (ainda curto) e verde (abrir agora = clique), com uma marca em 0,5 s e o fim da barra em 3,0 s. Quem usa precisa **ver** o que o sistema entendeu. `barra()` desenha o progresso dos outros gestos. `desenhar_olho()` usa `cv2.convexHull` como no detector de fadiga do Lab12 (verde aberto, vermelho fechado). `escrever()` desenha o texto duas vezes, grosso em preto e fino na cor, para o texto ficar legível sobre qualquer imagem.

### Bloco 4 — `main()`: preparação
`FAILSAFE`/`PAUSE=0` do pyautogui; abre a câmera (Lab01, com `CAP_DSHOW` no Windows); cria o `FaceLandmarker` em `RunningMode.VIDEO` com `with ... as ...` (Lab13); posiciona a janelinha de prévia no canto superior direito, sempre no topo.

### Bloco 5 — O loop (um quadro por vez)
1. `cv2.flip` (espelho) e conversão BGR→RGB para o `mp.Image`.
2. Timestamp crescente em ms (`perf_counter`), exigência do `detect_for_video`.
3. Calcula EAR dos dois olhos, lê o nariz e lê os blendshapes.
4. **Calibrando?** só coleta e mostra a barra. **Pronto?** segue para os gestos.
5. **Modo cursor:** a posição do nariz vira posição na tela: `0,5 + (nariz − centro) × ganho`, limitada entre 0 e 1. O cursor **só se move com os olhos abertos**, senão a cabeça mexe um pouco ao piscar e o cursor "escorrega" antes do clique.
6. **Modo rolagem:** o cursor fica **parado** e a altura do nariz em relação ao ponto em que a rolagem foi ligada vira a velocidade (com uma zona morta para não rolar sozinho). Ao desligar, `reancorar()` recalcula o centro para que a cabeça na posição atual corresponda ao cursor onde ele parou, evitando um "salto" na tela.
7. Wink esquerdo: o olho fechado + o outro **bem aberto** (margem de 10%, `WINK_MARGEM`) para não confundir com piscada dupla.

### Bloco 6 — Teclas de atalho (para quem ajuda a configurar)
**P** pausa, **C** recalibra, **ESC** sai. Funcionam com a janela da câmera em foco. A pessoa que usa o sistema não precisa de nenhuma delas: todos os comandos dela são gestos.

---

## 5. Como rodar e calibrar (primeira vez)

1. Luz **de frente** (janela ou luminária atrás da tela), nunca de costas.
2. Câmera na altura dos olhos, 50–70 cm.
3. Rode o `iniciar.bat`. Olhe para a tela 3 s com os olhos abertos, **rosto relaxado e boca fechada** (é daí que saem os valores de repouso dos gestos).
4. Mova a cabeça devagar: o cursor acompanha o nariz.
5. Feche os dois olhos até a barra "Clique" ficar **verde** e abra: clique. Piscada normal não faz nada. Mais de 3 s também não faz nada.
6. Teste o wink **esquerdo** (liga e desliga a rolagem).
7. Teste as **sobrancelhas** (arrastar uma janela) e o **beijinho** (pausa). As duas barras no canto da prévia enchem enquanto o gesto é mantido.
8. Algo estranho? Tecla **C** recalibra.

---

## 6. Ajustes e problemas comuns

| Sintoma | Solução (constante no topo do arquivo) |
|---|---|
| Câmera não abre / preta | Rodar `verificar_ambiente.py` e usar o índice indicado em `CAM_INDEX` |
| Cursor rápido demais | Diminuir `GANHO_X` / `GANHO_Y` (ex.: 3.5 e 4.5) |
| Cursor não alcança os cantos | Aumentar `GANHO_X` / `GANHO_Y` |
| Cursor trêmulo | Diminuir `SUAVIZACAO` (ex.: 0.15) |
| Cursor atrasado | Aumentar `SUAVIZACAO` (ex.: 0.40) |
| Clica sozinho ao piscar | Aumentar `CLIQUE_SEG` (ex.: 0.7) ou diminuir `EAR_FATOR` (ex.: 0.60) |
| Fecha o olho e não clica | Aumentar `EAR_FATOR` (ex.: 0.80) e recalibrar (**C**) |
| Wink dispara junto com piscada dupla | Aumentar `WINK_MARGEM` (ex.: 1.20) |
| Rolagem rápida/lenta demais | `ROLAGEM_GANHO` (ex.: 300 ou 900) |
| Rola sozinha | Aumentar `ROLAGEM_ZONA` (ex.: 0.05) |
| Arrasta sozinho | Aumentar `SOBRANCELHA_DELTA` (ex.: 0.45) ou `SOBRANCELHA_SEG` |
| Sobrancelhas não acionam | Diminuir `SOBRANCELHA_DELTA` (ex.: 0.25) |
| Pausa sozinha ao falar | Aumentar `BEIJO_DELTA` (ex.: 0.55) ou `BEIJO_SEG` (ex.: 1.3) |
| Prévia da câmera atrapalha cliques | Mudar `JANELA_LARGURA`/`JANELA_ALTURA` ou a posição em `cv2.moveWindow` |
| Com 2 monitores, o cursor não chega na segunda tela | Limitação conhecida: `pyautogui.size()` devolve só o monitor principal. Usar tudo no monitor principal |

**Segurança:** se o cursor "fugir", mouse físico no canto superior esquerdo (fail-safe) ou **Ctrl+C** no terminal.

---

## 7. Por que não digitamos texto (investigação documentada)

Esta seção existe porque é a pergunta mais provável do professor: *"e para escrever?"*. A resposta honesta, com as evidências:

Nós implementamos: o gesto de **abrir a boca** chamava o teclado virtual do Windows (`osk.exe`) e o gesto de **sorrir** apertava a tecla sob o cursor. O gesto era reconhecido corretamente, mas **a letra nunca entrava**. Investigamos e medimos:

| Teste | Resultado |
|---|---|
| `taskkill` para fechar o `osk.exe` | **Acesso negado** |
| Mensagem `WM_CLOSE` para a janela do `osk.exe` | bloqueada |
| `ShowWindow(SW_HIDE)` na janela do `osk.exe` | bloqueada |
| `pyautogui.click()` sobre uma tecla | nenhuma letra |
| Clique com duração humana (80 ms) sobre uma tecla | nenhuma letra |
| Cursor **parado** 2,5 s sobre a tecla (modo hover do Windows) | **digitou 2 letras** |
| `pyautogui.typewrite()` e `press()` numa janela comum | **funcionaram** |

**Conclusão:** o `osk.exe` roda com privilégio de **UIAccess**, acima do nosso programa, e o Windows **descarta cliques gerados por programa** sobre janelas privilegiadas. Não há ajuste no nosso código que resolva isso sem rodar como administrador. O modo "passar o mouse sobre as teclas" funciona porque lê a posição real do cursor em vez de depender de clique, mas aí quem digita é o Windows, não o nosso gesto.

Por isso **removemos a funcionalidade** em vez de entregar algo que não funciona.

**O caminho para a próxima versão** (e boa resposta para "como vocês resolveriam?"): o projeto desenha o **próprio teclado** na janela do OpenCV, sabe qual tecla está sob o cursor e envia a letra com `pyautogui.press()`. Isso usa envio de **teclas** em vez de cliques, que é um mecanismo diferente e **já testamos que funciona** nesta máquina, sem privilégio de administrador. Também fica mais acessível: teclas grandes e teclado como parte do produto.

---

## 8. Validação: números para o pitch

O enunciado pede **validar hipóteses** e **medir impacto**.

1. Janela 1: `iniciar.bat` (deixe rodando).
2. Janela 2: `validar.bat`.
3. Informe nome e modo (`rosto` ou `mouse`). Aparecem **8 alvos verdes** um por vez; o script mede tempo por acerto e cliques errados (usa o **evento de mouse do Lab11**, `cv2.setMouseCallback`).
4. Resultados em `resultados_validacao.csv`.

**Como fazer:** 3 a 5 pessoas, com consentimento, uma rodada `rosto` (sem tocar no mouse) e uma `mouse` (referência). Calculem taxa de acerto e tempo médio. Esses números entram no slide 4 do PowerPoint (`XX%` e `X,X s`).

**Sejam honestos:** esse teste mostra que a *tecnologia* funciona, mas ainda **não** foi feito com pessoas sem braços. Digam isso e apresentem como próximo passo (parceria com centro de reabilitação). Isso aumenta a credibilidade, um dos critérios do enunciado.

---

## 9. Perguntas que o professor pode fazer

**Por que MediaPipe e não Haar Cascade?** O Haar só dá um retângulo do rosto. Precisamos de olhos e nariz precisos; o MediaPipe dá 478 pontos em tempo real.

**Como diferencia piscada natural de clique?** Pela duração. A piscada natural dura bem menos que 0,5 s; o clique exige 0,5 s ou mais com os dois olhos abaixo de um limiar calibrado para a pessoa.

**Por que o clique acontece ao abrir os olhos?** Porque assim o sistema sabe quanto tempo durou o gesto e consegue separar clique (0,5 a 3 s) de descanso (mais de 3 s).

**Por que calibrar?** Cada rosto tem um EAR de olho aberto diferente; um limiar fixo falharia com algumas pessoas.

**Por que suavizar?** O detector oscila um pouco a cada quadro; a média móvel exponencial filtra o tremor (ideia parecida com os filtros de convolução do Lab04 para ruído).

**Como o programa sabe que a pessoa levantou as sobrancelhas?** O MediaPipe calcula "blendshapes" (números de 0 a 1 por expressão). Usamos a média de `browInnerUp`, `browOuterUpLeft` e `browOuterUpRight`, comparada ao valor de repouso da pessoa medido na calibração.

**Falar não aciona os gestos?** Os gestos exigem manter a posição por 0,7 a 1,0 s e passar de um limiar acima do repouso; fala comum não faz isso. Se mesmo assim atrapalhar, o beijinho pausa tudo.

**E para escrever um texto?** Ver a seção 7: investigamos, medimos e documentamos por que o teclado virtual do Windows não aceita cliques de programa, e qual é o caminho para resolver.

**E a privacidade?** Tudo roda localmente. Nenhuma imagem é gravada ou enviada. Só as posições dos pontos são usadas, quadro a quadro.

**Quais as limitações?** Precisa de boa luz frontal; não digita texto (seção 7); alcança só o monitor principal; ainda não foi validado com pessoas sem braços; pessoas com movimentos involuntários de cabeça podem precisar de ajustes.

---

## 10. Mapa de conteúdo da disciplina

| Parte do projeto | Lab |
|---|---|
| Captura de vídeo e loop principal | Lab01 |
| BGR→RGB, pixels e canais | Lab01 |
| Suavização como filtragem de ruído (conceito) | Lab04 |
| Contorno do olho (`convexHull`) | Lab05 / Lab12 |
| EAR | Lab12 |
| FaceLandmarker, modo VIDEO | Lab13 |
| Evento de mouse no teste de validação | Lab11 |

---

## 11. Melhorias futuras (slide de próximos passos)

- **Teclado próprio do projeto**, desenhado na janela do OpenCV, com teclas grandes e envio por `pyautogui.press()` (ver seção 7).
- Digitação por voz integrada a um gesto (Win + H) e sugestão de palavras.
- Suporte a múltiplos monitores.
- Equalização de histograma (Lab03) para pouca luz.
- Instalador `.exe` para uso sem programar.
- Testes com usuários reais em parceria com centros de reabilitação e associações.
