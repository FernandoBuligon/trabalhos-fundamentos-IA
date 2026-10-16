"""Verificações dos resultados preservados pela nova apresentação."""

import unittest
from unittest import mock

from main import (ALGORITMOS, PENALIDADE, a_estrela, criar_cenario, criar_heuristica,
                  executar_busca, manhattan, navegavel, sucessores)


class TestBuscas(unittest.TestCase):
    def setUp(self):
        self.mapa, self.origem, self.premio, self.recompensas = criar_cenario()

    def test_resultados_do_cenario_documentado(self):
        esperados = {"BFS": (241, 70, 5), "DFS": (73, 14, 1),
                     "Gulosa": (86, 58, 6), "A*": (47, 44, 5)}
        for nome, busca in ALGORITMOS.values():
            with self.subTest(algoritmo=nome):
                resultado = executar_busca(self.mapa, self.origem, self.premio,
                                           self.recompensas, busca)
                self.assertEqual((resultado["custo"], resultado["movimentos"],
                                  len(resultado["coletadas"])), esperados[nome])
                rota = resultado["rota"]
                self.assertEqual(rota[0], self.origem)
                self.assertEqual(rota[-1], self.premio)
                self.assertTrue(all(navegavel(self.mapa, ponto) for ponto in rota))
                self.assertTrue(all(manhattan(a, b) == 1 for a, b in zip(rota, rota[1:])))

    def test_a_estrela_coincide_com_custo_uniforme(self):
        """Com h = 0 a busca vira custo uniforme, que é ótima por definição."""
        sem_heuristica = lambda mapa, destino: lambda atual, restantes, final=False: 0
        destinos = [(x, y) for y, linha in enumerate(self.mapa)
                    for x in range(len(linha)) if navegavel(self.mapa, (x, y))]
        for destino in destinos:
            with self.subTest(destino=destino):
                a_estrela_ = executar_busca(self.mapa, self.origem, destino,
                                            self.recompensas, a_estrela)
                with mock.patch("main.criar_heuristica", sem_heuristica):
                    uniforme = executar_busca(self.mapa, self.origem, destino,
                                              self.recompensas, a_estrela)
                self.assertEqual(a_estrela_["rota"] is None, uniforme["rota"] is None)
                if uniforme["rota"] is not None:
                    self.assertEqual(a_estrela_["total"], uniforme["total"])

    def test_heuristica_nula_na_meta_e_consistente(self):
        """h(meta) = 0 e h(n) <= c(n, n') + h(n') em todas as transições alcançáveis."""
        h = criar_heuristica(self.mapa, self.premio)
        inicial = (self.origem, frozenset(self.recompensas), False)
        pendentes, vistos = [inicial], {inicial}
        while pendentes:
            estado = pendentes.pop()
            if estado[2]:
                self.assertEqual(h(*estado), 0)
                continue
            for proximo, custo in sucessores(self.mapa, self.premio, estado):
                self.assertLessEqual(h(*estado), custo + h(*proximo))
                if proximo not in vistos:
                    vistos.add(proximo)
                    pendentes.append(proximo)

    def test_metricas_de_memoria(self):
        for nome, busca in ALGORITMOS.values():
            with self.subTest(algoritmo=nome):
                resultado = executar_busca(self.mapa, self.origem, self.premio,
                                           self.recompensas, busca)
                self.assertGreater(resultado["pico_fronteira"], 0)
                self.assertGreaterEqual(resultado["armazenados"], resultado["expandidos"])
                self.assertGreaterEqual(resultado["armazenados"], resultado["pico_fronteira"]
                                        if nome != "DFS" else 1)
        a_estrela_ = executar_busca(self.mapa, self.origem, self.premio,
                                    self.recompensas, a_estrela)
        self.assertEqual(a_estrela_["total"], 67)

    def test_destino_inacessivel_nao_coleta_recompensas(self):
        for nome, busca in ALGORITMOS.values():
            with self.subTest(algoritmo=nome):
                resultado = executar_busca(self.mapa, self.origem, (8, 9),
                                           self.recompensas, busca)
                self.assertIsNone(resultado["rota"])
                self.assertIsNone(resultado["custo"])
                self.assertEqual(resultado["coletadas"], set())

    def test_destino_na_origem_tem_custo_zero(self):
        for nome, busca in ALGORITMOS.values():
            with self.subTest(algoritmo=nome):
                resultado = executar_busca(self.mapa, self.origem, self.origem,
                                           self.recompensas | {self.origem}, busca)
                self.assertEqual(resultado["rota"], [self.origem])
                self.assertEqual(resultado["custo"], 0)
                self.assertEqual(resultado["coletadas"], {self.origem})


if __name__ == "__main__":
    unittest.main()
