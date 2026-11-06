# Como digitar uma mensagem sem usar as mãos

Guia prático para escrever um texto (um e-mail, uma mensagem, uma busca) usando só a cabeça e as expressões do rosto. Serve também como roteiro da demonstração no pitch.

Nada aqui exige mudar o código. São ajustes de uso e de configuração do Windows.

---

## O essencial em uma frase

O teclado virtual do Windows digita **na janela que estava em foco antes**. Então a ordem é sempre: primeiro clicar no campo de texto, depois clicar nas teclas.

---

## Passo a passo da demonstração

### 1. Prepare a tela antes de começar

Deixe aberto o que vai receber o texto (Bloco de Notas, WhatsApp Web, campo de busca). Isso evita ter que navegar entre janelas durante a demonstração.

### 2. Inicie o sistema

```powershell
.\iniciar.bat
```

Durante os 3 segundos de calibração, olhe para a tela com os olhos abertos, a boca fechada e o rosto relaxado.

### 3. Abra o teclado virtual

Abra a boca por **0,8 segundos**. O aviso "TECLADO ABERTO" aparece na janela da câmera e o `osk.exe` surge na parte de baixo da tela.

(Alternativa para quem está ajudando: tecla **O** com a janela da câmera em foco.)

### 4. Ligue o modo "passar o mouse sobre as teclas" — o ajuste que faz a diferença

Esta é a parte que resolve o cansaço. Faça **uma vez só**; o Windows guarda a configuração.

1. No teclado virtual, clique na tecla **Opções** (canto inferior direito).
2. Em **Modo de digitação**, escolha **Passar o mouse sobre as teclas**.
3. Ajuste a **Duração da focalização** para algo entre **0,8 s e 1,2 s**.
4. Clique em **OK**.

A partir daí, você digita só **parando o cursor sobre a tecla**. Não precisa fechar os olhos para cada letra: a tecla é acionada sozinha depois do tempo escolhido.

Se o seu Windows não mostrar essa opção (a aparência do teclado virtual muda entre as versões), siga com o modo normal de clique, descrito no passo 6b.

### 5. Clique no campo de texto

Mova a cabeça até o campo onde o texto vai aparecer e **feche os dois olhos por cerca de 0,8 s** (entre 0,5 s e 1,2 s) para dar o clique. O cursor piscando no campo confirma que deu certo.

Esse passo é obrigatório: sem ele, as letras não têm para onde ir.

### 6. Escreva

**6a. Com o modo hover ligado (recomendado):** leve o cursor até a letra, pare por um instante, e ela é digitada. Siga para a próxima letra. Mantenha os olhos abertos o tempo todo — o cursor só se move com os olhos abertos.

**6b. Com cliques:** leve o cursor até a letra e feche os dois olhos por cerca de 0,8 s. Uma letra por clique.

Dica: enquanto o cursor está "a caminho" de uma tecla, não pisque de propósito. Piscadas naturais (perto de 0,2 s) são ignoradas, mas uma piscada demorada vira clique.

### 7. Maiúsculas, acentos e pontuação

- **Maiúscula:** clique em **Shift** e depois na letra. O teclado virtual mantém o Shift até a próxima tecla.
- **Acentos:** clique na tecla do acento (`´`, `~`, `^`) e depois na vogal, igual ao teclado físico.
- **Espaço:** a barra larga embaixo.
- **Apagar:** **Backspace**, no canto superior direito.
- **Enviar a mensagem:** **Enter**, ou mova o cursor até o botão de enviar e clique com os olhos.

### 8. Feche o teclado quando terminar

Abra a boca por 0,8 segundos de novo. O aviso "TECLADO FECHADO" confirma.

### 9. Pause para falar

Para explicar o que está acontecendo sem o cursor sair andando pela tela, faça um **beijinho (bico com os lábios) por 1,0 segundo**. O aviso "PAUSADO" aparece. Repita o beijinho para retomar: o programa reancora a cabeça na posição atual do cursor, então ele não salta.

Use isso sempre que for conversar com a banca.

---

## Se estiver difícil acertar as teclas

As teclas do teclado virtual são pequenas. Três caminhos, do mais simples ao que mexe em configuração:

**1. Aumente o teclado virtual.** Arraste a borda superior do `osk.exe` para cima com o próprio controle por rosto, ou use o modo arrastar: levante as sobrancelhas por 0,7 s (liga o arrastar), mova a cabeça para esticar a janela, e levante as sobrancelhas de novo para soltar. Teclas maiores = muito mais fácil acertar.

**2. Deixe o cursor mais calmo.** No topo do `controle_sem_toque.py`:

| Constante | Padrão | Para digitar melhor |
|---|---|---|
| `GANHO_X` | 5.0 | diminua para 3.0–4.0 (movimento mais fino) |
| `GANHO_Y` | 6.0 | diminua para 4.0–5.0 |
| `SUAVIZACAO` | 0.25 | diminua para 0.15 (cursor mais estável, menos tremor) |

Ganho menor = o cursor anda menos para o mesmo movimento de cabeça, o que dá mais precisão e menos alcance. Se o cursor não chegar mais nas bordas da tela, aumente um pouco de volta.

**3. Se o modo hover estiver ligado e as teclas dispararem sem querer**, aumente a duração da focalização nas Opções do teclado virtual (para 1,5 s, por exemplo).

## Problemas comuns na hora de digitar

**As letras não aparecem em lugar nenhum.** O campo de texto perdeu o foco. Clique nele outra vez (passo 5) e continue. Isso acontece se você clicou em qualquer outro lugar da tela no meio da digitação.

**A janela da câmera está na frente do teclado virtual.** A prévia fica no canto superior direito e o `osk.exe` embaixo, então normalmente não se cruzam. Se cruzarem, mova o teclado virtual para baixo arrastando pela barra de título dele.

**O cursor não se move.** Veja na janela da câmera: se estiver escrito "PAUSADO", faça o beijinho para retomar. Se estiver "MODO ROLAGEM", feche só o olho esquerdo por 0,6 s para sair. Se estiver "Rosto nao detectado", acenda mais luz no ambiente.

**Saiu um duplo clique no lugar de um clique.** Você fechou os olhos por mais de 1,2 s. Mire em 0,8 s: a barra "Clique" na janela da câmera fica **verde** na faixa do clique simples e **azul** na faixa do duplo. Use a cor da barra como guia.

**Um clique direito abriu um menu.** Você fechou só o olho direito por 0,6 s. Feche os olhos e abra rápido, ou aperte Esc, para fechar o menu.

## Roteiro curto para gravar o pitch

1. Mostrar o rosto e as mãos para trás, deixando claro que ninguém toca no notebook.
2. Iniciar e calibrar (3 s).
3. Mover o cursor pela tela, mostrando que a cabeça comanda.
4. Abrir a boca: o teclado virtual aparece.
5. Clicar no campo de texto com os olhos.
6. Digitar uma frase curta, por exemplo "oi, estou escrevendo sem usar as maos".
7. Enter para enviar.
8. Beijinho para pausar e explicar que tudo roda localmente, sem enviar imagem para a internet.

Frases curtas funcionam melhor em vídeo: cada letra leva de 1 a 2 segundos.
