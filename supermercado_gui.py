import tkinter as tk
from tkinter import messagebox, scrolledtext
import tkinter.ttk as ttk # Certifique-se de que esta linha está presente
import json
import os
from datetime import datetime

# --- Configurações de Arquivo ---
PRODUTOS_FILE = 'produtos.json'
VENDAS_FILE = 'vendas.json'

# --- Funções de Persistência de Dados ---
def carregar_dados(filepath):
    """Carrega dados de um arquivo JSON."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            messagebox.showwarning("Erro de Carregamento", f"O arquivo {filepath} está corrompido. Criando um novo.")
            return []
    return []

def salvar_dados(data, filepath):
    """Salva dados em um arquivo JSON."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Carrega os dados ao iniciar o programa
produtos = carregar_dados(PRODUTOS_FILE)
vendas = carregar_dados(VENDAS_FILE)

# --- Funções de Negócio ---

def adicionar_ou_atualizar_produto(codigo, nome, preco_str, estoque_str):
    """Adiciona um novo produto ou atualiza um existente."""
    if not codigo or not nome or not preco_str or not estoque_str:
        messagebox.showerror("Erro de Entrada", "Todos os campos do produto são obrigatórios.")
        return False

    try:
        preco = float(preco_str.replace(',', '.')) # Aceita vírgula ou ponto
        estoque = int(estoque_str)
        if preco <= 0 or estoque < 0:
            messagebox.showerror("Erro de Entrada", "Preço deve ser positivo e Estoque não pode ser negativo.")
            return False
    except ValueError:
        messagebox.showerror("Erro de Entrada", "Preço e Estoque devem ser números válidos.")
        return False

    # Verifica se o produto já existe para atualização
    for i, produto in enumerate(produtos):
        if produto['codigo'].upper() == codigo.upper():
            produtos[i] = {'codigo': codigo.upper(), 'nome': nome.title(), 'preco': preco, 'estoque': estoque}
            salvar_dados(produtos, PRODUTOS_FILE)
            messagebox.showinfo("Sucesso", f"Produto '{nome}' atualizado com sucesso!")
            return True

    # Se não existe, adiciona como novo
    novo_produto = {'codigo': codigo.upper(), 'nome': nome.title(), 'preco': preco, 'estoque': estoque}
    produtos.append(novo_produto)
    salvar_dados(produtos, PRODUTOS_FILE)
    messagebox.showinfo("Sucesso", f"Produto '{nome}' cadastrado com sucesso!")
    return True

def buscar_produto_por_codigo(codigo):
    """Retorna um produto pelo código."""
    for produto in produtos:
        if produto['codigo'].upper() == codigo.upper():
            return produto
    return None

def realizar_venda_logica(carrinho_itens):
    """Processa a lógica da venda e atualiza o estoque."""
    total_venda = 0.0
    venda_detalhes = {
        'data_hora': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'itens': [],
        'total': 0.0
    }

    for item in carrinho_itens:
        produto = buscar_produto_por_codigo(item['codigo'])
        if produto: # Garante que o produto ainda existe
            if produto['estoque'] >= item['quantidade']:
                produto['estoque'] -= item['quantidade']
                subtotal = produto['preco'] * item['quantidade']
                total_venda += subtotal
                venda_detalhes['itens'].append({
                    'codigo': item['codigo'],
                    'nome': produto['nome'],
                    'quantidade': item['quantidade'],
                    'preco_unitario': produto['preco'],
                    'subtotal': subtotal
                })
            else:
                messagebox.showwarning("Estoque Insuficiente", f"Estoque insuficiente para {produto['nome']}. Disponível: {produto['estoque']}")
                return False, 0.0 # Retorna falso se não foi possível concluir a venda

    if total_venda > 0:
        venda_detalhes['total'] = total_venda
        vendas.append(venda_detalhes)
        salvar_dados(produtos, PRODUTOS_FILE) # Salva o estoque atualizado
        salvar_dados(vendas, VENDAS_FILE)     # Salva o registro da venda
        return True, total_venda
    return False, 0.0

def excluir_produto_logica(codigo):
    """Remove um produto do estoque."""
    global produtos
    produtos_originais = len(produtos)
    produtos = [p for p in produtos if p['codigo'].upper() != codigo.upper()]
    if len(produtos) < produtos_originais:
        salvar_dados(produtos, PRODUTOS_FILE)
        return True
    return False

# --- Interface Gráfica Tkinter ---

class SupermercadoApp:
    def __init__(self, master):
        self.master = master
        master.title("Sistema de Supermercado")
        master.geometry("1000x700") # Tamanho inicial da janela
        master.configure(bg="#f0f0f0") # Cor de fundo

        # --- Frames Principais ---
        self.main_frame = tk.Frame(master, bg="#f0f0f0")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configura as colunas do main_frame para serem responsivas
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.create_widgets()
        self.carrinho_itens = []
        self.atualizar_lista_produtos_gui() # Carrega produtos na lista ao iniciar

    def create_widgets(self):
        # --- Frame Esquerdo: Cadastro/Venda/Consulta ---
        self.left_frame = tk.Frame(self.main_frame, bg="#e0e0e0", bd=2, relief="groove")
        self.left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # --- Abas (Notebook) para organização ---
        self.notebook = tk.ttk.Notebook(self.left_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Cadastro/Atualização de Produtos
        self.tab_cadastro = tk.Frame(self.notebook, bg="#e0e0e0")
        self.notebook.add(self.tab_cadastro, text="Produtos")
        self.setup_cadastro_tab(self.tab_cadastro)

        # Tab 2: Venda
        self.tab_venda = tk.Frame(self.notebook, bg="#e0e0e0")
        self.notebook.add(self.tab_venda, text="Venda")
        self.setup_venda_tab(self.tab_venda)

        # Tab 3: Relatórios
        self.tab_relatorios = tk.Frame(self.notebook, bg="#e0e0e0")
        self.notebook.add(self.tab_relatorios, text="Relatórios")
        self.setup_relatorios_tab(self.tab_relatorios)

        # --- Frame Direito: Lista de Produtos e Detalhes ---
        self.right_frame = tk.Frame(self.main_frame, bg="#d0d0d0", bd=2, relief="groove")
        self.right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        tk.Label(self.right_frame, text="Produtos Cadastrados", font=("Arial", 14, "bold"), bg="#d0d0d0").pack(pady=10)

        self.lista_produtos_scroll = scrolledtext.ScrolledText(self.right_frame, wrap=tk.WORD, width=50, height=25, font=("Arial", 10))
        self.lista_produtos_scroll.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.lista_produtos_scroll.config(state=tk.DISABLED) # Torna o campo somente leitura

        # Botão para atualizar a lista de produtos
        tk.Button(self.right_frame, text="Atualizar Lista", command=self.atualizar_lista_produtos_gui, font=("Arial", 10)).pack(pady=5)


    def setup_cadastro_tab(self, parent_frame):
        # Campos de entrada para cadastro/atualização
        form_frame = tk.Frame(parent_frame, bg="#e0e0e0")
        form_frame.pack(pady=20, padx=20)

        tk.Label(form_frame, text="Código:", bg="#e0e0e0").grid(row=0, column=0, pady=5, sticky="w")
        self.entry_codigo = tk.Entry(form_frame, width=30)
        self.entry_codigo.grid(row=0, column=1, pady=5, padx=5)

        tk.Label(form_frame, text="Nome:", bg="#e0e0e0").grid(row=1, column=0, pady=5, sticky="w")
        self.entry_nome = tk.Entry(form_frame, width=30)
        self.entry_nome.grid(row=1, column=1, pady=5, padx=5)

        tk.Label(form_frame, text="Preço:", bg="#e0e0e0").grid(row=2, column=0, pady=5, sticky="w")
        self.entry_preco = tk.Entry(form_frame, width=30)
        self.entry_preco.grid(row=2, column=1, pady=5, padx=5)

        tk.Label(form_frame, text="Estoque:", bg="#e0e0e0").grid(row=3, column=0, pady=5, sticky="w")
        self.entry_estoque = tk.Entry(form_frame, width=30)
        self.entry_estoque.grid(row=3, column=1, pady=5, padx=5)

        # Botões de ação
        button_frame = tk.Frame(parent_frame, bg="#e0e0e0")
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Cadastrar/Atualizar Produto", command=self.acao_adicionar_ou_atualizar, font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Excluir Produto (pelo Código)", command=self.acao_excluir_produto, font=("Arial", 10)).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Limpar Campos", command=self.limpar_campos_cadastro, font=("Arial", 10)).grid(row=0, column=2, padx=5)

        # Campo para busca rápida no cadastro
        tk.Label(parent_frame, text="Buscar Produto (pelo Código para preencher):", bg="#e0e0e0").pack(pady=5)
        self.entry_buscar_cadastro = tk.Entry(parent_frame, width=40)
        self.entry_buscar_cadastro.pack(pady=5)
        tk.Button(parent_frame, text="Buscar", command=self.acao_buscar_para_preencher, font=("Arial", 10)).pack(pady=5)


    def setup_venda_tab(self, parent_frame):
        # Entrada do código do produto para venda
        venda_input_frame = tk.Frame(parent_frame, bg="#e0e0e0")
        venda_input_frame.pack(pady=10)

        tk.Label(venda_input_frame, text="Código do Produto:", bg="#e0e0e0").grid(row=0, column=0, pady=5, sticky="w")
        self.entry_venda_codigo = tk.Entry(venda_input_frame, width=20)
        self.entry_venda_codigo.grid(row=0, column=1, pady=5, padx=5)
        self.entry_venda_codigo.bind("<Return>", lambda event: self.acao_adicionar_ao_carrinho()) # Adiciona ao carrinho ao pressionar Enter

        tk.Label(venda_input_frame, text="Quantidade:", bg="#e0e0e0").grid(row=1, column=0, pady=5, sticky="w")
        self.entry_venda_quantidade = tk.Entry(venda_input_frame, width=10)
        self.entry_venda_quantidade.grid(row=1, column=1, pady=5, padx=5)
        self.entry_venda_quantidade.insert(0, "1") # Quantidade padrão 1
        self.entry_venda_quantidade.bind("<Return>", lambda event: self.acao_adicionar_ao_carrinho()) # Adiciona ao carrinho ao pressionar Enter


        tk.Button(venda_input_frame, text="Adicionar ao Carrinho", command=self.acao_adicionar_ao_carrinho, font=("Arial", 10, "bold")).grid(row=2, column=0, columnspan=2, pady=10)

        # Lista do carrinho
        tk.Label(parent_frame, text="Carrinho de Compras", font=("Arial", 12, "bold"), bg="#e0e0e0").pack(pady=5)
        self.lista_carrinho = scrolledtext.ScrolledText(parent_frame, wrap=tk.WORD, width=40, height=10, font=("Arial", 10))
        self.lista_carrinho.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.lista_carrinho.config(state=tk.DISABLED)

        # Total da venda
        self.label_total_venda = tk.Label(parent_frame, text="Total: R$ 0.00", font=("Arial", 14, "bold"), bg="#e0e0e0", fg="blue")
        self.label_total_venda.pack(pady=10)

        # Botões de finalização da venda
        venda_buttons_frame = tk.Frame(parent_frame, bg="#e0e0e0")
        venda_buttons_frame.pack(pady=10)
        tk.Button(venda_buttons_frame, text="Finalizar Venda", command=self.acao_finalizar_venda, font=("Arial", 12, "bold"), bg="green", fg="white").grid(row=0, column=0, padx=10)
        tk.Button(venda_buttons_frame, text="Limpar Carrinho", command=self.limpar_carrinho_gui, font=("Arial", 10)).grid(row=0, column=1, padx=10)


    def setup_relatorios_tab(self, parent_frame):
        # Relatório de Estoque Baixo
        estoque_frame = tk.Frame(parent_frame, bg="#e0e0e0")
        estoque_frame.pack(pady=10, padx=10, fill=tk.X)
        tk.Label(estoque_frame, text="Relatório de Estoque Baixo", font=("Arial", 12, "bold"), bg="#e0e0e0").pack(pady=5)
        tk.Label(estoque_frame, text="Limite de Estoque:", bg="#e0e0e0").pack(side=tk.LEFT, padx=5)
        self.entry_limite_estoque = tk.Entry(estoque_frame, width=10)
        self.entry_limite_estoque.pack(side=tk.LEFT, padx=5)
        self.entry_limite_estoque.insert(0, "5")
        tk.Button(estoque_frame, text="Gerar", command=self.acao_relatorio_estoque_baixo, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

        self.text_relatorio_estoque = scrolledtext.ScrolledText(parent_frame, wrap=tk.WORD, width=60, height=10, font=("Arial", 10))
        self.text_relatorio_estoque.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.text_relatorio_estoque.config(state=tk.DISABLED)

        tk.Frame(parent_frame, height=1, bg="gray").pack(fill=tk.X, pady=10) # Separador

        # Relatório de Vendas do Dia
        vendas_frame = tk.Frame(parent_frame, bg="#e0e0e0")
        vendas_frame.pack(pady=10, padx=10, fill=tk.X)
        tk.Label(vendas_frame, text="Relatório de Vendas (Todas)", font=("Arial", 12, "bold"), bg="#e0e0e0").pack(pady=5)
        tk.Button(vendas_frame, text="Gerar Relatório de Vendas", command=self.acao_relatorio_vendas, font=("Arial", 10)).pack(pady=5)

        self.text_relatorio_vendas = scrolledtext.ScrolledText(parent_frame, wrap=tk.WORD, width=60, height=10, font=("Arial", 10))
        self.text_relatorio_vendas.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.text_relatorio_vendas.config(state=tk.DISABLED)

    # --- Métodos de Ação da GUI ---

    def limpar_campos_cadastro(self):
        """Limpa os campos de entrada do formulário de cadastro."""
        self.entry_codigo.delete(0, tk.END)
        self.entry_nome.delete(0, tk.END)
        self.entry_preco.delete(0, tk.END)
        self.entry_estoque.delete(0, tk.END)
        self.entry_buscar_cadastro.delete(0, tk.END)

    def acao_adicionar_ou_atualizar(self):
        """Chama a função de negócio para adicionar/atualizar e atualiza a GUI."""
        codigo = self.entry_codigo.get().strip()
        nome = self.entry_nome.get().strip()
        preco_str = self.entry_preco.get().strip()
        estoque_str = self.entry_estoque.get().strip()

        if adicionar_ou_atualizar_produto(codigo, nome, preco_str, estoque_str):
            self.limpar_campos_cadastro()
            self.atualizar_lista_produtos_gui()

    def acao_excluir_produto(self):
        """Chama a função de negócio para excluir e atualiza a GUI."""
        codigo = self.entry_codigo.get().strip()
        if not codigo:
            messagebox.showerror("Erro", "Digite o Código do produto que deseja excluir.")
            return

        if messagebox.askyesno("Confirmação", f"Tem certeza que deseja excluir o produto com código '{codigo}'?"):
            if excluir_produto_logica(codigo):
                messagebox.showinfo("Sucesso", f"Produto com código '{codigo}' excluído com sucesso!")
                self.limpar_campos_cadastro()
                self.atualizar_lista_produtos_gui()
            else:
                messagebox.showerror("Erro", f"Produto com código '{codigo}' não encontrado.")

    def acao_buscar_para_preencher(self):
        """Busca um produto e preenche os campos de cadastro para edição."""
        codigo_busca = self.entry_buscar_cadastro.get().strip()
        if not codigo_busca:
            messagebox.showwarning("Aviso", "Digite o código do produto para buscar.")
            return

        produto_encontrado = buscar_produto_por_codigo(codigo_busca)
        if produto_encontrado:
            self.entry_codigo.delete(0, tk.END)
            self.entry_codigo.insert(0, produto_encontrado['codigo'])
            self.entry_nome.delete(0, tk.END)
            self.entry_nome.insert(0, produto_encontrado['nome'])
            self.entry_preco.delete(0, tk.END)
            self.entry_preco.insert(0, str(produto_encontrado['preco']))
            self.entry_estoque.delete(0, tk.END)
            self.entry_estoque.insert(0, str(produto_encontrado['estoque']))
            messagebox.showinfo("Produto Encontrado", f"Dados do produto '{produto_encontrado['nome']}' carregados para edição.")
        else:
            messagebox.showerror("Não Encontrado", f"Produto com código '{codigo_busca}' não encontrado.")
            self.limpar_campos_cadastro()


    def atualizar_lista_produtos_gui(self):
        """Atualiza o widget ScrolledText com a lista atual de produtos."""
        self.lista_produtos_scroll.config(state=tk.NORMAL)
        self.lista_produtos_scroll.delete('1.0', tk.END)
        if not produtos:
            self.lista_produtos_scroll.insert(tk.END, "Nenhum produto cadastrado.")
        else:
            for produto in produtos:
                self.lista_produtos_scroll.insert(tk.END, f"Código: {produto['codigo']}\n")
                self.lista_produtos_scroll.insert(tk.END, f"Nome: {produto['nome']}\n")
                self.lista_produtos_scroll.insert(tk.END, f"Preço: R$ {produto['preco']:.2f}\n")
                self.lista_produtos_scroll.insert(tk.END, f"Estoque: {produto['estoque']}\n")
                self.lista_produtos_scroll.insert(tk.END, "-" * 30 + "\n")
        self.lista_produtos_scroll.config(state=tk.DISABLED)

    def acao_adicionar_ao_carrinho(self):
        """Adiciona um item ao carrinho de vendas."""
        codigo = self.entry_venda_codigo.get().strip().upper()
        quantidade_str = self.entry_venda_quantidade.get().strip()

        if not codigo or not quantidade_str:
            messagebox.showerror("Erro de Entrada", "Preencha o código e a quantidade.")
            return

        try:
            quantidade = int(quantidade_str)
            if quantidade <= 0:
                messagebox.showerror("Erro de Entrada", "Quantidade deve ser um número positivo.")
                return
        except ValueError:
            messagebox.showerror("Erro de Entrada", "Quantidade inválida. Digite um número inteiro.")
            return

        produto = buscar_produto_por_codigo(codigo)
        if not produto:
            messagebox.showerror("Produto Não Encontrado", f"Produto com código '{codigo}' não encontrado.")
            return
        
        if produto['estoque'] < quantidade:
            messagebox.showwarning("Estoque Insuficiente", f"Estoque insuficiente para '{produto['nome']}'. Disponível: {produto['estoque']}")
            return

        # Verifica se o item já está no carrinho para somar a quantidade
        item_no_carrinho = False
        for item in self.carrinho_itens:
            if item['codigo'] == codigo:
                item['quantidade'] += quantidade
                item_no_carrinho = True
                break
        
        if not item_no_carrinho:
            self.carrinho_itens.append({'codigo': codigo, 'quantidade': quantidade, 'nome': produto['nome'], 'preco_unitario': produto['preco']})
        
        self.atualizar_carrinho_gui()
        self.entry_venda_codigo.delete(0, tk.END)
        self.entry_venda_quantidade.delete(0, tk.END)
        self.entry_venda_quantidade.insert(0, "1") # Reseta para 1 após adicionar

    def atualizar_carrinho_gui(self):
        """Atualiza a lista do carrinho e o total na GUI."""
        self.lista_carrinho.config(state=tk.NORMAL)
        self.lista_carrinho.delete('1.0', tk.END)
        total_atual = 0.0

        if not self.carrinho_itens:
            self.lista_carrinho.insert(tk.END, "Carrinho vazio.")
        else:
            for item in self.carrinho_itens:
                subtotal = item['quantidade'] * item['preco_unitario']
                total_atual += subtotal
                self.lista_carrinho.insert(tk.END, f"{item['nome']} ({item['quantidade']}x) - R$ {subtotal:.2f}\n")
            self.lista_carrinho.insert(tk.END, "-" * 30 + "\n")
            self.lista_carrinho.insert(tk.END, f"Total do Carrinho: R$ {total_atual:.2f}\n")

        self.lista_carrinho.config(state=tk.DISABLED)
        self.label_total_venda.config(text=f"Total: R$ {total_atual:.2f}")

    def limpar_carrinho_gui(self):
        """Limpa o carrinho na GUI e na lógica."""
        self.carrinho_itens = []
        self.atualizar_carrinho_gui()
        messagebox.showinfo("Carrinho Limpo", "O carrinho foi esvaziado.")

    def acao_finalizar_venda(self):
        """Finaliza a venda, atualiza estoque e registra a venda."""
        if not self.carrinho_itens:
            messagebox.showwarning("Carrinho Vazio", "Adicione itens ao carrinho antes de finalizar a venda.")
            return

        if messagebox.askyesno("Confirmação de Venda", "Deseja finalizar esta venda?"):
            sucesso, total_arrecadado = realizar_venda_logica(self.carrinho_itens)
            if sucesso:
                messagebox.showinfo("Venda Concluída", f"Venda realizada com sucesso! Total: R$ {total_arrecadado:.2f}")
                self.carrinho_itens = [] # Limpa o carrinho após a venda
                self.atualizar_carrinho_gui()
                self.atualizar_lista_produtos_gui() # Atualiza estoque visivelmente
            else:
                # A mensagem de erro específica já é mostrada por 'realizar_venda_logica'
                pass
        else:
            messagebox.showinfo("Venda Cancelada", "A venda não foi finalizada.")

    def acao_relatorio_estoque_baixo(self):
        """Gera e exibe o relatório de estoque baixo."""
        self.text_relatorio_estoque.config(state=tk.NORMAL)
        self.text_relatorio_estoque.delete('1.0', tk.END)

        try:
            limite = int(self.entry_limite_estoque.get().strip())
            if limite < 0:
                messagebox.showerror("Erro", "O limite deve ser um número positivo ou zero.")
                self.text_relatorio_estoque.insert(tk.END, "Limite inválido.")
                self.text_relatorio_estoque.config(state=tk.DISABLED)
                return
        except ValueError:
            messagebox.showerror("Erro", "Limite inválido. Digite um número inteiro.")
            self.text_relatorio_estoque.insert(tk.END, "Limite inválido.")
            self.text_relatorio_estoque.config(state=tk.DISABLED)
            return

        produtos_baixo_estoque = [p for p in produtos if p['estoque'] <= limite]

        if not produtos_baixo_estoque:
            self.text_relatorio_estoque.insert(tk.END, f"Nenhum produto com estoque abaixo de {limite} unidades.\n")
        else:
            self.text_relatorio_estoque.insert(tk.END, f"--- Produtos com Estoque Abaixo ou Igual a {limite} Unidades ---\n\n")
            for produto in produtos_baixo_estoque:
                self.text_relatorio_estoque.insert(tk.END, f"Código: {produto['codigo']}\n")
                self.text_relatorio_estoque.insert(tk.END, f"Nome: {produto['nome']}\n")
                self.text_relatorio_estoque.insert(tk.END, f"Estoque: {produto['estoque']}\n")
                self.text_relatorio_estoque.insert(tk.END, "-" * 30 + "\n")
        self.text_relatorio_estoque.config(state=tk.DISABLED)

    def acao_relatorio_vendas(self):
        """Gera e exibe o relatório de todas as vendas."""
        self.text_relatorio_vendas.config(state=tk.NORMAL)
        self.text_relatorio_vendas.delete('1.0', tk.END)

        if not vendas:
            self.text_relatorio_vendas.insert(tk.END, "Nenhuma venda registrada ainda.\n")
        else:
            total_geral = 0.0
            self.text_relatorio_vendas.insert(tk.END, "--- Relatório de Todas as Vendas ---\n\n")
            for i, venda in enumerate(vendas):
                self.text_relatorio_vendas.insert(tk.END, f"Venda #{i+1} - Data/Hora: {venda['data_hora']}\n")
                self.text_relatorio_vendas.insert(tk.END, "Itens:\n")
                for item in venda['itens']:
                    self.text_relatorio_vendas.insert(tk.END, f"  - {item['nome']} ({item['quantidade']}x) @ R$ {item['preco_unitario']:.2f} = R$ {item['subtotal']:.2f}\n")
                self.text_relatorio_vendas.insert(tk.END, f"Total da Venda: R$ {venda['total']:.2f}\n")
                self.text_relatorio_vendas.insert(tk.END, "=" * 40 + "\n\n")
                total_geral += venda['total']
            
            self.text_relatorio_vendas.insert(tk.END, f"TOTAL GERAL ARRECADADO: R$ {total_geral:.2f}\n")
        
        self.text_relatorio_vendas.config(state=tk.DISABLED)


# --- Execução da Aplicação ---
if __name__ == "__main__":
    root = tk.Tk()
    app = SupermercadoApp(root)
    root.mainloop()