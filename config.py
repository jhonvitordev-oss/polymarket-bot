# ============================================
# CONFIGURAÇÕES DO BOT - POLYMARKET
# PERFIL: CONSERVADOR / COMPORTAMENTO HUMANO
# ============================================

# CAPITAL E RISCO
CAPITAL_INICIAL = 100.00        # Seu capital em dólares
RISCO_POR_TRADE = 0.01          # 1% por trade (muito conservador)
STOP_LOSS_GLOBAL = 0.10         # Para tudo se perder 10%
STOP_LOSS_DIARIO = 0.03         # Para o dia se perder 3%

# FILTROS DE MERCADO (exigentes)
PROBABILIDADE_MINIMA = 0.72     # Só entra acima de 72%
PROBABILIDADE_MAXIMA = 0.85     # Evita retorno muito baixo
VOLUME_MINIMO = 20000           # Volume alto = mercado saudável
TEMPO_MINIMO_HORAS = 48         # Mínimo 48h para resolver
TEMPO_MAXIMO_DIAS = 21          # Máximo 21 dias

# SCORE DE CONFIANÇA (mais exigente)
SCORE_MINIMO = 80               # Aumentado para 80
PESO_PROBABILIDADE = 0.30
PESO_SENTIMENTO = 0.25
PESO_VOLUME = 0.20
PESO_TENDENCIA = 0.15
PESO_HISTORICO = 0.10

# COMPORTAMENTO HUMANO NATURAL
PAUSA_MINIMA_SEGUNDOS = 120     # Mínimo 2 minutos entre ações
PAUSA_MAXIMA_SEGUNDOS = 600     # Máximo 10 minutos entre ações
PAUSA_ENTRE_TRADES_HORAS = 4    # Mínimo 4h entre um trade e outro
TRADES_POR_DIA = 2              # Máximo 2 trades por dia
DIAS_OPERANDO = [0,1,2,3,4]     # Só segunda a sexta
HORARIO_INICIO = 10             # Começa às 10h
HORARIO_FIM = 20                # Para às 20h

# PROTEÇÃO EXTRA
MAX_TRADES_SIMULTANEOS = 1      # 1 trade por vez
ERROS_PARA_PAUSAR = 2           # Pausa após 2 erros seguidos
HORAS_PAUSA_APOS_ERRO = 24      # 24h de pausa após erros
ERROS_PARA_PARAR = 3            # Para completamente após 3 erros
CONFIRMACAO_DUPLA = True        # Confirma análise 2x antes de entrar
HORAS_ESTABILIDADE = 2          # Mercado estável por 2h antes de entrar

# DIVERSIFICAÇÃO
MAX_TRADES_POR_CATEGORIA = 1    # 1 trade por categoria ao mesmo tempo
CATEGORIAS_CORRELACIONADAS = [  # Nunca entra em paralelo
    ["politica_eua", "economia_eua"],
    ["esporte_time_a", "esporte_time_b"]
]

# PASTAS
PASTA_DADOS = "dados"
PASTA_LOGS = "logs"
PASTA_MODELO = "modelo"

# CATEGORIAS
CATEGORIAS = ["politica", "economia", "esportes"]
