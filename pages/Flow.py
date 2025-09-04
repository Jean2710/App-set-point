import streamlit as st
import math
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- Configuração do app ---
st.set_page_config(page_title="Flow Dashboard", layout="wide")

# --- Estilo Neon SCADA ---
st.markdown("""
<style>
body {background-color:#1e1e2f; color:#ffffff;}
.stMarkdown, .stDataFrame, .stNumberInput, .stSelectbox, .stCheckbox, .stButton {color:#ffffff;}
.card {border-radius:12px; padding:20px; font-weight:bold; text-align:center; margin-bottom:10px;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #00ffff;'>💧 Flow Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #aaaaaa;'>Visualização interativa e em tempo real</p>", unsafe_allow_html=True)

# --- Inicializa session_state para inputs ---
if 'diametro' not in st.session_state: st.session_state.diametro = 1.0
if 'velocidade' not in st.session_state: st.session_state.velocidade = 0.0
if 'densidade' not in st.session_state: st.session_state.densidade = 1000.0
if 'btu_choice' not in st.session_state: st.session_state.btu_choice = 10000

# --- Função para limpar inputs ---
def limpar_inputs():
    st.session_state.diametro = 1.0
    st.session_state.velocidade = 0.0
    st.session_state.densidade = 1000.0
    st.session_state.btu_choice = 10000

# --- Sidebar ---
with st.sidebar:
    st.header("Parâmetros do sistema")
    st.subheader("Capacidade térmica da máquina")
    capacidades_btu = [10000, 12000, 16000, 20000, 25000, 32000, 42000, 44000, 55000, 36000, 12000, 24000]
    btu_choice = st.selectbox("Btu/h", capacidades_btu, key='btu_choice')
    diametro = st.number_input("Diâmetro interno do tubo (mm)", min_value=1.0, step=0.01, key='diametro')
    velocidade = st.number_input("Velocidade do fluido (m/s)", min_value=0.0, step=0.01, key='velocidade')
    densidade = st.number_input("Densidade do fluido (kg/m³)", min_value=0, step=1, format="%d", key='densidade')
    st.subheader("Visualizações")
    mostrar_tabela = st.checkbox("Mostrar tabela detalhada", value=True)
    st.button("🧹 Limpar Inputs", on_click=limpar_inputs)

# --- Constantes ---
btu_to_kw = 0.000293
cp = 4186
delta_T = 5.5
rho = 1000

# --- Cálculo automático ---
p_kw = st.session_state.btu_choice * btu_to_kw
m_dot = (p_kw * 1000) / (cp * delta_T)
q_m3_s = m_dot / rho
q_m3_h = q_m3_s * 3600
q_l_h = q_m3_h * 1000
limite_min_lh = q_l_h * 0.8
limite_max_lh = q_l_h * 1.2

# --- Tipo de cálculo ---
use_manual = False
if st.session_state.diametro > 0 and st.session_state.velocidade > 0:
    st.success("✅ Cálculo realizado usando capacidade da máquina **e** inputs manuais.")
    use_manual = True
else:
    st.info("ℹ️ Cálculo realizado **somente a partir da capacidade térmica da máquina, aplicando a formula da termodinâmica sobre o conceito da convervação de energia**.")

# --- Cálculo manual ---
if use_manual:
    area = math.pi * (st.session_state.diametro/1000 / 2) ** 2
    vazao_m3s = area * st.session_state.velocidade
    vazao_m3h = vazao_m3s * 3600
    vazao_lh = vazao_m3h * 1000
    massa_kg_s = vazao_m3s * st.session_state.densidade
    massa_kg_h = massa_kg_s * 3600
else:
    area = vazao_m3h = vazao_lh = massa_kg_s = massa_kg_h = np.nan

# --- Funções SCADA ---
def cor_faixa(valor, minimo, maximo):
    if pd.isna(valor): return "⚪"
    elif valor < minimo: return "🔴"
    elif valor > maximo: return "🟠"
    else: return "🟢"

def faixa_gauge(valor, minimo, maximo):
    if pd.isna(valor): return "grey"
    elif valor < minimo: return "red"
    elif valor > maximo: return "orange"
    else: return "green"

def gauge_with_refs(valor, minimo, maximo, unidade, cor_numero, titulo):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=valor,
        number={'suffix':f' {unidade}','font':{'color':cor_numero,'size':24}},
        delta={'reference':maximo,'increasing':{'color':'#ff3333'}},
        title={'text': f"{titulo}<br><span style='font-size:0.8em;color:#aaaaaa'>Faixa: {minimo:.2f} – {maximo:.2f} {unidade}</span>",
               'font':{'size':20,'color':'#ffffff'}},
        gauge={
            'axis': {'range':[0, valor*1.5], 'tickcolor':'#ffffff', 'tickwidth':2},
            'bar': {'color':faixa_gauge(valor,minimo,maximo)},
            'steps': [
                {'range':[0,minimo],'color':'#ff1a1a'},
                {'range':[minimo,maximo],'color':'#33ff33'},
                {'range':[maximo,valor*1.5],'color':'#ffcc33'}
            ],
            'threshold': {'line':{'color':'#00ffff','width':4}, 'thickness':0.75,'value':maximo}
        }
    ))
    # Linha mínima neon
    fig.add_trace(go.Indicator(
        mode="gauge",
        value=valor,
        gauge={'axis':{'range':[0,valor*1.5],'visible':False},
               'threshold':{'line':{'color':'#ff00ff','width':4}, 'thickness':0.75,'value':minimo},
               'bar':{'color':'rgba(0,0,0,0)'}},
        domain={'x':[0,1],'y':[0,1]}
    ))
    fig.update_layout(paper_bgcolor="#1e1e2f", font={'color':'#ffffff'}, margin=dict(t=30,b=20,l=20,r=20))
    return fig

def card_neon(valor, minimo, maximo, unidade, emoji, cor_texto):
    status = cor_faixa(valor,minimo,maximo)
    return f"""
    <div class='card' style='background-color:#0a1f44; color:{cor_texto};'>
        {emoji}<br>
        <span style='font-size:24px;'>{valor:.2f} {unidade}</span><br>
        {status}<br>
        <span style='font-size:12px; color:#00ffff;'>Mín: {minimo:.2f}</span> |
        <span style='font-size:12px; color:#ff00ff;'>Máx: {maximo:.2f}</span>
    </div>
    """

# --- Sugestão automática de diâmetro ---
if q_m3_s > 0 and st.session_state.velocidade > 0:
    area_necessaria = q_m3_s / st.session_state.velocidade
    diametro_sugerido_mm = 2 * (area_necessaria / math.pi) ** 0.5 * 1000
    st.info(f"💡 Diâmetro sugerido: **{diametro_sugerido_mm:.1f} mm** (assumindo {st.session_state.velocidade:.1f} m/s)")

# --- Cartões neon ---
col1, col2, col3 = st.columns(3)
col1.markdown(card_neon(q_l_h, limite_min_lh, limite_max_lh, "L/h", "💧", "#00ffff"), unsafe_allow_html=True)
col2.markdown(card_neon(q_m3_h, limite_min_lh/1000, limite_max_lh/1000, "m³/h", "⚡", "#00ff00"), unsafe_allow_html=True)
col3.markdown(card_neon(m_dot, limite_min_lh/3600, limite_max_lh/3600, "kg/s", "🧪", "#ffcc33"), unsafe_allow_html=True)

# --- Gauges neon ---

st.markdown("<h3 style='text-align:center;color:#00ffff;'>📊 Flow verification</h3>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
col1.plotly_chart(gauge_with_refs(q_l_h,limite_min_lh,limite_max_lh,"L/h","#00ffff","Vazão em l/h"), use_container_width=True)
col2.plotly_chart(gauge_with_refs(q_m3_h,limite_min_lh/1000,limite_max_lh/1000,"m³/h","#00ff00","Vazão em m³/h"), use_container_width=True)
col3.plotly_chart(gauge_with_refs(m_dot,limite_min_lh/3600,limite_max_lh/3600,"kg/s","#ffcc33","Vazão em kg/s"), use_container_width=True)

# --- Legenda ---
st.markdown("<h4 style='color:#00ffff;'>📌 Legenda de Status</h4>", unsafe_allow_html=True)
st.markdown("""
<div style='display:flex; gap:40px; font-size:16px;'>
    <div>🔴 Valor abaixo do mínimo</div>
    <div>🟢 Valor dentro do limite</div>
    <div>🟠 Valor acima do máximo</div>
</div>
""", unsafe_allow_html=True)

# --- Tabela detalhada ---
if mostrar_tabela:
    unidades = ["Área da seção (m²)","Vazão m³/h","Vazão L/h","Vazão kg/h","Vazão kg/s"]
    manual = [area if use_manual else np.nan, vazao_m3h if use_manual else np.nan,
              vazao_lh if use_manual else np.nan, massa_kg_h if use_manual else np.nan,
              massa_kg_s if use_manual else np.nan]
    maquina = [np.nan, q_m3_h, q_l_h, q_m3_h*rho, m_dot]

    def status(val, minimo, maximo):
        if pd.isna(val): return "-"
        if val < minimo: return "🔴"
        elif val > maximo: return "🟠"
        else: return "🟢"

    df = pd.DataFrame({
        "Unidade": unidades,
        "Seleção Manual": [f"{v:.2f}" if pd.notna(v) else "-" for v in manual],
        "Status (Manual)": [status(v, limite_min_lh if i in [1,2,3] else np.nan, limite_max_lh if i in [1,2,3] else np.nan) for i,v in enumerate(manual)],
        "Seleção Máquina": [f"{v:.2f}" if pd.notna(v) else "-" for v in maquina],
        "Status (Máquina)": [status(v, limite_min_lh if i in [1,2,3] else np.nan, limite_max_lh if i in [1,2,3] else np.nan) for i,v in enumerate(maquina)]
    })

    st.markdown("<h3 style='color:#00ffff;'>🔎 Tabela Detalhada</h3>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)
