# ============================================
# PROTETOR DE CAPITAL - POLYMARKET BOT
# Kelly Criterion + Stop Loss + Segurança
# ============================================

import pandas as pd
import os
from datetime import datetime, date
from config import *

# ============================================
# KELLY CRITERION
# ============================================
def calcular_kelly(probabilidade, odd_retorno):
    """Calcula tamanho ideal da aposta"""
    
    # Fórmula de Kelly
    q = 1 - probabilidade
    kelly = (probabilidade * odd_retorno - q) / odd_retorno
    
    # Usa Kelly fracionário (25%) — mais conservador
    kelly_fracionario = kelly * 0.25
    
    # Nunca ultrapassa 1% do capital
    kelly_final = min(kelly_fracionario, RISCO_POR_TRADE)
    
    # Nunca negativo
    kelly_final = max(kelly_final, 0)
    
    return kelly_final

# ============================================
# CALCULAR VALOR DA APOSTA
# ============================================
def calcular_aposta(capital_atual, probabilidade, odd_retorno):
    """Retorna valor exato a apostar em dólares"""
    
    percentual = calcular_kelly(probabilidade, odd_retorno)
    valor = capital_atual * percentual
    
    # Mínimo de $1 para entrar no Polymarket
    if valor < 1.0:
        print(f"⚠️ Aposta calculada (${valor:.2f}) abaixo do mínimo — ignorado")
        return 0
    
    print(f"💰 Aposta calculada: ${valor:.2f} ({percentual:.1%} do capital)")
    return round(valor, 2)

# ============================================
# VERIFICAR STOP LOSS
# ============================================
def verificar_stop_loss(capital_inicial, capital_atual):
    """Verifica se deve parar por stop loss"""
    
    perda = (capital_inicial - capital_atual) / capital_inicial
    
    # Stop loss global
    if perda >= STOP_LOSS_GLOBAL:
        print(f"🛑 STOP LOSS GLOBAL ATIVADO!")
        print(f"   Perda: {perda:.1%} do capital inicial")
        registrar_evento("STOP_LOSS_GLOBAL", f"Perda de {perda:.1%}")
        return True, "global"
    
    # Verifica stop loss diário
    perda_hoje = calcular_perda_hoje()
    if perda_hoje >= STOP_LOSS_DIARIO:
        print(f"🛑 STOP LOSS DIÁRIO ATIVADO!")
        print(f"   Perda hoje: {perda_hoje:.1%}")
        registrar_evento("STOP_LOSS_DIARIO", f"Perda de {perda_hoje:.1%} hoje")
        return True, "diario"
    
    return False, None

# ============================================
# CALCULAR PERDA DO DIA
# ============================================
def calcular_perda_hoje():
    """Calcula perda acumulada hoje"""
    caminho = f"{PASTA_DADOS}/trades.csv"
    
    if not os.path.exists(caminho):
        return 0
    
    try:
        df = pd.read_csv(caminho)
        hoje = date.today().strftime("%Y-%m-%d")
        df_hoje = df[df["data"].str.startswith(hoje)]
        
        if df_hoje.empty:
            return 0
        
        resultado_hoje = df_hoje["resultado_usd"].sum()
        capital = CAPITAL_INICIAL
        
        return max(0, -resultado_hoje / capital)
        
    except:
        return 0

# ============================================
# VERIFICAR ERROS CONSECUTIVOS
# ============================================
def verificar_erros_consecutivos():
    """Verifica se deve pausar por erros seguidos"""
    caminho = f"{PASTA_DADOS}/trades.csv"
    
    if not os.path.exists(caminho):
        return False, 0
    
    try:
        df = pd.read_csv(caminho)
        
        if df.empty:
            return False, 0
        
        # Pega últimos trades
        ultimos = df.tail(ERROS_PARA_PARAR)
        erros_seguidos = (ultimos["acertou"] == False).sum()
        
        if erros_seguidos >= ERROS_PARA_PARAR:
            print(f"⚠️ {erros_seguidos} erros consecutivos — pausando!")
            registrar_evento("PAUSA_ERROS", f"{erros_seguidos} erros seguidos")
            return True, erros_seguidos
            
        if erros_seguidos >= ERROS_PARA_PAUSAR:
            print(f"⚠️ {erros_seguidos} erros seguidos — pausa de 24h")
            return True, erros_seguidos
            
        return False, erros_seguidos
        
    except:
        return False, 0

# ============================================
# REGISTRAR TRADE
# ============================================
def registrar_trade(mercado, valor_apostado, resultado_usd, acertou):
    """Registra resultado do trade"""
    os.makedirs(PASTA_DADOS, exist_ok=True)
    caminho = f"{PASTA_DADOS}/trades.csv"
    
    registro = {
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mercado_id": mercado.get("id", ""),
        "titulo": mercado.get("titulo", "")[:50],
        "categoria": mercado.get("categoria", ""),
        "probabilidade": mercado.get("probabilidade", 0),
        "valor_apostado": valor_apostado,
        "resultado_usd": resultado_usd,
        "acertou": acertou,
        "capital_apos": calcular_capital_atual()
    }
    
    df_novo = pd.DataFrame([registro])
    
    if os.path.exists(caminho):
        df_existente = pd.read_csv(caminho)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
    else:
        df_final = df_novo
    
    df_final.to_csv(caminho, index=False)
    
    emoji = "✅" if acertou else "❌"
    print(f"{emoji} Trade registrado: {'+' if resultado_usd > 0 else ''}${resultado_usd:.2f}")

# ============================================
# CALCULAR CAPITAL ATUAL
# ============================================
def calcular_capital_atual():
    """Calcula capital atual baseado nos trades"""
    caminho = f"{PASTA_DADOS}/trades.csv"
    
    if not os.path.exists(caminho):
        return CAPITAL_INICIAL
    
    try:
        df = pd.read_csv(caminho)
        total_resultado = df["resultado_usd"].sum()
        return round(CAPITAL_INICIAL + total_resultado, 2)
    except:
        return CAPITAL_INICIAL

# ============================================
# REGISTRAR EVENTO
# ============================================
def registrar_evento(tipo, descricao):
    """Registra eventos importantes no log"""
    os.makedirs(PASTA_LOGS, exist_ok=True)
    caminho = f"{PASTA_LOGS}/eventos.csv"
    
    registro = {
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tipo": tipo,
        "descricao": descricao
    }
    
    df_novo = pd.DataFrame([registro])
    
    if os.path.exists(caminho):
        df_existente = pd.read_csv(caminho)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
    else:
        df_final = df_novo
    
    df_final.to_csv(caminho, index=False)

# ============================================
# RELATÓRIO RÁPIDO
# ============================================
def relatorio_rapido():
    """Mostra situação atual do capital"""
    capital_atual = calcular_capital_atual()
    lucro = capital_atual - CAPITAL_INICIAL
    percentual = (lucro / CAPITAL_INICIAL) * 100
    
    print("\n" + "="*40)
    print("📊 SITUAÇÃO ATUAL DO BOT")
    print("="*40)
    print(f"Capital inicial:  ${CAPITAL_INICIAL:.2f}")
    print(f"Capital atual:    ${capital_atual:.2f}")
    print(f"Resultado:        {'+' if lucro >= 0 else ''}${lucro:.2f} ({percentual:+.1f}%)")
    
    caminho = f"{PASTA_DADOS}/trades.csv"
    if os.path.exists(caminho):
        df = pd.read_csv(caminho)
        if not df.empty:
            acertos = df["acertou"].sum()
            total = len(df)
            print(f"Trades:           {total} ({acertos} acertos / {total-acertos} erros)")
            print(f"Taxa de acerto:   {acertos/total:.1%}")
    print("="*40)

# ============================================
# TESTE
# ============================================
if __name__ == "__main__":
    print("🧪 Testando protetor...")
    
    aposta = calcular_aposta(100, 0.75, 0.40)
    print(f"Aposta sugerida: ${aposta}")
    
    parar, motivo = verificar_stop_loss(100, 95)
    print(f"Stop loss: {parar} ({motivo})")
    
    relatorio_rapido()
    print("✅ Protetor funcionando!")