# ============================================
# MAIN - POLYMARKET BOT
# Orquestra todos os módulos
# ============================================

import time
import random
import schedule
import os
from datetime import datetime
import pandas as pd

from config import *
from coletor import buscar_mercados, buscar_noticias
from analisador import confirmar_duas_vezes, calcular_score
from protetor import (
    calcular_aposta, verificar_stop_loss,
    verificar_erros_consecutivos, registrar_trade,
    calcular_capital_atual, relatorio_rapido,
    registrar_evento
)

# ============================================
# VERIFICAR HORÁRIO DE OPERAÇÃO
# ============================================
def horario_permitido():
    """Verifica se está no horário de operar"""
    agora = datetime.now()
    hora_atual = agora.hour
    dia_semana = agora.weekday()
    
    if dia_semana not in DIAS_OPERANDO:
        print("📅 Final de semana — bot em repouso")
        return False
    
    if not (HORARIO_INICIO <= hora_atual < HORARIO_FIM):
        print(f"🕐 Fora do horário ({hora_atual}h) — aguardando...")
        return False
    
    return True

# ============================================
# CONTAR TRADES DE HOJE
# ============================================
def trades_hoje():
    """Conta quantos trades foram feitos hoje"""
    caminho = f"{PASTA_DADOS}/trades.csv"
    
    if not os.path.exists(caminho):
        return 0
    
    try:
        df = pd.read_csv(caminho)
        hoje = datetime.now().strftime("%Y-%m-%d")
        return len(df[df["data"].str.startswith(hoje)])
    except:
        return 0

# ============================================
# PAUSA HUMANA
# ============================================
def pausar(motivo=""):
    """Pausa com comportamento humano natural"""
    segundos = random.gauss(
        (PAUSA_MINIMA_SEGUNDOS + PAUSA_MAXIMA_SEGUNDOS) / 2,
        60
    )
    segundos = max(PAUSA_MINIMA_SEGUNDOS, min(segundos, PAUSA_MAXIMA_SEGUNDOS))
    
    if motivo:
        print(f"⏳ {motivo} — aguardando {segundos/60:.1f} minutos...")
    
    time.sleep(segundos)

# ============================================
# CICLO PRINCIPAL
# ============================================
def ciclo_principal():
    """Executa um ciclo completo de análise"""
    
    print("\n" + "="*50)
    print(f"🤖 CICLO INICIADO — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("="*50)
    
    # Verifica horário
    if not horario_permitido():
        return
    
    # Verifica capital atual
    capital_atual = calcular_capital_atual()
    
    # Verifica stop loss
    parar, motivo = verificar_stop_loss(CAPITAL_INICIAL, capital_atual)
    if parar:
        print(f"🛑 Bot pausado por stop loss ({motivo})")
        registrar_evento("BOT_PAUSADO", f"Stop loss {motivo}")
        return
    
    # Verifica erros consecutivos
    pausar_erros, num_erros = verificar_erros_consecutivos()
    if pausar_erros:
        print(f"⚠️ Pausado por {num_erros} erros consecutivos")
        return
    
    # Verifica limite diário
    total_hoje = trades_hoje()
    if total_hoje >= TRADES_POR_DIA:
        print(f"📊 Limite diário atingido ({total_hoje} trades) — descansando")
        return
    
    # Mostra situação atual
    relatorio_rapido()
    
    # Pausa humana antes de buscar
    pausar("Preparando busca de mercados")
    
    # Busca mercados
    mercados = buscar_mercados()
    
    if not mercados:
        print("😴 Nenhum mercado válido agora — tentando mais tarde")
        return
    
    print(f"\n🎯 {len(mercados)} mercados para analisar")
    
    # Embaralha para não seguir padrão
    random.shuffle(mercados)
    
    # Analisa cada mercado
    for mercado in mercados[:5]:  # Máximo 5 por ciclo
        
        # Verifica limite diário novamente
        if trades_hoje() >= TRADES_POR_DIA:
            print("📊 Limite diário atingido — encerrando ciclo")
            break
        
        # Pausa humana entre análises
        pausar(f"Analisando {mercado['titulo'][:30]}...")
        
        # Busca notícias
        noticias = buscar_noticias(mercado)
        
        # Pausa humana
        pausar()
        
        # Confirmação dupla (segurança máxima)
        aprovado = confirmar_duas_vezes(mercado, noticias)
        
        if not aprovado:
            print(f"⏭️ Mercado não aprovado — próximo")
            continue
        
        # Calcula aposta
        odd_retorno = (1 - mercado["probabilidade"]) / mercado["probabilidade"]
        valor_aposta = calcular_aposta(
            capital_atual,
            mercado["probabilidade"],
            odd_retorno
        )
        
        if valor_aposta <= 0:
            print("⚠️ Valor de aposta inválido — pulando")
            continue
        
        # LOG ANTES DE EXECUTAR
        print("\n" + "="*40)
        print("🎯 OPORTUNIDADE ENCONTRADA")
        print("="*40)
        print(f"Mercado:      {mercado['titulo'][:45]}")
        print(f"Categoria:    {mercado['categoria']}")
        print(f"Probabilidade: {mercado['probabilidade']:.1%}")
        print(f"Volume:       ${mercado['volume']:,.0f}")
        print(f"Valor aposta: ${valor_aposta:.2f}")
        print(f"Retorno pot.: ${valor_aposta * odd_retorno:.2f}")
        print("="*40)
        
        # MODO SIMULAÇÃO — registra sem executar de verdade
        # Quando tiver as keys do Polymarket, troca por execução real
        print("📝 MODO SIMULAÇÃO — registrando trade...")
        
        # Simula resultado baseado na probabilidade
        import random as r
        acertou = r.random() < mercado["probabilidade"]
        
        if acertou:
            resultado = valor_aposta * odd_retorno
        else:
            resultado = -valor_aposta
        
        # Registra o trade
        registrar_trade(mercado, valor_aposta, resultado, acertou)
        
        # Atualiza capital
        capital_atual = calcular_capital_atual()
        
        # Pausa longa após trade (comportamento humano)
        pausa_pos_trade = PAUSA_ENTRE_TRADES_HORAS * 3600
        variacao = random.uniform(0.8, 1.2)
        print(f"😴 Descansando {PAUSA_ENTRE_TRADES_HORAS}h após trade...")
        time.sleep(min(pausa_pos_trade * variacao, 60))  # Cap em 60s no teste
        
        break  # Um trade por ciclo no modo conservador

    print(f"\n✅ Ciclo concluído — {datetime.now().strftime('%H:%M')}")

# ============================================
# AGENDAMENTO
# ============================================
def iniciar_agendamento():
    """Agenda ciclos ao longo do dia"""
    
    # Roda a cada 2 horas em horários naturais
    schedule.every(2).hours.do(ciclo_principal)
    
    print("⏰ Agendamento ativado — ciclo a cada 2 horas")
    print("🤖 Bot rodando... pressione Ctrl+C para parar\n")
    
    # Executa um ciclo imediatamente
    ciclo_principal()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# ============================================
# INICIAR BOT — MODO GITHUB ACTIONS
# Roda um ciclo e encerra
# ============================================
if __name__ == "__main__":
    print("="*50)
    print("🚀 POLYMARKET BOT — INICIANDO")
    print("="*50)
    print(f"Capital inicial: ${CAPITAL_INICIAL}")
    print(f"Risco por trade: {RISCO_POR_TRADE:.1%}")
    print(f"Stop loss:       {STOP_LOSS_GLOBAL:.1%}")
    print(f"Score mínimo:    {SCORE_MINIMO}/100")
    print(f"Modo:            SIMULAÇÃO")
    print("="*50)
    
    # Roda apenas um ciclo e encerra
    ciclo_principal()
    relatorio_rapido()
    print("\n✅ Ciclo concluído — bot encerrado")