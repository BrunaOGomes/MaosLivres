# MãosLivres

## Controle do computador por gestos faciais para pessoas sem uso dos membros superiores

**CitizenTech — Global Solution FIAP 2026.2**
**Disciplina:** Cognitive Computing, Computer Vision and IoT Systems — Prof. Arnaldo Jr.

| Integrante | RM |
|---|---|
| [Bruna Oliveira Gomes] | [553135] |
| [Thiago Luiz Pereira] | [553720] |

**Turma:** [Turma]
**Repositório:** <https://github.com/BrunaOGomes/MaosLivres>

---

## 1. Contexto e relevância do problema

Mouse e teclado exigem as mãos. Para pessoas sem braços (amputação, ausência congênita, paralisia) ou sem função nos membros superiores, isso fecha a porta de entrada para estudar, trabalhar e acessar serviços digitais.

O Censo 2022 do IBGE registrou **2,7 milhões de pessoas** com muita dificuldade ou impossibilidade de pegar pequenos objetos, que é a função dos membros superiores. O IBGE não mede "ausência de braços" isoladamente, então esse é o dado oficial mais próximo. Além disso, apenas **29%** das pessoas com deficiência de 14 anos ou mais estavam ocupadas em 2022.

As soluções comerciais de acesso alternativo (rastreadores oculares dedicados, ponteiros de cabeça com sensor) custam de centenas a milhares de reais, o que as torna inacessíveis para a maior parte desse público.

### Pergunta de pesquisa

> É possível controlar o computador apenas com gestos do rosto, usando a webcam que o notebook já possui, sem custo adicional de hardware e sem enviar imagens para a nuvem?

### Solução proposta

O **MãosLivres** transforma a webcam do notebook em mouse. O cursor segue a ponta do nariz e os comandos são dados por expressões faciais: olhos, sobrancelhas e lábios. O processamento é integralmente local.

---

## 2. Métodos

### 2.1 Arquitetura

```
Webcam
  └─> OpenCV (captura, espelhamento, BGR→RGB)
        └─> MediaPipe FaceLandmarker (modo VIDEO, 478 pontos 3D + 52 blendshapes)
              └─> EAR dos olhos + blendshapes + posição do nariz
                    └─> Calibração individual + suavização temporal
                          └─> PyAutoGUI (mouse do sistema operacional)
```

Como o controle acontece no nível do sistema operacional, a solução funciona em qualquer programa, sem integração específica.

**Tecnologias:** Python 3.12.10, OpenCV 5.0.0.93, MediaPipe 1.2.2, NumPy 2.5.4, PyAutoGUI 0.9.54, Matplotlib 3.11.2.

### 2.2 Justificativa das escolhas técnicas

Comparamos três abordagens de detecção facial vistas na disciplina:

| Abordagem | O que entrega | Decisão |
|---|---|---|
| **Haar Cascade** (OpenCV) | Retângulo delimitador do rosto | **Descartada.** Entrega apenas a região do rosto, sem localizar pálpebras com a precisão necessária para medir abertura ocular. |
| **dlib + shape_predictor_68** | 68 pontos faciais 2D | **Descartada.** Exige compilação com CMake e Visual Studio C++ no Windows, com falhas frequentes no Python 3.12; pesos grandes com download separado; modelo de 68 pontos treinado em dataset com restrição de uso comercial. |
| **MediaPipe FaceLandmarker** | 478 pontos 3D + 52 blendshapes | **Escolhida.** Instalação via `pip`, pontos mais estáveis, modo VIDEO com rastreamento temporal, blendshapes prontos para expressões, licença Apache 2.0, tempo real em CPU. |

**Por que o modo VIDEO e não IMAGE:** o `RunningMode.VIDEO` recebe um timestamp crescente e mantém rastreamento entre quadros, o que estabiliza os pontos e reduz tremor. O modo IMAGE trataria cada quadro isoladamente, sem memória temporal.

**Aproveitamento da disciplina:** a função `eye_aspect_ratio()` e a ordem dos 6 pontos do olho são as mesmas do laboratório de detecção de fadiga, mudando apenas a origem dos pontos. O contorno do olho usa `cv2.convexHull`, e o experimento de validação usa o evento de mouse do OpenCV (`cv2.setMouseCallback`).

### 2.3 Métricas de detecção de cada gesto

Esta é a parte quantitativa central do sistema: **como um número vira um comando**.

Todos os limiares são **relativos ao rosto da pessoa**, medidos nos 3 segundos iniciais de calibração. Usamos a **mediana** e não a média porque a mediana descarta valores extremos: se a pessoa piscar durante a calibração, a média seria contaminada, a mediana não.

#### 2.3.1 Olhos — EAR (Eye Aspect Ratio)

A métrica é a razão entre a **abertura vertical** e a **largura** da pálpebra, calculada sobre 6 pontos por olho:

```
        p2   p3
   p1              p4     EAR = ( |p2−p6| + |p3−p5| ) / ( 2 · |p1−p4| )
        p6   p5
```

| Item | Valor |
|---|---|
| Pontos do olho esquerdo (tela) | 33, 160, 158, 133, 153, 144 |
| Pontos do olho direito (tela) | 362, 385, 387, 263, 373, 380 |
| EAR típico de olho aberto | 0,25 a 0,35 |
| EAR de olho fechado | próximo de 0 |
| **Limiar de "olho fechado"** | **EAR < 70% do EAR de repouso da pessoa** (`EAR_FATOR = 0,70`) |

Dividir pela largura do olho é o que torna a medida **independente da distância até a câmera**: se a pessoa se aproxima, altura e largura crescem juntas e a razão se mantém.

**Por que 70% e não um valor fixo de EAR:** o EAR de olho aberto varia de pessoa para pessoa (formato do olho, uso de óculos, ângulo da câmera). Um limiar absoluto excluiria parte dos usuários. O limiar proporcional adapta o sistema ao rosto, e não o contrário.

#### 2.3.2 Olhos — separação entre piscada e comando

O limiar de EAR diz *se* o olho está fechado. O que diferencia piscada de comando é a **duração**:

| Duração dos dois olhos fechados | Interpretação |
|---|---|
| menos de 0,5 s | piscada natural, ignorada (piscada típica: 0,1 a 0,4 s) |
| **0,5 s a 3,0 s** | **clique**, executado no instante em que a pessoa abre os olhos |
| mais de 3,0 s | ignorado, permite descansar os olhos sem acionar nada |

A ação é decidida **ao abrir** os olhos, e não ao fechar, porque só então a duração total é conhecida.

#### 2.3.3 Wink — um olho só

Para o gesto de um olho (liga/desliga rolagem), exigimos duas condições simultâneas:

| Condição | Valor |
|---|---|
| Olho alvo fechado | EAR < 70% do repouso daquele olho |
| Outro olho **bem aberto** | EAR > 110% do próprio limiar (`WINK_MARGEM = 1,10`) |
| Duração mínima | 0,6 s (`WINK_ESQUERDO_SEG`) |

A margem de 10% no olho oposto evita que uma piscada dos dois olhos ligeiramente assimétrica seja interpretada como wink.

#### 2.3.4 Sobrancelhas e beijinho — blendshapes

O MediaPipe fornece 52 *blendshapes*: coeficientes de 0 a 1 indicando o quanto cada expressão está ativa. Usamos dois:

| Gesto | Blendshape usado | Limiar | Duração |
|---|---|---|---|
| **Sobrancelhas levantadas** (arrastar) | média de `browInnerUp`, `browOuterUpLeft`, `browOuterUpRight` | repouso + **0,35** | 0,7 s |
| **Beijinho / bico** (pausar) | `mouthPucker` | repouso + **0,45** | 1,0 s |

A média dos três coeficientes de sobrancelha é mais estável que qualquer um isolado, porque reduz o efeito de assimetria facial.

**Por que um delta somado e não um valor absoluto:** o valor de repouso varia entre pessoas. Alguém com sobrancelhas naturalmente mais altas já parte de um coeficiente maior. O delta mede a **variação em relação ao próprio rosto**.

#### 2.3.5 Nariz — controle do cursor

A ponta do nariz (landmark 1) é mapeada linearmente para a posição na tela:

```
posição_tela = 0,5 + (posição_nariz − centro_calibrado) × ganho
```

| Parâmetro | Valor | Significado |
|---|---|---|
| `GANHO_X` | 5,0 | deslocar 20% da largura da imagem cruza a tela na horizontal |
| `GANHO_Y` | 6,0 | deslocar ~17% da altura da imagem cruza a tela na vertical |
| `SUAVIZACAO` (α) | 0,25 | filtro temporal da posição |

O resultado é limitado entre 0 e 1 para o cursor nunca sair da tela.

**Suavização:** aplicamos média móvel exponencial, `x ← x + α·(alvo − x)`. O detector oscila alguns pixels por quadro, e esse ruído tornaria o cursor trêmulo e impossível de mirar. Com α = 0,25, cada quadro move o cursor 25% da distância que falta até o alvo. Valores menores dão mais estabilidade e menos resposta: é o compromisso clássico entre ruído e latência, a mesma lógica dos filtros de suavização vistos na disciplina.

**Congelamento durante gestos:** enquanto qualquer gesto facial está ativo, o cursor para de se mover. Isso existe porque fazer uma expressão move a cabeça involuntariamente, e sem esse travamento o cursor escorregaria do alvo no momento do clique.

#### 2.3.6 Rolagem

| Parâmetro | Valor | Significado |
|---|---|---|
| `ROLAGEM_ZONA` | 0,03 | zona morta de 3% da altura, abaixo da qual nada rola |
| `ROLAGEM_GANHO` | 600 | fator de velocidade de rolagem |

A zona morta impede rolagem involuntária quando a cabeça está praticamente parada.

#### 2.3.7 Resumo dos limiares

| Gesto | Métrica | Limiar | Duração |
|---|---|---|---|
| Mover cursor | posição do nariz (landmark 1) | — | contínuo |
| Clique | EAR dos 2 olhos | < 70% do repouso | 0,5 a 3,0 s |
| Rolagem liga/desliga | EAR olho esquerdo + oposto > 110% | < 70% do repouso | 0,6 s |
| Arrastar liga/desliga | média dos 3 `brow*` | repouso + 0,35 | 0,7 s |
| Pausar / retomar | `mouthPucker` | repouso + 0,45 | 1,0 s |

### 2.4 Segurança e privacidade

- **Fail-safe:** mover o mouse físico para o canto superior esquerdo aborta imediatamente (recurso do PyAutoGUI). `Ctrl+C` no terminal e `ESC` na janela também encerram.
- **Nunca deixa o botão preso:** ao pausar, recalibrar ou sair, o programa libera o botão do mouse.
- **Processamento 100% local:** nenhuma imagem, vídeo ou dado biométrico é gravado ou transmitido. O único acesso à rede é o download do modelo do MediaPipe na primeira execução.

### 2.5 Protocolo experimental

**Experimento 1 — desempenho computacional.** O `benchmark_desempenho.py` mede 300 quadros, descartando 20 de aquecimento, cronometrando separadamente cada etapa do pipeline.

**Experimento 2 — desempenho de uso.** O `teste_validacao.py` exibe 8 alvos circulares (raio 45 px) um por vez, em posições sorteadas com no mínimo 200 px de distância do alvo anterior, numa janela de 860×500. O participante clica em cada alvo usando o controle facial. O sistema registra acertos, cliques errados, tempo até cada acerto e tempo total, usando o evento de mouse do OpenCV.

**Experimento 3 — métricas de gesto.** O `metricas_gestos.py` registra EAR, blendshapes e posição do nariz quadro a quadro, com roteiro guiado de gestos, e gera as séries temporais com os limiares sobrepostos.

---

## 3. Análise dos resultados

### 3.1 Desempenho computacional

Um sistema de acessibilidade precisa responder em tempo real. Uma webcam de 30 FPS entrega um quadro a cada **33,3 ms**, e esse é o orçamento de tempo disponível por quadro.

**Configuração:** notebook com CPU sem GPU dedicada, webcam integrada a 640×480, 300 quadros medidos.

| Etapa do pipeline | Média | Mediana | p95 | Máximo |
|---|---|---|---|---|
| Pré-processamento (flip + BGR→RGB) | 0,46 ms | 0,39 ms | 0,63 ms | 4,89 ms |
| **Inferência MediaPipe** | **2,42 ms** | 2,20 ms | 3,68 ms | 7,65 ms |
| Pós-processamento (EAR + blendshapes) | 0,00 ms | 0,00 ms | 0,00 ms | 0,00 ms |
| **Processamento total (nosso código)** | **2,88 ms** | 2,59 ms | 4,80 ms | 8,01 ms |
| Espera da webcam (`cap.read`) | 47,34 ms | 45,54 ms | 62,82 ms | 68,71 ms |
| Total do ciclo | 50,22 ms | 48,14 ms | 66,03 ms | 71,02 ms |

**Indicadores derivados:**

| Indicador | Valor |
|---|---|
| FPS real (limitado pela webcam) | 20,3 |
| FPS que o algoritmo suportaria | 365 |
| Ocupação do orçamento de 33,3 ms | **8,6%** |
| Folga computacional | **11,6×** |

*Figura 1 — `resultados/grafico_latencia.png`: distribuição da latência de processamento por quadro.*
*Figura 2 — `resultados/grafico_etapas.png`: participação de cada etapa no ciclo.*
*Figura 3 — `resultados/grafico_fps.png`: FPS ao longo da execução.*

#### Análise crítica

O resultado mais relevante é contraintuitivo: **o gargalo não é o algoritmo de visão computacional, é o hardware da câmera.** A inferência do MediaPipe consome 2,42 ms, enquanto a espera pelo próximo quadro da webcam consome 47,34 ms, ou 94% do ciclo.

Três consequências:

1. O processamento ocupa apenas **8,6% do orçamento de tempo real**, confirmando que a solução roda em notebook comum **sem GPU dedicada** — requisito central para uma tecnologia assistiva de custo zero.
2. **Otimizar o algoritmo não aumentaria a fluidez.** Ganho de FPS exigiria uma câmera melhor ou captura em *thread* separada, não código mais rápido. Essa conclusão redireciona qualquer esforço futuro de otimização.
3. A folga de 11,6× é o que viabiliza os próximos passos (teclado próprio, novos gestos) sem comprometer o tempo real.

**Nota metodológica.** A separação entre "processamento" e "espera da câmera" é necessária porque o `cap.read()` do OpenCV é bloqueante: ele só retorna quando a câmera entrega o quadro. Medir apenas o tempo total atribuiria ao algoritmo uma latência que é, na verdade, limitação física do sensor. Foi um erro que cometemos na primeira medição e corrigimos ao investigar por que a inferência parecia desproporcionalmente barata.

### 3.2 Desempenho de uso

**Amostra:** 4 participantes, 1 rodada cada, 8 alvos por rodada, 32 alvos no total.

| Participante | Alvos | Acertos | Cliques errados | Precisão | Tempo médio/alvo | Tempo total |
|---|---|---|---|---|---|---|
| Thiago | 8 | 8 | 0 | 100,0% | 2,98 s | 23,80 s |
| Bruna | 8 | 8 | 2 | 80,0% | 4,16 s | 33,25 s |
| Rogério | 8 | 8 | 8 | 50,0% | 10,68 s | 85,46 s |
| Zuck Felipe | 8 | 8 | 2 | 80,0% | 10,10 s | 80,81 s |
| **Agregado** | **32** | **32** | **12** | **77,5%** | **6,98 s** | — |

| Indicador | Valor |
|---|---|
| Taxa de conclusão da tarefa | **100%** (4 de 4 participantes concluíram os 8 alvos) |
| Precisão média de clique | 77,5% |
| Desvio padrão da precisão | 17,9 pontos percentuais |
| Tempo médio por alvo | 6,98 s |
| Desvio padrão do tempo | 3,44 s |
| Amplitude de tempo | 2,98 s a 10,68 s (3,6× entre o melhor e o pior) |

*Figura 4 — `resultados/grafico_taxa_acerto.png`*
*Figura 5 — `resultados/grafico_tempo_alvo.png`*
*Figura 6 — `resultados/grafico_por_participante.png`*

#### Análise crítica

**Todos concluíram a tarefa.** Os 4 participantes acertaram os 8 alvos, sem exceção. Essa é a evidência central: a hipótese de que é possível operar o cursor apenas com gestos faciais se sustenta. Note que "acertos" é sempre 8 porque o experimento só termina quando todos os alvos são atingidos — o que varia é o **custo** para chegar lá, medido em cliques errados e tempo.

**A variação entre pessoas é grande e é o achado mais informativo.** A precisão foi de 50% a 100% e o tempo por alvo de 2,98 s a 10,68 s. Como todos usaram o sistema pela primeira vez, sem treino prévio, essa dispersão sugere uma **curva de aprendizado acentuada** em vez de um limite da tecnologia. Reforça essa leitura o fato de que o participante com 100% de precisão também foi o mais rápido: precisão e velocidade andaram juntas, o que é típico de domínio da interface, não de compromisso velocidade-precisão.

**Interpretação dos cliques errados.** O participante com 8 cliques errados produziu exatamente um erro por alvo, em média. O padrão é compatível com o cursor escorregando no momento de fechar os olhos, antes de o gesto ser reconhecido. É o comportamento que a suavização e o congelamento durante gestos atacam, e indica que, para alguns rostos, `SUAVIZACAO` menor ou `CLIQUE_SEG` maior melhorariam o resultado — um ajuste por usuário, coerente com a filosofia de calibração individual do projeto.

**Ausência de linha de base com mouse.** O protocolo previa uma rodada com mouse convencional para dimensionar o custo relativo de interação. Essa coleta não foi realizada, então **não podemos quantificar quantas vezes o controle facial é mais lento que o mouse**. É uma lacuna reconhecida. Vale registrar, porém, que o mouse nunca foi a meta: para o público-alvo a alternativa real não é o mouse, é depender de outra pessoa. O indicador decisivo continua sendo a taxa de conclusão de 100%.

#### Validade e limitações da avaliação

1. **Amostra de 4 participantes**, sem poder estatístico. Trata-se de estudo exploratório de viabilidade, não de experimento com inferência. Nenhum teste de significância é aplicável.
2. **Nenhum participante é pessoa sem braços.** Os números medem **viabilidade técnica da interação**, não o desempenho do público-alvo. Validar com o público real, em parceria com centros de reabilitação, é o próximo passo indispensável.
3. **Uma rodada por pessoa**, sem rodada de treino descartada, o que mistura aprendizado com desempenho.
4. **Ambiente único**, com a mesma iluminação e o mesmo equipamento para todos.

### 3.3 Métricas de detecção medidas

Os valores abaixo foram medidos com o `metricas_gestos.py` em um rosto real, e são preenchidos automaticamente pelo `gerar_relatorio.py` a partir de `resultados/metricas_gestos_resumo.csv`.

<!-- TABELA_METRICAS_GESTOS -->

Esses números são a comprovação de que os limiares descritos na seção 2.3 não são arbitrários: cada um foi derivado do rosto da pessoa durante a calibração.

*Figura 7 — `resultados/grafico_ear.png`: EAR no tempo, com o limiar sobreposto. Permite ver piscadas naturais passando pelo limiar rapidamente e o gesto de clique permanecendo abaixo dele.*
*Figura 8 — `resultados/grafico_blendshapes.png`: coeficientes de sobrancelha e beijinho no tempo, com repouso e limiar.*
*Figura 9 — `resultados/grafico_nariz.png`: trajetória do nariz e amplitude usada para cobrir a tela.*

---

## 4. Reprodutibilidade

```powershell
# 1. ambiente
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. conferir instalação, câmera e modelo
venv\Scripts\python.exe verificar_ambiente.py

# 3. desempenho computacional
venv\Scripts\python.exe benchmark_desempenho.py

# 4. métricas de detecção dos gestos
venv\Scripts\python.exe metricas_gestos.py

# 5. coleta de uso
.\iniciar.bat     # janela 1: controle facial
.\validar.bat     # janela 2: experimento com alvos

# 6. indicadores e gráficos
venv\Scripts\python.exe analise_resultados.py
```

### Dados brutos no repositório

| Arquivo | Conteúdo |
|---|---|
| `resultados/desempenho_quadros.csv` | uma linha por quadro medido (300 linhas) |
| `resultados/desempenho_resumo.csv` | estatísticas por etapa: média, mediana, p95, mín, máx |
| `resultados_validacao.csv` | uma linha por rodada de participante, com data e hora |
| `resultados/validacao_resumo.csv` | indicadores agregados |
| `resultados/metricas_gestos.csv` | EAR, blendshapes e nariz quadro a quadro |
| `resultados/metricas_gestos_resumo.csv` | limiares calibrados e estatísticas por gesto |

### Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| `controle_sem_toque.py` | aplicação principal: captura, detecção, gestos, controle do mouse |
| `teste_validacao.py` | experimento de validação com alvos |
| `benchmark_desempenho.py` | medição de latência, FPS e taxa de detecção |
| `metricas_gestos.py` | medição dos limiares de detecção de gesto |
| `analise_resultados.py` | indicadores e gráficos da validação |
| `analise_resultados.ipynb` | notebook com as análises consolidadas |
| `verificar_ambiente.py` | diagnóstico de instalação, câmera e modelo |
| `requirements.txt` | dependências com versão fixa |
| `iniciar.bat` / `validar.bat` | atalhos de execução |
| `resultados/` | CSVs e gráficos gerados |
| `docs/` | documentação técnica e roteiro de apresentação |

---

## 5. Considerações finais

### Resposta à pergunta de pesquisa

| Critério | Resultado |
|---|---|
| Controle do computador sem as mãos | **Sim.** Mover, clicar, rolar, arrastar e pausar, com 5 gestos. |
| Conclusão da tarefa pelos participantes | **100%** (4 de 4) |
| Tempo real em hardware comum | **Sim.** 8,6% do orçamento de 33,3 ms, folga de 11,6×. |
| Custo adicional de hardware | **R$ 0.** Webcam integrada, sem GPU dedicada. |
| Privacidade | **Sim.** Processamento local, nenhuma imagem gravada ou transmitida. |
| Digitação de texto | **Não.** Limitação documentada na seção 5.2. |

### 5.1 Limitações

- **Não digita texto** (detalhado abaixo).
- **Validação sem o público-alvo**: 4 participantes, nenhum sem uso dos membros superiores.
- **Dependência de iluminação frontal**: luz de fundo degrada a detecção.
- **Monitor único**: o sistema usa `pyautogui.size()`, que retorna apenas o monitor principal; em configurações multi-monitor o cursor não alcança as telas secundárias.
- **Movimentos involuntários de cabeça** podem exigir ajuste de ganho e suavização.
- **Sem linha de base com mouse** para dimensionar o custo relativo de interação.

### 5.2 Limitação de digitação: investigação documentada

Implementamos o acionamento do teclado virtual do Windows por gestos faciais e a função não operou. Em vez de descartar por tentativa e erro, medimos sistematicamente oito abordagens:

| Teste | Resultado |
|---|---|
| `taskkill` no processo `osk.exe` | Acesso negado |
| Mensagem `WM_CLOSE` para a janela | Bloqueada |
| `ShowWindow(SW_HIDE)` | Bloqueada |
| `ShowWindow(SW_MINIMIZE)` | Funcionou |
| `pyautogui.click()` sobre uma tecla | Nenhuma letra digitada |
| Clique com duração humana (80 ms) | Nenhuma letra digitada |
| Cursor parado 2,5 s sobre a tecla | Digitou 2 letras |
| `pyautogui.typewrite()` / `press()` em janela comum | Funcionaram |

**Diagnóstico:** o `osk.exe` executa com privilégio de UIAccess, acima do processo da aplicação, e o Windows descarta entrada sintética direcionada a janelas privilegiadas. O modo de permanência ("passar o mouse sobre as teclas") funciona porque depende da posição real do cursor, não de um evento de clique.

**Decisão:** remover a funcionalidade em vez de entregar comportamento inconsistente, e documentar o caminho correto.

**Solução mapeada:** o próprio projeto desenhar seu teclado na janela do OpenCV e enviar as teclas com `pyautogui.press()`, mecanismo já verificado como funcional e que não exige privilégio elevado.

### 5.3 Próximos passos

1. **Teclado próprio do projeto**, com teclas grandes e envio por `pyautogui.press()`.
2. **Validação com o público-alvo**, em parceria com centros de reabilitação e associações, com protocolo de múltiplas sessões para separar aprendizado de desempenho.
3. **Linha de base com mouse e rodadas de treino descartadas**, para quantificar o custo relativo de interação.
4. **Suporte a múltiplos monitores.**
5. **Captura em thread separada**, único caminho com potencial real de ganho de FPS, conforme a análise da seção 3.1.
6. **Equalização de histograma** para robustez em baixa luminosidade.
7. **Instalador `.exe`** para uso sem conhecimento de programação.

### 5.4 Conclusão

O MãosLivres demonstra que uma webcam comum é suficiente para controlar o cursor e executar as operações básicas de interação com o computador, com processamento que ocupa menos de 9% do orçamento de tempo real em hardware sem GPU dedicada e sem transmitir qualquer imagem.

Todos os 4 participantes concluíram a tarefa proposta, com precisão de clique entre 50% e 100% e dispersão compatível com curva de aprendizado de primeiro uso.

A decisão de projeto mais relevante foi **priorizar poucas funções que operam de forma confiável** em vez de muitas funções parciais, documentando com evidências a razão pela qual a digitação ficou fora desta versão.

---

## 6. Referências

- IBGE. **Censo Demográfico 2022 — Pessoas com Deficiência.** 14,4 milhões de pessoas com deficiência (7,3% da população de 2 anos ou mais); 2,7 milhões com dificuldade permanente para pegar pequenos objetos.
- IBGE. **Pessoas com Deficiência e as Desigualdades Sociais no Brasil.** Nível de ocupação de 29% entre pessoas com deficiência de 14 anos ou mais, 2022.
- SOUKUPOVÁ, T.; ČECH, J. **Real-Time Eye Blink Detection using Facial Landmarks.** 21st Computer Vision Winter Workshop, 2016. (origem do Eye Aspect Ratio)
- KAZEMI, V.; SULLIVAN, J. **One Millisecond Face Alignment with an Ensemble of Regression Trees.** CVPR, 2014. (método do `shape_predictor_68` da dlib)
- GOOGLE. **MediaPipe Face Landmarker.** Documentação da MediaPipe Tasks Vision API.
- FIAP. **Global Solution 2026.2 — Tema CitizenTech.**

---

## 7. Anexo A — Evidências de funcionamento

As capturas abaixo foram feitas durante a execução real do `controle_sem_toque.py`, com a janela de depuração da aplicação em primeiro plano. A janela mostra, sobrepostos ao vídeo da webcam: o **modo ativo** no topo, os valores de **EAR** de cada olho, a **barra de progresso do clique**, as **barras de sobrancelha e beijinho** com seus limiares, o contorno dos olhos (**verde** = aberto, **vermelho** = fechado) e o **ponto azul** sobre a ponta do nariz, que é o marcador que comanda o cursor.

O código-fonte completo, os CSVs e os gráficos estão em: <https://github.com/BrunaOGomes/MaosLivres>

### A.1 Calibração inicial

*Figura 10 — `evidencias/01_calibracao.png`: tela de calibração dos primeiros 3 segundos. A aplicação pede rosto relaxado, olhos abertos e boca fechada, e a barra laranja mostra o progresso da coleta. Nesse intervalo são medidos o EAR de repouso de cada olho, o coeficiente de sobrancelha e de beijinho em repouso, e o centro do nariz. Os limiares passam a ser relativos a esses valores (70% do EAR de repouso, repouso + 0,35 para sobrancelha, repouso + 0,45 para beijinho), e é por isso que o sistema funciona com rostos diferentes, com óculos e em distâncias distintas da câmera, sem ajuste manual de código.*

### A.2 Gesto de clique em andamento

*Figura 11 — `evidencias/02_clique.png`: os dois olhos fechados, com EAR caindo para 0,078 e 0,085, contra um repouso próximo de 0,37. O contorno dos dois olhos fica **vermelho**, sinalizando olho fechado, e a barra "Clique" avança em **verde** enquanto a condição se mantém. O clique só é emitido quando os olhos reabrem dentro da janela de 0,5 a 3,0 segundos. Essa dupla condição é o que separa o gesto intencional da piscada natural, que dura cerca de 100 a 400 ms e nunca completa a barra, e também do descanso dos olhos acima de 3 segundos, que é descartado de propósito.*

### A.3 Beijinho: pausa e retomada

*Figura 12 — `evidencias/03_beijinho.png`: gesto de biquinho detectado pelo blendshape `mouthPucker` da MediaPipe. A barra "Beijo" em **rosa** cruzou o limiar e permaneceu acima dele por 1,0 segundo, o que dispara a pausa ou a retomada de todo o controle. Essa é a função de segurança do projeto: permite ao usuário conversar, se coçar ou se reposicionar sem que o cursor se mexa, e retomar com o mesmo gesto. Note que os olhos seguem com contorno **verde**, ou seja, o gesto da boca é reconhecido de forma independente do gesto dos olhos.*

### A.4 Modo rolagem

*Figura 13 — `evidencias/04_rolagem.png`: modo de rolagem ativo, indicado no topo da janela. Aqui a inclinação da cabeça para cima rola a página para cima e para baixo rola para baixo, em vez de mover o cursor. O olho esquerdo da tela aparece com contorno **vermelho**, ou seja, fechado, que é justamente o gesto que encerra o modo e devolve o controle ao cursor. Também fica visível a assimetria proposital do projeto: cada olho tem papel distinto, e o olho direito não dispara nada.*

### A.5 Estado de repouso, com os limiares visíveis

*Figura 14 — `evidencias/05_sobrancelha.png`: sobrancelhas levantadas, com a barra "Sobr." em **azul** preenchida acima do limiar. Mantido por 0,7 segundo, esse gesto liga e desliga o arrastar, equivalente a segurar o botão do mouse, usado para mover janelas e selecionar texto. Os olhos permanecem **verdes** e o EAR em 0,373 e 0,372, perto do valor de repouso, confirmando que levantar a sobrancelha não contamina a detecção de clique.*

### A.6 Aplicação em execução no ambiente de desenvolvimento

*Figura 15 — `evidencias/06_execucao.png`: a aplicação rodando a partir do `iniciar.bat`, com o terminal ao lado. O log mostra a inicialização do MediaPipe Face Landmarker com o delegate XNNPACK em CPU, sem GPU dedicada, e a linha `Calibrado! limiar olho A=0.150 | olho B=0.113`, que é a confirmação de que os limiares foram calculados a partir da calibração daquela sessão. No canto superior direito, a janela da câmera mostra o cursor sendo controlado sem uso das mãos.*

---
