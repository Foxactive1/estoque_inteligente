"""
🎯 SISTEMA DE PREVISÃO DE ESTOQUE INTELIGENTE
Autor: Dione Castro Alves - InNovaIdeia
Análise preditiva de estoque com IA e padrões de vendas
"""

from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import math


class SmartInventoryForecast:
    """Motor de Previsão Inteligente de Estoque"""

    def __init__(self, db_manager):
        self.db = db_manager

    def analisar_rotatividade_produtos(self):
        """Analisa velocidade de vendas por produto"""
        sql = """
        SELECT 
            p.id,
            p.nome,
            p.categoria,
            p.estoque_atual,
            p.estoque_minimo,
            COUNT(DISTINCT pi.pedido_id) as total_pedidos,
            SUM(pi.quantidade) as total_vendido,
            AVG(pi.quantidade) as media_por_pedido,
            MAX(ped.data_pedido) as ultima_venda
        FROM produtos p
        LEFT JOIN pedido_itens pi ON p.id = pi.produto_id
        LEFT JOIN pedidos ped ON pi.pedido_id = ped.id
        WHERE ped.status != 'cancelado'
        GROUP BY p.id
        ORDER BY total_vendido DESC
        """
        
        resultados = self.db.execute(sql)
        
        print("\n" + "="*80)
        print("📊 ANÁLISE DE ROTATIVIDADE DE PRODUTOS")
        print("="*80)
        
        for produto in resultados:
            velocidade = self._calcular_velocidade_venda(produto)
            status_estoque = self._avaliar_status_estoque(produto)
            
            print(f"\n🏷️  {produto['nome']} ({produto['categoria']})")
            print(f"   Estoque Atual: {produto['estoque_atual']} | Mínimo: {produto['estoque_minimo']}")
            print(f"   Total Vendido: {produto['total_vendido'] or 0} unidades")
            print(f"   Pedidos: {produto['total_pedidos'] or 0}")
            print(f"   Velocidade: {velocidade}")
            print(f"   Status: {status_estoque}")
            
        return resultados

    def prever_demanda_futura(self, dias_previsao=30):
        """Prevê demanda futura baseada em histórico"""
        sql = """
        SELECT 
            p.id,
            p.nome,
            p.estoque_atual,
            p.estoque_minimo,
            pi.produto_id,
            SUM(pi.quantidade) as total_vendido,
            COUNT(DISTINCT DATE(ped.data_pedido)) as dias_com_venda,
            MIN(ped.data_pedido) as primeira_venda,
            MAX(ped.data_pedido) as ultima_venda
        FROM produtos p
        LEFT JOIN pedido_itens pi ON p.id = pi.produto_id
        LEFT JOIN pedidos ped ON pi.pedido_id = ped.id
        WHERE ped.status = 'concluido'
        GROUP BY p.id
        """
        
        produtos = self.db.execute(sql)
        
        print("\n" + "="*80)
        print(f"🔮 PREVISÃO DE DEMANDA - Próximos {dias_previsao} dias")
        print("="*80)
        
        previsoes = []
        
        for produto in produtos:
            if not produto['total_vendido']:
                continue
                
            # Calcular média diária de vendas
            dias_historico = self._calcular_dias_entre_datas(
                produto['primeira_venda'], 
                produto['ultima_venda']
            )
            
            if dias_historico == 0:
                dias_historico = 1
                
            media_diaria = produto['total_vendido'] / dias_historico
            demanda_prevista = math.ceil(media_diaria * dias_previsao)
            
            # Calcular quando precisará repor
            dias_ate_reposicao = self._calcular_dias_reposicao(
                produto['estoque_atual'],
                media_diaria,
                produto['estoque_minimo']
            )
            
            nivel_urgencia = self._definir_urgencia(dias_ate_reposicao)
            quantidade_sugerida = self._calcular_quantidade_reposicao(
                produto['estoque_atual'],
                demanda_prevista,
                produto['estoque_minimo']
            )
            
            previsao = {
                'produto': produto['nome'],
                'estoque_atual': produto['estoque_atual'],
                'media_diaria': round(media_diaria, 2),
                'demanda_prevista': demanda_prevista,
                'dias_ate_reposicao': dias_ate_reposicao,
                'urgencia': nivel_urgencia,
                'quantidade_sugerida': quantidade_sugerida
            }
            
            previsoes.append(previsao)
            
            # Exibir previsão
            print(f"\n📦 {produto['nome']}")
            print(f"   Estoque: {produto['estoque_atual']} unidades")
            print(f"   Média Diária: {round(media_diaria, 2)} unidades/dia")
            print(f"   Demanda {dias_previsao}d: {demanda_prevista} unidades")
            print(f"   Dias até Reposição: {dias_ate_reposicao}")
            print(f"   Urgência: {nivel_urgencia}")
            print(f"   💡 Sugestão: Repor {quantidade_sugerida} unidades")
        
        return previsoes

    def detectar_sazonalidade(self):
        """Detecta padrões sazonais de vendas"""
        sql = """
        SELECT 
            strftime('%m', ped.data_pedido) as mes,
            strftime('%Y', ped.data_pedido) as ano,
            p.categoria,
            SUM(pi.quantidade) as total_vendido
        FROM pedidos ped
        JOIN pedido_itens pi ON ped.id = pi.pedido_id
        JOIN produtos p ON pi.produto_id = p.id
        WHERE ped.status = 'concluido'
        GROUP BY mes, ano, p.categoria
        ORDER BY ano, mes
        """
        
        vendas = self.db.execute(sql)
        
        print("\n" + "="*80)
        print("📈 ANÁLISE DE SAZONALIDADE")
        print("="*80)
        
        # Agrupar por categoria e mês
        vendas_por_categoria = defaultdict(lambda: defaultdict(int))
        
        for venda in vendas:
            mes_nome = self._nome_mes(int(venda['mes']))
            vendas_por_categoria[venda['categoria']][mes_nome] += venda['total_vendido']
        
        for categoria, meses in vendas_por_categoria.items():
            print(f"\n🏷️  {categoria}")
            
            if len(meses) > 1:
                valores = list(meses.values())
                media = statistics.mean(valores)
                desvio = statistics.stdev(valores) if len(valores) > 1 else 0
                
                print(f"   Média Mensal: {round(media, 2)} unidades")
                print(f"   Variação: ±{round(desvio, 2)}")
                
                # Identificar meses de pico
                mes_pico = max(meses, key=meses.get)
                mes_baixo = min(meses, key=meses.get)
                
                print(f"   🔥 Pico: {mes_pico} ({meses[mes_pico]} unidades)")
                print(f"   📉 Baixa: {mes_baixo} ({meses[mes_baixo]} unidades)")
            else:
                print(f"   Dados insuficientes para análise sazonal")
        
        return vendas_por_categoria

    def gerar_alertas_reposicao(self):
        """Gera alertas inteligentes de reposição"""
        sql = """
        SELECT 
            p.id,
            p.nome,
            p.categoria,
            p.estoque_atual,
            p.estoque_minimo,
            COALESCE(SUM(pi.quantidade), 0) as total_vendido,
            COUNT(DISTINCT ped.id) as total_pedidos
        FROM produtos p
        LEFT JOIN pedido_itens pi ON p.id = pi.produto_id
        LEFT JOIN pedidos ped ON pi.pedido_id = ped.id
        WHERE ped.status = 'concluido' OR ped.status IS NULL
        GROUP BY p.id
        """
        
        produtos = self.db.execute(sql)
        
        print("\n" + "="*80)
        print("🚨 ALERTAS DE REPOSIÇÃO INTELIGENTE")
        print("="*80)
        
        alertas = {
            'critico': [],
            'atencao': [],
            'normal': []
        }
        
        for produto in produtos:
            nivel = self._avaliar_nivel_estoque(produto)
            
            if nivel == 'critico':
                alertas['critico'].append(produto)
            elif nivel == 'atencao':
                alertas['atencao'].append(produto)
            else:
                alertas['normal'].append(produto)
        
        # Exibir alertas críticos
        if alertas['critico']:
            print("\n🔴 CRÍTICO - Ação Imediata Necessária:")
            for p in alertas['critico']:
                print(f"   • {p['nome']}: {p['estoque_atual']} unidades (mín: {p['estoque_minimo']})")
        
        # Exibir alertas de atenção
        if alertas['atencao']:
            print("\n🟡 ATENÇÃO - Planejar Reposição:")
            for p in alertas['atencao']:
                print(f"   • {p['nome']}: {p['estoque_atual']} unidades (mín: {p['estoque_minimo']})")
        
        # Status normal
        if alertas['normal']:
            print(f"\n🟢 NORMAL - {len(alertas['normal'])} produtos com estoque adequado")
        
        return alertas

    def relatorio_completo(self):
        """Gera relatório completo de inteligência de estoque"""
        print("\n" + "="*80)
        print("🧠 RELATÓRIO DE INTELIGÊNCIA DE ESTOQUE")
        print(f"📅 Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print("="*80)
        
        self.analisar_rotatividade_produtos()
        self.prever_demanda_futura(30)
        self.detectar_sazonalidade()
        self.gerar_alertas_reposicao()
        
        print("\n" + "="*80)
        print("✅ Relatório Completo Finalizado")
        print("="*80)

    # Métodos auxiliares
    
    def _calcular_velocidade_venda(self, produto):
        """Classifica velocidade de venda"""
        total = produto['total_vendido'] or 0
        
        if total >= 10:
            return "🔥 Alta Rotatividade"
        elif total >= 5:
            return "⚡ Média Rotatividade"
        elif total > 0:
            return "🐌 Baixa Rotatividade"
        else:
            return "❌ Sem Vendas"

    def _avaliar_status_estoque(self, produto):
        """Avalia status atual do estoque"""
        atual = produto['estoque_atual']
        minimo = produto['estoque_minimo']
        
        if atual <= minimo:
            return "🔴 CRÍTICO - Repor Urgente"
        elif atual <= minimo * 1.5:
            return "🟡 ATENÇÃO - Planejar Reposição"
        else:
            return "🟢 ADEQUADO"

    def _calcular_dias_entre_datas(self, data_inicio, data_fim):
        """Calcula diferença em dias entre duas datas"""
        if not data_inicio or not data_fim:
            return 1
            
        try:
            d1 = datetime.strptime(data_inicio, '%Y-%m-%d')
            d2 = datetime.strptime(data_fim, '%Y-%m-%d')
            return max(1, (d2 - d1).days)
        except:
            return 1

    def _calcular_dias_reposicao(self, estoque_atual, media_diaria, estoque_minimo):
        """Calcula em quantos dias precisará repor"""
        if media_diaria == 0:
            return 999
            
        estoque_disponivel = estoque_atual - estoque_minimo
        
        if estoque_disponivel <= 0:
            return 0
            
        return math.floor(estoque_disponivel / media_diaria)

    def _definir_urgencia(self, dias):
        """Define nível de urgência baseado em dias"""
        if dias <= 3:
            return "🔴 URGENTE"
        elif dias <= 7:
            return "🟡 ATENÇÃO"
        elif dias <= 15:
            return "🟢 NORMAL"
        else:
            return "⚪ SEM PRESSA"

    def _calcular_quantidade_reposicao(self, estoque_atual, demanda_prevista, estoque_minimo):
        """Calcula quantidade ideal para reposição"""
        estoque_desejado = max(demanda_prevista, estoque_minimo * 3)
        quantidade = estoque_desejado - estoque_atual
        return max(0, math.ceil(quantidade))

    def _nome_mes(self, numero_mes):
        """Converte número do mês para nome"""
        meses = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março',
            4: 'Abril', 5: 'Maio', 6: 'Junho',
            7: 'Julho', 8: 'Agosto', 9: 'Setembro',
            10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        return meses.get(numero_mes, 'Desconhecido')

    def _avaliar_nivel_estoque(self, produto):
        """Avalia criticidade do nível de estoque"""
        atual = produto['estoque_atual']
        minimo = produto['estoque_minimo']
        
        if atual < minimo:
            return 'critico'
        elif atual <= minimo * 1.5:
            return 'atencao'
        else:
            return 'normal'


# ===========================
# 🎯 EXEMPLO DE USO
# ===========================

if __name__ == "__main__":
    # Importar Database do seu projeto
    from database import DatabaseManager
    
    # Inicializar banco (se necessário)
    DatabaseManager.initialize()
    
    # Criar instância do sistema de previsão
    forecast = SmartInventoryForecast(DatabaseManager)
    
    # Executar relatório completo
    forecast.relatorio_completo()
    
    print("\n" + "="*80)
    print("💡 DICA: Integre este sistema ao seu dashboard Flask!")
    print("="*80)