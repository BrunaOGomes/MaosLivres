# Tutorial: gerar o relatório final em PDF

Três comandos e uma impressão. Tempo total: **cerca de 5 minutos**, sendo 1,5 minuto de gravação com a câmera.

---

## Como as peças se encaixam

Entender isso evita confusão depois:

```
metricas_gestos.py ──┐
benchmark_desempenho.py ──┤──> resultados/*.csv e *.png
analise_resultados.py ──┘           │
                                    │
RELATORIO_FINAL.md  (o texto) ──────┤
                                    v
                         gerar_relatorio.py
                                    │
                                    v
                      RELATORIO_FINAL.html  ──Ctrl+P──> PDF
```

Os scripts **medem** e salvam em `resultados/`. O `gerar_relatorio.py` junta o texto com os números e os gráficos num arquivo só. O navegador transforma em PDF.

**Você nunca precisa copiar número do CSV para o relatório à mão.** A tabela da seção 3.3 e as 9 figuras entram automaticamente.

---

## Passo 1 — Medir as métricas de gesto (1,5 min)

Abra o PowerShell na pasta do projeto e rode:

```powershell
venv\Scripts\python.exe metricas_gestos.py
```

Uma janela com sua câmera abre e mostra instruções no topo. **Siga o roteiro**, que dura 63 segundos:

| Tempo | O que fazer |
|---|---|
| 0 – 3 s | **Calibração.** Rosto relaxado, olhos abertos, boca fechada. Não faça gesto nenhum. |
| 3 – 13 s | Apenas olhe para a tela, normal. |
| 13 – 23 s | **Pisque naturalmente** várias vezes. |
| 23 – 33 s | **Feche os dois olhos por 1 segundo e abra.** Repita umas 5 vezes. |
| 33 – 43 s | **Levante as sobrancelhas**, segure 1 segundo, solte. Repita. |
| 43 – 53 s | **Faça biquinho**, segure 1,5 segundo, solte. Repita. |
| 53 – 63 s | **Mova a cabeça** nos 4 cantos da tela. |

A janela fecha sozinha no fim. O script **não mexe no seu mouse**.

Por que o roteiro importa: as etapas 13–23 s e 23–33 s são o que gera o gráfico mais forte do relatório, aquele que mostra visualmente que **piscada natural não vira clique**. Sem piscar de verdade nessa janela de tempo, o gráfico fica vazio.

No fim ele imprime os números no terminal e cria:

```
resultados/metricas_gestos.csv
resultados/metricas_gestos_resumo.csv
resultados/grafico_ear.png
resultados/grafico_blendshapes.png
resultados/grafico_nariz.png
```

---

## Passo 2 — Corrigir o benchmark (30 s)

O benchmark que já está no relatório foi rodado **sem rosto na frente da câmera**, então a taxa de detecção ficou em 0%. Rode de novo, agora **sentada na frente da câmera**:

```powershell
venv\Scripts\python.exe benchmark_desempenho.py
```

Fique olhando para a tela durante os 300 quadros (uns 15 segundos). Ele não abre janela e não mexe no mouse.

Isso corrige a taxa de detecção e o tempo de inferência, que estava subestimado porque sem rosto o modelo trabalha menos.

---

## Passo 3 — Gerar o arquivo final

```powershell
venv\Scripts\python.exe gerar_relatorio.py
```

Saída esperada:

```
RELATORIO GERADO
Arquivo .......... ...\RELATORIO_FINAL.html
Tamanho .......... 500 KB
Tabela 3.3 ....... preenchida com os dados medidos
Figuras embutidas  9
  OK   resultados/grafico_latencia.png
  ...
```

**Confira duas linhas:**

- `Tabela 3.3 ....... preenchida com os dados medidos` — se disser "VAZIA", o Passo 1 não rodou.
- `Figuras embutidas  9` — se for menos de 9, ele lista quais faltam e qual script rodar.

---

## Passo 4 — Abrir o HTML

Três formas, use a que preferir.

**Pelo Explorador de Arquivos:** abra a pasta do projeto e dê **duplo clique** em `RELATORIO_FINAL.html`. Abre no navegador padrão.

**Pelo PowerShell:**

```powershell
start RELATORIO_FINAL.html
```

**Pelo Chrome/Edge:** arraste o arquivo para dentro de uma aba vazia do navegador.

O arquivo é **autocontido**: os gráficos estão embutidos dentro dele em base64. Você pode mandar só esse `.html` por e-mail e as imagens vão junto. Não existe pasta de imagens para esquecer.

---

## Passo 5 — Converter para PDF

Com o relatório aberto no navegador:

1. Aperte **`Ctrl + P`**
2. Em **Destino** (ou *Impressora*), escolha **"Salvar como PDF"**
3. Clique em **"Mais configurações"**
4. Marque **"Gráficos de fundo"** (em inglês: *Background graphics*)
5. Deixe **Margens: Padrão** e **Escala: Padrão**
6. Clique em **Salvar** e escolha o nome, por exemplo `MaosLivres_Relatorio.pdf`

### O passo 4 não é opcional

Sem marcar **"Gráficos de fundo"**, os cabeçalhos azuis das tabelas saem brancos e as tabelas ficam quase ilegíveis no PDF. É o erro mais comum nessa conversão.

### Se o PDF sair com problema

| Problema | Solução |
|---|---|
| Tabelas sem cor, cabeçalho branco | Marque "Gráficos de fundo" nas configurações de impressão |
| Tabela cortada no meio entre duas páginas | Diminua a escala para 90% em "Escala" → "Personalizada" |
| Gráficos não aparecem | O HTML foi gerado antes dos gráficos existirem. Rode `gerar_relatorio.py` de novo |
| Aparece uma caixa amarela de aviso no topo | É proposital: ela avisa que falta figura e **não sai na impressão**. Mas resolva o que ela aponta antes de entregar |
| Caixa vermelha tracejada no lugar de um gráfico | Aquele gráfico não existe. Veja qual script o `gerar_relatorio.py` mandou rodar |

---

## Antes de enviar: 4 coisas para preencher à mão

Abra o **`RELATORIO_FINAL.md`** (é o texto editável) e complete:

1. **Nomes completos e RMs** de todos os integrantes, no topo
2. **Turma**
3. **URL do repositório no GitHub**
4. Na seção 3.2, a **análise crítica** já está escrita com base nos seus números reais — leia e ajuste se quiser pôr algo seu

Depois rode `gerar_relatorio.py` de novo para o HTML pegar as mudanças.

---

## Sequência completa, para copiar e colar

```powershell
venv\Scripts\python.exe metricas_gestos.py
venv\Scripts\python.exe benchmark_desempenho.py
venv\Scripts\python.exe analise_resultados.py
venv\Scripts\python.exe gerar_relatorio.py
start RELATORIO_FINAL.html
```

Depois: `Ctrl+P` → Salvar como PDF → marcar "Gráficos de fundo".

---

## O que você entrega no fim

| Arquivo | Para quê |
|---|---|
| `MaosLivres_Relatorio.pdf` | o PDF que o professor pede |
| Link do repositório GitHub | com scripts, notebook, CSVs e gráficos |

E o repositório precisa conter a pasta `resultados/` com os CSVs e PNGs, porque é a "comprovação das métricas" que o enunciado exige. O `.gitignore` já está configurado para **não** ignorar essa pasta.
