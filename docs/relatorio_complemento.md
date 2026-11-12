# Complemento do relatório em PDF

Seções para **acrescentar** ao PDF que você já tem. O que está lá (Contexto, Métodos, Análises, Considerações finais) está correto: isto preenche as lacunas que a rubrica cobra e que hoje não estão no documento.

Onde inserir cada bloco está indicado no título. Os valores entre `[ ]` são os que você preenche com os dados reais.

---

## ➜ INSERIR em "2. Métodos", como nova seção 2.2 (antes da atual 2.2)

### 2.2 Justificativa das escolhas técnicas

A rubrica pede justificar as escolhas técnicas. Comparamos três abordagens de detecção facial vistas na disciplina:

| Abordagem | O que entrega | Por que foi ou não escolhida |
|---|---|---|
| **Haar Cascade** (OpenCV) | Retângulo delimitador do rosto | **Descartada.** Entrega apenas a região do rosto, sem localizar olhos e nariz com a precisão necessária para calcular abertura ocular. |
| **dlib + shape_predictor_68** | 68 pontos faciais 2D | **Descartada.** Exige compilação com CMake e Visual Studio C++ no Windows, com falhas frequentes no Python 3.12; o arquivo de pesos é grande e precisa de download separado; o modelo de 68 pontos foi treinado em dataset com restrição de uso comercial. |
| **MediaPipe FaceLandmarker** (escolhida) | 478 pontos 3D + 52 blendshapes | **Escolhida.** Instalação por `pip`, 478 pontos mais estáveis, modo VIDEO com rastreamento temporal, blendshapes prontos para expressões, licença Apache 2.0, roda em CPU em tempo real. |

**Aproveitamento da disciplina:** a função `eye_aspect_ratio()` e a ordem dos 6 pontos do olho são as mesmas do laboratório de detecção de fadiga; mudou apenas a origem dos pontos (MediaPipe em vez de dlib). O contorno do olho usa `cv2.convexHull`, e o teste de validação usa o evento de mouse do OpenCV (`cv2.setMouseCallback`).

**Por que modo VIDEO e não IMAGE:** o `RunningMode.VIDEO` recebe um timestamp crescente e mantém rastreamento entre quadros, o que estabiliza os pontos e reduz o tremor. O modo IMAGE trataria cada quadro isoladamente.

**Por que calibração individual:** um limiar fixo de abertura ocular excluiria pessoas, porque o EAR de olho aberto varia de rosto para rosto. Nos 3 segundos iniciais medimos a **mediana** do EAR de cada olho e definimos o limiar em 70% desse valor. Usamos mediana e não média justamente para que piscadas ocorridas durante a calibração não contaminem a medida.

**Por que média móvel exponencial:** o detector oscila alguns pixels por quadro. A suavização `x ← x + α·(alvo − x)` com α = 0,25 filtra esse ruído, mesma lógica dos filtros de suavização vistos na disciplina. Valores menores de α dão mais estabilidade e menos resposta.

**Por que a duração define o gesto:** separar comando intencional de movimento natural exige tempo mínimo. Uma piscada natural dura cerca de 0,1 a 0,4 s; exigimos 0,5 s para o clique. O limite superior de 3 s existe para que a pessoa possa fechar os olhos para descansar sem acionar nada.

---

## ➜ INSERIR em "3. Análises", como nova seção 3.1 (antes da tabela de validação)

### 3.1 Desempenho computacional

Um sistema de acessibilidade precisa responder em tempo real: se o processamento de cada quadro não couber no intervalo entre dois quadros da câmera, o cursor atrasa e a interação se torna inviável. Uma webcam de 30 FPS entrega um quadro a cada **33,3 ms**, que é o orçamento de tempo disponível.

Medimos com o `benchmark_desempenho.py`, em 300 quadros, descartando 20 quadros de aquecimento. Hardware: notebook, CPU sem placa de vídeo dedicada, webcam integrada a 640x480.

| Etapa | Média | Mediana | p95 |
|---|---|---|---|
| Pré-processamento (flip + BGR→RGB) | [0,46] ms | [0,39] ms | [0,63] ms |
| Inferência MediaPipe (`detect_for_video`) | [2,42] ms | [2,20] ms | [3,68] ms |
| Pós-processamento (EAR + blendshapes) | [0,00] ms | [0,00] ms | [0,00] ms |
| **Processamento total (nosso código)** | **[2,88] ms** | [2,59] ms | [4,80] ms |
| Espera da webcam (`cap.read`) | [47,34] ms | [45,54] ms | [62,82] ms |
| **Total do ciclo** | **[50,22] ms** | [48,14] ms | [66,03] ms |

Indicadores:

- **Taxa de detecção do rosto:** [preencher] %
- **FPS real:** [20,3]
- **Ocupação do orçamento de tempo real:** [9] % dos 33,3 ms
- **Folga computacional:** [11]x

*Figura 1 — `resultados/grafico_latencia.png`: distribuição da latência de processamento por quadro.*

*Figura 2 — `resultados/grafico_etapas.png`: participação de cada etapa no ciclo.*

*Figura 3 — `resultados/grafico_fps.png`: FPS ao longo da execução.*

**Análise crítica.** O resultado mais relevante é contraintuitivo: **o gargalo não é o algoritmo de visão computacional, é o hardware da câmera.** A inferência do MediaPipe consome cerca de [2,4] ms, enquanto a espera pelo próximo quadro da webcam consome cerca de [47] ms, ou [94] % do ciclo.

Três consequências:

1. O processamento ocupa apenas [9] % do orçamento de tempo real, o que confirma que a solução roda em notebook comum **sem GPU dedicada** — requisito central para uma tecnologia assistiva de custo zero.
2. Otimizar o algoritmo não aumentaria a fluidez. Ganho de FPS exigiria uma câmera melhor ou captura em *thread* separada, não código mais rápido.
3. A folga de [11]x é o que viabiliza os próximos passos (teclado próprio, novos gestos) sem comprometer o tempo real.

**Nota metodológica.** A separação entre "processamento" e "espera da câmera" é necessária porque o `cap.read()` do OpenCV é bloqueante: ele devolve o quadro somente quando a câmera o entrega. Medir apenas o tempo total atribuiria ao algoritmo uma latência que é, na verdade, limitação física do sensor.

---

## ➜ SUBSTITUIR a numeração da seção de validação por "3.2" e acrescentar ao final dela

### 3.2 Desempenho de uso

*(mantenha o texto e a tabela que você já tem, e acrescente:)*

Indicadores derivados:

- **Custo relativo de tempo:** o controle por rosto levou [X]x o tempo do mouse por alvo.
- **Diferença de acerto:** [±X] pontos percentuais em relação ao mouse.
- **Desvio padrão entre participantes:** [X] s no modo rosto, [X] s no modo mouse.

*Figura 4 — `resultados/grafico_taxa_acerto.png`*

*Figura 5 — `resultados/grafico_tempo_alvo.png`*

*Figura 6 — `resultados/grafico_por_participante.png`*

**Análise crítica.** [Escreva depois de ver os seus números. Pontos a abordar:]

- A taxa de acerto no modo rosto é alta o suficiente para uso prático? Erros concentraram-se em alvos perto das bordas da tela?
- O custo de tempo observado é aceitável para o público-alvo, considerando que a alternativa é depender de outra pessoa?
- O desvio padrão entre participantes foi alto? Isso indicaria curva de aprendizado, já que todos usaram o sistema pela primeira vez.
- **Validade:** amostra de [N] participantes, nenhum deles pessoa sem braços. Os números medem viabilidade técnica, não desempenho do público-alvo. Amostra pequena não permite inferência estatística; trate como estudo exploratório.

---

## ➜ INSERIR como nova seção, antes das "Considerações finais"

### 4. Reprodutibilidade

Todo o experimento pode ser repetido a partir do repositório:

```powershell
# 1. ambiente
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. conferir instalação, câmera e modelo
venv\Scripts\python.exe verificar_ambiente.py

# 3. medir o desempenho computacional (sente-se na frente da câmera)
venv\Scripts\python.exe benchmark_desempenho.py

# 4. coletar os dados de uso
.\iniciar.bat     # numa janela: o controle por rosto
.\validar.bat     # em outra: o teste, nos modos rosto e mouse

# 5. gerar indicadores e gráficos
venv\Scripts\python.exe analise_resultados.py
```

O notebook `analise_resultados.ipynb` reúne as duas avaliações com os gráficos e a leitura crítica.

**Dados brutos no repositório:**

| Arquivo | Conteúdo |
|---|---|
| `resultados/desempenho_quadros.csv` | uma linha por quadro medido, para auditoria |
| `resultados/desempenho_resumo.csv` | estatísticas por etapa (média, mediana, p95, mín, máx) |
| `resultados_validacao.csv` | uma linha por rodada de participante |
| `resultados/validacao_resumo.csv` | indicadores agregados por modo |

**Versões fixadas** em `requirements.txt`: Python 3.12.10, mediapipe 1.2.2, opencv-python 5.0.0.93, pyautogui 0.9.54, numpy 2.5.4, matplotlib 3.11.2.

### 5. Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| `controle_sem_toque.py` | aplicação principal: captura, detecção, gestos e controle do mouse |
| `teste_validacao.py` | experimento de validação com alvos |
| `benchmark_desempenho.py` | medição de latência, FPS e taxa de detecção |
| `analise_resultados.py` | indicadores e gráficos da validação |
| `analise_resultados.ipynb` | notebook com as duas análises |
| `verificar_ambiente.py` | diagnóstico de instalação, câmera e modelo |
| `requirements.txt` | dependências com versão fixa |
| `iniciar.bat` / `validar.bat` | atalhos de execução |
| `resultados/` | CSVs e gráficos gerados |
| `docs/passo_a_passo.md` | documentação técnica, código bloco por bloco |
| `docs/pitch_e_gravacao.md` | roteiro de apresentação |
| `README.md` | visão geral e instruções de execução |

---

## ➜ ACRESCENTAR ao final das "Considerações finais"

### Respostas à pergunta de pesquisa

A pergunta era: *é possível controlar o computador só com gestos do rosto, usando a webcam que o notebook já tem, sem custo de hardware e sem enviar imagens para a nuvem?*

| Critério | Resultado |
|---|---|
| Controle sem as mãos | **Sim.** Mover, clicar, rolar, arrastar e pausar, com 5 gestos. |
| Tempo real em hardware comum | **Sim.** Processamento ocupa [9] % do orçamento de 33,3 ms. |
| Custo de hardware | **R$ 0.** Webcam integrada, sem GPU dedicada. |
| Privacidade | **Sim.** Processamento 100 % local; nenhuma imagem gravada ou transmitida. |
| Digitação de texto | **Não.** Limitação documentada, com solução mapeada. |

### Aprendizado de engenharia

A tentativa de digitação é parte do resultado, não um fracasso omitido. Implementamos o acionamento do teclado virtual do Windows por gestos e a função não operou. Em vez de descartar por tentativa e erro, medimos sistematicamente sete abordagens:

| Teste | Resultado |
|---|---|
| `taskkill` no `osk.exe` | Acesso negado |
| `WM_CLOSE` na janela | bloqueado |
| `ShowWindow(SW_HIDE)` | bloqueado |
| `ShowWindow(SW_MINIMIZE)` | funcionou |
| `pyautogui.click()` sobre a tecla | nenhuma letra digitada |
| Clique com duração humana (80 ms) | nenhuma letra digitada |
| Cursor parado 2,5 s sobre a tecla | digitou 2 letras |
| `pyautogui.typewrite()` / `press()` em janela comum | funcionaram |

**Diagnóstico:** o `osk.exe` executa com privilégio de UIAccess, acima do processo da aplicação, e o Windows descarta entrada sintética direcionada a janelas privilegiadas. O modo de permanência funciona porque depende da posição real do cursor, não do clique.

**Decisão:** remover a funcionalidade em vez de entregar comportamento inconsistente, e documentar o caminho correto — o projeto desenhar o próprio teclado e enviar as teclas com `pyautogui.press()`, mecanismo verificado como funcional.

---

## Checklist da rubrica

| Item | Pontos | Status |
|---|---|---|
| Relevância do problema | 1,5 | pronto (seção 1, dados do IBGE) |
| Desenvolvimento e rigor técnico | 2,5 | pronto após inserir a seção 2.2 |
| Avaliação e análise dos resultados | 2,0 | **depende de você coletar os dados** |
| Clareza na documentação e estrutura do código | 1,0 | pronto |
| Repositório no GitHub com scripts e notebooks | — | **pendente: criar o repositório** |
| Visualizações gráficas e indicadores | — | scripts prontos; falta rodar com dados |
| README com instruções | — | pronto |
