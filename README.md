# Trabalho 1 — Algoritmos de Busca

Execute com Python 3 e suporte a Tkinter:

```bash
python3 main.py
```

O comando abre uma janela gráfica com o mapa colorido e os controles da
simulação. Não é necessário instalar pacotes com `pip`. Se Tkinter estiver
ausente, instale o suporte Tk correspondente ao Python utilizado; no Python
do sistema em Debian/Ubuntu, o pacote é `python3-tk`. A janela precisa de
uma sessão gráfica disponível.

### Como usar a janela

- Escolha **BFS**, **DFS**, **Gulosa** ou **A\*** no seletor de algoritmo.
- Informe o destino nos campos **X** (coluna) e **Y** (linha), começando em
  zero. Digite os valores ou clique em uma célula livre do mapa. Ao lado dos campos aparece o terreno escolhido. **Prêmio** seleciona
  `(15, 1)`; deixar os dois campos vazios também usa esse destino.
- **Executar** calcula a rota e inicia a animação. **Pausar** interrompe o
  movimento; **Continuar** retoma do mesmo ponto.
- **Passo** calcula a rota, se necessário, e avança um movimento por clique.
- Ajuste a velocidade entre **1 e 12 passos por segundo**, inclusive durante
  a animação. A janela continua respondendo aos controles.
- **Reiniciar** devolve o agente à origem e restaura todas as recompensas,
  mantendo o algoritmo e o destino selecionados. Mudar o algoritmo ou o
  destino também descarta o percurso anterior.
- Ative **Custos** para ver o custo de entrada dos terrenos e **Rota planejada**
  para mostrar o percurso completo em linha tracejada. O caminho já percorrido
  aparece em azul. Passe o mouse sobre uma célula para consultar seus detalhes.
- Atalhos: **Espaço** executa ou pausa, **→** avança um passo e **R** reinicia
  (fora dos campos de texto).
- **Comparar todos** pausa a animação e preenche a tabela de resultados
  para o destino escolhido na aba **Comparação**. Cartões no topo indicam o
  melhor algoritmo em total, tempo, nós expandidos e memória; a linha com o
  menor total fica em verde, e um gráfico de barras compara tempo, nós
  expandidos, nós armazenados e total (★ marca o menor valor de cada métrica). Dê um duplo clique em uma
  linha (ou selecione-a e use **Ver rota selecionada** ou Enter) para carregar
  a rota desse algoritmo, inicialmente pausada, na aba **Mapa e animação**.
  **Voltar ao mapa** permite retornar sem carregar uma nova rota.

O painel distingue o custo e as recompensas do percurso já executado das
métricas da busca e do custo final planejado. Destinos inválidos e ausência
de caminho são informados na própria janela. O mapa se ajusta ao tamanho
da janela, sem imprimir um novo quadro no terminal a cada movimento.

### Modo terminal

O menu original continua disponível, inclusive em máquinas sem interface gráfica:

```bash
python3 main.py --terminal
```

Nesse modo, escolha `1` a `4` para executar uma busca, `5` para comparar
ou `0` para sair. Informe o destino como `x y` ou pressione Enter para usar
o prêmio final. Cada execução reinicia o cenário.

O mapa fixo tem 70 vértices navegáveis, paredes, becos sem saída e sete
recompensas. A legenda aparece abaixo do mapa. Os terrenos são separados do
agente, destino e recompensas: entrar em plano custa 1, areia 4, rocha 10
e pântano 20. Apenas movimentos horizontais e verticais são permitidos.
A origem não é cobrada; cada entrada posterior, inclusive retornos, é cobrada.

## BFS e DFS: coleta durante a exploração

BFS processa a fronteira com uma fila; DFS, com uma pilha. Na DFS, o vértice
é descoberto ao sair da pilha, com o pai do ramo efetivamente aprofundado;
candidatos pendentes não impedem essa descoberta. A ordem dos vizinhos é
direita, baixo, esquerda e cima. As recompensas dos vértices processados
antes do encerramento da busca entram no percurso
que será executado. Para cada coleta, o agente segue as ligações da árvore
da busca desde sua última posição, retornando pelos ancestrais quando
necessário. Depois da última coleta, segue até o objetivo. A animação visita
fisicamente todas essas recompensas e contabiliza os custos dos retornos.

BFS encontra uma ligação com o menor número de passos até o destino,
mas o percurso completo de coleta pode ser maior. BFS e DFS não garantem
o menor custo em terrenos ponderados. Se o destino estiver inacessível,
nenhum percurso é executado e nenhuma recompensa é contabilizada como coletada.

## Gulosa e A*: recompensas na heurística

**Decisão de modelagem do projeto.** O enunciado define a melhor rota pelo
menor custo, mas também pede que o agente avalie quando compensa desviar
para pegar recompensas. Ele não atribui um valor às recompensas. Para
colocar os dois critérios na mesma escala, o projeto adota uma penalidade
fixa `PENALIDADE = 10` (o custo de um terreno rochoso) por recompensa
deixada para trás. Esse valor é uma escolha nossa, não uma regra do
enunciado: com ele, um desvio compensa quando custa menos de 10 por
recompensa coletada. As buscas informadas tratam o problema composto:

```text
total = custo dos terrenos + 10 × recompensas não coletadas
```

Esse total é diferente do menor custo apenas em terrenos (25 no destino
padrão) e não equivale a pegar todas as recompensas a qualquer preço.

**Formulação.** O estado é `(p, R, final)`: posição, recompensas restantes
e se a rota já foi encerrada. As ações são mover para um vizinho (custo do
terreno de entrada) e, ao chegar no destino `d`, **finalizar**: a única ação
disponível em `d`, que leva ao estado meta com custo `10 × |R|`. Assim a
penalidade faz parte de `g`, e a meta é o estado finalizado.

**Heurística.** Seja `dist = Manhattan(p, d)`. Passar por uma recompensa `r`
alonga o caminho mínimo em
`desvio(r) = Manhattan(p, r) + Manhattan(r, d) - dist`. Para pegar as `k`
recompensas de menor desvio, o agente anda pelo menos `dist` mais o maior
desvio entre elas e deixa de pagar `k` penalidades:

```text
h(p, R) = min sobre k = 0..|R| de  c_min × (dist + desvio_k) + 10 × (|R| - k)
h(d, R) = 10 × |R|        (custo exato da ação de finalizar)
h(meta) = 0
```

`c_min = 1` é o menor custo de terreno e `desvio_0 = 0`. Paredes e terrenos
caros só aumentam o custo real, então `h` nunca superestima o custo
restante do problema composto: é admissível e consistente. Um teste
percorre todas as transições alcançáveis do destino padrão conferindo
`h(n) ≤ c(n, n') + h(n')` e `h(meta) = 0`.

**A\*** ordena a fronteira por `f = g + h` e para quando retira a meta.
A garantia de otimalidade vale **para o total composto**, não para o custo
apenas dos terrenos. Um teste compara o A* com a busca de custo uniforme
(`h = 0`) em todos os 70 destinos.

**Gulosa** ordena apenas por `h(n)`. Ela tenta reduzir o mesmo total, mas
não garante o menor valor. Empates seguem a ordem de inserção.

## Comparação e apresentação

A janela mostra cada posição, coleta e custo acumulado, com velocidade
ajustável (inicialmente 4 passos por segundo). No modo terminal, o intervalo
continua sendo 0,12 segundo. `time.perf_counter()` mede a busca e a
construção do percurso, sem entrada ou animação. A comparação mostra:

| Coluna | Significado |
|---|---|
| Tempo | Busca e construção do percurso, em milissegundos. |
| Expandidos | Nós retirados da fronteira cujos sucessores foram gerados. O objetivo é testado ao sair da fronteira e não é expandido; entradas obsoletas do A* não contam. |
| Pico da fronteira | Maior número de entradas na fronteira ao mesmo tempo (inclui duplicatas da pilha da DFS e entradas obsoletas do heap, pois ocupam memória). |
| Armazenados | Estados distintos gerados e mantidos na memória da busca (abertos e fechados), contados uma vez. |
| Terrenos | Soma dos custos de entrada do percurso, incluindo retornos. |
| Total | Terrenos + 10 por recompensa não coletada. Só Gulosa/A* usam esse critério. |

BFS/DFS operam sobre posições; Gulosa/A* operam sobre
`(posição, recompensas restantes, final)`. Por isso a mesma posição pode
aparecer em vários estados, e os números de memória não são diretamente
equivalentes entre os dois grupos. Neste problema, as buscas informadas
expandem **mais** estados que as cegas, porque resolvem um problema maior.
Recompensas encontradas na exploração são mostradas separadamente das
efetivamente coletadas pelo percurso.

Para apresentar, clique em **Comparar todos** usando o destino padrão
`(15, 1)` (ou escolha `5` e Enter no modo terminal):

| Algoritmo | Terrenos | Total | Movimentos | Coletadas | Expandidos | Pico da fronteira | Armazenados |
|---|---:|---:|---:|---:|---:|---:|---:|
| BFS | 241 | 261 | 70 | 5 | 48 | 6 | 51 |
| DFS | 73 | 133 | 14 | 1 | 14 | 3 | 17 |
| Gulosa | 86 | 96 | 58 | 6 | 524 | 77 | 601 |
| A* | 47 | 67 | 44 | 5 | 1118 | 113 | 1219 |

O total conta as sete recompensas do mapa, inclusive a da sala isolada.
O A* desvia para cinco recompensas com custo 47 (total 47 + 2 × 10 = 67).
Ir direto custaria 25, mas deixaria seis recompensas (total 85). Pegar as
seis acessíveis custa 75 (total 85). A Gulosa coleta as seis, mas paga
mais que o A*. A sala em `(8, 9)`, nas linhas 8 a 10 do mapa e marcada com contorno
tracejado na janela, é isolada: só paredes a cercam. Use esse destino para
demonstrar ausência de caminho. Sua recompensa não é alcançável a partir da origem.

## Verificação

Execute os testes com a biblioteca padrão do Python:

```bash
python3 -m unittest discover -s tests -v
```

Os testes conferem os resultados dos quatro algoritmos, a consistência da
heurística, as métricas de memória, destinos inválidos
e inacessíveis, a reprodução dos custos e coletas, pausa, continuação,
reinício, comparação e seleção do destino após redimensionar a janela.
Os testes dos widgets precisam de Tkinter e de uma sessão gráfica;
quando indisponíveis, são marcados como ignorados. Os testes das buscas
continuam executando normalmente.
