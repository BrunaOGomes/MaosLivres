 # Pitch + Gravação — CitizenTech: **MãosLivres**

> Os slides prontos estão em **`MaosLivres_Pitch.pptx`** (7 slides, com roteiro nas notas de cada slide). "MãosLivres" é um nome sugerido: se trocarem, troquem também no PPT, no vídeo e no PDF.

---

## 0. Pontos de atenção do enunciado

- Vídeo de **no máximo 3 min** (tolerância de 15 s: entre 2:45 e 3:15).
- Aparecem **imagem e voz** do aluno que apresenta. **Nomes e RMs também aparecem dentro do vídeo.**
- Entrega: **PDF** com nome e RM de todos + **link público do YouTube** (link que não abre = vídeo desconsiderado).
- Onde: área de trabalhos da disciplina **Análise de Negócios e Inteligência Empresarial**.
- O vídeo **não vale nota** (só concorre ao prêmio), mas **cada disciplina tem o seu próprio entregável**: confiram os enunciados.
- **Data:** o documento diz "até 19/11, quarta-feira, 23h55", mas **19/11/2026 cai numa quinta**. Confirmem com o professor e, na dúvida, entreguem até **18/11**.
- Entregas iguais são zeradas: não compartilhem código, slides nem roteiro em grupos ou repositório público.
- Só **um** faz o upload, mas **todos** baixam o arquivo enviado e conferem.

---

## 1. Resumo do projeto (para PDF e relatório)

**Cidadão beneficiado:** pessoas sem braços (amputação, ausência congênita, paralisia) ou sem função nos membros superiores, que precisam usar o notebook para estudar, trabalhar e acessar serviços.

**Problema:** mouse e teclado exigem as mãos. O Censo 2022 do IBGE registrou **2,7 milhões de pessoas com muita dificuldade ou impossibilidade de pegar objetos pequenos** (função dos membros superiores). O IBGE **não mede "ausência de braços" isoladamente**, então esse é o dado oficial mais próximo: digam isso se perguntarem. Além disso, só **29%** das pessoas com deficiência de 14 anos ou mais estavam ocupadas em 2022.

**Solução:** a webcam do notebook vira mouse. Mover a cabeça move o cursor; fechar os dois olhos por meio segundo e abrir faz o clique; piscar só com o olho esquerdo liga e desliga a rolagem da página; levantar as sobrancelhas arrasta janelas; o beijinho pausa tudo para a pessoa conversar sem mexer no cursor.

**Como funciona:** webcam → OpenCV → MediaPipe (478 pontos do rosto) → EAR + calibração individual + suavização → PyAutoGUI controla o mouse do Windows. Funciona em qualquer programa.

**Ecossistema:** usuário, família e cuidadores, centros de reabilitação e associações (testes e adoção), escolas e empresas (inclusão), comunidade de código aberto.

**ODS:**

| ODS | Contribuição |
|---|---|
| **10** — Redução das desigualdades | Reduz a barreira de acesso digital com hardware comum |
| **3** — Saúde e bem-estar | Mais autonomia e independência no dia a dia |
| **4** — Educação de qualidade | Acesso a aulas e materiais online |
| **9** — Indústria, inovação e infraestrutura | Inovação acessível com visão computacional |

**Como medir o impacto:** taxa de acerto e tempo por alvo (`teste_validacao.py`), tempo de calibração (3 s), custo de hardware adicional (R$ 0). Futuro: usuários atendidos e satisfação, com centros de reabilitação.

**Como ampliar:** teclado próprio do projeto (ver limitações), instalador `.exe`, voz integrada, suporte a múltiplos monitores, parcerias com associações e centros de reabilitação, código aberto.

**Privacidade e inclusão:** processamento 100% local, sem gravar ou enviar imagens; calibração individual; só uma webcam comum.

**Limitações (falem, passa credibilidade):** precisa de boa luz frontal; ainda não validado com pessoas sem braços; movimentos involuntários da cabeça podem exigir ajuste; alcança só o monitor principal; **não digita texto** — testamos e comprovamos que o Windows descarta cliques de programa no teclado virtual (`osk.exe`), por privilégio de UIAccess, e o caminho é o projeto desenhar o próprio teclado e enviar as teclas com `pyautogui.press()`. O detalhamento dos testes está na seção 7 do `passo_a_passo.md`: se o professor perguntar "e para escrever?", a resposta está lá.

---

## 2. Roteiro do vídeo (≈ 3 min)

Cerca de 150 palavras por minuto. **Treinem com cronômetro.** `[DEMO]` = tela mostrando o sistema.

| Tempo | Slide | Narração |
|---|---|---|
| **0:00–0:20** | 1. Abertura | "Imagine acordar amanhã e não conseguir segurar um mouse. O computador continua ali: a escola, o trabalho, os serviços. Mas a porta de entrada fechou. O Censo 2022 do IBGE registrou **2,7 milhões de brasileiros** com muita dificuldade, ou sem conseguir, usar as mãos para pegar objetos pequenos." |
| **0:20–0:50** | 2. Problema | "Quem não tem braços, ou não os usa, depende de outra pessoa até para tarefas simples no computador. E só **29%** das pessoas com deficiência em idade de trabalhar estavam ocupadas em 2022. O acesso digital é uma das portas que precisam estar abertas." |
| **0:50–1:35** | 3. Solução **[DEMO]** | "Apresentamos o **MãosLivres**: a webcam do notebook vira mouse. Eu movo a cabeça, e o cursor acompanha, ponto por ponto. Fecho os dois olhos por meio segundo e abro: clique. Pisco só com o olho esquerdo e a página começa a rolar com a inclinação da minha cabeça; pisco de novo e volto ao cursor. Levanto as sobrancelhas para arrastar uma janela, e levanto outra vez para soltar. E com um beijinho eu pauso tudo, para conversar sem o cursor sair andando pela tela. Uma piscada normal não clica: o sistema aprende o seu rosto nos três primeiros segundos e se calibra para ele." |
| **1:35–2:05** | 4. Valor e impacto | "Sem hardware novo, sem internet e sem enviar imagem para nenhuma nuvem: tudo roda no próprio notebook. Testamos com **[N] pessoas**: **[X]%** de acerto e **[Y] segundos** por alvo. Ainda não testamos com pessoas sem braços, e esse é o nosso próximo passo, com centros de reabilitação. Contribuímos com os ODS 10, 3, 4 e 9." |
| **2:05–2:35** | 5. Tecnologia | "Usamos Python, OpenCV e MediaPipe para achar 478 pontos no rosto. Calculamos a abertura dos olhos com o EAR, calibrada para cada pessoa, suavizamos o movimento e controlamos o mouse do Windows com PyAutoGUI. Por isso funciona em qualquer programa." |
| **2:35–2:50** | 6. Time | "Somos **[nomes]**, alunos do 4º semestre de Sistemas de Informação da FIAP." |
| **2:50–3:00** | 7. Encerramento | "A tecnologia é o meio. A autonomia é o objetivo. **MãosLivres**: o computador ao alcance de quem tem a vontade, do jeito que puder." |

**Preencham `[N]`, `[X]`, `[Y]`** (e o `XX%` / `X,X s` do slide 4) com os resultados reais do `resultados_validacao.csv`. **Não inventem números**: se testaram 3 pessoas, digam 3.

**Dicas de fala:** olhem para a câmera na abertura e no encerramento; pausa curta depois do dado de impacto; falem um pouco mais devagar do que parece natural. Se passar de 3:15, encurtem o slide 5, nunca a demo.

**Roteiro da demo (≈ 45 s):**
1. Mover o cursor só com a cabeça, sem tocar no mouse (deixem as mãos visíveis fora do teclado: é a prova visual mais forte).
2. Clicar 2 ou 3 alvos fechando os olhos (mostre a barra "Clique" ficando verde).
3. Piscar normalmente **sem** clicar (prova que não confunde piscada com comando).
4. Wink esquerdo, rolar uma página inclinando a cabeça, wink esquerdo de novo para sair.
5. **Levantar as sobrancelhas**, arrastar uma janela pela tela, levantar de novo para soltar.
6. **Beijinho** para pausar antes de voltar a falar com a câmera.

Dica: o `teste_validacao.py` (`validar.bat`) é um ótimo plano de fundo para o item 2, porque os alvos verdes deixam óbvio que o clique acertou. E ele já gera os números do slide 4.

**Atenção na gravação:** enquanto vocês narram, a boca se mexe e a cabeça também. Façam a demo **narrando por cima depois** (grave a demo em silêncio e regrave a voz) ou use o beijinho para pausar enquanto falam. Comecem a demo só depois da calibração (rosto relaxado, boca fechada).

---

## 3. Antes de gravar (checklist)

- [ ] `controle_sem_toque.py` rodando e **calibrado** na luz do local da gravação
- [ ] `teste_validacao.py` feito com 3+ pessoas e números no slide 4
- [ ] Nomes, RMs e funções preenchidos no slide 6
- [ ] **OBS Studio** instalado (https://obsproject.com/) ou outra ferramenta
- [ ] Notificações desligadas (Não Perturbe), apps fechados (WhatsApp, Discord, e-mail), área de trabalho limpa
- [ ] Luz **de frente**, fundo organizado, ambiente silencioso, microfone próximo (fone com microfone ajuda)
- [ ] Câmera na altura dos olhos

---

## 4. Como gravar (jeito mais simples)

**Problema técnico:** no Windows, normalmente **só um programa por vez usa a webcam**. O OBS e o `controle_sem_toque.py` não conseguem usá-la ao mesmo tempo. Por isso gravem **em partes** e juntem depois.

**Parte A — slides 1 e 2.** No OBS, cena **"Apresentador"**: *Captura de Exibição* (slides em tela cheia, modo apresentação) + *Dispositivo de Captura de Vídeo* (sua webcam num cantinho). Em *Propriedades* da webcam, marque **"Desativar quando não estiver visível"**.

**Parte B — demo (slide 3), a mais importante.**
1. Troque para uma cena **"Demo"** só com *Captura de Exibição* (isso libera a câmera).
2. Abra o `controle_sem_toque.py` e espere a calibração. A **janelinha de prévia mostra o seu rosto** com o contorno dos olhos (verde/vermelho): é ela que prova que a imagem é real. Para ficar bem visível, aumente `JANELA_LARGURA`/`JANELA_ALTURA` no topo do código (ex.: 560 × 420).
3. Grave narrando por cima. **2 ou 3 takes**, escolha o melhor.
4. Durante a demo, tire as mãos do mouse e do teclado (ficam visíveis na tela os gestos do rosto, não as mãos).

**Parte C — slides 4 a 7.** Volte à cena "Apresentador". Nomes e RMs precisam aparecer: o slide 6 resolve (ou coloquem um título com nome e RM no início ou no fim).

**OBS (Configurações):** 1920×1080 · 30 FPS · MP4 (ou MKV + Remux) · escolha o microfone e faça 10 s de teste de áudio antes.

---

## 5. Edição e entrega

1. Junte as partes no **Clipchamp** (Windows 11), CapCut ou DaVinci Resolve. Corte silêncios e confirme duração entre **2:45 e 3:15**.
2. Título com **nomes e RMs** dentro do vídeo (obrigatório).
3. Exporte em MP4 1080p.
4. **YouTube com visibilidade Pública** (o enunciado exige link público). Título sugerido: *"MãosLivres — CitizenTech | FIAP Global Solution 2026"*.
5. Abra o link numa **janela anônima** para garantir que abre sem login.
6. **PDF** (uma página): nome do projeto, nome completo e RM de todos, link do YouTube, turma e disciplina.
7. Upload na área de trabalhos de *Análise de Negócios e Inteligência Empresarial*. Todos conferem baixando o arquivo enviado.

---

## 6. Cronograma sugerido (hoje é 05/11)

| Data | Tarefa |
|---|---|
| 05–06/11 | Instalar, rodar, calibrar, entender o código |
| 07–09/11 | Ajustar sensibilidade; teste de validação com 3+ pessoas |
| 10–12/11 | Preencher o PPT; treinar o roteiro com cronômetro; entregáveis das outras disciplinas |
| 13–15/11 | Gravar demo e apresentação |
| 16–17/11 | Editar, subir no YouTube, montar o PDF |
| **18/11** | **Entregar** (1 dia de folga; confirmem o prazo real) |

---

## 7. Checklist final

- [ ] Vídeo entre 2:45 e 3:15, com imagem e voz do apresentador
- [ ] Nomes e RMs **no vídeo**
- [ ] Link do YouTube público, testado em janela anônima
- [ ] PDF com nomes, RMs e link
- [ ] Os 7 tópicos: abertura, problema, solução, valor/impacto, tecnologias/arquitetura, time, encerramento
- [ ] ODS citados com a explicação de como o projeto contribui
- [ ] Números do slide 4 batem com o `resultados_validacao.csv` (sem `XX%` esquecido)
- [ ] Nada compartilhado em grupos ou repositório público antes da entrega
- [ ] Entregáveis das outras disciplinas conferidos

---

## 8. Fontes (rodapé do slide, se quiserem)

- IBGE, Censo Demográfico 2022 — Pessoas com Deficiência: 14,4 milhões (7,3% da população de 2 anos ou mais); dificuldade permanente para pegar pequenos objetos: 2,7 milhões.
- IBGE, *Pessoas com Deficiência e as Desigualdades Sociais no Brasil* (divulgação de set/2026): nível de ocupação de 29% entre pessoas com deficiência de 14 anos ou mais em 2022.
- Site da Global Solution FIAP: https://www.fiap.com.br/graduacao/global-solution/

> Antes de gravar, abram o site do IBGE e confirmem os números. Dá segurança se o professor perguntar a fonte.
