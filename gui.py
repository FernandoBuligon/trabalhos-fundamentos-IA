"""Janela Tkinter para explorar e comparar os percursos dos algoritmos."""

import tkinter as tk
from tkinter import font as tkfont, ttk

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


VERDE = "#15803d"
SUAVE = "#f5f7fb"
TRILHA = "#e9eef5"
RESUMOS = (("total", "Menor total"), ("tempo", "Mais rápido"),
           ("expandidos", "Menos expandidos"), ("armazenados", "Menos memória"))
CORES_ALGORITMOS = {"BFS": "#7c8fa9", "DFS": "#a07cc5", "Gulosa": "#e0913a", "A*": AZUL}
SALA_ISOLADA = ((7, 9), (9, 9))  # Primeira e última célula da sala sem entrada.


def interpretar_destino(mapa, x, y, premio):
    """Valida as coordenadas X e Y sem depender de widgets."""
    x, y = x.strip(), y.strip()
    if not x and not y:
        return premio
    try:
        destino = int(x), int(y)
    except ValueError:
        raise ValueError("Informe X (coluna) e Y (linha) como números inteiros.") from None
    if not navegavel(mapa, destino):
        raise ValueError("Escolha uma célula livre dentro do mapa.")
    return destino


def descrever_celula(mapa, ponto):
    x, y = ponto
    if not (0 <= y < len(mapa) and 0 <= x < len(mapa[y])):
        return "fora do mapa"
    nome = TERRENOS[mapa[y][x]][0]
    return f"{nome} · custo {CUSTOS[mapa[y][x]]}" if mapa[y][x] in CUSTOS else nome


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
        self.destino_x = tk.StringVar(janela, str(self.premio[0]))
        self.destino_y = tk.StringVar(janela, str(self.premio[1]))
        self.info_destino = tk.StringVar(janela, "")
        self.ultimo_texto_destino = self._texto_destino()
        self.velocidade = tk.DoubleVar(janela, 4)
        self.texto_velocidade = tk.StringVar(janela, "4 passos/s")
        self.mostrar_custos = tk.BooleanVar(janela, True)
        self.mostrar_planejada = tk.BooleanVar(janela, False)
        self.estado = tk.StringVar(janela, "Pronto")
        self.mensagem = tk.StringVar(janela, "Escolha um algoritmo e clique em Executar.")
        self.info_celula = tk.StringVar(janela, "Clique no mapa para escolher o destino.")
        self.metricas = {
            chave: tk.StringVar(janela, "—")
            for chave in ("custo", "passos", "coletas", "posicao", "tempo",
                          "expandidos", "pico_fronteira", "armazenados", "encontradas",
                          "custo_final", "total", "movimentos")
        }
        self._criar_widgets()
        self.info_destino.set(descrever_celula(self.mapa, self.destino))
        self.reiniciar()
        # O tamanho mínimo acompanha a fonte real do sistema: nada fica cortado.
        # Reserva uma linha extra para mensagens que quebram no rodapé.
        janela.update_idletasks()
        linha_extra = tkfont.Font(janela, font=(FONTE, 10)).metrics("linespace")
        janela.minsize(min(janela.winfo_reqwidth(), janela.winfo_screenwidth() - 60),
                       min(janela.winfo_reqheight() + linha_extra, janela.winfo_screenheight() - 80))
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
        estilo.configure("Titulo.TLabel", font=(FONTE, 18, "bold"))
        estilo.configure("Discreto.TLabel", foreground=DISCRETO)
        estilo.configure("Cartao.TFrame", background="white")
        estilo.configure("Cartao.TLabel", background="white")
        estilo.configure("Secao.TLabel", background="white", font=(FONTE, 11, "bold"))
        estilo.configure("Metrica.TLabel", background="white", font=(FONTE, 9))
        estilo.configure("Valor.TLabel", background="white", foreground=AZUL,
                         font=(FONTE, 20, "bold"))
        estilo.configure("TButton", padding=(10, 5), font=(FONTE, 10), width=-6)
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

        estilo.configure("Mini.TLabel", background="white", foreground=DISCRETO, font=(FONTE, 8))
        estilo.configure("MiniValor.TLabel", background="white", font=(FONTE, 11, "bold"))
        estilo.configure("Termo.TLabel", background="white", font=(FONTE, 9, "bold"))
        estilo.configure("Definicao.TLabel", background="white", foreground=DISCRETO, font=(FONTE, 9))
        estilo.configure("Resumo.TFrame", background=SUAVE)
        estilo.configure("ResumoTitulo.TLabel", background=SUAVE, foreground=DISCRETO, font=(FONTE, 8))
        estilo.configure("ResumoValor.TLabel", background=SUAVE, font=(FONTE, 13, "bold"))
        estilo.configure("ResumoDetalhe.TLabel", background=SUAVE, foreground=DISCRETO, font=(FONTE, 9))
        estilo.configure("Leitura.TFrame", background=SUAVE)
        estilo.configure("LeituraTermo.TLabel", background=SUAVE, font=(FONTE, 9, "bold"))
        estilo.configure("LeituraTexto.TLabel", background=SUAVE, foreground=DISCRETO, font=(FONTE, 9))
        estilo.configure("Comparacao.Treeview", rowheight=30, font=(FONTE, 10), borderwidth=0,
                         background="white", fieldbackground="white")
        estilo.configure("Comparacao.Treeview.Heading", font=(FONTE, 9, "bold"), padding=(6, 7),
                         background=SUAVE, foreground=DISCRETO, relief="flat", borderwidth=0)
        estilo.map("Comparacao.Treeview.Heading", background=[("active", "#e2e8f0")])

        base = ttk.Frame(janela, padding=(16, 12))
        base.pack(fill="both", expand=True)
        base.columnconfigure(0, weight=1)
        base.rowconfigure(2, weight=1)
        cabecalho = ttk.Frame(base)
        cabecalho.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        cabecalho.columnconfigure(0, weight=1)
        ttk.Label(cabecalho, text="Vale do Prêmio", style="Titulo.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(cabecalho, text="Algoritmos de busca · terrenos, caminhos e recompensas",
                  style="Discreto.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Label(cabecalho, textvariable=self.estado, foreground=AZUL,
                  font=(FONTE, 11, "bold")).grid(row=0, column=1, rowspan=2, sticky="e")

        controles = ttk.Frame(base, style="Cartao.TFrame", padding=10)
        controles.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        linha = ttk.Frame(controles, style="Cartao.TFrame")
        linha.pack(fill="x")
        ttk.Label(linha, text="Algoritmo", style="Cartao.TLabel").pack(side="left", padx=(0, 6))
        self.seletor = ttk.Combobox(linha, textvariable=self.algoritmo,
                                    values=list(self.algoritmos), state="readonly", width=8)
        self.seletor.pack(side="left", padx=(0, 18))
        self.seletor.bind("<<ComboboxSelected>>", lambda evento: self.reiniciar())
        ttk.Label(linha, text="Destino", style="Cartao.TLabel").pack(side="left", padx=(0, 6))
        self.campos_destino = []
        for rotulo, variavel in (("X", self.destino_x), ("Y", self.destino_y)):
            ttk.Label(linha, text=rotulo, style="Mini.TLabel").pack(side="left", padx=(4, 3))
            campo = ttk.Entry(linha, textvariable=variavel, width=4, justify="center")
            campo.pack(side="left")
            campo.bind("<KeyRelease>", self._destino_editado)
            campo.bind("<Return>", lambda evento: self.executar())
            self.campos_destino.append(campo)
        self.campo_destino = self.campos_destino[0]
        self.rotulo_info_destino = ttk.Label(linha, textvariable=self.info_destino,
                                             style="Mini.TLabel")
        self.rotulo_info_destino.pack(side="left", padx=(8, 8))
        ttk.Button(linha, text="Prêmio", command=self.usar_premio).pack(side="left")
        ttk.Button(linha, text="Comparar todos", command=self.comparar).pack(side="right")

        linha = ttk.Frame(controles, style="Cartao.TFrame")
        linha.pack(fill="x", pady=(8, 0))
        self.botao_executar = ttk.Button(linha, text="Executar", style="Principal.TButton",
                                        command=self.executar)
        self.botao_executar.pack(side="left", padx=(0, 6))
        self.botao_pausar = ttk.Button(linha, text="Pausar", command=self.pausar)
        self.botao_pausar.pack(side="left", padx=(0, 6))
        self.botao_passo = ttk.Button(linha, text="Passo", command=self.avancar_um_passo)
        self.botao_passo.pack(side="left", padx=(0, 6))
        ttk.Button(linha, text="Reiniciar", command=self.reiniciar).pack(side="left")
        ttk.Label(linha, textvariable=self.texto_velocidade,
                  style="Cartao.TLabel", width=9).pack(side="right")
        ttk.Scale(linha, from_=1, to=12, variable=self.velocidade,
                  command=self._velocidade_alterada, length=120).pack(side="right", padx=8)
        ttk.Label(linha, text="Velocidade", style="Cartao.TLabel").pack(side="right")

        self.abas = ttk.Notebook(base)
        self.abas.grid(row=2, column=0, sticky="nsew")
        self.aba_mapa = ttk.Frame(self.abas, padding=(0, 8, 0, 0))
        self.aba_mapa.columnconfigure(0, weight=1)
        self.aba_mapa.rowconfigure(0, weight=1)
        self.aba_comparacao = ttk.Frame(self.abas, style="Cartao.TFrame", padding=14)
        self.abas.add(self.aba_mapa, text="Mapa e animação")
        self.abas.add(self.aba_comparacao, text="Comparação")
        conteudo = ttk.Frame(self.aba_mapa)
        conteudo.grid(row=0, column=0, sticky="nsew")
        conteudo.columnconfigure(0, weight=1)
        conteudo.rowconfigure(0, weight=1)
        tabuleiro = ttk.Frame(conteudo, style="Cartao.TFrame", padding=10)
        tabuleiro.grid(row=0, column=0, sticky="nsew")
        tabuleiro.columnconfigure(0, weight=1)
        tabuleiro.rowconfigure(1, weight=1)
        opcoes = ttk.Frame(tabuleiro, style="Cartao.TFrame")
        opcoes.grid(row=0, column=0, sticky="ew")
        ttk.Label(opcoes, textvariable=self.info_celula, style="Cartao.TLabel",
                  foreground=DISCRETO, font=(FONTE, 9)).pack(side="left")
        ttk.Checkbutton(opcoes, text="Rota planejada", variable=self.mostrar_planejada,
                        command=self.desenhar_mapa).pack(side="right")
        ttk.Checkbutton(opcoes, text="Custos", variable=self.mostrar_custos,
                        command=self.desenhar_mapa).pack(side="right", padx=8)
        self.canvas = tk.Canvas(tabuleiro, background="white", highlightthickness=0,
                                width=300, height=200)
        self.canvas.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self.canvas.bind("<Configure>", self._pedir_redesenho)
        self.canvas.bind("<Button-1>", self._clicar_mapa)
        self.canvas.bind("<Motion>", self._inspecionar_celula)
        self.canvas.bind("<Leave>", lambda evento: self.info_celula.set(
            "Clique no mapa para escolher o destino."))
        legenda = ttk.Frame(tabuleiro, style="Cartao.TFrame")
        legenda.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        for terreno, (nome, cor) in TERRENOS.items():
            tk.Label(legenda, text="  ", background=cor).pack(side="left", padx=(0, 4))
            texto = f"{nome} ({CUSTOS[terreno]})" if terreno in CUSTOS else nome
            ttk.Label(legenda, text=texto, style="Definicao.TLabel").pack(side="left", padx=(0, 10))
        ttk.Label(tabuleiro, text="O origem · F prêmio · D destino · $ recompensa · @ agente",
                  style="Definicao.TLabel").grid(row=3, column=0, sticky="w", pady=(2, 0))

        painel = ttk.Frame(conteudo, style="Cartao.TFrame", padding=12)
        painel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        painel.columnconfigure(0, weight=1)
        ttk.Label(painel, text="Percurso executado", style="Secao.TLabel").grid(sticky="w")
        ttk.Label(painel, text="Custo acumulado", style="Mini.TLabel").grid(sticky="w", pady=(4, 0))
        ttk.Label(painel, textvariable=self.metricas["custo"], style="Valor.TLabel").grid(sticky="w")
        self._grade_metricas(painel, 3, (("Passos", "passos"), ("Coletadas", "coletas"),
                                         ("Posição", "posicao")))
        self.progresso = ttk.Progressbar(painel, maximum=1)
        self.progresso.grid(sticky="ew", pady=(8, 8))
        ttk.Separator(painel).grid(sticky="ew")
        ttk.Label(painel, text="Busca e planejamento", style="Secao.TLabel").grid(
            sticky="w", pady=(8, 0))
        self._grade_metricas(painel, 2, (
            ("Tempo", "tempo"), ("Expandidos", "expandidos"),
            ("Pico fronteira", "pico_fronteira"), ("Armazenados", "armazenados"),
            ("Encontradas", "encontradas"), ("Movimentos", "movimentos"),
            ("Terrenos", "custo_final"), ("Total", "total")))

        comparacao = self.aba_comparacao
        comparacao.columnconfigure(0, weight=1)
        comparacao.rowconfigure(3, weight=1)
        topo_comparacao = ttk.Frame(comparacao, style="Cartao.TFrame")
        topo_comparacao.grid(row=0, column=0, sticky="ew")
        titulo = ttk.Frame(topo_comparacao, style="Cartao.TFrame")
        titulo.pack(side="left")
        ttk.Label(titulo, text="Comparação dos algoritmos", style="Secao.TLabel").pack(anchor="w")
        self.subtitulo_comparacao = tk.StringVar(janela, "Ainda sem resultados.")
        ttk.Label(titulo, textvariable=self.subtitulo_comparacao, style="Definicao.TLabel").pack(anchor="w")
        ttk.Button(topo_comparacao, text="Voltar ao mapa",
                   command=lambda: self.abas.select(self.aba_mapa)).pack(side="right")
        ttk.Button(topo_comparacao, text="Ver rota selecionada", style="Principal.TButton",
                   command=lambda: self._abrir_comparacao(None)).pack(side="right", padx=(0, 8))

        resumo = ttk.Frame(comparacao, style="Cartao.TFrame")
        resumo.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        self.resumo = {}
        for coluna, (chave, titulo_cartao) in enumerate(RESUMOS):
            resumo.columnconfigure(coluna, weight=1, uniform="resumo")
            cartao = ttk.Frame(resumo, style="Resumo.TFrame", padding=(12, 6))
            cartao.grid(row=0, column=coluna, sticky="nsew", padx=(0 if coluna == 0 else 8, 0))
            ttk.Label(cartao, text=titulo_cartao.upper(), style="ResumoTitulo.TLabel").grid(
                row=0, column=0, columnspan=2, sticky="w")
            valor = ttk.Label(cartao, text="—", style="ResumoValor.TLabel")
            valor.grid(row=1, column=0, sticky="w")
            detalhe = ttk.Label(cartao, text="", style="ResumoDetalhe.TLabel")
            detalhe.grid(row=1, column=1, sticky="sw", padx=(8, 0), pady=(0, 3))
            self.resumo[chave] = (valor, detalhe)

        colunas = ("algoritmo", "tempo", "expandidos", "pico_fronteira", "armazenados", "custo",
                   "total", "movimentos", "coletadas", "estado")
        self.tabela = ttk.Treeview(comparacao, columns=colunas, show="headings", height=4,
                                   selectmode="browse", style="Comparacao.Treeview")
        titulos = ("Algoritmo", "Tempo (ms)", "Expandidos", "Pico fronteira", "Armazenados",
                   "Terrenos", "Total", "Movimentos", "Coletadas", "Resultado")
        for coluna, titulo_coluna in zip(colunas, titulos):
            alinhamento = "w" if coluna in {"algoritmo", "estado"} else "e"
            self.tabela.heading(coluna, text=titulo_coluna, anchor=alinhamento)
            self.tabela.column(coluna, width=90, minwidth=60, anchor=alinhamento)
        self.tabela.tag_configure("par", background="#fbfcfe")
        self.tabela.tag_configure("melhor", background="#e8f7ee", foreground="#14532d",
                                  font=(FONTE, 10, "bold"))
        self.tabela.tag_configure("falhou", foreground=DISCRETO)
        self.tabela.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        self.tabela.bind("<Double-1>", self._abrir_comparacao)
        self.tabela.bind("<Return>", self._abrir_comparacao)
        self.grafico = tk.Canvas(comparacao, background="white", highlightthickness=0, height=150)
        self.grafico.grid(row=3, column=0, sticky="nsew", pady=(12, 12))
        self.grafico.bind("<Configure>", lambda evento: self.desenhar_grafico())

        leitura = ttk.Frame(comparacao, style="Leitura.TFrame", padding=(12, 8))
        leitura.grid(row=4, column=0, sticky="ew")
        leitura.columnconfigure((1, 3), weight=1, uniform="definicoes")
        definicoes = (
            ("Pico fronteira", "maior fronteira simultânea"),
            ("Terrenos", "custo de entrada, com retornos"),
            ("Total", f"terrenos + {PENALIDADE} por recompensa não coletada (penalidade do projeto). "
                      "Só o A* garante o menor Total; BFS e DFS não o usam. Linha verde: menor Total."),
        )
        for indice, (termo, texto) in enumerate(definicoes):
            linha_def, coluna = divmod(indice, 2)
            ttk.Label(leitura, text=termo, style="LeituraTermo.TLabel").grid(
                row=linha_def, column=2 * coluna, sticky="nw", padx=(16 if coluna else 0, 8), pady=1)
            ultima = indice == len(definicoes) - 1
            ttk.Label(leitura, text=texto, style="LeituraTexto.TLabel",
                      wraplength=900 if ultima else 450).grid(
                row=linha_def, column=2 * coluna + 1, columnspan=3 if ultima else 1,
                sticky="nw", pady=1)
        rodape_janela = ttk.Frame(base)
        rodape_janela.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        rodape_janela.columnconfigure(0, weight=1)
        self.rotulo_mensagem = ttk.Label(rodape_janela, textvariable=self.mensagem)
        self.rotulo_mensagem.grid(row=0, column=0, sticky="ew")
        atalhos = ttk.Label(rodape_janela, text="Espaço executa/pausa · → passo · R reinicia",
                            style="Discreto.TLabel", font=(FONTE, 8))
        atalhos.grid(row=0, column=1, sticky="e", padx=(12, 0))
        rodape_janela.bind("<Configure>", lambda evento: self.rotulo_mensagem.configure(
            wraplength=max(250, evento.width - atalhos.winfo_reqwidth() - 20)))
        for tecla, acao in (("<space>", self._alternar_execucao), ("<Right>", self.avancar_um_passo),
                            ("<r>", self.reiniciar), ("<R>", self.reiniciar)):
            janela.bind(tecla, lambda evento, acao=acao: self._atalho(evento, acao))

    def _atalho(self, evento, acao):
        # Atalhos não competem com a digitação nos campos nem com os botões.
        if isinstance(evento.widget, (ttk.Entry, tk.Entry, ttk.Button)):
            return None
        acao()
        return "break"

    def _alternar_execucao(self):
        if self.tocando:
            self.pausar()
        else:
            self.executar()

    def _grade_metricas(self, painel, colunas, metricas):
        """Métricas pequenas (título acima do valor) em uma grade compacta."""
        grade = ttk.Frame(painel, style="Cartao.TFrame")
        grade.grid(sticky="ew")
        for coluna in range(colunas):
            grade.columnconfigure(coluna, weight=1, uniform="metricas")
        for indice, (titulo, chave) in enumerate(metricas):
            linha, coluna = divmod(indice, colunas)
            ttk.Label(grade, text=titulo, style="Mini.TLabel").grid(
                row=2 * linha, column=coluna, sticky="w", pady=(6, 0), padx=(0, 10))
            ttk.Label(grade, textvariable=self.metricas[chave], style="MiniValor.TLabel").grid(
                row=2 * linha + 1, column=coluna, sticky="w", padx=(0, 10))

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
        self.subtitulo_comparacao.set("Ainda sem resultados.")
        for valor, detalhe in self.resumo.values():
            valor.configure(text="—", foreground=TEXTO)
            detalhe.configure(text="")
        self.desenhar_grafico()

    def _atualizar_resumo(self):
        """Cartões com o melhor algoritmo em cada critério (empates listam todos)."""
        sucesso = {nome: r for nome, r in self.comparacao.items() if r["rota"] is not None}
        formatos = {"total": "total {}", "tempo": "{:.3f} ms",
                    "expandidos": "{} nós", "armazenados": "{} nós"}
        for chave, (valor, detalhe) in self.resumo.items():
            candidatos = sucesso if chave == "total" else self.comparacao
            if not candidatos:
                valor.configure(text="—", foreground=TEXTO)
                detalhe.configure(text="nenhum caminho")
                continue
            menor = min(r[chave] for r in candidatos.values())
            nomes = [nome for nome, r in candidatos.items() if r[chave] == menor]
            valor.configure(text=" / ".join(nomes), foreground=CORES_ALGORITMOS.get(nomes[0], AZUL))
            detalhe.configure(text=formatos[chave].format(menor * 1000 if chave == "tempo" else menor))

    def desenhar_grafico(self):
        """Um cartão por métrica com barras arredondadas; ★ marca o menor valor."""
        canvas = self.grafico
        canvas.delete("all")
        largura, altura = canvas.winfo_width(), canvas.winfo_height()
        if not self.comparacao:
            canvas.create_text(largura / 2, altura / 2, fill=DISCRETO, font=(FONTE, 10),
                               text="O gráfico aparece depois de Comparar todos.")
            return
        metricas = (("Tempo (ms)", "busca + percurso, sem animação", lambda r: r["tempo"] * 1000, "{:.2f}"),
                    ("Nós expandidos", "nós com sucessores gerados", lambda r: r["expandidos"], "{}"),
                    ("Nós armazenados", "estados distintos na memória", lambda r: r["armazenados"], "{}"),
                    ("Total", "terrenos + penalidades", lambda r: r["total"], "{}"))
        nomes = list(self.comparacao)
        fonte = tkfont.Font(canvas, font=(FONTE, 9))
        fonte_valor = tkfont.Font(canvas, font=(FONTE, 8, "bold"))
        rotulo = max(fonte.measure(nome) for nome in nomes) + 10
        reserva_valor = fonte_valor.measure("00000.00 ★") + 8
        intervalo, margem = 8, 12
        largura_cartao = (largura - intervalo * (len(metricas) - 1)) / len(metricas)
        fonte_nota = tkfont.Font(canvas, font=(FONTE, 8))
        topo = margem + fonte.metrics("linespace") + fonte_nota.metrics("linespace") + 8
        passo = (altura - topo - margem) / len(nomes)
        espessura = max(6, min(14, passo - 8))
        for indice, (titulo, nota, valor, formato) in enumerate(metricas):
            x0 = indice * (largura_cartao + intervalo)
            self._retangulo_arredondado(canvas, x0, 0, x0 + largura_cartao, altura, 10, SUAVE)
            canvas.create_text(x0 + margem, margem, text=titulo, anchor="nw", fill=TEXTO,
                               font=(FONTE, 9, "bold"))
            canvas.create_text(x0 + margem, margem + fonte.metrics("linespace"), text=nota,
                               anchor="nw", fill=DISCRETO, font=fonte_nota)
            valores = {nome: valor(r) for nome, r in self.comparacao.items()
                       if r["rota"] is not None or not titulo.startswith("Total")}
            maximo = max(valores.values(), default=0) or 1
            menor = min(valores.values(), default=None)
            inicio = x0 + margem + rotulo
            espaco = max(10, largura_cartao - margem * 2 - rotulo - reserva_valor)
            for linha, nome in enumerate(nomes):
                y = topo + (linha + .5) * passo
                canvas.create_text(x0 + margem, y, text=nome, anchor="w", fill=DISCRETO, font=fonte)
                canvas.create_line(inicio, y, inicio + espaco, y, fill=TRILHA, width=espessura,
                                   capstyle="round")
                if nome not in valores:
                    canvas.create_text(inicio + 4, y, text="sem caminho", anchor="w",
                                       fill=DISCRETO, font=(FONTE, 8))
                    continue
                fim_barra = inicio + max(1, espaco * valores[nome] / maximo)
                canvas.create_line(inicio, y, fim_barra, y, width=espessura, capstyle="round",
                                   fill=CORES_ALGORITMOS.get(nome, AZUL))
                texto = formato.format(valores[nome]) + (" ★" if valores[nome] == menor else "")
                canvas.create_text(inicio + espaco + 8, y, text=texto, anchor="w",
                                   fill=VERDE if valores[nome] == menor else TEXTO, font=fonte_valor)

    @staticmethod
    def _retangulo_arredondado(canvas, x0, y0, x1, y1, raio, cor):
        pontos = (x0 + raio, y0, x1 - raio, y0, x1, y0, x1, y0 + raio, x1, y1 - raio, x1, y1,
                  x1 - raio, y1, x0 + raio, y1, x0, y1, x0, y1 - raio, x0, y0 + raio, x0, y0)
        canvas.create_polygon(pontos, smooth=True, fill=cor, outline="")

    def _texto_destino(self):
        return self.destino_x.get(), self.destino_y.get()

    def definir_destino(self, ponto):
        """Preenche os campos X e Y e valida o novo destino."""
        self.destino_x.set(str(ponto[0]))
        self.destino_y.set(str(ponto[1]))
        self.reiniciar()
        return self._validar_destino()

    def _validar_destino(self):
        self.ultimo_texto_destino = self._texto_destino()
        try:
            destino = interpretar_destino(self.mapa, *self._texto_destino(), self.premio)
        except ValueError as erro:
            self.info_destino.set("inválido")
            self.rotulo_info_destino.configure(foreground="#b42318")
            self._avisar("Destino inválido", str(erro), erro=True)
            return False
        self.info_destino.set(descrever_celula(self.mapa, destino))
        self.rotulo_info_destino.configure(foreground=DISCRETO)
        if destino != self.destino:
            self.destino = destino
            self.reiniciar()
            self._limpar_comparacao()
        self.desenhar_mapa()
        return True

    def _destino_editado(self, evento):
        if evento.keysym == "Return":
            return
        self._destino_alterado()

    def _destino_alterado(self):
        if self._texto_destino() == self.ultimo_texto_destino:
            return
        self.reiniciar()
        self._limpar_comparacao()
        self._validar_destino()

    def usar_premio(self):
        self.definir_destino(self.premio)

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
            tags = ("falhou",) if not sucesso else ("par",) if len(self.comparacao) % 2 == 0 else ()
            self.tabela.insert("", "end", iid=nome, tags=tags, values=(
                nome, f"{resultado['tempo'] * 1000:.3f}", resultado["expandidos"],
                resultado["pico_fronteira"], resultado["armazenados"],
                resultado["custo"] if sucesso else "—",
                resultado["total"] if sucesso else "—",
                resultado["movimentos"] if sucesso else "—",
                len(resultado["coletadas"]), "Sucesso" if sucesso else "Sem caminho"))
        totais = {nome: r["total"] for nome, r in self.comparacao.items() if r["rota"] is not None}
        if totais:
            menor = min(totais.values())
            for nome, total in totais.items():
                if total == menor:
                    self.tabela.item(nome, tags=("melhor",))
        self.subtitulo_comparacao.set(f"Origem {self.origem} → destino {self.destino} · "
                                      "duplo clique carrega a rota")
        self._atualizar_resumo()
        self.desenhar_grafico()
        self._avisar("Comparação pronta", f"Resultados até {self.destino}. "
                     "Duplo clique em uma linha para carregar a rota.")
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
            self._avisar("Selecione um resultado", "Clique em Comparar todos e selecione uma linha da tabela.")

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
        (x_ini, y_sala), (x_fim, _) = SALA_ISOLADA
        sala_x0, sala_y0 = esquerda + (x_ini - 1) * tamanho, topo + (y_sala - 1) * tamanho
        sala_x1, sala_y1 = esquerda + (x_fim + 2) * tamanho, topo + (y_sala + 2) * tamanho
        canvas.create_rectangle(sala_x0 + 2, sala_y0 + 2, sala_x1 - 2, sala_y1 - 2,
                                outline="#f8c75a", width=2, dash=(5, 3))
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
        self.definir_destino(ponto)
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
