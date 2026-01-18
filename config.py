# config.py
import os
from dotenv import load_dotenv

# Carrega .env uma única vez
load_dotenv(".env")

class Config:
    """Configurações centrais da aplicação"""

    # Ative/desative providers
    USE_GEMINI = True
    USE_OPENAI = False  # Desative até resolver a quota
    USE_OLLAMA = False  # Desative até ter servidor
    
    # Modelos
    GEMINI_MODEL = "gemini-pro"
    OPENAI_MODEL = "gpt-4o-mini"
    
    # Chaves (ou defina no .env)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Database
    DB_NAME = os.getenv("DB_NAME", "ecommerce_db.sqlite")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    
    # Cache
    CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "100"))
    CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))
    
    # Logging
    LOG_DIR = os.getenv("LOG_DIR", "logs")
    ENABLE_CONSOLE_LOG = os.getenv("ENABLE_CONSOLE_LOG", "True").lower() == "true"
    
    # Security
    MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", "500"))
    VALIDATION_LEVEL = os.getenv("VALIDATION_LEVEL", "moderate")  # strict, moderate, permissive
    
    # Schema utilizado no prompt NL→SQL
    DATABASE_SCHEMA = """
    SCHEMA DO BANCO E-COMMERCE:

    TABELA clientes:
      id, nome, email, telefone, data_cadastro, status

    TABELA produtos:
      id, nome, descricao, preco, categoria,
      estoque_atual, estoque_minimo, data_cadastro

    TABELA pedidos:
      id, cliente_id, data_pedido, status, total

    TABELA pedido_itens:
      id, pedido_id, produto_id, quantidade,
      preco_unitario, subtotal

    TABELA estoque_movimentacao:
      id, produto_id, tipo, quantidade,
      data_movimentacao, motivo
    """
    
    # API Configuration
    API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "100 per day")