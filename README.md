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

O PDF define a melhor rota como a de menor custo, mas também pede avaliar
se compensa desviar para coletar recompensas, sem atribuir valor às coletas
ou definir quanto custo adicional aceitar. Adotamos a interpretação apoiada
na definição explícita: **primeiro minimizar o custo físico; em empate,
maximizar as coletas**. Um percurso mais longo pode compensar se atravessar
terrenos baratos e mantiver o mesmo custo. Não há pesos ou penalidades
inventados. Essa é uma interpretação da ambiguidade, não uma regra adicional
do professor.

Cada estado contém a posição `p` e as recompensas restantes `R`. Se `R0`
é o conjunto inicial, `q = |R0| - |R|` conta as coletas únicas, incluindo
uma recompensa na origem ou no destino. A chegada ao destino `d` encerra
a rota. O critério final é o par `(C, -q)`, ordenado lexicograficamente:

```text
C = soma de c(v) em cada entrada do percurso, exceto a posição inicial
h(p) = c_min × (|x_p - x_d| + |y_p - y_d|)
P(p, R) = quantidade de r em R com:
          Manhattan(p, r) + Manhattan(r, d) = Manhattan(p, d)
          e c(r) = c_min
```

`c(v)` é o custo do terreno de `v`; `c_min = 1` é o menor custo possível.
`h` estima o deslocamento restante. `P` estima coletas em terrenos baratos
sem aumentar a distância geométrica mínima; paredes podem impedir essas
coletas e não se garante que todas caibam no mesmo percurso. O potencial
serve apenas para desempatar a avaliação de custo.

**A\*** usa a avaliação `(g + h, -(q + P), -q)`, em que `g` é o custo físico
acumulado. Como cada passo custa pelo menos `c_min`, `h` é admissível e
consistente. A busca não termina no primeiro objetivo: continua enquanto
houver candidatos com `g + h` menor ou igual ao melhor custo encontrado.
Assim encontra o custo mínimo e, entre essas rotas, o máximo de coletas.

**Gulosa** usa a avaliação local `(c(v) + h(v), -(q + P), -q)` para cada
candidato `v`: considera o custo real da próxima entrada e estima o
restante. Não soma `g` à prioridade, preservando a diferença para A*.
A origem não é cobrada. Essa avaliação evita preferir um pântano próximo
somente pela recompensa, mas não garante menor custo nem máximo global
de coletas. Gulosa encerra no primeiro objetivo processado.

No objetivo, `h = 0` e `P = 0`; a recompensa do destino já foi removida de
`R`. A avaliação do A* é `(g, -q, -q)` e a da Gulosa é `(c(d), -q, -q)`:
esta inclui a entrada que levou ao destino. Se a origem já for o destino,
a entrada e a avaliação de custo são zero. Não há penalidade por deixar
recompensas. Empates restantes seguem a ordem determinística de inserção.
Por exemplo, escolhendo `(8, 1)` como destino no mapa, a heurística na
origem retorna `h = 7` e `P = 1`; no destino, retorna ambos iguais a zero.

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
| Gulosa | 29 | 26 | 2 |
| A* | 25 | 22 | 1 |

A* encontra custo físico mínimo 25 e a maior quantidade de coletas possível
nesse custo: uma. Coletar cinco recompensas exige custo mínimo 47; coletar
as seis acessíveis exige 75. Esses percursos não são preferidos pelo critério
adotado. A sala em `(8, 9)` é isolada: use esse destino para demonstrar ausência
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
