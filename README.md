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
- Informe o destino como `x y` (coluna e linha, começando em zero), ou
  clique em uma célula livre do mapa. **Usar prêmio** seleciona `(15, 1)`;
  deixar o campo vazio também usa esse destino.
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
- **Comparar os quatro** pausa a animação e preenche a tabela de resultados
  para o destino escolhido na aba **Comparação**. Dê um duplo clique em uma
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

Para decidir se compensa desviar, cada recompensa deixada para trás custa
uma penalidade fixa `PENALIDADE = 10` (o mesmo custo de um terreno rochoso).
As buscas informadas minimizam:

```text
total = custo dos terrenos + 10 × recompensas não coletadas
```

Assim, um desvio vale a pena quando custa menos de 10 por recompensa
coletada. Cada estado contém a posição `p` e as recompensas restantes `R`.

**Heurística.** Seja `dist = Manhattan(p, d)`, sendo `d` o destino. Passar
por uma recompensa `r` alonga o caminho mínimo em
`desvio(r) = Manhattan(p, r) + Manhattan(r, d) - dist`. Para pegar as `k`
recompensas de menor desvio, o agente anda pelo menos `dist` mais o maior
desvio entre elas e deixa de pagar `k` penalidades:

```text
h(p, R) = min sobre k = 0..|R| de  c_min × (dist + desvio_k) + 10 × (|R| - k)
h(d, R) = 10 × |R|        (a rota termina no destino)
```

`c_min = 1` é o menor custo de terreno e `desvio_0 = 0`. Paredes e terrenos
caros só aumentam o custo real, então `h` nunca superestima: é admissível e
consistente.

**A\*** ordena a fronteira por `f = g + h`, em que `g` é o custo dos terrenos
já percorridos, e para no primeiro destino retirado da fronteira. Esse
resultado tem o menor total possível. Um teste compara o A* com a busca de
custo uniforme (`h = 0`) em todos os 70 destinos.

**Gulosa** ordena apenas por `h(n)` e também para no primeiro destino. É
mais rápida de pensar, mas não garante o menor total. Empates seguem a ordem
de inserção.

## Comparação e apresentação

A janela mostra cada posição, coleta e custo acumulado, com velocidade
ajustável (inicialmente 4 passos por segundo). No modo terminal, o intervalo
continua sendo 0,12 segundo. A comparação mostra tempo, nós expandidos, custo dos
terrenos, movimentos, recompensas coletadas e sucesso ou
ausência de caminho. `time.perf_counter()` mede a busca e a construção
do percurso, sem entrada ou animação.

Uma expansão corresponde a um estado retirado da fronteira e processado,
inclusive o destino; entradas obsoletas do A* não contam. BFS/DFS processam
cada vértice uma vez. Gulosa/A* podem processar a mesma posição com
diferentes conjuntos de recompensas restantes. Essa diferença faz parte
da comparação. Recompensas encontradas na exploração são mostradas
separadamente das efetivamente coletadas pelo percurso.

Para apresentar, clique em **Comparar os quatro** usando o destino padrão
`(15, 1)` (ou escolha `5` e Enter no modo terminal):

| Algoritmo | Custo dos terrenos | Movimentos | Coletadas |
|---|---:|---:|---:|
| BFS | 241 | 70 | 5 |
| DFS | 73 | 14 | 1 |
| Gulosa | 86 | 58 | 6 |
| A* | 47 | 44 | 5 |

O A* desvia para cinco recompensas com custo 47 (total 47 + 2 × 10 = 67).
Ir direto custaria 25, mas deixaria seis recompensas (total 85). Pegar as
seis acessíveis custa 75 (total 85). A Gulosa coleta as seis, mas paga
mais que o A*. A sala em `(8, 9)` é isolada: use esse destino para demonstrar ausência
de caminho. Sua recompensa não é alcançável a partir da origem.

## Verificação

Execute os testes com a biblioteca padrão do Python:

```bash
python3 -m unittest discover -s tests -v
```

Os testes conferem os resultados dos quatro algoritmos, destinos inválidos
e inacessíveis, a reprodução dos custos e coletas, pausa, continuação,
reinício, comparação e seleção do destino após redimensionar a janela.
Os testes dos widgets precisam de Tkinter e de uma sessão gráfica;
quando indisponíveis, são marcados como ignorados. Os testes das buscas
continuam executando normalmente.
