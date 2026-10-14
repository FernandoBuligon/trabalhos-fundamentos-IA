"""Verificações dos resultados preservados pela nova apresentação."""

import unittest

from main import ALGORITMOS, criar_cenario, executar_busca, manhattan, navegavel


class TestBuscas(unittest.TestCase):
    def setUp(self):
        self.mapa, self.origem, self.premio, self.recompensas = criar_cenario()

    def test_resultados_do_cenario_documentado(self):
        esperados = {"BFS": (241, 70, 5), "DFS": (73, 14, 1),
                     "Gulosa": (29, 26, 2), "A*": (25, 22, 1)}
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
