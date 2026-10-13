# Trabalho 1 — Algoritmos de Busca

Execute com Python 3, sem instalar dependências:

```bash
python3 main.py
```

O menu permite escolher BFS, DFS, Gulosa, A* ou comparar os quatro. Informe
o destino como `x y` (coluna e linha, começando em zero) ou pressione Enter
para usar o prêmio final `(15, 1)`. Cada execução reinicia o cenário.

O mapa fixo tem 70 vértices navegáveis, paredes, becos sem saída e sete
recompensas. A legenda aparece no terminal. Os terrenos são separados do
agente, destino e recompensas: entrar em plano custa 1, areia 4, rocha 10
e pântano 20. Apenas movimentos horizontais e verticais são permitidos.
A origem não é cobrada; entradas repetidas durante desvios são cobradas.

BFS usa uma fila e encontra o menor número de movimentos. DFS usa uma
pilha. Ambos identificam recompensas nos nós processados, mas coletam
somente aquelas da rota executada. Nenhum dos dois garante menor custo
em terrenos ponderados. Gulosa prioriza a distância de Manhattan
`h = |x - x_destino| + |y - y_destino|`. A* prioriza `g + h`, em que `g`
é o custo acumulado. Como todo movimento custa pelo menos 1, essa
heurística é admissível e A* encontra o menor custo entre dois pontos.

Gulosa e A* primeiro calculam a rota direta. Para cada recompensa fora
dela, avaliam pontos próximos dessa rota e buscam ida e volta usando
o próprio algoritmo. Escolhem o trecho de menor custo adicional encontrado
e aceitam desvios de até 10 por recompensa. Todas as elegíveis são
consideradas, priorizando menor custo adicional e evitando repetir coletas,
inclusive as incidentais. Os desvios retornam ao ponto de saída e não
passam pelo destino antes do encerramento. O limite é individual; a soma
dos desvios pode superar 10. A heurística do A* permanece inalterada;
a rota completa com recompensas pode custar mais que a direta ótima.

A movimentação mostra cada posição, coleta e custo acumulado, com pausa
de 0,12 segundo. A comparação mostra tempo, nós expandidos, custo real,
movimentos, recompensas coletadas e sucesso ou ausência de caminho.
O tempo usa `time.perf_counter()` e inclui busca e planejamento, sem entrada
ou animação. Um nó expandido é retirado da fronteira e processado, inclusive
o destino; entradas obsoletas do A* não contam. Buscas auxiliares somam
suas expansões, mesmo ao processar novamente um vértice em outra busca.
Recompensas encontradas incluem a exploração dessas buscas auxiliares;
coletadas são posições únicas efetivamente percorridas.

Para apresentar, escolha `5` e Enter: BFS/DFS têm custo 73; Gulosa com
desvios, 81 e duas coletas; A* direto, 25; A* com desvios, 53 e cinco coletas.
A recompensa em `(13, 7)` exige um desvio caro. O destino e a recompensa
em `(8, 9)` ficam numa sala isolada, permitindo demonstrar ausência de caminho.
