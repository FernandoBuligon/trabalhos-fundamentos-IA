"""Janela Tkinter para explorar e comparar os percursos dos algoritmos."""

import tkinter as tk
from tkinter import ttk

from main import ALGORITMOS, CUSTOS, PENALIDADE, criar_cenario, executar_busca, navegavel


FUNDO = "#f2f5fa"
TEXTO = "#24334a"
DISCRETO = "#64748b"
AZUL = "#2563eb"
FONTE = "Helvetica"
TERRENOS = {
    ".": ("Plano", "#e8f2e9"),
    "s": ("Areia", "#f2d596"),
    "r": ("Rocha", "#a9b6c7"),
    "p": ("Pântano", "#9bc9bd"),
    "#": ("Parede", "#334155"),
}


def interpretar_destino(mapa, entrada, premio):
    """Valida coordenadas sem depender de widgets ou da entrada do terminal."""
    if not entrada.strip():
        return premio
    partes = entrada.replace(",", " ").split()
    try:
        if len(partes) != 2:
            raise ValueError
        destino = tuple(int(parte) for parte in partes)
    except ValueError:
        raise ValueError("Informe coluna e linha, por exemplo: 15 1.") from None
    if not navegavel(mapa, destino):
        raise ValueError("Escolha uma célula livre dentro do mapa.")
    return destino


class InterfaceBusca:
    def __init__(self, janela):
        self.janela = janela
        self.mapa, self.origem, self.premio, self.recompensas = criar_cenario()
        self.algoritmos = dict(ALGORITMOS.values())
        self.destino = self.premio
        self.resultado = None
        self.comparacao = {}
        self.passo = 0
        self.custo = 0
        self.coletadas = set()
        self.posicao = self.origem
        self.tocando = False
        self.agendamento = None
        self.redesenho = None
        self.geometria_mapa = None
        self.algoritmo = tk.StringVar(janela, "A*")
        self.entrada_destino = tk.StringVar(janela, "15 1")
        self.ultimo_texto_destino = self.entrada_destino.get()
        self.velocidade = tk.DoubleVar(janela, 4)
        self.texto_velocidade = tk.StringVar(janela, "4 passos/s")
        self.mostrar_custos = tk.BooleanVar(janela, True)
        self.mostrar_planejada = tk.BooleanVar(janela, False)
        self.estado = tk.StringVar(janela, "Pronto")
        self.mensagem = tk.StringVar(janela, "Escolha um algoritmo e clique em Executar.")
        self.info_celula = tk.StringVar(janela, "Clique em uma célula livre para escolher o destino.")
        self.metricas = {
            chave: tk.StringVar(janela, "—")
            for chave in ("custo", "passos", "coletas", "posicao", "tempo",
                          "expandidos", "pico_fronteira", "armazenados", "encontradas",
                          "custo_final", "total", "movimentos")
        }
        self._criar_widgets()
        self.reiniciar()
        janela.protocol("WM_DELETE_WINDOW", self.fechar)

    def _criar_widgets(self):
        janela = self.janela
        janela.title("Vale do Prêmio — Algoritmos de Busca")
        largura = min(1180, janela.winfo_screenwidth() - 60)
        altura = min(880, janela.winfo_screenheight() - 80)
        janela.geometry(f"{largura}x{altura}")
        janela.minsize(min(940, largura), min(700, altura))
        janela.configure(background=FUNDO)
        estilo = ttk.Style(janela)
        estilo.theme_use("clam")
        estilo.configure("TFrame", background=FUNDO)
        estilo.configure("TLabel", background=FUNDO, foreground=TEXTO, font=(FONTE, 10))
        estilo.configure("Titulo.TLabel", font=(FONTE, 20, "bold"))
        estilo.configure("Discreto.TLabel", foreground=DISCRETO)
        estilo.configure("Cartao.TFrame", background="white")
        estilo.configure("Cartao.TLabel", background="white")
        estilo.configure("Secao.TLabel", background="white", font=(FONTE, 11, "bold"))
        estilo.configure("Metrica.TLabel", background="white", font=(FONTE, 9))
        estilo.configure("Valor.TLabel", background="white", foreground=AZUL,
                         font=(FONTE, 20, "bold"))
        estilo.configure("TButton", padding=(12, 7), font=(FONTE, 10))
        estilo.configure("Principal.TButton", background=AZUL, foreground="white")
        estilo.map("Principal.TButton", background=[("active", "#1d4ed8"),
                                                    ("disabled", "#cbd5e1")])
        estilo.configure("TCheckbutton", background="white", font=(FONTE, 9))
        estilo.configure("Treeview", rowheight=29, font=(FONTE, 10))
        estilo.configure("Treeview.Heading", font=(FONTE, 10, "bold"), padding=(5, 6))
        estilo.map("Treeview", background=[("selected", "#dbeafe")],
                   foreground=[("selected", "#1e40af")])
        estilo.configure("TNotebook", background=FUNDO, borderwidth=0)
        estilo.configure("TNotebook.Tab", font=(FONTE, 10), padding=(16, 7))
        estilo.map("TNotebook.Tab", background=[("selected", "white")],
                   foreground=[("selected", AZUL)])
        estilo.configure("Horizontal.TProgressbar", background=AZUL,
                         troughcolor="#edf2fa", bordercolor="#edf2fa")

        base = ttk.Frame(janela, padding=20)
        base.pack(fill="both", expand=True)
        base.columnconfigure(0, weight=1)
        base.rowconfigure(2, weight=1)
        cabecalho = ttk.Frame(base)
        cabecalho.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        cabecalho.columnconfigure(0, weight=1)
        ttk.Label(cabecalho, text="Vale do Prêmio", style="Titulo.TLabel").grid(sticky="w")
        ttk.Label(cabecalho, text="Algoritmos de busca · terrenos, caminhos e recompensas",
                  style="Discreto.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Label(cabecalho, textvariable=self.estado, foreground=AZUL,
                  font=(FONTE, 11, "bold")).grid(row=0, column=1, rowspan=2)

        controles = ttk.Frame(base, style="Cartao.TFrame", padding=12)
        controles.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        linha = ttk.Frame(controles, style="Cartao.TFrame")
        linha.pack(fill="x")
        ttk.Label(linha, text="Algoritmo", style="Cartao.TLabel").pack(side="left", padx=(0, 8))
        self.seletor = ttk.Combobox(linha, textvariable=self.algoritmo,
                                    values=list(self.algoritmos), state="readonly", width=9)
        self.seletor.pack(side="left", padx=(0, 18))
        self.seletor.bind("<<ComboboxSelected>>", lambda evento: self.reiniciar())
        ttk.Label(linha, text="Destino (x y)", style="Cartao.TLabel").pack(side="left", padx=(0, 8))
        self.campo_destino = ttk.Entry(linha, textvariable=self.entrada_destino, width=9)
        self.campo_destino.pack(side="left", padx=(0, 8))
        self.campo_destino.bind("<KeyRelease>", self._destino_editado)
        self.campo_destino.bind("<Return>", lambda evento: self.executar())
        ttk.Button(linha, text="Usar prêmio", command=self.usar_premio).pack(side="left")
        ttk.Button(linha, text="Comparar os quatro", command=self.comparar).pack(side="right")

        linha = ttk.Frame(controles, style="Cartao.TFrame")
        linha.pack(fill="x", pady=(10, 0))
        self.botao_executar = ttk.Button(linha, text="Executar", style="Principal.TButton",
                                        command=self.executar)
        self.botao_executar.pack(side="left", padx=(0, 6))
        self.botao_pausar = ttk.Button(linha, text="Pausar", command=self.pausar)
        self.botao_pausar.pack(side="left", padx=(0, 6))
        self.botao_passo = ttk.Button(linha, text="Passo", command=self.avancar_um_passo)
        self.botao_passo.pack(side="left", padx=(0, 6))
        ttk.Button(linha, text="Reiniciar", command=self.reiniciar).pack(side="left")
        ttk.Label(linha, textvariable=self.texto_velocidade,
                  style="Cartao.TLabel", width=12).pack(side="right")
        ttk.Scale(linha, from_=1, to=12, variable=self.velocidade,
                  command=self._velocidade_alterada, length=140).pack(side="right", padx=10)
        ttk.Label(linha, text="Velocidade", style="Cartao.TLabel").pack(side="right")

        self.abas = ttk.Notebook(base)
        self.abas.grid(row=2, column=0, sticky="nsew")
        self.aba_mapa = ttk.Frame(self.abas, padding=(0, 12, 0, 0))
        self.aba_mapa.columnconfigure(0, weight=1)
        self.aba_mapa.rowconfigure(0, weight=1)
        self.aba_comparacao = ttk.Frame(self.abas, style="Cartao.TFrame", padding=16)
        self.abas.add(self.aba_mapa, text="Mapa e animação")
        self.abas.add(self.aba_comparacao, text="Comparação")
        conteudo = ttk.Frame(self.aba_mapa)
        conteudo.grid(row=0, column=0, sticky="nsew")
        conteudo.columnconfigure(0, weight=1)
        conteudo.rowconfigure(0, weight=1)
        tabuleiro = ttk.Frame(conteudo, style="Cartao.TFrame", padding=12)
        tabuleiro.grid(row=0, column=0, sticky="nsew")
        tabuleiro.columnconfigure(0, weight=1)
        tabuleiro.rowconfigure(1, weight=1)
        opcoes = ttk.Frame(tabuleiro, style="Cartao.TFrame")
        opcoes.grid(row=0, column=0, sticky="ew")
        ttk.Label(opcoes, text="Mapa do cenário", style="Secao.TLabel").pack(side="left")
        ttk.Checkbutton(opcoes, text="Rota planejada", variable=self.mostrar_planejada,
                        command=self.desenhar_mapa).pack(side="right")
        ttk.Checkbutton(opcoes, text="Custos", variable=self.mostrar_custos,
                        command=self.desenhar_mapa).pack(side="right", padx=8)
        self.canvas = tk.Canvas(tabuleiro, background="white", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        self.canvas.bind("<Configure>", self._pedir_redesenho)
        self.canvas.bind("<Button-1>", self._clicar_mapa)
        self.canvas.bind("<Motion>", self._inspecionar_celula)
        self.canvas.bind("<Leave>", lambda evento: self.info_celula.set(
            "Clique em uma célula livre para escolher o destino."))
        ttk.Label(tabuleiro, textvariable=self.info_celula, style="Cartao.TLabel",
                  foreground=DISCRETO, font=(FONTE, 9)).grid(row=2, column=0, sticky="w")

        painel = ttk.Frame(conteudo, style="Cartao.TFrame", padding=12)
        painel.grid(row=0, column=1, sticky="nsew", padx=(14, 0))
        painel.columnconfigure(1, weight=1)
        ttk.Label(painel, text="Percurso executado", style="Secao.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        ttk.Label(painel, text="Custo acumulado", style="Cartao.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w")
        ttk.Label(painel, textvariable=self.metricas["custo"], style="Valor.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="w")
        for linha, (titulo, chave) in enumerate(
                (("Passos", "passos"), ("Coletadas", "coletas"), ("Posição", "posicao")), 3):
            self._metrica(painel, linha, titulo, chave)
        self.progresso = ttk.Progressbar(painel, maximum=1)
        self.progresso.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8, 8))
        ttk.Separator(painel).grid(row=7, column=0, columnspan=2, sticky="ew")
        ttk.Label(painel, text="Busca e planejamento", style="Secao.TLabel").grid(
            row=8, column=0, columnspan=2, sticky="w", pady=(8, 4))
        for linha, (titulo, chave) in enumerate(
                (("Tempo", "tempo"), ("Nós expandidos", "expandidos"),
                 ("Pico da fronteira", "pico_fronteira"), ("Nós armazenados", "armazenados"),
                 ("Encontradas na busca", "encontradas"), ("Custo dos terrenos", "custo_final"),
                 ("Total com penalidades", "total"), ("Movimentos totais", "movimentos")), 9):
            self._metrica(painel, linha, titulo, chave)

        legenda = ttk.Frame(self.aba_mapa)
        legenda.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        for terreno, (nome, cor) in TERRENOS.items():
            tk.Label(legenda, text="  ", background=cor).pack(side="left", padx=(0, 4))
            texto = f"{nome} ({CUSTOS[terreno]})" if terreno in CUSTOS else nome
            ttk.Label(legenda, text=texto, font=(FONTE, 9)).pack(side="left", padx=(0, 12))
        ttk.Label(legenda, text="@ agente · $ recompensa · F prêmio · D destino",
                  font=(FONTE, 9)).pack(side="right")

        comparacao = self.aba_comparacao
        ttk.Label(comparacao, text="Comparação dos algoritmos", style="Secao.TLabel").pack(anchor="w")
        colunas = ("algoritmo", "tempo", "expandidos", "pico_fronteira", "armazenados", "custo",
                   "total", "movimentos", "coletadas", "estado")
        self.tabela = ttk.Treeview(comparacao, columns=colunas, show="headings", height=4,
                                   selectmode="browse")
        titulos = ("Algoritmo", "Tempo (ms)", "Expandidos", "Pico fronteira", "Armazenados",
                   "Terrenos", "Total", "Movimentos", "Coletadas", "Resultado")
        for coluna, titulo in zip(colunas, titulos):
            self.tabela.heading(coluna, text=titulo)
            self.tabela.column(coluna, width=95, minwidth=70,
                               anchor="w" if coluna in {"algoritmo", "estado"} else "e")
        self.tabela.pack(fill="x", pady=(6, 4))
        self.tabela.bind("<Double-1>", self._abrir_comparacao)
        self.tabela.bind("<Return>", self._abrir_comparacao)
        ttk.Label(comparacao, text="Clique em Comparar os quatro. Duplo clique em um resultado carrega sua rota.",
                  style="Cartao.TLabel", foreground=DISCRETO, font=(FONTE, 9)).pack(anchor="w")
        acoes = ttk.Frame(comparacao, style="Cartao.TFrame")
        acoes.pack(fill="x", pady=16)
        ttk.Button(acoes, text="Ver rota selecionada", style="Principal.TButton",
                   command=lambda: self._abrir_comparacao(None)).pack(side="left", padx=(0, 8))
        ttk.Button(acoes, text="Voltar ao mapa",
                   command=lambda: self.abas.select(self.aba_mapa)).pack(side="left")
        ttk.Label(comparacao, style="Cartao.TLabel", foreground=DISCRETO, justify="left",
                  text="O tempo mede apenas a busca e a construção do percurso.\n"
                       "Terrenos: entradas em terrenos, incluindo retornos para coletar recompensas.\n"
                       f"Total: terrenos + {PENALIDADE} por recompensa não coletada (penalidade definida pelo projeto).\n"
                       "Só o A* garante o menor Total; a Gulosa tenta reduzi-lo sem garantia; BFS e DFS não o utilizam.\n"
                       "Expandidos: nós cujos sucessores foram gerados. Pico fronteira: maior fronteira simultânea.\n"
                       "Armazenados: estados distintos mantidos na memória (Gulosa/A* incluem as recompensas restantes).").pack(anchor="w")
        self.rotulo_mensagem = ttk.Label(base, textvariable=self.mensagem, wraplength=1000)
        self.rotulo_mensagem.grid(row=3, column=0, sticky="ew", pady=(10, 0))

    def _metrica(self, painel, linha, titulo, chave):
        ttk.Label(painel, text=titulo, style="Metrica.TLabel", foreground=DISCRETO).grid(
            row=linha, column=0, sticky="w", padx=(0, 14), pady=2)
        ttk.Label(painel, textvariable=self.metricas[chave], style="Metrica.TLabel").grid(
            row=linha, column=1, sticky="e", pady=2)

    def _avisar(self, estado, mensagem, erro=False):
        self.estado.set(estado)
        self.mensagem.set(mensagem)
        self.rotulo_mensagem.configure(foreground="#b42318" if erro else TEXTO)

    def _cancelar_agendamento(self):
        if self.agendamento is not None:
            self.janela.after_cancel(self.agendamento)
            self.agendamento = None

    def reiniciar(self):
        self._cancelar_agendamento()
        self.tocando = False
        self.resultado = None
        self.passo = self.custo = 0
        self.coletadas = set()
        self.posicao = self.origem
        for variavel in self.metricas.values():
            variavel.set("—")
        self.progresso.configure(maximum=1, value=0)
        self.abas.select(self.aba_mapa)
        self._avisar("Pronto", "Escolha um algoritmo e clique em Executar. Cada execução reinicia as recompensas.")
        self._atualizar_percurso()
        self._atualizar_botoes()
        self.desenhar_mapa()

    def _limpar_comparacao(self):
        self.comparacao = {}
        self.tabela.delete(*self.tabela.get_children())

    def _validar_destino(self):
        self.ultimo_texto_destino = self.entrada_destino.get()
        try:
            destino = interpretar_destino(self.mapa, self.entrada_destino.get(), self.premio)
        except ValueError as erro:
            self._avisar("Destino inválido", str(erro), erro=True)
            return False
        if destino != self.destino:
            self.destino = destino
            self.reiniciar()
            self._limpar_comparacao()
        self.desenhar_mapa()
        return True

    def _destino_editado(self, evento):
        if evento.keysym == "Return" or self.entrada_destino.get() == self.ultimo_texto_destino:
            return
        self.reiniciar()
        self._limpar_comparacao()
        self._validar_destino()

    def usar_premio(self):
        self.entrada_destino.set(f"{self.premio[0]} {self.premio[1]}")
        self.reiniciar()
        self._validar_destino()

    def _preparar(self, resultado=None):
        self.reiniciar()
        if not self._validar_destino():
            return False
        if resultado is None:
            resultado = executar_busca(self.mapa, self.origem, self.destino,
                                       self.recompensas, self.algoritmos[self.algoritmo.get()])
        self.resultado = resultado
        self.metricas["tempo"].set(f"{resultado['tempo'] * 1000:.3f} ms")
        for chave in ("expandidos", "pico_fronteira", "armazenados"):
            self.metricas[chave].set(str(resultado[chave]))
        self.metricas["encontradas"].set(str(len(resultado["encontradas"])))
        if resultado["rota"] is None:
            self._avisar("Sem caminho", f"{self.algoritmo.get()}: não existe caminho até {self.destino}. "
                         "Nenhuma recompensa foi coletada.", erro=True)
            self._atualizar_botoes()
            return False
        self.metricas["custo_final"].set(str(resultado["custo"]))
        self.metricas["total"].set(str(resultado["total"]))
        self.metricas["movimentos"].set(str(resultado["movimentos"]))
        self.posicao = resultado["rota"][0]
        self.coletadas = {self.posicao} & self.recompensas
        self._atualizar_percurso()
        self._avisar("Pausado", f"{self.algoritmo.get()}: rota calculada até {self.destino}. "
                     "Use Continuar ou Passo para acompanhar o percurso.")
        if self._concluido():
            self._finalizar()
        self._atualizar_botoes()
        self.desenhar_mapa()
        return True

    def _concluido(self):
        return (self.resultado is not None and self.resultado["rota"] is not None
                and self.passo == len(self.resultado["rota"]) - 1)

    def executar(self):
        if self.tocando:
            return
        # Também valida o texto alterado por colagem ou por recursos de acessibilidade.
        if not self._validar_destino():
            return
        if (self.resultado is None or self.resultado["rota"] is None or self._concluido()
                or self.resultado["rota"][-1] != self.destino):
            if not self._preparar():
                return
        if self._concluido():
            return
        self.abas.select(self.aba_mapa)
        self.tocando = True
        self._avisar("Em execução", f"{self.algoritmo.get()}: seguindo a rota até {self.destino}.")
        self._atualizar_botoes()
        self._agendar_passo()

    def _agendar_passo(self):
        self.agendamento = self.janela.after(
            max(1, round(1000 / self.velocidade.get())), self._passo_agendado)

    def _passo_agendado(self):
        self.agendamento = None
        if self.tocando:
            self._avancar()
            if self.tocando:
                self._agendar_passo()

    def pausar(self):
        self._cancelar_agendamento()
        self.tocando = False
        if self.resultado is not None and self.resultado["rota"] and not self._concluido():
            self._avisar("Pausado", "Animação pausada. Use Continuar ou Passo para seguir.")
        self._atualizar_botoes()

    def avancar_um_passo(self):
        if self.tocando:
            return
        if not self._validar_destino():
            return
        if (self.resultado is None or self.resultado["rota"] is None
                or self.resultado["rota"][-1] != self.destino):
            if not self._preparar():
                return
        if not self._concluido():
            self.abas.select(self.aba_mapa)
            self._avancar()

    def _avancar(self):
        self.passo += 1
        self.posicao = self.resultado["rota"][self.passo]
        x, y = self.posicao
        self.custo += CUSTOS[self.mapa[y][x]]
        if self.posicao in self.recompensas and self.posicao not in self.coletadas:
            self.coletadas.add(self.posicao)
            self._avisar("Em execução" if self.tocando else "Pausado",
                         f"Recompensa coletada em {self.posicao}. Total: {len(self.coletadas)}.")
        self._atualizar_percurso()
        self.desenhar_mapa()
        if self._concluido():
            self._finalizar()
        self._atualizar_botoes()

    def _finalizar(self):
        self._cancelar_agendamento()
        self.tocando = False
        self._avisar("Concluído", f"{self.algoritmo.get()}: objetivo alcançado em {self.posicao}. "
                     f"Custo {self.custo} · {self.passo} movimentos · {len(self.coletadas)} recompensas coletadas.")

    def _atualizar_percurso(self):
        total = self.resultado["movimentos"] if self.resultado and self.resultado["rota"] else 0
        self.metricas["custo"].set(str(self.custo))
        self.metricas["passos"].set(f"{self.passo} / {total}")
        self.metricas["coletas"].set(f"{len(self.coletadas)} / {len(self.recompensas)}")
        self.metricas["posicao"].set(str(self.posicao))
        self.progresso.configure(maximum=max(1, total), value=(1 if self._concluido() and total == 0 else self.passo))

    def _atualizar_botoes(self):
        pausado = (self.resultado is not None and self.resultado["rota"] is not None
                   and not self._concluido())
        self.botao_executar.configure(text="Continuar" if pausado and not self.tocando else "Executar",
                                      state="disabled" if self.tocando else "normal")
        self.botao_pausar.configure(state="normal" if self.tocando else "disabled")
        self.botao_passo.configure(state="disabled" if self.tocando or self._concluido() else "normal")

    def _velocidade_alterada(self, valor):
        self.texto_velocidade.set(f"{float(valor):.0f} passos/s")
        if self.tocando:
            self._cancelar_agendamento()
            self._agendar_passo()

    def comparar(self):
        self.pausar()
        if not self._validar_destino():
            return
        self._limpar_comparacao()
        for nome, busca in self.algoritmos.items():
            resultado = executar_busca(self.mapa, self.origem, self.destino, self.recompensas, busca)
            self.comparacao[nome] = resultado
            sucesso = resultado["rota"] is not None
            self.tabela.insert("", "end", iid=nome, values=(
                nome, f"{resultado['tempo'] * 1000:.3f}", resultado["expandidos"],
                resultado["pico_fronteira"], resultado["armazenados"],
                resultado["custo"] if sucesso else "—",
                resultado["total"] if sucesso else "—",
                resultado["movimentos"] if sucesso else "—",
                len(resultado["coletadas"]), "Sucesso" if sucesso else "Sem caminho"))
        self._avisar("Comparação pronta", f"Resultados até {self.destino}. Tempo mede a busca e o planejamento, "
                     "sem animação. Duplo clique em uma linha para carregar a rota.")
        self.abas.select(self.aba_comparacao)

    def _abrir_comparacao(self, evento):
        if not self._validar_destino():
            return
        selecao = self.tabela.selection()
        if selecao:
            nome = selecao[0]
            self.algoritmo.set(nome)
            self._preparar(self.comparacao[nome])
        else:
            self._avisar("Selecione um resultado", "Clique em Comparar os quatro e selecione uma linha da tabela.")

    def _pedir_redesenho(self, evento):
        if self.redesenho is None:
            self.redesenho = self.janela.after_idle(self._redesenhar)

    def _redesenhar(self):
        self.redesenho = None
        self.desenhar_mapa()

    def desenhar_mapa(self):
        canvas = self.canvas
        largura, altura = canvas.winfo_width(), canvas.winfo_height()
        colunas, linhas = len(self.mapa[0]), len(self.mapa)
        tamanho = min((largura - 42) / colunas, (altura - 36) / linhas)
        if tamanho <= 0:
            self.geometria_mapa = None
            return
        esquerda = (largura - colunas * tamanho) / 2 + 10
        topo = (altura - linhas * tamanho) / 2 + 10
        self.geometria_mapa = (esquerda, topo, tamanho)
        canvas.delete("all")
        fonte = (FONTE, max(7, min(11, int(tamanho / 3))))
        for x in range(colunas):
            canvas.create_text(esquerda + (x + .5) * tamanho, topo - 13, text=x, fill=DISCRETO, font=fonte)
        for y, linha in enumerate(self.mapa):
            canvas.create_text(esquerda - 15, topo + (y + .5) * tamanho, text=y, fill=DISCRETO, font=fonte)
            for x, terreno in enumerate(linha):
                x0, y0 = esquerda + x * tamanho, topo + y * tamanho
                canvas.create_rectangle(x0 + 1, y0 + 1, x0 + tamanho - 1, y0 + tamanho - 1,
                                        fill=TERRENOS[terreno][1], outline="")
                if self.mostrar_custos.get() and terreno in CUSTOS:
                    canvas.create_text(x0 + tamanho * .8, y0 + tamanho * .2,
                                       text=CUSTOS[terreno], fill="#3d5360", font=(FONTE, max(6, fonte[1] - 2)))
        if self.resultado and self.resultado["rota"]:
            rota = self.resultado["rota"]
            if self.mostrar_planejada.get():
                self._desenhar_rota(rota, "#7c8fa9", 2, (4, 4))
            self._desenhar_rota(rota[:self.passo + 1], AZUL, 3)
        for ponto, letra, cor in ((self.origem, "O", DISCRETO), (self.premio, "F", "#b7791f"),
                                  (self.destino, "D" if self.destino != self.premio else "F", "#d44d36")):
            cx, cy = self._centro(ponto)
            raio = tamanho * .34
            canvas.create_rectangle(cx - raio, cy - raio, cx + raio, cy + raio, outline=cor, width=2)
            canvas.create_text(cx, cy, text=letra, fill=cor, font=(FONTE, fonte[1], "bold"))
        for ponto in self.recompensas - self.coletadas:
            cx, cy = self._centro(ponto)
            raio = tamanho * .27
            canvas.create_polygon(cx, cy - raio, cx + raio, cy, cx, cy + raio, cx - raio, cy,
                                  fill="#f8c75a", outline="#9c6b10", width=1)
            canvas.create_text(cx, cy, text="$", fill="#654611", font=(FONTE, fonte[1], "bold"))
        cx, cy = self._centro(self.posicao)
        raio = tamanho * .3
        canvas.create_oval(cx - raio, cy - raio, cx + raio, cy + raio, fill=AZUL, outline="white", width=2)
        canvas.create_text(cx, cy, text="@", fill="white", font=(FONTE, fonte[1], "bold"))

    def _centro(self, ponto):
        esquerda, topo, tamanho = self.geometria_mapa
        x, y = ponto
        return esquerda + (x + .5) * tamanho, topo + (y + .5) * tamanho

    def _desenhar_rota(self, rota, cor, espessura, tracejado=()):
        if len(rota) > 1:
            coordenadas = [valor for ponto in rota for valor in self._centro(ponto)]
            self.canvas.create_line(*coordenadas, fill=cor, width=espessura,
                                    dash=tracejado, capstyle="round", joinstyle="round")

    def _ponto_do_evento(self, evento):
        if self.geometria_mapa is None:
            return None
        esquerda, topo, tamanho = self.geometria_mapa
        x = int((evento.x - esquerda) // tamanho)
        y = int((evento.y - topo) // tamanho)
        if 0 <= y < len(self.mapa) and 0 <= x < len(self.mapa[y]):
            return x, y
        return None

    def _clicar_mapa(self, evento):
        ponto = self._ponto_do_evento(evento)
        if ponto is None:
            return
        if not navegavel(self.mapa, ponto):
            self._avisar(self.estado.get(), "Uma parede não pode ser o destino.", erro=True)
            return
        self.entrada_destino.set(f"{ponto[0]} {ponto[1]}")
        self.reiniciar()
        self._validar_destino()
        self._avisar("Pronto", f"Destino selecionado: {ponto}. Clique em Executar ou Passo.")

    def _inspecionar_celula(self, evento):
        ponto = self._ponto_do_evento(evento)
        if ponto is not None:
            x, y = ponto
            terreno = self.mapa[y][x]
            descricao = f"{ponto} · {TERRENOS[terreno][0]}"
            if terreno in CUSTOS:
                descricao += f" · custo de entrada {CUSTOS[terreno]}"
            if ponto in self.recompensas:
                descricao += " · recompensa coletada" if ponto in self.coletadas else " · recompensa disponível"
            self.info_celula.set(descricao)

    def fechar(self):
        self._cancelar_agendamento()
        if self.redesenho is not None:
            self.janela.after_cancel(self.redesenho)
        self.janela.destroy()


def iniciar_interface():
    janela = tk.Tk()
    InterfaceBusca(janela)
    janela.mainloop()
