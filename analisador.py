# ============================================
# ANALISADOR - POLYMARKET BOT
# Calcula score de confiança de cada mercado
# ============================================

import pandas as pd
import numpy as np
from datetime import datetime
import os
import json
from config import *

# ============================================
# CALCULAR SCORE PRINCIPAL
# ============================================
def calcular_score(mercado, noticias):
    """Calcula score de 0 a 100 para o mercado"""
    
    print(f"\n🧮 Analisando: {mercado['titulo'][:50]}...")
    
    # COMPONENTE 1 — Probabilidade (30 pontos)
    prob = mercado["probabilidade"]
    if 0.72 <= prob <= 0.80:
        score_prob = 30        # Zona ideal
    elif 0.80 < prob <= 0.85:
        score_prob = 20        # Bom mas retorno menor
    else:
        score_prob = 0         # Fora da zona
    
    # COMPONENTE 2 — Sentimento das notícias (25 pontos)
    score_sent = calcular_sentimento(noticias)
    
    # COMPONENTE 3 — Volume (20 pontos)
    volume = mercado["volume"]
    if volume >= 50000:
        score_volume = 20
    elif volume >= 30000:
        score_volume = 15
    elif volume >= 20000:
        score_volume = 10
    else:
        score_volume = 0
    
    # COMPONENTE 4 — Tempo restante (15 pontos)
    horas = mercado["horas_restantes"]
    if 72 <= horas <= 168:     # 3 a 7 dias — ideal
        score_tempo = 15
    elif 48 <= horas < 72:     # 2 a 3 dias — ok
        score_tempo = 10
    elif 168 < horas <= 336:   # 7 a 14 dias — aceitável
        score_tempo = 8
    else:
        score_tempo = 3
    
    # COMPONENTE 5 — Histórico da categoria (10 pontos)
    score_hist = calcular_historico(mercado["categoria"])
    
    # SCORE FINAL
    score_total = (
        score_prob +
        score_sent +
        score_volume +
        score_tempo +
        score_hist
    )
    
    detalhes = {
        "score_total": score_total,
        "score_probabilidade": score_prob,
        "score_sentimento": score_sent,
        "score_volume": score_volume,
        "score_tempo": score_tempo,
        "score_historico": score_hist,
        "aprovado": score_total >= SCORE_MINIMO,
        "analisado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Mostra resultado
    status = "✅ APROVADO" if detalhes["aprovado"] else "❌ REPROVADO"
    print(f"   Score: {score_total}/100 → {status}")
    print(f"   Prob: {score_prob} | Sent: {score_sent} | Vol: {score_volume} | Tempo: {score_tempo} | Hist: {score_hist}")
    
    salvar_analise(mercado, detalhes)
    return detalhes

# ============================================
# CALCULAR SENTIMENTO
# ============================================
def calcular_sentimento(noticias):
    """Converte sentimento das notícias em pontos"""
    if not noticias:
        return 0
    
    # Média dos sentimentos compostos
    sentimentos = [n.get("sentimento_composto", 0) for n in noticias]
    media = np.mean(sentimentos) if sentimentos else 0
    
    # Converte para pontos (0 a 25)
    if media >= 0.5:
        return 25    # Muito positivo
    elif media >= 0.2:
        return 20    # Positivo
    elif media >= 0.0:
        return 12    # Neutro
    elif media >= -0.2:
        return 6     # Levemente negativo
    else:
        return 0     # Muito negativo

# ============================================
# CALCULAR HISTÓRICO
# ============================================
def calcular_historico(categoria):
    """Verifica taxa de acerto histórica da categoria"""
    caminho = f"{PASTA_DADOS}/performance.csv"
    
    if not os.path.exists(caminho):
        return 5     # Sem histórico — pontuação neutra
    
    try:
        df = pd.read_csv(caminho)
        df_cat = df[df["categoria"] == categoria]
        
        if len(df_cat) < 5:
            return 5     # Poucos dados ainda
        
        taxa_acerto = df_cat["acertou"].mean()
        
        if taxa_acerto >= 0.75:
            return 10
        elif taxa_acerto >= 0.65:
            return 7
        elif taxa_acerto >= 0.55:
            return 4
        else:
            return 0
            
    except:
        return 5

# ============================================
# CONFIRMAÇÃO DUPLA
# ============================================
def confirmar_duas_vezes(mercado, noticias):
    """Analisa duas vezes com intervalo — segurança extra"""
    import time
    import random
    
    print("\n🔄 Primeira análise...")
    score1 = calcular_score(mercado, noticias)
    
    if not score1["aprovado"]:
        print("❌ Reprovado na primeira análise")
        return False
    
    # Aguarda entre 2 e 4 minutos (comportamento humano)
    espera = random.uniform(120, 240)
    print(f"\n⏳ Aguardando {espera/60:.1f} minutos para segunda análise...")
    time.sleep(espera)
    
    print("\n🔄 Segunda análise...")
    score2 = calcular_score(mercado, noticias)
    
    if not score2["aprovado"]:
        print("❌ Reprovado na segunda análise")
        return False
    
    # Verifica se os scores são consistentes
    diferenca = abs(score1["score_total"] - score2["score_total"])
    if diferenca > 10:
        print(f"⚠️ Scores inconsistentes ({diferenca} pontos de diferença) — descartado")
        return False
    
    print(f"✅ Confirmado nas duas análises! Score médio: {(score1['score_total'] + score2['score_total'])/2:.0f}")
    return True

# ============================================
# SALVAR ANÁLISE
# ============================================
def salvar_analise(mercado, detalhes):
    """Salva análise no CSV"""
    os.makedirs(PASTA_DADOS, exist_ok=True)
    caminho = f"{PASTA_DADOS}/analises.csv"
    
    registro = {**mercado, **detalhes}
    df_novo = pd.DataFrame([registro])
    
    if os.path.exists(caminho):
        df_existente = pd.read_csv(caminho)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
    else:
        df_final = df_novo
    
    df_final.to_csv(caminho, index=False)

# ============================================
# TESTE
# ============================================
if __name__ == "__main__":
    print("🧪 Testando analisador...")
    
    mercado_teste = {
        "id": "teste_001",
        "titulo": "Will the Fed cut rates in June 2026?",
        "probabilidade": 0.75,
        "volume": 35000,
        "horas_restantes": 120,
        "categoria": "economia"
    }
    
    noticias_teste = [
        {"sentimento_composto": 0.6},
        {"sentimento_composto": 0.4},
        {"sentimento_composto": 0.5}
    ]
    
    resultado = calcular_score(mercado_teste, noticias_teste)
    print(f"\n✅ Analisador funcionando!")