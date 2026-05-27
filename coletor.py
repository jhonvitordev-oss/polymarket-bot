# ============================================
# COLETOR DE DADOS - POLYMARKET BOT
# Busca mercados e notícias gratuitamente
# ============================================

import requests
import feedparser
import pandas as pd
from datetime import datetime, timedelta
import time
import random
import os
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from config import *

# Analisador de sentimento
analisador_sentimento = SentimentIntensityAnalyzer()

# ============================================
# FONTES DE NOTÍCIAS GRÁTIS POR CATEGORIA
# ============================================
FONTES_RSS = {
    "politica": [
        "https://news.google.com/rss/search?q=politics+election&hl=en",
        "http://feeds.reuters.com/Reuters/PoliticsNews",
        "http://feeds.bbci.co.uk/news/politics/rss.xml"
    ],
    "economia": [
        "https://news.google.com/rss/search?q=economy+federal+reserve&hl=en",
        "http://feeds.reuters.com/reuters/businessNews",
        "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"
    ],
    "esportes": [
        "https://news.google.com/rss/search?q=sports+results&hl=en",
        "http://feeds.bbci.co.uk/sport/rss.xml",
        "https://www.espn.com/espn/rss/news"
    ]
}

# ============================================
# BUSCAR MERCADOS DO POLYMARKET
# ============================================
def buscar_mercados():
    """Busca mercados ativos no Polymarket"""
    print("\n🔍 Buscando mercados no Polymarket...")
    
    mercados_validos = []
    
    try:
        # Busca mercados ativos
        url = "https://gamma-api.polymarket.com/markets"
        params = {
            "active": True,
            "closed": False,
            "limit": 100
        }
        
        # Pausa humana antes de requisitar
        time.sleep(random.uniform(2, 5))
        
        resposta = requests.get(url, params=params, timeout=10)
        
        if resposta.status_code != 200:
            print(f"⚠️ Erro ao buscar mercados: {resposta.status_code}")
            return []
        
        mercados = resposta.json()
        
        agora = datetime.now()
        
        for mercado in mercados:
            try:
                # Pega probabilidade
                prob = float(mercado.get("outcomePrices", ["0"])[0])
                
                # Pega volume
                volume = float(mercado.get("volume", 0))
                
                # Pega data de resolução
                data_fim = mercado.get("endDate", "")
                if data_fim:
                    data_fim = datetime.fromisoformat(
                        data_fim.replace("Z", "+00:00")
                    ).replace(tzinfo=None)
                    horas_restantes = (data_fim - agora).total_seconds() / 3600
                else:
                    continue
                
                # Aplica filtros conservadores
                if (PROBABILIDADE_MINIMA <= prob <= PROBABILIDADE_MAXIMA and
                    volume >= VOLUME_MINIMO and
                    TEMPO_MINIMO_HORAS <= horas_restantes <= TEMPO_MAXIMO_DIAS * 24):
                    
                    mercados_validos.append({
                        "id": mercado.get("id", ""),
                        "titulo": mercado.get("question", ""),
                        "probabilidade": prob,
                        "volume": volume,
                        "horas_restantes": horas_restantes,
                        "categoria": detectar_categoria(mercado.get("question", "")),
                        "coletado_em": agora.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
            except Exception as e:
                continue
        
        print(f"✅ {len(mercados_validos)} mercados válidos encontrados")
        salvar_mercados(mercados_validos)
        return mercados_validos
        
    except Exception as e:
        print(f"❌ Erro na coleta: {e}")
        return []

# ============================================
# DETECTAR CATEGORIA DO MERCADO
# ============================================
def detectar_categoria(titulo):
    """Detecta categoria baseado no título"""
    titulo = titulo.lower()
    
    palavras_politica = ["election", "president", "vote", "congress", 
                         "senate", "trump", "biden", "government", "law"]
    palavras_economia = ["fed", "inflation", "gdp", "rate", "bitcoin", 
                         "crypto", "stock", "market", "economy", "dollar"]
    palavras_esportes = ["nba", "nfl", "soccer", "football", "basketball",
                         "championship", "win", "game", "match", "sport"]
    
    score_politica = sum(1 for p in palavras_politica if p in titulo)
    score_economia = sum(1 for p in palavras_economia if p in titulo)
    score_esportes = sum(1 for p in palavras_esportes if p in titulo)
    
    maximo = max(score_politica, score_economia, score_esportes)
    
    if maximo == 0:
        return "geral"
    elif maximo == score_politica:
        return "politica"
    elif maximo == score_economia:
        return "economia"
    else:
        return "esportes"

# ============================================
# BUSCAR NOTÍCIAS POR MERCADO
# ============================================
def buscar_noticias(mercado):
    """Busca notícias relacionadas ao mercado"""
    categoria = mercado.get("categoria", "geral")
    titulo = mercado.get("titulo", "")
    
    print(f"\n📰 Buscando notícias para: {titulo[:50]}...")
    
    noticias = []
    fontes = FONTES_RSS.get(categoria, FONTES_RSS["politica"])
    
    for fonte in fontes:
        try:
            # Pausa humana entre requisições
            time.sleep(random.uniform(1, 3))
            
            feed = feedparser.parse(fonte)
            
            for entrada in feed.entries[:5]:
                texto = f"{entrada.get('title', '')} {entrada.get('summary', '')}"
                
                # Analisa sentimento
                sentimento = analisador_sentimento.polarity_scores(texto)
                
                noticias.append({
                    "titulo": entrada.get("title", ""),
                    "fonte": fonte,
                    "sentimento_positivo": sentimento["pos"],
                    "sentimento_negativo": sentimento["neg"],
                    "sentimento_neutro": sentimento["neu"],
                    "sentimento_composto": sentimento["compound"],
                    "coletado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
        except Exception as e:
            continue
    
    print(f"✅ {len(noticias)} notícias coletadas")
    salvar_noticias(noticias, categoria)
    return noticias

# ============================================
# SALVAR DADOS
# ============================================
def salvar_mercados(mercados):
    """Salva mercados em CSV"""
    if not mercados:
        return
    
    caminho = f"{PASTA_DADOS}/mercados.csv"
    os.makedirs(PASTA_DADOS, exist_ok=True)
    
    df_novo = pd.DataFrame(mercados)
    
    if os.path.exists(caminho):
        df_existente = pd.read_csv(caminho)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
        df_final = df_final.drop_duplicates(subset=["id"])
    else:
        df_final = df_novo
    
    df_final.to_csv(caminho, index=False)
    print(f"💾 Mercados salvos em {caminho}")

def salvar_noticias(noticias, categoria):
    """Salva notícias em CSV"""
    if not noticias:
        return
    
    caminho = f"{PASTA_DADOS}/{categoria}/noticias.csv"
    os.makedirs(f"{PASTA_DADOS}/{categoria}", exist_ok=True)
    
    df_novo = pd.DataFrame(noticias)
    
    if os.path.exists(caminho):
        df_existente = pd.read_csv(caminho)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
    else:
        df_final = df_novo
    
    df_final.to_csv(caminho, index=False)

# ============================================
# TESTE DO COLETOR
# ============================================
if __name__ == "__main__":
    print("🤖 Testando coletor...")
    mercados = buscar_mercados()
    
    if mercados:
        print(f"\n📊 Primeiro mercado encontrado:")
        print(f"   Título: {mercados[0]['titulo']}")
        print(f"   Probabilidade: {mercados[0]['probabilidade']:.1%}")
        print(f"   Volume: ${mercados[0]['volume']:,.0f}")
        print(f"   Categoria: {mercados[0]['categoria']}")
        
        noticias = buscar_noticias(mercados[0])
        print(f"\n✅ Coletor funcionando perfeitamente!")
    else:
        print("⚠️ Nenhum mercado encontrado no momento")