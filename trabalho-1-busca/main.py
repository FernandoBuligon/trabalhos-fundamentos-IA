"""Trabalho 1: buscas em uma matriz com terrenos e recompensas."""

from collections import deque
from heapq import heappop, heappush
from itertools import count
import time


CUSTOS = {".": 1, "s": 4, "r": 10, "p": 20}
LIMITE_DESVIO = 10
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


def bfs(mapa, origem, destino, recompensas):
    if not navegavel(mapa, origem) or not navegavel(mapa, destino):
        return None, 0, set()
    fronteira = deque([origem])
    pais = {origem: None}
    expandidos = 0
    encontradas = set()
    while fronteira:
        atual = fronteira.popleft()
        expandidos += 1
        if atual in recompensas:
            encontradas.add(atual)
        if atual == destino:
            return reconstruir_rota(pais, destino), expandidos, encontradas
        for proximo in vizinhos(mapa, atual):
            if proximo not in pais:
                pais[proximo] = atual
                fronteira.append(proximo)
    return None, expandidos, encontradas


def dfs(mapa, origem, destino, recompensas):
    if not navegavel(mapa, origem) or not navegavel(mapa, destino):
        return None, 0, set()
    fronteira = [origem]
    pais = {origem: None}
    expandidos = 0
    encontradas = set()
    while fronteira:
        atual = fronteira.pop()
        expandidos += 1
        if atual in recompensas:
            encontradas.add(atual)
        if atual == destino:
            return reconstruir_rota(pais, destino), expandidos, encontradas
        # A pilha inverte a ordem: inserir ao contrário visita a direita primeiro.
        for proximo in reversed(vizinhos(mapa, atual)):
            if proximo not in pais:
                pais[proximo] = atual
                fronteira.append(proximo)
    return None, expandidos, encontradas


def gulosa(mapa, origem, destino, recompensas):
    if not navegavel(mapa, origem) or not navegavel(mapa, destino):
        return None, 0, set()
    ordem = count()
    fronteira = [(manhattan(origem, destino), next(ordem), origem)]
    pais = {origem: None}
    expandidos = 0
    encontradas = set()
    while fronteira:
        _, _, atual = heappop(fronteira)
        expandidos += 1
        if atual in recompensas:
            encontradas.add(atual)
        if atual == destino:
            return reconstruir_rota(pais, destino), expandidos, encontradas
        for proximo in vizinhos(mapa, atual):
            if proximo not in pais:
                pais[proximo] = atual
                heappush(fronteira, (manhattan(proximo, destino), next(ordem), proximo))
    return None, expandidos, encontradas


def a_estrela(mapa, origem, destino, recompensas):
    if not navegavel(mapa, origem) or not navegavel(mapa, destino):
        return None, 0, set()
    ordem = count()
    fronteira = [(manhattan(origem, destino), next(ordem), 0, origem)]
    pais = {origem: None}
    custos = {origem: 0}
    expandidos = 0
    encontradas = set()
    while fronteira:
        _, _, custo, atual = heappop(fronteira)
        if custo != custos[atual]:
            continue  # Uma entrada antiga da fila não é processada nem contada.
        expandidos += 1
        if atual in recompensas:
            encontradas.add(atual)
        if atual == destino:
            return reconstruir_rota(pais, destino), expandidos, encontradas
        for proximo in vizinhos(mapa, atual):
            novo_custo = custo + custo_entrada(mapa, proximo)
            if novo_custo < custos.get(proximo, float("inf")):
                custos[proximo] = novo_custo
                pais[proximo] = atual
                prioridade = novo_custo + manhattan(proximo, destino)
                heappush(fronteira, (prioridade, next(ordem), novo_custo, proximo))
    return None, expandidos, encontradas


ALGORITMOS = {
    "1": ("BFS", bfs),
    "2": ("DFS", dfs),
    "3": ("Gulosa", gulosa),
    "4": ("A*", a_estrela),
}


def planejar_recompensas(mapa, direta, recompensas, busca, limite=LIMITE_DESVIO):
    """Escolhe voltas até recompensas, sempre retornando à rota direta."""
    previstas = set(direta) & recompensas
    candidatos = []
    expandidos = 0
    encontradas = set()
    destino = direta[-1]
    for recompensa in sorted(recompensas - previstas):
        melhor = None
        # Não há desvios após chegar ao destino, inclusive se origem == destino.
        for indice, ponto in enumerate(direta[:-1]):
            if 2 * manhattan(ponto, recompensa) > limite:
                continue  # Cada passo custa pelo menos 1, em ambas as direções.
            ida, nos, vistas = busca(mapa, ponto, recompensa, recompensas)
            expandidos += nos
            encontradas.update(vistas)
            if ida is None or destino in ida:
                continue
            volta, nos, vistas = busca(mapa, recompensa, ponto, recompensas)
            expandidos += nos
            encontradas.update(vistas)
            if volta is None or destino in volta:
                continue
            adicional = custo_rota(mapa, ida) + custo_rota(mapa, volta)
            if adicional <= limite and (melhor is None or adicional < melhor[0]):
                melhor = (adicional, recompensa, indice, ida + volta[1:])
        if melhor is not None:
            candidatos.append(melhor)

    desvios = {}
    # Decide primeiro pelas recompensas com menor custo adicional.
    for _, recompensa, indice, trecho in sorted(candidatos):
        if recompensa not in previstas:
            desvios.setdefault(indice, []).append(trecho)
            previstas.update(set(trecho) & recompensas)

    rota = []
    for indice, ponto in enumerate(direta):
        rota.append(ponto)
        for trecho in desvios.get(indice, []):
            rota.extend(trecho[1:])
    return rota, expandidos, encontradas


def executar_busca(mapa, origem, destino, recompensas, busca, com_desvios=True):
    """Mede a busca inteira, incluindo as buscas auxiliares do planejamento."""
    inicio = time.perf_counter()
    direta, expandidos, encontradas = busca(mapa, origem, destino, recompensas)
    rota = direta
    if direta is not None and com_desvios and busca in (gulosa, a_estrela):
        rota, adicionais, vistas = planejar_recompensas(mapa, direta, recompensas, busca)
        expandidos += adicionais
        encontradas.update(vistas)
    resultado = {
        "rota": rota,
        "rota_direta": direta,
        "expandidos": expandidos,
        "encontradas": encontradas,
        "coletadas": set(rota or []) & recompensas,
        "custo": custo_rota(mapa, rota) if rota is not None else None,
        "custo_direto": custo_rota(mapa, direta) if direta is not None else None,
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
        print(f"Custo direto: {resultado['custo_direto']} | Custo executado: {resultado['custo']} "
              f"| Movimentos: {resultado['movimentos']}")
        print(f"Recompensas coletadas na rota: {len(resultado['coletadas'])} "
              f"{sorted(resultado['coletadas'])}")
    else:
        print("Não existe caminho até o destino. Nenhuma rota foi executada.")


def comparar(mapa, origem, destino, recompensas):
    custo_direto_astar = None
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
        if busca is a_estrela and sucesso:
            custo_direto_astar = resultado["custo_direto"]
    print("BFS minimiza movimentos; BFS e DFS não garantem o menor custo.")
    print("Gulosa e A*: custos, movimentos e coletas incluem os desvios planejados.")
    print("Tempo e expansões incluem todas as buscas auxiliares, sem animação.")
    if custo_direto_astar is not None:
        print(f"A* sem desvios: custo mínimo {custo_direto_astar}.")


def main():
    mapa, origem, premio, recompensas = criar_cenario()
    print("Trabalho 1 — Algoritmos de Busca | Cenário: Vale do Prêmio")
    while True:
        mostrar_mapa(mapa, origem, premio, recompensas)
        mostrar_legenda()
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


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nEncerrado.")
