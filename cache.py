"""
cache.py - Sistema de Cache LRU com TTL
Armazena resultados de queries frequentes em memória
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from collections import OrderedDict
import threading


class QueryCache:
    """
    Cache LRU (Least Recently Used) com suporte a TTL
    Thread-safe para aplicações concorrentes
    """

    def __init__(self, max_size: int = 100, default_ttl_hours: int = 24):
        """
        Args:
            max_size: Máximo de entradas no cache
            default_ttl_hours: Tempo de vida padrão em horas
        """
        self.max_size = max_size
        self.default_ttl_hours = default_ttl_hours
        self.cache: OrderedDict = OrderedDict()
        self.lock = threading.RLock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'total_queries': 0
        }

    def _generate_key(self, pergunta: str) -> str:
        """Gera chave MD5 a partir da pergunta"""
        return hashlib.md5(pergunta.lower().strip().encode()).hexdigest()

    def _is_expired(self, entry: Dict) -> bool:
        """Verifica se entrada expirou"""
        if not entry.get('expires_at'):
            return False
        
        return datetime.now() > datetime.fromisoformat(entry['expires_at'])

    def get(self, pergunta: str) -> Optional[Dict[str, Any]]:
        """
        Obtém resultado do cache se existir e não tiver expirado
        
        Args:
            pergunta: Pergunta em linguagem natural
            
        Returns:
            Dicionário com resultado ou None se não encontrado/expirado
        """
        with self.lock:
            key = self._generate_key(pergunta)
            
            if key not in self.cache:
                self.stats['misses'] += 1
                return None
            
            entry = self.cache[key]
            
            # Verificar expiração
            if self._is_expired(entry):
                del self.cache[key]
                self.stats['misses'] += 1
                return None
            
            # Move para o final (recentemente usado)
            self.cache.move_to_end(key)
            
            self.stats['hits'] += 1
            return entry['resultado']

    def set(self, pergunta: str, resultado: Dict, ttl_hours: Optional[int] = None) -> bool:
        """
        Armazena resultado no cache
        
        Args:
            pergunta: Pergunta em linguagem natural
            resultado: Resultado da query (dados + metadata)
            ttl_hours: Tempo de vida em horas (usa padrão se None)
            
        Returns:
            True se armazenado com sucesso
        """
        with self.lock:
            key = self._generate_key(pergunta)
            ttl = ttl_hours or self.default_ttl_hours
            
            # Remove se já existe (para mover para o final)
            if key in self.cache:
                del self.cache[key]
            
            # Se cache está cheio, remove o mais antigo
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
            
            # Calcula expiração
            expires_at = (datetime.now() + timedelta(hours=ttl)).isoformat()
            
            # Armazena
            self.cache[key] = {
                'pergunta': pergunta,
                'resultado': resultado,
                'criado_em': datetime.now().isoformat(),
                'expires_at': expires_at
            }
            
            self.stats['total_queries'] += 1
            return True

    def delete(self, pergunta: str) -> bool:
        """Remove entrada específica do cache"""
        with self.lock:
            key = self._generate_key(pergunta)
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self) -> int:
        """Limpa todo o cache e retorna quantidade de itens removidos"""
        with self.lock:
            size = len(self.cache)
            self.cache.clear()
            return size

    def cleanup_expired(self) -> int:
        """Remove entradas expiradas"""
        with self.lock:
            expired_keys = [
                k for k, v in self.cache.items()
                if self._is_expired(v)
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso do cache"""
        with self.lock:
            total = self.stats['hits'] + self.stats['misses']
            hit_rate = (
                (self.stats['hits'] / total * 100) if total > 0 else 0
            )
            
            return {
                'tamanho_atual': len(self.cache),
                'tamanho_maximo': self.max_size,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'taxa_acerto': f"{hit_rate:.2f}%",
                'total_queries_armazenadas': self.stats['total_queries']
            }

    def list_cached_queries(self) -> list:
        """Lista todas as queries em cache (para debug)"""
        with self.lock:
            return [
                {
                    'pergunta': entry['pergunta'],
                    'criado_em': entry['criado_em'],
                    'expires_at': entry['expires_at']
                }
                for entry in self.cache.values()
            ]