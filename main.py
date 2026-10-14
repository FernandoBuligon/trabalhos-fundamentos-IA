"""Trabalho 1: buscas em uma matriz com terrenos e recompensas."""

from collections import deque
from heapq import heappop, heappush
from itertools import count
import argparse
import sys
import time


CUSTOS = {".": 1, "s": 4, "r": 10, "p": 20}
INTERVALO = 0.12


def criar_cenario():
    """Terrenos e paredes ficam separados dos elementos sobrepostos."""
    mapa = (
        "#################",
        "#...rrpp....s...#",
        "#.######.######.#",
        "#...#.......#...#",
        "#.###.#####.###.#",
        "#.....ss........#",
        "#.###.#####.###.#",
        "#...#.....#..p..#",
        "#################",
        "#######...#######",
        "#################",
    )
    origem = (1, 1)
    premio = (15, 1)
    recompensas = {(3, 3), (8, 1), (3, 7), (6, 7), (8, 7), (13, 7), (8, 9)}
    return mapa, origem, premio, recompensas


def navegavel(mapa, posicao):
    x, y = posicao
    return 0 <= y < len(mapa) and 0 <= x < len(mapa[y]) and mapa[y][x] in CUSTOS


def vizinhos(mapa, posicao):
    x, y = posicao
    return [
        ponto
        for ponto in ((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1))
        if navegavel(mapa, ponto)
    ]


def manhattan(atual, destino):
    return abs(atual[0] - destino[0]) + abs(atual[1] - destino[1])


def custo_entrada(mapa, posicao):
    x, y = posicao
    return CUSTOS[mapa[y][x]]


def custo_rota(mapa, rota):
    """A origem não é cobrada; cada entrada posterior é cobrada uma vez."""
    return sum(custo_entrada(mapa, ponto) for ponto in rota[1:])


def reconstruir_rota(pais, destino):
    rota = []
    atual = destino
    while atual is not None:
        rota.append(atual)
        atual = pais[atual]
    return rota[::-1]


def caminho_na_arvore(pais, origem, destino):
    """Liga dois vértices pela árvore da busca, sem atravessar paredes."""
    ida = reconstruir_rota(pais, origem)
    volta = reconstruir_rota(pais, destino)
    comuns = 0
    while comuns < min(len(ida), len(volta)) and ida[comuns] == volta[comuns]:
        comuns += 1
    return ida[comuns - 1:][::-1] + volta[comuns:]


def busca_cega(mapa, origem, destino, recompensas, profundidade=False):
    """Explora em BFS/DFS e monta o percurso físico das coletas encontradas."""
    if not navegavel(mapa, origem) or not navegavel(mapa, destino):
        return None, 0, set()
    fronteira = deque([(origem, None)]) if profundidade else deque([origem])
    pais = {} if profundidade else {origem: None}
    rota = [origem]
    expandidos = 0
    encontradas = set()
    while fronteira:
        if profundidade:
            atual, pai = fronteira.pop()
            if atual in pais:
                continue
            # Candidatos na pilha não estão descobertos: o ramo atual pode
            # alcançá-los antes. O pai é o deste aprofundamento efetivo.
            pais[atual] = pai
        else:
            atual = fronteira.popleft()
        expandidos += 1
        if atual in recompensas:
            encontradas.add(atual)
            # A recompensa sai da exploração e entra no percurso animado.
            rota.extend(caminho_na_arvore(pais, rota[-1], atual)[1:])
        if atual == destino:
            rota.extend(caminho_na_arvore(pais, rota[-1], destino)[1:])
            return rota, expandidos, encontradas
        proximos = vizinhos(mapa, atual)
        if profundidade:
            proximos.reverse()  # A pilha visita a direita primeiro.
        for proximo in proximos:
            if proximo not in pais:
                if profundidade:
                    fronteira.append((proximo, atual))
                else:
                    pais[proximo] = atual
                    fronteira.append(proximo)
    return None, expandidos, encontradas


def bfs(mapa, origem, destino, recompensas):
    return busca_cega(mapa, origem, destino, recompensas)


def dfs(mapa, origem, destino, recompensas):
    return busca_cega(mapa, origem, destino, recompensas, profundidade=True)


def criar_heuristica(mapa, destino):
    """Retorna custo geométrico mínimo e potencial de coletas sem desvio.

    O potencial conta recompensas em trajetos Manhattan mínimos, em terreno
    de custo mínimo. É uma estimativa: paredes podem impedir essas coletas.
    Ele só desempata a prioridade de custo, nunca reduz o custo dos terrenos.
    """
    menor_custo = min(CUSTOS.values())

    def heuristica(atual, restantes):
        if atual == destino:
            return 0, 0
        distancia = manhattan(atual, destino)
        potenciais = sum(
            manhattan(atual, recompensa) + manhattan(recompensa, destino) == distancia
            and custo_entrada(mapa, recompensa) == menor_custo
            for recompensa in restantes
        )
        return distancia * menor_custo, potenciais

    return heuristica


def reconstruir_estados(pais, estado):
    return [posicao for posicao, _ in reconstruir_rota(pais, estado)]


def busca_informada(mapa, origem, destino, recompensas, usar_custo):
    """A* usa g+h; Gulosa usa custo da próxima entrada+h, sem somar g.

    O estado registra posição e recompensas restantes. As coletas previstas
    e já feitas só desempatam a avaliação de custo. A* examina todos os
    candidatos com f <= custo ótimo antes de escolher o objetivo com mais
    coletas. Gulosa encerra no primeiro objetivo e não garante otimalidade.
    """
    if not navegavel(mapa, origem) or not navegavel(mapa, destino):
        return None, 0, set()
    heuristica = criar_heuristica(mapa, destino)
    restantes = frozenset(recompensas) - {origem}
    inicial = (origem, restantes)
    ordem = count()
    h, potenciais = heuristica(origem, restantes)
    coletadas = len(recompensas) - len(restantes)
    fronteira = [(h, -(coletadas + potenciais), -coletadas, next(ordem), 0, inicial)]
    pais = {inicial: None}
    custos = {inicial: 0}
    expandidos = 0
    encontradas = set()
    melhor_objetivo = None
    melhor_criterio = None
    while fronteira:
        avaliacao, _, _, _, custo, estado = heappop(fronteira)
        if usar_custo and melhor_criterio is not None and avaliacao > melhor_criterio[0]:
            break  # Nenhum candidato restante pode melhorar custo ou coletas.
        if usar_custo and custo != custos[estado]:
            continue
        atual, restantes = estado
        expandidos += 1
        if atual in recompensas:
            encontradas.add(atual)
        if atual == destino:
            if not usar_custo:
                return reconstruir_estados(pais, estado), expandidos, encontradas
            criterio = (custo, -(len(recompensas) - len(restantes)))
            if melhor_criterio is None or criterio < melhor_criterio:
                melhor_criterio = criterio
                melhor_objetivo = estado
            continue  # Não se pode sair do objetivo para buscar recompensas.
        for proximo in vizinhos(mapa, atual):
            outras = restantes - {proximo}
            novo_estado = (proximo, outras)
            novo_custo = custo + custo_entrada(mapa, proximo)
            if usar_custo:
                if novo_custo >= custos.get(novo_estado, float("inf")):
                    continue
            elif novo_estado in pais:
                continue
            pais[novo_estado] = estado
            custos[novo_estado] = novo_custo
            h, potenciais = heuristica(proximo, outras)
            coletadas = len(recompensas) - len(outras)
            # Gulosa considera o terreno do candidato, sem o custo acumulado.
            avaliacao = novo_custo + h if usar_custo else custo_entrada(mapa, proximo) + h
            prioridade = (avaliacao, -(coletadas + potenciais), -coletadas,
                          next(ordem), novo_custo, novo_estado)
            heappush(fronteira, prioridade)
    if melhor_objetivo is not None:
        return reconstruir_estados(pais, melhor_objetivo), expandidos, encontradas
    return None, expandidos, encontradas


def gulosa(mapa, origem, destino, recompensas):
    return busca_informada(mapa, origem, destino, recompensas, False)


def a_estrela(mapa, origem, destino, recompensas):
    return busca_informada(mapa, origem, destino, recompensas, True)


ALGORITMOS = {
    "1": ("BFS", bfs),
    "2": ("DFS", dfs),
    "3": ("Gulosa", gulosa),
    "4": ("A*", a_estrela),
}


def executar_busca(mapa, origem, destino, recompensas, busca):
    """Mede a busca e a construção do percurso, sem entrada ou animação."""
    inicio = time.perf_counter()
    rota, expandidos, encontradas = busca(mapa, origem, destino, recompensas)
    coletadas = set(rota or []) & recompensas
    custo = custo_rota(mapa, rota) if rota is not None else None
    resultado = {
        "rota": rota,
        "expandidos": expandidos,
        "encontradas": encontradas,
        "coletadas": coletadas,
        "custo": custo,
        "criterio": (custo, -len(coletadas)) if rota is not None else None,
        "movimentos": len(rota) - 1 if rota is not None else None,
    }
    resultado["tempo"] = time.perf_counter() - inicio
    return resultado


def mostrar_mapa(mapa, agente, premio, recompensas, destino=None):
    print("\n    " + " ".join(f"{x:2}" for x in range(len(mapa[0]))))
    for y, linha in enumerate(mapa):
        simbolos = []
        for x, terreno in enumerate(linha):
            ponto = (x, y)
            simbolo = terreno
            if ponto in recompensas:
                simbolo = "$"
            if ponto == premio:
                simbolo = "F"
            if ponto == destino and destino != premio:
                simbolo = "D"
            if ponto == agente:
                simbolo = "@"
            simbolos.append(f"{simbolo:>2}")
        print(f"{y:2}  " + " ".join(simbolos))


def mostrar_legenda():
    print("\n. plano (1) | s areia (4) | r rocha (10) | p pântano (20) | # parede")
    print("@ agente | F prêmio final | $ recompensa | D destino escolhido")
    print("Coordenadas (x, y): x = coluna, y = linha, começando em 0.")


def ler_destino(mapa, premio):
    while True:
        entrada = input(f"Destino x y (Enter para o prêmio {premio}): ").strip()
        if not entrada:
            return premio
        partes = entrada.replace(",", " ").split()
        try:
            if len(partes) != 2:
                raise ValueError
            destino = tuple(int(valor) for valor in partes)
        except ValueError:
            print("Informe dois números inteiros, por exemplo: 15 1.")
            continue
        if not navegavel(mapa, destino):
            print("Coordenadas inválidas: escolha uma posição dentro do mapa e sem parede.")
            continue
        return destino


def animar(mapa, rota, premio, recompensas, intervalo=INTERVALO):
    restantes = set(recompensas)
    coletadas = set()
    custo = 0
    for passo, ponto in enumerate(rota):
        if passo:
            time.sleep(intervalo)
            custo += custo_entrada(mapa, ponto)
        mostrar_mapa(mapa, ponto, premio, restantes, rota[-1])
        print(f"Passo {passo}/{len(rota) - 1} | Posição {ponto} | Custo acumulado: {custo}")
        if ponto in restantes:
            restantes.remove(ponto)
            coletadas.add(ponto)
            print(f"Recompensa coletada em {ponto}! Total: {len(coletadas)}")
    print(f"Objetivo alcançado em {rota[-1]}!")
    return coletadas


def mostrar_resultado(nome, resultado):
    print(f"\n{nome}: {'sucesso' if resultado['rota'] is not None else 'sem caminho'}")
    print(f"Tempo de busca e planejamento: {resultado['tempo'] * 1000:.3f} ms")
    print(f"Nós expandidos: {resultado['expandidos']}")
    print(f"Recompensas encontradas na exploração: {len(resultado['encontradas'])} "
          f"{sorted(resultado['encontradas'])}")
    if resultado["rota"] is not None:
        print(f"Custo dos terrenos: {resultado['custo']} "
              f"| Movimentos: {resultado['movimentos']}")
        print(f"Recompensas coletadas na rota: {len(resultado['coletadas'])} "
              f"{sorted(resultado['coletadas'])}")
    else:
        print("Não existe caminho até o destino. Nenhuma rota foi executada.")


def comparar(mapa, origem, destino, recompensas):
    print(f"\nComparação: origem {origem}, destino {destino}")
    print(f"{'Algoritmo':<10} {'Tempo (ms)':>11} {'Expandidos':>11} {'Custo':>7} "
          f"{'Movimentos':>11} {'Coletadas':>10} {'Resultado':>12}")
    for nome, busca in ALGORITMOS.values():
        resultado = executar_busca(mapa, origem, destino, recompensas, busca)
        sucesso = resultado["rota"] is not None
        custo = str(resultado["custo"]) if sucesso else "-"
        movimentos = str(resultado["movimentos"]) if sucesso else "-"
        estado = "sucesso" if sucesso else "sem caminho"
        print(f"{nome:<10} {resultado['tempo'] * 1000:>11.3f} {resultado['expandidos']:>11} "
              f"{custo:>7} {movimentos:>11} {len(resultado['coletadas']):>10} {estado:>12}")
    print("BFS e DFS coletam todas as recompensas dos vértices processados até o objetivo.")
    print("Custo é a soma dos terrenos do percurso, incluindo os retornos para coletar.")
    print("Prioridade: menor custo físico; em empate, mais recompensas.")
    print("Gulosa avalia o próximo terreno + h; A* usa g+h e garante o ótimo.")
    print("Expansões de Gulosa/A* contam estados (posição, recompensas restantes).")
    print("Tempo inclui a busca e construção do percurso, sem animação.")


def main_terminal():
    mapa, origem, premio, recompensas = criar_cenario()
    print("Trabalho 1 — Algoritmos de Busca | Cenário: Vale do Prêmio")
    while True:
        mostrar_mapa(mapa, origem, premio, recompensas)
        mostrar_legenda()
        print("Buscas informadas: custo primeiro; recompensas nos empates.")
        print("\n1 - BFS | 2 - DFS | 3 - Gulosa | 4 - A* | 5 - Comparar | 0 - Sair")
        opcao = input("Opção: ").strip()
        if opcao == "0":
            print("Encerrado.")
            return
        if opcao not in ALGORITMOS and opcao != "5":
            print("Opção inválida. Escolha um número de 0 a 5.")
            continue
        destino = ler_destino(mapa, premio)
        if opcao == "5":
            comparar(mapa, origem, destino, recompensas)
        else:
            nome, busca = ALGORITMOS[opcao]
            resultado = executar_busca(mapa, origem, destino, recompensas, busca)
            if resultado["rota"] is not None:
                print(f"\nRota de {nome} calculada. Iniciando movimentação...")
                animar(mapa, resultado["rota"], premio, recompensas)
            mostrar_resultado(nome, resultado)
        print("\nCada execução começa novamente na origem, com todas as recompensas.")


def main():
    parser = argparse.ArgumentParser(description="Visualizador de algoritmos de busca.")
    parser.add_argument("--terminal", action="store_true", help="usar o menu de texto")
    argumentos = parser.parse_args()
    if argumentos.terminal:
        main_terminal()
        return 0
    try:
        from tkinter import TclError
        from gui import iniciar_interface
    except ImportError as erro:
        if erro.name not in {"tkinter", "_tkinter"}:
            raise
        print("Tkinter não está disponível neste Python. Instale o suporte Tk "
              "ou execute: python3 main.py --terminal", file=sys.stderr)
        return 1
    try:
        iniciar_interface()
    except TclError as erro:
        print(f"Não foi possível abrir a janela gráfica: {erro}\n"
              "Confira o suporte Tk e a sessão gráfica. "
              "Alternativa: python3 main.py --terminal", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (EOFError, KeyboardInterrupt):
        print("\nEncerrado.")
