import sqlite3
from config import Config


class Database:
    """Camada responsável pela conexão e inicialização do banco."""

    @staticmethod
    def get_connection():
        """Retorna conexão com RowFactory habilitado."""
        conn = sqlite3.connect(Config.DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def initialize():
        print(f"🗄️ Inicializando banco: {Config.DB_NAME}")

        with Database.get_connection() as conn:
            cursor = conn.cursor()
            Database._create_schema(cursor)
            Database._create_indexes(cursor)
            Database._seed_data(cursor)
            conn.commit()

        print(f"✅ Banco '{Config.DB_NAME}' pronto para uso.")

    @staticmethod
    def _create_schema(cursor):
        schema = """
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            telefone TEXT,
            cidade TEXT,
            estado TEXT,
            data_cadastro DATE DEFAULT CURRENT_DATE,
            status TEXT DEFAULT 'ativo'
        );

        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco DECIMAL(10,2) NOT NULL,
            custo DECIMAL(10,2),
            categoria TEXT NOT NULL,
            estoque_atual INTEGER DEFAULT 0,
            estoque_minimo INTEGER DEFAULT 5,
            margem_lucro DECIMAL(5,2),
            data_cadastro DATE DEFAULT CURRENT_DATE
        );

        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            data_pedido DATE DEFAULT CURRENT_DATE,
            status TEXT DEFAULT 'pendente',
            total DECIMAL(10,2),
            desconto DECIMAL(10,2) DEFAULT 0,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        );

        CREATE TABLE IF NOT EXISTS pedido_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario DECIMAL(10,2),
            subtotal DECIMAL(10,2),
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        );

        CREATE TABLE IF NOT EXISTS estoque_movimentacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            data_movimentacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            motivo TEXT,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        );

        CREATE TABLE IF NOT EXISTS avaliacoes_produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            cliente_id INTEGER NOT NULL,
            nota INTEGER,
            comentario TEXT,
            data_avaliacao DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (produto_id) REFERENCES produtos(id),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        );

        CREATE TABLE IF NOT EXISTS promocoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            desconto_percentual DECIMAL(5,2),
            data_inicio DATE,
            data_fim DATE,
            status TEXT DEFAULT 'ativa'
        );

        CREATE TABLE IF NOT EXISTS campanhas_marketing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            data_inicio DATE,
            data_fim DATE,
            investimento DECIMAL(10,2),
            roi DECIMAL(5,2),
            status TEXT DEFAULT 'planejamento'
        );
        """

        cursor.executescript(schema)
        print("📌 Tabelas criadas ou já existentes.")

    @staticmethod
    def _create_indexes(cursor):
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(email);",
            "CREATE INDEX IF NOT EXISTS idx_clientes_status ON clientes(status);",
            "CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos(categoria);",
            "CREATE INDEX IF NOT EXISTS idx_pedidos_cliente ON pedidos(cliente_id);",
            "CREATE INDEX IF NOT EXISTS idx_pedidos_data ON pedidos(data_pedido);",
            "CREATE INDEX IF NOT EXISTS idx_pedidos_status ON pedidos(status);",
            "CREATE INDEX IF NOT EXISTS idx_itens_pedido ON pedido_itens(pedido_id);",
            "CREATE INDEX IF NOT EXISTS idx_itens_produto ON pedido_itens(produto_id);",
            "CREATE INDEX IF NOT EXISTS idx_estoque_produto ON estoque_movimentacao(produto_id);",
            "CREATE INDEX IF NOT EXISTS idx_estoque_data ON estoque_movimentacao(data_movimentacao);",
            "CREATE INDEX IF NOT EXISTS idx_avaliacoes_produto ON avaliacoes_produtos(produto_id);",
        ]

        for idx in indexes:
            cursor.execute(idx)

        print("⚡ Índices criados para melhorar desempenho.")

    @staticmethod
    def _seed_data(cursor):
        cursor.execute("SELECT COUNT(*) AS total FROM clientes;")
        total = cursor.fetchone()["total"]

        if total > 0:
            print("📎 Dados já existem — seed ignorado.")
            return

        print("🌱 Inserindo dados de exemplo...")

        # Clientes
        clientes = [
            ("João Silva", "joao@email.com", "11987654321", "São Paulo", "SP", "2024-01-15"),
            ("Maria Santos", "maria@email.com", "21987654321", "Rio de Janeiro", "RJ", "2024-01-20"),
            ("Carlos Oliveira", "carlos@email.com", "31987654321", "Belo Horizonte", "MG", "2024-02-01"),
            ("Ana Costa", "ana@email.com", "85987654321", "Fortaleza", "CE", "2024-02-10"),
            ("Pedro Martins", "pedro@email.com", "47987654321", "Florianópolis", "SC", "2024-02-15"),
        ]

        cursor.executemany(
            "INSERT INTO clientes (nome, email, telefone, cidade, estado, data_cadastro) VALUES (?, ?, ?, ?, ?, ?)",
            clientes
        )

        # Produtos
        produtos = [
            ("Camisa Social", "Camisa social masculina", 89.90, 30.00, "Roupas", 25, 5, 199.67, "2024-01-01"),
            ("Calça Jeans", "Calça jeans tradicional", 129.90, 45.00, "Roupas", 18, 5, 188.64, "2024-01-05"),
            ("Sapato Social", "Sapato social preto", 249.90, 100.00, "Calçados", 10, 3, 149.55, "2024-01-10"),
            ("Caneca Personalizada", "Caneca cerâmica 300ml", 35.90, 10.00, "Acessórios", 50, 10, 259.00, "2024-01-15"),
            ("Livro Python Avançado", "Guia completo de Python", 89.90, 25.00, "Livros", 30, 5, 259.60, "2024-02-01"),
            ("Mouse Gamer RGB", "Mouse com 12000 DPI", 199.90, 70.00, "Eletrônicos", 8, 3, 185.43, "2024-02-05"),
            ("Teclado Mecânico", "Teclado RGB switches MX", 449.90, 150.00, "Eletrônicos", 5, 2, 199.93, "2024-02-10"),
            ("Mochila Executiva", "Mochila com carregamento USB", 159.90, 50.00, "Acessórios", 15, 5, 219.80, "2024-02-15"),
        ]

        cursor.executemany(
            "INSERT INTO produtos (nome, descricao, preco, custo, categoria, estoque_atual, estoque_minimo, margem_lucro, data_cadastro) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            produtos
        )

        # Pedidos com variação de datas
        pedidos = [
            (1, "2024-04-01", "concluido", 89.90, 0),
            (2, "2024-04-02", "concluido", 269.80, 10),
            (3, "2024-04-03", "concluido", 449.80, 0),
            (4, "2024-04-05", "concluido", 199.90, 0),
            (5, "2024-04-10", "concluido", 349.70, 50),
            (1, "2024-04-15", "concluido", 685.70, 0),
            (2, "2024-04-20", "pendente", 199.90, 0),
            (3, "2024-04-25", "concluido", 279.80, 0),
            (4, "2024-05-01", "concluido", 449.80, 25),
            (5, "2024-05-05", "em_processo", 89.90, 0),
        ]

        cursor.executemany(
            "INSERT INTO pedidos (cliente_id, data_pedido, status, total, desconto) VALUES (?, ?, ?, ?, ?)",
            pedidos
        )

        # Itens dos pedidos
        itens = [
            (1, 1, 1, 89.90, 89.90),
            (2, 2, 2, 129.90, 129.90),
            (2, 3, 3, 249.90, 249.90),
            (3, 4, 4, 35.90, 35.90),
            (4, 5, 6, 199.90, 199.90),
            (4, 6, 7, 449.90, 449.90),
            (5, 5, 5, 89.90, 89.90),
            (6, 1, 2, 129.90, 129.90),
            (6, 8, 8, 159.90, 159.90),
            (7, 3, 3, 249.90, 249.90),
            (8, 2, 2, 129.90, 129.90),
            (8, 4, 4, 35.90, 35.90),
            (9, 6, 7, 449.90, 449.90),
            (10, 1, 1, 89.90, 89.90),
        ]

        cursor.executemany(
            "INSERT INTO pedido_itens (pedido_id, produto_id, quantidade, preco_unitario, subtotal) VALUES (?, ?, ?, ?, ?)",
            itens
        )

        # Avaliações
        avaliacoes = [
            (1, 1, 5, "Excelente qualidade!"),
            (2, 2, 4, "Bom custo-benefício"),
            (3, 3, 5, "Produto perfeito"),
            (4, 4, 4, "Boa qualidade"),
            (5, 6, 5, "Mouse muito bom"),
            (6, 7, 5, "Teclado top!"),
            (7, 8, 4, "Mochila resistente"),
            (1, 2, 5, "Calça confortável"),
        ]

        cursor.executemany(
            "INSERT INTO avaliacoes_produtos (produto_id, cliente_id, nota, comentario) VALUES (?, ?, ?, ?)",
            avaliacoes
        )

        # Promoções
        promocoes = [
            ("Promoção de Verão", 15.00, "2024-04-01", "2024-04-30", "ativa"),
            ("Black Friday Antecipada", 30.00, "2024-05-01", "2024-05-15", "planejamento"),
        ]

        cursor.executemany(
            "INSERT INTO promocoes (nome, desconto_percentual, data_inicio, data_fim, status) VALUES (?, ?, ?, ?, ?)",
            promocoes
        )

        print("✅ Seed inserido com sucesso.")

# database.py - Adicione este método execute() e verifique indentação

# ... todo o código anterior permanece ...

    @staticmethod
    def execute(sql: str) -> list:
        """Executa SQL e retorna resultados como lista de dicionários."""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            
            # Verificar se é SELECT para retornar resultados
            if sql.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                conn.commit()
                return []
	# Adicionar no final da classe Database:
    @staticmethod
    def execute(sql: str) -> list:
        """Executa SQL e retorna resultados"""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            
            if sql.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                conn.commit()
                return []

# Remover a linha solta: DatabaseManager = Database
# ... resto do código permanece ...
DatabaseManager = Database