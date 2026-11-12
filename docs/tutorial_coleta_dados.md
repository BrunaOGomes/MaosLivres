# Tutorial: coletar os dados de validação

Este é o passo a passo para gerar os números que faltam no relatório. Vale **2,0 pontos** na rubrica ("Avaliação e análise dos resultados obtidos").

Tempo total: cerca de **40 a 50 minutos** para 4 participantes.

---

## Antes de começar: 5 armadilhas

Leia isto primeiro. Qualquer uma destas estraga a coleta e obriga a refazer.

| Armadilha | Consequência | Como evitar |
|---|---|---|
| **Não recalibrar para cada pessoa** | Os limiares de olho ficam calibrados no rosto da pessoa anterior. Os cliques falham ou disparam sozinhos. | Aperte **C** na janela da câmera a cada troca de participante. |
| **Apertar ESC antes de acertar os 8 alvos** | **Nada é salvo.** O script só grava quando a rodada é concluída. | Só aperte ESC depois de aparecer "TESTE CONCLUIDO!". |
| **Usar o monitor secundário** | O cursor controlado pelo rosto não alcança a segunda tela. | Deixe tudo no monitor principal. |
| **Escrever o nome diferente nas duas rodadas** | Rodadas da mesma pessoa não se agrupam. | Use sempre o mesmo nome, minúsculo e sem acento: `ana`, `bruno`. |
| **Contar a primeira tentativa de todas** | Todo mundo está usando pela primeira vez: o número mede confusão, não a tecnologia. | Faça **1 rodada de treino descartada** antes da que conta. |

---

## Preparação (uma vez só)

1. **Ambiente:** luz de frente (janela ou lâmpada atrás da tela), nunca de costas. Câmera na altura dos olhos, 50 a 70 cm de distância.

2. **Tela limpa:** feche WhatsApp, Discord, e-mail. Ligue o "Não Perturbe". Uma notificação no meio da rodada rouba o clique e vira erro no seu dado.

3. **Confira o ambiente:**

```powershell
venv\Scripts\python.exe verificar_ambiente.py
```

Tem que dar OK em tudo. Se a câmera não for o índice 0, ajuste `CAM_INDEX` no topo do `controle_sem_toque.py`.

4. **Prepare uma folha de papel** com a tabela do final deste documento. Você vai anotar à mão como backup, caso algo não salve.

---

## O procedimento, participante por participante

Para **cada pessoa**, você vai fazer 4 rodadas: treino no rosto, valendo no rosto, treino no mouse, valendo no mouse.

### Passo 1 — Abra as duas janelas

**Janela 1** (PowerShell, na pasta do projeto):

```powershell
.\iniciar.bat
```

Espere a calibração de 3 segundos. Quem senta na frente da câmera é **o participante**, não você.

Durante a calibração o participante deve: olhar para a tela, **olhos abertos**, **boca fechada**, **rosto relaxado**.

**Janela 2** (outro PowerShell):

```powershell
.\validar.bat
```

### Passo 2 — Rodada de TREINO no rosto (descartada)

No `validar.bat`, responda:

```
Nome do participante: treino
Modo (rosto / mouse): rosto
```

Use o nome `treino` de propósito: assim essa rodada fica identificada no CSV e você não a confunde com as que valem.

O participante clica nos 8 alvos usando só a cabeça e os olhos:
- **mover a cabeça** leva o cursor até o alvo verde
- **fechar os dois olhos por cerca de 1 segundo e abrir** dá o clique

Quando aparecer "TESTE CONCLUIDO!", aperte **ESC**.

Essa rodada serve para a pessoa entender o sistema. O número dela não entra na análise.

### Passo 3 — Rodada VALENDO no rosto

No `validar.bat` de novo:

```
Nome do participante: ana
Modo (rosto / mouse): rosto
```

Mesma coisa: 8 alvos, só com o rosto. **ESC só depois de "TESTE CONCLUIDO!"**.

Regras durante a rodada:
- o participante **não toca** no mouse nem no teclado
- você, que está ajudando, **não dá dicas** de onde está o alvo
- se o cursor travar, confira na janela da câmera: "PAUSADO" (beijinho para retomar), "MODO ROLAGEM" (olho esquerdo 0,6 s para sair), "Rosto nao detectado" (mais luz)

### Passo 4 — Rodadas no mouse

Agora a referência de comparação. O participante usa o mouse normal.

Rodada de treino:

```
Nome do participante: treino
Modo (rosto / mouse): mouse
```

E a que vale:

```
Nome do participante: ana
Modo (rosto / mouse): mouse
```

Pode deixar o `iniciar.bat` rodando, mas **pause o controle por rosto** antes: beijinho de 1 segundo, ou tecla **P** na janela da câmera. Se não pausar, a cabeça do participante vai disputar o cursor com a mão dele e o dado do mouse fica inválido.

### Passo 5 — Trocar de participante

1. O novo participante senta na frente da câmera.
2. Clique na **janela da câmera** para dar foco nela.
3. Aperte **C**. A calibração de 3 segundos recomeça.
4. Volte ao Passo 2.

**Não pule o C.** É o erro mais comum e o mais difícil de perceber depois.

---

## Alterne a ordem entre os participantes

Quem faz rosto primeiro já chega cansado no mouse; quem faz mouse primeiro já entendeu a tarefa quando vai para o rosto. Isso se chama efeito de ordem, e a forma de neutralizar é alternar:

| Participante | Ordem |
|---|---|
| 1 | rosto, depois mouse |
| 2 | mouse, depois rosto |
| 3 | rosto, depois mouse |
| 4 | mouse, depois rosto |

Anote qual ordem cada um fez. Se o professor perguntar como você controlou o efeito de aprendizado, essa é a resposta.

---

## Quantas pessoas

| Participantes | O que você pode afirmar |
|---|---|
| 1 a 2 | nada além de "funcionou com essas pessoas" |
| **3 a 5** | **suficiente para o trabalho**: estudo exploratório de viabilidade |
| 6 ou mais | melhor, se der tempo |

O próprio `analise_resultados.py` avisa se você tiver menos de 3.

**Peça consentimento verbal** e explique que nenhuma imagem é gravada, só os tempos e acertos. Isso é verdade e vale citar no relatório.

---

## Gerar os resultados

Terminada a coleta:

```powershell
venv\Scripts\python.exe analise_resultados.py
```

Saída esperada:

```
================================================================
INDICADORES DE VALIDACAO
================================================================
Rodadas registradas: 8

modo      rodadas  pessoas    acerto   tempo/alvo
rosto           4        4      ...%        ... s
mouse           4        4      ...%        ... s

Custo relativo: o controle por rosto levou ...x o tempo do mouse.
```

Gera em `resultados/`: `validacao_resumo.csv`, `grafico_taxa_acerto.png`, `grafico_tempo_alvo.png` e `grafico_por_participante.png`.

### Remover as rodadas de treino

As rodadas com o nome `treino` vão aparecer misturadas. Antes de gerar os gráficos finais, abra o `resultados_validacao.csv` em um editor de texto e **apague as linhas que começam com o nome `treino`**.

Guarde uma cópia do arquivo original antes, para não perder nada.

### Depois, no notebook

```
analise_resultados.ipynb
```

Abra e use **Run All**. Ele traz as duas avaliações (desempenho computacional e de uso) com os gráficos e a leitura crítica, que é o que o professor vai ler.

---

## O que colocar no relatório

Preencha a tabela da seção 3 do seu PDF com os valores do `validacao_resumo.csv`, e escreva a análise crítica usando os pontos de apoio do `docs/relatorio_complemento.md`.

**Declare sempre três coisas:**

1. O **N real**. Se foram 4 pessoas, escreva 4.
2. Que os participantes **não são pessoas sem braços**, então os números medem viabilidade técnica, não o desempenho do público-alvo.
3. Que a amostra é pequena e o estudo é **exploratório**, sem inferência estatística.

Declarar limitação não tira ponto. Esconder, quando o professor pergunta na arguição individual, tira.

**Não invente números.** A arguição é individual e o professor pode pedir o CSV bruto, que tem data e hora de cada rodada.

---

## Tabela para anotar à mão (backup)

| # | Participante | Ordem | Modo | Acertos | Erros | Taxa % | Tempo médio | Observações |
|---|---|---|---|---|---|---|---|---|
| 1 | | | rosto | | | | | |
| 1 | | | mouse | | | | | |
| 2 | | | rosto | | | | | |
| 2 | | | mouse | | | | | |
| 3 | | | rosto | | | | | |
| 3 | | | mouse | | | | | |
| 4 | | | rosto | | | | | |
| 4 | | | mouse | | | | | |

Em "Observações", anote qualquer coisa fora do normal: notificação que apareceu, pessoa de óculos, luz que mudou, participante que riu e perdeu o clique. Isso enriquece a análise crítica e mostra rigor.

---

## Se algo der errado

| Problema | O que fazer |
|---|---|
| O clique não sai | Aperte **C** e recalibre. Se persistir, aumente `EAR_FATOR` para 0.80 no topo do `controle_sem_toque.py`. |
| Clica sozinho ao piscar | Aumente `CLIQUE_SEG` para 0.7, ou diminua `EAR_FATOR` para 0.60. |
| O cursor não alcança os alvos das bordas | Aumente `GANHO_X` e `GANHO_Y`. |
| O cursor está trêmulo e difícil de mirar | Diminua `SUAVIZACAO` para 0.15. |
| Nada foi salvo no CSV | A rodada não foi concluída. Os 8 alvos precisam ser acertados antes do ESC. |
| A rodada ficou inválida (notificação, interrupção) | Refaça com o mesmo nome e **apague a linha ruim** do CSV. Anote na folha o que aconteceu. |

Se mudar qualquer constante no meio da coleta, **comece de novo**: os dados antes e depois da mudança não são comparáveis. E registre no relatório o valor final usado.
