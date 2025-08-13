#!/usr/bin/env python3
"""
CVCRM ETL - Dashboard Web para Análise de Vendas Imobiliárias
Interface Flask com visualizações Plotly - Estrutura CVDW corrigida Agosto 2025

Funcionalidades:
- KPIs em tempo real (vendas, ticket médio, comissões)
- Gráficos interativos de evolução de vendas
- Ranking de corretores por performance
- Análise VSO (Velocity of Sales and Operations)
- Health checks e monitoramento
- APIs REST para integração BI

Deploy: Railway (processo web) + Gunicorn
LGPD: Compliant - dados corporativos agregados
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import plotly.graph_objs as go
import plotly.utils
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

class DashboardData:
    """Classe para gerenciar dados do dashboard"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL não encontrada")
    
    def get_connection(self):
        """Cria conexão com o banco"""
        return psycopg2.connect(self.database_url)
    
    def get_kpis(self):
        """Busca KPIs focados em vendas e análises"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # KPIs principais de vendas
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_vendas,
                            COALESCE(SUM(valor), 0) as valor_total_vendas,
                            COALESCE(AVG(valor), 0) as ticket_medio,
                            COALESCE(SUM(comissao_valor), 0) as total_comissoes,
                            COALESCE(AVG(comissao_valor), 0) as media_comissoes
                        FROM vendas 
                        WHERE ativo = 'S'
                        AND data_venda IS NOT NULL
                        AND data_venda >= CURRENT_DATE - INTERVAL '12 months'
                    """)
                    
                    vendas_gerais = cursor.fetchone()
                    
                    # Vendas do mês atual
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as vendas_mes_atual,
                            COALESCE(SUM(valor), 0) as valor_mes_atual,
                            COALESCE(AVG(valor), 0) as ticket_medio_mes
                        FROM vendas 
                        WHERE DATE_TRUNC('month', data_venda) = DATE_TRUNC('month', CURRENT_DATE)
                        AND ativo = 'S'
                        AND data_venda IS NOT NULL
                    """)
                    
                    vendas_mes = cursor.fetchone()
                    
                    # Comparação ano atual vs passado
                    cursor.execute("""
                        SELECT * FROM vw_vendas_ano_atual_vs_passado
                        ORDER BY ano DESC
                    """)
                    
                    comparacao_anual = cursor.fetchall()
                    
                    # VSO mensal (último mês)
                    cursor.execute("""
                        SELECT 
                            vso_valor,
                            vso_ticket_medio
                        FROM vw_vso_mensal 
                        ORDER BY mes DESC 
                        LIMIT 1
                    """)
                    
                    vso = cursor.fetchone()
                    
                    # Total de empreendimentos e corretores ativos
                    cursor.execute("""
                        SELECT 
                            COUNT(DISTINCT e.id) as total_empreendimentos,
                            COUNT(DISTINCT v.corretor_nome) as total_corretores,
                            COUNT(DISTINCT v.time_corretor) as total_times
                        FROM empreendimentos e
                        LEFT JOIN vendas v ON e.cvcrm_id = v.empreendimento_id
                        WHERE v.data_venda >= CURRENT_DATE - INTERVAL '12 months'
                        AND v.status NOT IN ('cancelado', 'distratado')
                    """)
                    
                    estrutura = cursor.fetchone()
                    
                    # Prosoluto total
                    cursor.execute("""
                        SELECT 
                            COALESCE(SUM(valor_prosoluto), 0) as total_prosoluto,
                            COALESCE(AVG(valor_prosoluto), 0) as media_prosoluto
                        FROM prosoluto 
                        WHERE data_calculo >= CURRENT_DATE - INTERVAL '12 months'
                        AND status NOT IN ('cancelado')
                    """)
                    
                    prosoluto = cursor.fetchone()
                    
                    # Crescimento mensal (últimos 2 meses)
                    cursor.execute("""
                        WITH vendas_ultimos_2_meses AS (
                            SELECT 
                                DATE_TRUNC('month', data_venda) as mes,
                                SUM(valor_venda) as valor_mes
                            FROM vendas
                            WHERE data_venda >= CURRENT_DATE - INTERVAL '2 months'
                            AND status NOT IN ('cancelado', 'distratado')
                            GROUP BY DATE_TRUNC('month', data_venda)
                            ORDER BY mes DESC
                            LIMIT 2
                        )
                        SELECT 
                            CASE 
                                WHEN LAG(valor_mes) OVER (ORDER BY mes) > 0
                                THEN ROUND(((valor_mes - LAG(valor_mes) OVER (ORDER BY mes)) / LAG(valor_mes) OVER (ORDER BY mes) * 100), 2)
                                ELSE 0
                            END as crescimento_mensal
                        FROM vendas_ultimos_2_meses
                        ORDER BY mes DESC
                        LIMIT 1
                    """)
                    
                    crescimento = cursor.fetchone()
                    
                    return {
                        # Vendas gerais
                        'total_vendas': int(vendas_gerais['total_vendas']),
                        'valor_total_vendas': float(vendas_gerais['valor_total_vendas']),
                        'ticket_medio_geral': float(vendas_gerais['ticket_medio']),
                        'total_comissoes': float(vendas_gerais['total_comissoes']),
                        'media_comissoes': float(vendas_gerais['media_comissoes']),
                        
                        # Vendas do mês
                        'vendas_mes_atual': int(vendas_mes['vendas_mes_atual']),
                        'valor_mes_atual': float(vendas_mes['valor_mes_atual']),
                        'ticket_medio_mes': float(vendas_mes['ticket_medio_mes']),
                        
                        # VSO
                        'vso_valor': float(vso['vso_valor'] if vso and vso['vso_valor'] else 0),
                        'vso_ticket_medio': float(vso['vso_ticket_medio'] if vso and vso['vso_ticket_medio'] else 0),
                        
                        # Estrutura
                        'total_empreendimentos': int(estrutura['total_empreendimentos']),
                        'total_corretores': int(estrutura['total_corretores']),
                        'total_times': int(estrutura['total_times']),
                        
                        # Prosoluto
                        'total_prosoluto': float(prosoluto['total_prosoluto']),
                        'media_prosoluto': float(prosoluto['media_prosoluto']),
                        
                        # Comparação anual
                        'ano_atual': comparacao_anual[0] if comparacao_anual else None,
                        'ano_passado': comparacao_anual[1] if len(comparacao_anual) > 1 else None,
                        
                        # Crescimento
                        'crescimento_mensal': float(crescimento['crescimento_mensal'] if crescimento and crescimento['crescimento_mensal'] else 0)
                    }
                    
        except Exception as e:
            logging.error(f"Erro ao buscar KPIs: {e}")
            return {
                'total_vendas': 0,
                'valor_total_vendas': 0,
                'ticket_medio_geral': 0,
                'total_comissoes': 0,
                'media_comissoes': 0,
                'vendas_mes_atual': 0,
                'valor_mes_atual': 0,
                'ticket_medio_mes': 0,
                'vso_valor': 0,
                'vso_ticket_medio': 0,
                'total_empreendimentos': 0,
                'total_corretores': 0,
                'total_times': 0,
                'total_prosoluto': 0,
                'media_prosoluto': 0,
                'ano_atual': None,
                'ano_passado': None,
                'crescimento_mensal': 0
            }
    
    def get_vendas_mensais_chart_data(self):
        """Dados para gráfico de vendas mensais com comparação anual"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM vw_vendas_mensais
                        ORDER BY mes
                    """)
                    
                    data = cursor.fetchall()
                    
                    return {
                        'meses': [row['mes'].strftime('%Y-%m') for row in data],
                        'valores': [float(row['valor_total_vendas'] or 0) for row in data],
                        'quantidades': [int(row['quantidade_vendas']) for row in data],
                        'tickets_medios': [float(row['ticket_medio'] or 0) for row in data],
                        'vgv': [float(row['vgv_total'] or 0) for row in data],
                        'comissoes': [float(row['total_comissoes'] or 0) for row in data]
                    }
                    
        except Exception as e:
            logging.error(f"Erro ao buscar dados de vendas mensais: {e}")
            return {'meses': [], 'valores': [], 'quantidades': [], 'tickets_medios': [], 'vgv': [], 'comissoes': []}
    
    def get_vso_chart_data(self):
        """Dados para gráfico de VSO mensal"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM vw_vso_mensal
                        ORDER BY mes
                    """)
                    
                    data = cursor.fetchall()
                    
                    return {
                        'meses': [row['mes'].strftime('%Y-%m') for row in data],
                        'vso_valores': [float(row['vso_valor'] or 0) for row in data],
                        'vso_tickets': [float(row['vso_ticket_medio'] or 0) for row in data],
                        'quantidades': [int(row['quantidade_vendas']) for row in data]
                    }
                    
        except Exception as e:
            logging.error(f"Erro ao buscar dados VSO: {e}")
            return {'meses': [], 'vso_valores': [], 'vso_tickets': [], 'quantidades': []}
    
    def get_top_empreendimentos(self, limit=10):
        """Top empreendimentos por vendas"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(f"""
                        SELECT * FROM vw_vendas_por_empreendimento 
                        WHERE quantidade_vendas > 0
                        ORDER BY valor_total_vendas DESC 
                        LIMIT {limit}
                    """)
                    
                    return cursor.fetchall()
                    
        except Exception as e:
            logging.error(f"Erro ao buscar top empreendimentos: {e}")
            return []
    
    def get_top_corretores(self, limit=15):
        """Top corretores por vendas"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(f"""
                        SELECT * FROM vw_vendas_por_corretor 
                        ORDER BY valor_total_vendas DESC 
                        LIMIT {limit}
                    """)
                    
                    return cursor.fetchall()
                    
        except Exception as e:
            logging.error(f"Erro ao buscar top corretores: {e}")
            return []
    
    def get_vendas_por_time(self):
        """Vendas por time de corretores"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM vw_vendas_por_time 
                        ORDER BY valor_total_vendas DESC
                    """)
                    
                    return cursor.fetchall()
                    
        except Exception as e:
            logging.error(f"Erro ao buscar vendas por time: {e}")
            return []
    
    def get_prosoluto_chart_data(self):
        """Dados para análise de prosoluto"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM vw_prosoluto_analise
                        ORDER BY mes
                    """)
                    
                    data = cursor.fetchall()
                    
                    return {
                        'meses': [row['mes'].strftime('%Y-%m') for row in data],
                        'valores_prosoluto': [float(row['valor_total_prosoluto'] or 0) for row in data],
                        'medias_prosoluto': [float(row['media_prosoluto'] or 0) for row in data],
                        'percentuais': [float(row['percentual_prosoluto_sobre_venda'] or 0) for row in data]
                    }
                    
        except Exception as e:
            logging.error(f"Erro ao buscar dados prosoluto: {e}")
            return {'meses': [], 'valores_prosoluto': [], 'medias_prosoluto': [], 'percentuais': []}
    
    def get_sync_status(self):
        """Status da última sincronização"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT 
                            MAX(updated_at) as last_sync,
                            COUNT(*) as total_records
                        FROM (
                            SELECT updated_at FROM clients
                            UNION ALL
                            SELECT updated_at FROM opportunities  
                            UNION ALL
                            SELECT updated_at FROM sales
                        ) t
                    """)
                    
                    result = cursor.fetchone()
                    last_sync = result['last_sync']
                    
                    if last_sync:
                        time_diff = datetime.now() - last_sync.replace(tzinfo=None)
                        hours_ago = int(time_diff.total_seconds() / 3600)
                        
                        if hours_ago == 0:
                            status_text = "Agora mesmo"
                        elif hours_ago == 1:
                            status_text = "1 hora atrás"
                        else:
                            status_text = f"{hours_ago} horas atrás"
                    else:
                        status_text = "Nunca"
                    
                    return {
                        'last_sync': status_text,
                        'last_sync_date': last_sync.strftime('%d/%m/%Y %H:%M') if last_sync else 'N/A',
                        'total_records': result['total_records']
                    }
                    
        except Exception as e:
            logging.error(f"Erro ao buscar status: {e}")
            return {
                'last_sync': 'Erro',
                'last_sync_date': 'N/A',
                'total_records': 0
            }

dashboard_data = DashboardData()

# Template HTML do dashboard focado em vendas
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>CVCRM - Dashboard de Vendas</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css">
    <style>
        .dashboard-header {
            background: linear-gradient(135deg, #2E8B57 0%, #20B2AA 100%);
            color: white;
            padding: 2rem 0;
        }
        .kpi-card {
            transition: transform 0.3s ease;
            border: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            height: 100%;
        }
        .kpi-card:hover {
            transform: translateY(-3px);
        }
        .kpi-value {
            font-size: 1.8rem;
            font-weight: bold;
        }
        .kpi-small {
            font-size: 1.2rem;
            font-weight: bold;
        }
        .chart-container {
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        .comparison-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: none;
            border-radius: 10px;
        }
        .growth-positive {
            color: #28a745;
        }
        .growth-negative {
            color: #dc3545;
        }
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h1><i class="bi bi-graph-up-arrow"></i> CVCRM - Dashboard de Vendas</h1>
                    <p class="mb-0">Análises de vendas, VSO, ticket médio, comissões e prosoluto</p>
                </div>
                <div class="col-md-4 text-end">
                    <span class="badge bg-light text-dark fs-6">
                        <i class="bi bi-clock"></i> Última sync: {{ sync_status.last_sync }}
                    </span>
                </div>
            </div>
        </div>
    </div>

    <div class="container-fluid my-4">
        <!-- KPIs Principais de Vendas -->
        <div class="row mb-4">
            <div class="col-xl-2 col-md-4 mb-3">
                <div class="card kpi-card">
                    <div class="card-body text-center">
                        <i class="bi bi-cash-stack text-success" style="font-size: 2rem;"></i>
                        <div class="kpi-value text-success">{{ kpis.total_vendas }}</div>
                        <div class="text-muted small">Total Vendas (12m)</div>
                    </div>
                </div>
            </div>
            <div class="col-xl-2 col-md-4 mb-3">
                <div class="card kpi-card">
                    <div class="card-body text-center">
                        <i class="bi bi-currency-dollar text-primary" style="font-size: 2rem;"></i>
                        <div class="kpi-small text-primary">R$ {{ "%.0f"|format(kpis.valor_total_vendas) }}</div>
                        <div class="text-muted small">Valor Total</div>
                    </div>
                </div>
            </div>
            <div class="col-xl-2 col-md-4 mb-3">
                <div class="card kpi-card">
                    <div class="card-body text-center">
                        <i class="bi bi-ticket text-warning" style="font-size: 2rem;"></i>
                        <div class="kpi-small text-warning">R$ {{ "%.0f"|format(kpis.ticket_medio_geral) }}</div>
                        <div class="text-muted small">Ticket Médio</div>
                    </div>
                </div>
            </div>
            <div class="col-xl-2 col-md-4 mb-3">
                <div class="card kpi-card">
                    <div class="card-body text-center">
                        <i class="bi bi-building text-info" style="font-size: 2rem;"></i>
                        <div class="kpi-value text-info">{{ kpis.total_empreendimentos }}</div>
                        <div class="text-muted small">Empreendimentos</div>
                    </div>
                </div>
            </div>
            <div class="col-xl-2 col-md-4 mb-3">
                <div class="card kpi-card">
                    <div class="card-body text-center">
                        <i class="bi bi-people text-secondary" style="font-size: 2rem;"></i>
                        <div class="kpi-value text-secondary">{{ kpis.total_corretores }}</div>
                        <div class="text-muted small">Corretores</div>
                    </div>
                </div>
            </div>
            <div class="col-xl-2 col-md-4 mb-3">
                <div class="card kpi-card">
                    <div class="card-body text-center">
                        <i class="bi bi-award text-danger" style="font-size: 2rem;"></i>
                        <div class="kpi-small text-danger">R$ {{ "%.0f"|format(kpis.total_comissoes) }}</div>
                        <div class="text-muted small">Comissões</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Comparação Anual -->
        {% if kpis.ano_atual and kpis.ano_passado %}
        <div class="row mb-4">
            <div class="col-12">
                <div class="card comparison-card">
                    <div class="card-body">
                        <h5><i class="bi bi-calendar-check"></i> Comparação Ano Atual vs Ano Passado</h5>
                        <div class="row text-center">
                            <div class="col-md-2">
                                <h6>{{ kpis.ano_atual.ano }} (Atual)</h6>
                                <strong class="text-success">{{ kpis.ano_atual.quantidade_vendas }} vendas</strong><br>
                                <span>R$ {{ "%.0f"|format(kpis.ano_atual.valor_total) }}</span>
                            </div>
                            <div class="col-md-2">
                                <h6>{{ kpis.ano_passado.ano }} (Anterior)</h6>
                                <strong class="text-primary">{{ kpis.ano_passado.quantidade_vendas }} vendas</strong><br>
                                <span>R$ {{ "%.0f"|format(kpis.ano_passado.valor_total) }}</span>
                            </div>
                            <div class="col-md-2">
                                <h6>Crescimento Vendas</h6>
                                {% set crescimento_qty = ((kpis.ano_atual.quantidade_vendas - kpis.ano_passado.quantidade_vendas) / kpis.ano_passado.quantidade_vendas * 100) if kpis.ano_passado.quantidade_vendas > 0 else 0 %}
                                <strong class="{% if crescimento_qty >= 0 %}growth-positive{% else %}growth-negative{% endif %}">
                                    {{ "%.1f"|format(crescimento_qty) }}%
                                </strong>
                            </div>
                            <div class="col-md-2">
                                <h6>Crescimento Valor</h6>
                                {% set crescimento_valor = ((kpis.ano_atual.valor_total - kpis.ano_passado.valor_total) / kpis.ano_passado.valor_total * 100) if kpis.ano_passado.valor_total > 0 else 0 %}
                                <strong class="{% if crescimento_valor >= 0 %}growth-positive{% else %}growth-negative{% endif %}">
                                    {{ "%.1f"|format(crescimento_valor) }}%
                                </strong>
                            </div>
                            <div class="col-md-2">
                                <h6>Ticket Médio Atual</h6>
                                <strong>R$ {{ "%.0f"|format(kpis.ano_atual.ticket_medio) }}</strong>
                            </div>
                            <div class="col-md-2">
                                <h6>Crescimento Mensal</h6>
                                <strong class="{% if kpis.crescimento_mensal >= 0 %}growth-positive{% else %}growth-negative{% endif %}">
                                    {{ "%.1f"|format(kpis.crescimento_mensal) }}%
                                </strong>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- Gráficos -->
        <div class="row mb-4">
            <div class="col-lg-8">
                <div class="chart-container">
                    <h4><i class="bi bi-bar-chart-line"></i> Vendas Mensais</h4>
                    <div id="vendas-mensais-chart" style="height: 400px;"></div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="chart-container">
                    <h4><i class="bi bi-graph-up"></i> VSO & Ticket Médio</h4>
                    <div id="vso-chart" style="height: 400px;"></div>
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col-lg-6">
                <div class="chart-container">
                    <h4><i class="bi bi-building-fill"></i> Top 10 Empreendimentos</h4>
                    <div class="table-responsive">
                        <table class="table table-sm table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>Empreendimento</th>
                                    <th>Vendas</th>
                                    <th>Valor Total</th>
                                    <th>Ticket Médio</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for emp in top_empreendimentos %}
                                <tr>
                                    <td><strong>{{ emp.empreendimento }}</strong></td>
                                    <td><span class="badge bg-success">{{ emp.quantidade_vendas }}</span></td>
                                    <td>R$ {{ "%.0f"|format(emp.valor_total_vendas) }}</td>
                                    <td>R$ {{ "%.0f"|format(emp.ticket_medio) }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="chart-container">
                    <h4><i class="bi bi-person-badge"></i> Top 15 Corretores</h4>
                    <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                        <table class="table table-sm table-hover">
                            <thead class="table-dark sticky-top">
                                <tr>
                                    <th>Corretor</th>
                                    <th>Time</th>
                                    <th>Vendas</th>
                                    <th>Valor</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for corretor in top_corretores %}
                                <tr>
                                    <td><strong>{{ corretor.corretor_nome }}</strong></td>
                                    <td><small>{{ corretor.time_corretor or 'N/A' }}</small></td>
                                    <td><span class="badge bg-primary">{{ corretor.quantidade_vendas }}</span></td>
                                    <td>R$ {{ "%.0f"|format(corretor.valor_total_vendas) }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Times e Prosoluto -->
        <div class="row mb-4">
            <div class="col-lg-6">
                <div class="chart-container">
                    <h4><i class="bi bi-people-fill"></i> Vendas por Time</h4>
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead class="table-dark">
                                <tr>
                                    <th>Time</th>
                                    <th>Corretores</th>
                                    <th>Vendas</th>
                                    <th>Valor Total</th>
                                    <th>Ticket Médio</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for time in vendas_por_time %}
                                <tr>
                                    <td><strong>{{ time.time_corretor }}</strong></td>
                                    <td>{{ time.total_corretores }}</td>
                                    <td><span class="badge bg-warning">{{ time.quantidade_vendas }}</span></td>
                                    <td>R$ {{ "%.0f"|format(time.valor_total_vendas) }}</td>
                                    <td>R$ {{ "%.0f"|format(time.ticket_medio) }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="chart-container">
                    <h4><i class="bi bi-cash-coin"></i> Análise Prosoluto</h4>
                    <div id="prosoluto-chart" style="height: 350px;"></div>
                    <div class="row text-center mt-3">
                        <div class="col-6">
                            <h6>Total Prosoluto (12m)</h6>
                            <strong class="text-success">R$ {{ "%.0f"|format(kpis.total_prosoluto) }}</strong>
                        </div>
                        <div class="col-6">
                            <h6>Média Prosoluto</h6>
                            <strong class="text-primary">R$ {{ "%.0f"|format(kpis.media_prosoluto) }}</strong>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Gráfico de Vendas Mensais
        var vendasMensais = {{ vendas_mensais_chart_data|tojson }};
        
        var trace1 = {
            x: vendasMensais.meses,
            y: vendasMensais.valores,
            type: 'bar',
            name: 'Valor Vendas',
            marker: { color: 'rgba(40, 167, 69, 0.8)' }
        };
        
        var trace2 = {
            x: vendasMensais.meses,
            y: vendasMensais.quantidades,
            yaxis: 'y2',
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Quantidade',
            line: { color: 'rgba(255, 193, 7, 1)' }
        };
        
        var layout1 = {
            title: 'Evolução de Vendas',
            xaxis: { title: 'Mês' },
            yaxis: { title: 'Valor (R$)', side: 'left' },
            yaxis2: { title: 'Quantidade', side: 'right', overlaying: 'y' },
            showlegend: true,
            margin: { t: 50, b: 50, l: 80, r: 80 }
        };
        
        Plotly.newPlot('vendas-mensais-chart', [trace1, trace2], layout1, {responsive: true});

        // Gráfico VSO
        var vsoData = {{ vso_chart_data|tojson }};
        
        var trace3 = {
            x: vsoData.meses,
            y: vsoData.vso_tickets,
            type: 'bar',
            name: 'VSO Ticket Médio',
            marker: { color: 'rgba(23, 162, 184, 0.8)' }
        };
        
        var layout2 = {
            title: 'VSO Ticket Médio',
            xaxis: { title: 'Mês' },
            yaxis: { title: 'Valor (R$)' },
            showlegend: false,
            margin: { t: 50, b: 50, l: 60, r: 20 }
        };
        
        Plotly.newPlot('vso-chart', [trace3], layout2, {responsive: true});

        // Gráfico Prosoluto
        var prosolutData = {{ prosoluto_chart_data|tojson }};
        
        var trace4 = {
            x: prosolutData.meses,
            y: prosolutData.valores_prosoluto,
            type: 'bar',
            name: 'Valor Prosoluto',
            marker: { color: 'rgba(220, 53, 69, 0.8)' }
        };
        
        var layout3 = {
            title: 'Evolução do Prosoluto',
            xaxis: { title: 'Mês' },
            yaxis: { title: 'Valor (R$)' },
            showlegend: false,
            margin: { t: 50, b: 50, l: 60, r: 20 }
        };
        
        Plotly.newPlot('prosoluto-chart', [trace4], layout3, {responsive: true});

        // Auto-refresh a cada 10 minutos
        setTimeout(function() {
            location.reload();
        }, 600000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Dashboard principal focado em análises de vendas"""
    try:
        # Carregar todos os dados necessários
        kpis = dashboard_data.get_kpis()
        vendas_mensais_chart_data = dashboard_data.get_vendas_mensais_chart_data()
        vso_chart_data = dashboard_data.get_vso_chart_data()
        prosoluto_chart_data = dashboard_data.get_prosoluto_chart_data()
        top_empreendimentos = dashboard_data.get_top_empreendimentos()
        top_corretores = dashboard_data.get_top_corretores()
        vendas_por_time = dashboard_data.get_vendas_por_time()
        sync_status = dashboard_data.get_sync_status()
        
        return render_template_string(
            DASHBOARD_TEMPLATE,
            kpis=kpis,
            vendas_mensais_chart_data=vendas_mensais_chart_data,
            vso_chart_data=vso_chart_data,
            prosoluto_chart_data=prosoluto_chart_data,
            top_empreendimentos=top_empreendimentos,
            top_corretores=top_corretores,
            vendas_por_time=vendas_por_time,
            sync_status=sync_status
        )
    except Exception as e:
        logging.error(f"Erro no dashboard: {e}")
        return f"Erro ao carregar dashboard de vendas: {e}", 500

@app.route('/health')
def health():
    """Health check para monitoring"""
    try:
        with dashboard_data.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "cvcrm-etl-dashboard"
        }), 200
        
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/kpis')
def api_kpis():
    """API endpoint para KPIs"""
    try:
        kpis = dashboard_data.get_kpis()
        return jsonify(kpis)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vendas-mensais')
def api_vendas_mensais():
    """API endpoint para dados de vendas mensais"""
    try:
        data = dashboard_data.get_vendas_mensais_chart_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tabela-geral-vendas')
def api_tabela_geral_vendas():
    """API endpoint para tabela geral de vendas"""
    try:
        with dashboard_data.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM vw_tabela_geral_vendas
                    ORDER BY data_venda DESC
                    LIMIT 1000
                """)
                
                vendas = cursor.fetchall()
                
                # Converter para formato JSON serializável
                result = []
                for venda in vendas:
                    item = dict(venda)
                    # Converter datas e decimais para string
                    for key, value in item.items():
                        if hasattr(value, 'isoformat'):
                            item[key] = value.isoformat()
                        elif hasattr(value, '__float__'):
                            item[key] = float(value) if value is not None else 0
                    result.append(item)
                
                return jsonify({
                    'total': len(result),
                    'vendas': result
                })
                
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/comparacao-anual')
def api_comparacao_anual():
    """API endpoint para comparação anual"""
    try:
        with dashboard_data.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM vw_vendas_ano_atual_vs_passado ORDER BY ano DESC")
                data = cursor.fetchall()
                
                return jsonify([dict(row) for row in data])
                
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('RAILWAY_ENVIRONMENT') != 'production'
    
    app.run(host='0.0.0.0', port=port, debug=debug)