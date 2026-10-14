"""Testes de integração dos controles com widgets Tk reais."""

from types import SimpleNamespace
import unittest

try:
    import tkinter as tk
    from gui import InterfaceBusca, interpretar_destino
except ImportError as erro:
    if erro.name not in {"tkinter", "_tkinter"}:
        raise
    tk = None

from main import criar_cenario


@unittest.skipIf(tk is None, "Tkinter não está instalado")
class TestDestino(unittest.TestCase):
    def test_formatos_validos(self):
        mapa, _, premio, _ = criar_cenario()
        for entrada in ("", "  ", "15 1", "15, 1"):
            with self.subTest(entrada=entrada):
                self.assertEqual(interpretar_destino(mapa, entrada, premio), premio)

    def test_coordenadas_invalidas(self):
        mapa, _, premio, _ = criar_cenario()
        for entrada in ("a b", "15", "1 1 1", "1.5 1", "0 0", "-1 1", "17 1", "1 11"):
            with self.subTest(entrada=entrada):
                with self.assertRaises(ValueError):
                    interpretar_destino(mapa, entrada, premio)


@unittest.skipIf(tk is None, "Tkinter não está instalado")
class TestInterface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            janela = tk.Tk()
        except tk.TclError as erro:
            raise unittest.SkipTest(f"Sessão gráfica indisponível: {erro}") from erro
        janela.withdraw()
        janela.destroy()

    def setUp(self):
        self.janela = tk.Tk()
        self.janela.withdraw()
        self.erros_callbacks = []
        self.janela.report_callback_exception = lambda *erro: self.erros_callbacks.append(erro)
        self.app = InterfaceBusca(self.janela)
        self.janela.update_idletasks()

    def tearDown(self):
        self.app.fechar()
        self.assertEqual(self.erros_callbacks, [])

    def test_passos_reproduzem_custo_e_coletas_de_todos_algoritmos(self):
        for nome in self.app.algoritmos:
            with self.subTest(algoritmo=nome):
                self.app.algoritmo.set(nome)
                self.app.reiniciar()
                self.app.avancar_um_passo()
                while not self.app._concluido():
                    self.app.avancar_um_passo()
                self.assertEqual(self.app.custo, self.app.resultado["custo"])
                self.assertEqual(self.app.coletadas, self.app.resultado["coletadas"])
                self.assertEqual(self.app.passo, self.app.resultado["movimentos"])
                self.assertEqual(self.app.estado.get(), "Concluído")
                self.assertIsNone(self.app.agendamento)
                self.assertTrue(self.app.botao_passo.instate(["disabled"]))

    def test_pausa_continuacao_e_reinicio_cancelam_callbacks(self):
        self.app.executar()
        primeiro_callback = self.app.agendamento
        self.assertIsNotNone(primeiro_callback)
        self.app.pausar()
        self.assertFalse(self.app.tocando)
        self.assertIsNone(self.app.agendamento)
        self.assertNotIn(primeiro_callback, self.janela.tk.call("after", "info"))
        self.app.avancar_um_passo()
        self.app.executar()
        self.assertEqual(self.app.passo, 1)
        self.assertTrue(self.app.tocando)
        segundo_callback = self.app.agendamento
        self.app.reiniciar()
        self.assertIsNone(self.app.resultado)
        self.assertEqual((self.app.passo, self.app.custo), (0, 0))
        self.assertEqual(self.app.coletadas, set())
        self.assertNotIn(segundo_callback, self.janela.tk.call("after", "info"))

    def test_animacao_automatica_avanca_sem_bloquear_eventos(self):
        self.app.velocidade.set(12)
        self.app.executar()
        self.janela.after(210, self.janela.quit)
        self.janela.mainloop()
        self.app.pausar()
        self.assertGreaterEqual(self.app.passo, 1)
        self.assertEqual(self.app.posicao, self.app.resultado["rota"][self.app.passo])

    def test_destino_na_origem_conclui_sem_agendar_movimento(self):
        self.app.entrada_destino.set("1 1")
        self.app.executar()
        self.assertEqual(self.app.estado.get(), "Concluído")
        self.assertEqual(self.app.custo, 0)
        self.assertEqual(self.app.passo, 0)
        self.assertIsNone(self.app.agendamento)

    def test_recompensa_na_origem_e_coletada_sem_cobrar_entrada(self):
        self.app.recompensas.add(self.app.origem)
        self.app.entrada_destino.set("1 1")
        self.app.executar()
        self.assertEqual(self.app.coletadas, {self.app.origem})
        self.assertEqual(self.app.custo, 0)

    def test_destino_inacessivel_e_entrada_invalida(self):
        self.app.entrada_destino.set("8 9")
        self.app.executar()
        self.assertEqual(self.app.estado.get(), "Sem caminho")
        self.assertEqual(self.app.coletadas, set())
        self.assertIsNone(self.app.agendamento)
        self.app.entrada_destino.set("0 0")
        self.app.executar()
        self.assertEqual(self.app.estado.get(), "Destino inválido")
        self.assertEqual(self.app.custo, 0)

    def test_comparacao_carrega_resultado_sem_coletar_antes_da_animacao(self):
        self.app.comparar()
        self.assertEqual(len(self.app.tabela.get_children()), 4)
        self.app.tabela.selection_set("BFS")
        self.app._abrir_comparacao(None)
        self.assertEqual(self.app.algoritmo.get(), "BFS")
        self.assertEqual(self.app.estado.get(), "Pausado")
        self.assertEqual(self.app.custo, 0)
        self.assertEqual(self.app.coletadas, set())
        self.assertEqual(self.app.resultado["custo"], 241)

    def test_mudar_destino_descarta_rota_e_comparacao_anteriores(self):
        self.app.executar()
        self.app.comparar()
        self.app.entrada_destino.set("8 1")
        self.app._destino_editado(SimpleNamespace(keysym="1"))
        self.assertEqual(self.app.destino, (8, 1))
        self.assertIsNone(self.app.resultado)
        self.assertIsNone(self.app.agendamento)
        self.assertEqual(self.app.comparacao, {})
        self.assertEqual(self.app.tabela.get_children(), ())

    def test_colar_destino_antes_de_comparar_reinicia_percurso_antigo(self):
        self.app.avancar_um_passo()
        self.app.entrada_destino.set("8 1")
        self.app.comparar()
        self.assertEqual(self.app.destino, (8, 1))
        self.assertIsNone(self.app.resultado)
        self.assertEqual(self.app.posicao, self.app.origem)
        self.assertEqual(self.app.custo, 0)

    def test_teclas_de_navegacao_no_campo_nao_reiniciam_animacao(self):
        self.app.avancar_um_passo()
        self.app._destino_editado(SimpleNamespace(keysym="Left"))
        self.assertEqual(self.app.passo, 1)
        self.assertIsNotNone(self.app.resultado)

    def test_comparacao_de_destino_inacessivel(self):
        self.app.entrada_destino.set("8 9")
        self.app.comparar()
        for nome, resultado in self.app.comparacao.items():
            with self.subTest(algoritmo=nome):
                self.assertIsNone(resultado["rota"])
                self.assertEqual(resultado["coletadas"], set())
                self.assertEqual(self.app.tabela.item(nome, "values")[-1], "Sem caminho")

    def test_janela_compacta_mantem_mapa_legivel_e_metricas_visiveis(self):
        self.janela.deiconify()
        self.janela.geometry("940x700")
        self.janela.update()
        self.assertGreaterEqual(self.app.geometria_mapa[2], 22)
        painel = self.app.progresso.master
        limite_inferior = painel.winfo_rooty() + painel.winfo_height()
        limite_direito = painel.winfo_rootx() + painel.winfo_width()
        for widget in painel.winfo_children():
            with self.subTest(widget=str(widget)):
                self.assertTrue(widget.winfo_ismapped())
                self.assertLessEqual(widget.winfo_rooty() + widget.winfo_height(), limite_inferior)
                self.assertLessEqual(widget.winfo_rootx() + widget.winfo_width(), limite_direito)

    def test_clique_no_mapa_funciona_apos_redimensionamento(self):
        self.janela.deiconify()
        self.janela.geometry("1000x760")
        self.janela.update()
        self.app.desenhar_mapa()
        x, y = self.app._centro((8, 1))
        self.app.canvas.event_generate("<Button-1>", x=round(x), y=round(y))
        self.assertEqual(self.app.destino, (8, 1))
        self.janela.geometry("1100x820")
        self.janela.update()
        self.app.desenhar_mapa()
        x, y = self.app._centro((3, 3))
        self.app.canvas.event_generate("<Button-1>", x=round(x), y=round(y))
        self.assertEqual(self.app.destino, (3, 3))
        x, y = self.app._centro((0, 0))
        self.app.canvas.event_generate("<Button-1>", x=round(x), y=round(y))
        self.assertEqual(self.app.destino, (3, 3))


if __name__ == "__main__":
    unittest.main()
