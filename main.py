import streamlit as st
import pandas as pd
import base64
from io import BytesIO
import re
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib import colors
# ----------------------------
# Funções auxiliares
# ----------------------------
def titulo_com_logo(texto: str, logo_base64: str, largura: int = 50):
    st.markdown(
        f"""
        <h3 style="display: flex; align-items: center;">
            <img src="data:image/png;base64,{logo_base64}" 
                 width="{largura}" style="margin-right:8px;">
            {texto}
        </h3>
        """,
        unsafe_allow_html=True
    )

def carregar_logo_base64(caminho: str) -> str:
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode()

def gerar_excel(df: pd.DataFrame, ajuste: int, vazao_lh: float):
    output = BytesIO()
    df_export = df.copy()
    resumo = pd.DataFrame({
        "Resumo Ajuste (%)": [f"Ajuste recomendado: {ajuste}%"],
        "Resumo Vazão (L/h)": [f"Vazão L/h: {vazao_lh:.2f}"]
    })
    df_export = pd.concat([df_export, resumo], axis=1)
    df_export.to_excel(output, index=False)
    return output.getvalue()

def normalize_label(label):
    return re.sub(r'[^a-z0-9]', '', str(label).lower())

def find_matching_dn_column(dn_label, dn_options):
    if dn_label is None: return None
    dn_norm = normalize_label(dn_label)
    for col in dn_options:
        if dn_norm in normalize_label(col):
            return col
    return None

# ----------------------------
# Carregar dados
# ----------------------------
df_valvulas = pd.read_excel("C:/Users/user/Desktop/app.setpoint/tabela_valvulas.xlsx")
df_maquinas = pd.read_excel("C:/Users/user/desktop/app.setpoint/Relação de capacidade das máquinas.xlsx")

# ----------------------------
# Processar tabela válvulas
# ----------------------------
if 'Setting (%)' in df_valvulas.columns:
    df_valvulas['Setting (%)'] = (
        df_valvulas['Setting (%)']
        .astype(str)
        .str.replace('%', '', regex=True)
        .astype(float)
        .round()
        .astype(int)
    )
    dn_options = [col for col in df_valvulas.columns if col != "Setting (%)"]
    df_valvulas[dn_options] = df_valvulas[dn_options].apply(pd.to_numeric, errors='coerce')
else:
    st.error("A tabela de válvulas não contém a coluna 'Setting (%)'. Verifique o arquivo Excel.")
    st.stop()

# ----------------------------
# Sidebar com logo e cores
# ----------------------------
logo_sidebar = carregar_logo_base64("maquina.png")
st.sidebar.markdown(
    f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="data:image/png;base64,{logo_sidebar}" width="200" style="cursor:pointer;">
        <p style="font-size: 14px; color: #888;">Setpoint Tools</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Seleção de capacidade
# ----------------------------
st.sidebar.markdown("## Seleção da capacidade")
unique_caps = sorted(pd.Series(df_maquinas["Capacidade (Btuh)"].dropna().unique()).astype(int).tolist())
opcoes_capacidades = ["Selecione..."] + unique_caps

if "selecao_cap" not in st.session_state:
    st.session_state["selecao_cap"] = "Selecione..."

selecao_cap = st.sidebar.selectbox(
    "Capacidade (Btu/h)", 
    opcoes_capacidades, 
    index=opcoes_capacidades.index(st.session_state["selecao_cap"])
)
st.session_state["selecao_cap"] = selecao_cap

capacidade_to_dn = {
    10000: "DN 15",
    12000: "DN 15 HF",
    16000: "DN 15 HF",
    20000: "DN 15 HF",
    24000: "DN 15 HF",
    25000: "DN 15 HF",
    32000: "DN 20 HF",
    36000: "DN 20 HF",
    42000: "DN 32",
    44000: "DN 32",
    55000: "DN 32"
}

st.sidebar.markdown("## Setup de cores")
opcoes_cores = ["#00ffea", "#ff00ff", "#00ff00", "#ff0000"]
cor_titulo = st.sidebar.selectbox("Seleção da cor do título", opcoes_cores)
cor_hover_logo = st.sidebar.selectbox("Seleção da cor da logo", opcoes_cores)

# ----------------------------
# Cabeçalho futurista
# ----------------------------
logo_path = "valvula.png"
logo_base64 = carregar_logo_base64(logo_path)

st.markdown(f"""
<style>
@keyframes glow {{
    0% {{ text-shadow: 0 0 5px {cor_titulo}, 0 0 10px {cor_titulo}, 0 0 15px {cor_titulo}; color: {cor_titulo}; }}
    50% {{ text-shadow: 0 0 15px {cor_titulo}, 0 0 30px {cor_titulo}, 0 0 45px {cor_titulo}; color: {cor_titulo}; }}
    100% {{ text-shadow: 0 0 5px {cor_titulo}, 0 0 10px {cor_titulo}, 0 0 15px {cor_titulo}; color: {cor_titulo}; }}
}}
.logo-hover:hover {{
    transform: scale(1.15);
    filter: drop-shadow(0 0 15px {cor_hover_logo});
    transition: all 0.3s ease;
    cursor: pointer;
}}
</style>

<div style="
    display: flex; 
    align-items: center; 
    gap: 10px; 
    margin-bottom: 20px;
    background-color: #111; 
    padding: 10px 15px;
    border-radius: 10px;
">
    <img src="data:image/png;base64,{logo_base64}" 
         class="logo-hover"
         style="
            max-height: 75px; 
            width: auto; 
            background: linear-gradient(135deg, #ffffff, #dddddd); 
            padding: 5px; 
            border-radius: 8px;
         " />
    <h1 style="
        margin: 0; 
        font-size: 2.5rem; 
        line-height: 1.2; 
        animation: glow 3s infinite;
        font-family: 'Orbitron', monospace;
    ">
        Valve Calibration AB-QM
    </h1>
</div>
""", unsafe_allow_html=True)

# ----------------------------
# Botão para limpar seleções
# ----------------------------
def limpar_selecoes():
    st.session_state["selecao_cap"] = "Selecione..."
    st.session_state["dn_manual"] = None
    st.session_state["dn_manual_fallback"] = None
    st.session_state["dn_comparativo"] = []
    st.session_state["flow_m3h"] = 0.0

st.sidebar.button("🧹 Limpar seleções", on_click=limpar_selecoes)

# ----------------------------
# Seleção de DN e vazão
# ----------------------------
col1_dn, col2_vaz = st.columns(2)
with col1_dn:
    if selecao_cap != "Selecione...":
        wanted_dn_label = capacidade_to_dn.get(int(selecao_cap))
        dn_choice_auto = find_matching_dn_column(wanted_dn_label, dn_options)
        if dn_choice_auto:
            dn_choice = dn_choice_auto
            st.success(f"DN selecionado automaticamente: **{dn_choice}**")
        else:
            st.warning(f"DN automático '{wanted_dn_label}' não encontrado. Escolha manualmente:")
            dn_choice = st.selectbox("Escolha o DN", dn_options, key="dn_manual_fallback")
    else:
        dn_choice = st.selectbox("Escolha o DN", dn_options, key="dn_manual")

with col2_vaz:
    flow_m3h = st.number_input("Digite a vazão de projeto (m³/h):", min_value=0.0, step=0.01, key="flow_m3h")

# ----------------------------
# Multiselect para comparar DNs
# ----------------------------
with st.expander("Comparar múltiplos DNs"):
    if dn_options is not None:
        dn_comparar = st.multiselect(
            "Comparar múltiplos DNs",
            options=dn_options,
            key="dn_comparativo"
        )
    else:
        dn_comparar = []

# ----------------------------
# Cálculo do ajuste (dinâmico)
# ----------------------------
ajuste = None
vazao_lh = None

if dn_choice and flow_m3h > 0:
    flow_lh = flow_m3h * 1000
    melhor_linha = df_valvulas.iloc[(df_valvulas[dn_choice] - flow_lh).abs().argsort()[0]]
    ajuste = melhor_linha['Setting (%)']
    vazao_lh = melhor_linha[dn_choice]
    vazao_m3h = vazao_lh / 1000

# ----------------------------
# Mostrar resultados
# ----------------------------
if ajuste is not None and vazao_lh is not None:
    st.markdown("### Resultado")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"💧 Vazão em m³/h: {vazao_m3h:.2f}")
    with col2:
        st.write(f"🔧 Ajuste recomendado: **{ajuste}%** → ({vazao_lh:.0f} L/h)")

# ----------------------------
# ----------------------------
# Gráfico interativo aprimorado
with st.expander("Visualizar curvas das válvulas"):
    if dn_choice is not None and dn_choice != "":
        st.markdown("### Curvas das válvulas")
        df_plot = df_valvulas[['Setting (%)', dn_choice]].copy()
        
        fig = px.line(
            df_plot,
            x='Setting (%)',
            y=dn_choice,
            markers=True,
            labels={'Setting (%)':'Setting (%)', dn_choice:'Vazão (L/h)'},
            title=f"Curva de ajuste {dn_choice}"
        )
        
        # Ponto recomendado
        if ajuste is not None and vazao_lh is not None:
            # Encontrar índice da linha mais próxima da vazão
            idx = (df_plot[dn_choice] - vazao_lh).abs().idxmin()
            fig.add_scatter(
                x=[df_plot.loc[idx, 'Setting (%)']],
                y=[df_plot.loc[idx, dn_choice]],
                mode='markers+text',
                marker=dict(color='red', size=14, symbol='star'),
                text=[f"💧 {vazao_lh:.0f} L/h"],
                textposition='top center',
                name='Ponto recomendado'
            )

        # Comparar múltiplos DNs
        for dn in dn_comparar:
            if dn is not None and dn != "" and dn in df_valvulas.columns:
                df_tmp = df_valvulas[['Setting (%)', dn]].copy()
                fig.add_scatter(
                    x=df_tmp['Setting (%)'],
                    y=df_tmp[dn],
                    mode='lines+markers',
                    name=f"DN {dn}"
                )

        # Customizações visuais
        fig.update_layout(
            template='plotly_dark',
            title_font=dict(family='Orbitron, monospace', size=22, color=cor_titulo),
            legend=dict(title='Legenda', font=dict(family='Orbitron, monospace', size=12)),
            xaxis=dict(title='Setting (%)', showgrid=True, gridcolor='#333'),
            yaxis=dict(title='Vazão (L/h)', showgrid=True, gridcolor='#333'),
            plot_bgcolor='#111111',
            paper_bgcolor='#111111'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Selecione um DN para visualizar o gráfico.")


# ----------------------------
# Subheader da tabela
# ----------------------------
logo_base64_fab = carregar_logo_base64("logo_fabricante.png")
titulo_com_logo("Tabela de referência Danfoss (L/h)", logo_base64_fab, largura=70)

# ----------------------------
# Tabela Neon
# ----------------------------
df_display = df_valvulas.copy()
def neon_pulse_style(row):
    styles = []
    for col in df_display.columns:
        if col == dn_choice and ajuste is not None:
            if row[col] == vazao_lh:
                styles.append(f"background-color: {cor_titulo}; color: #000; font-weight: bold;")
            else:
                diff = abs(row[col] - vazao_lh)
                intensity = max(0, 1 - diff / vazao_lh)
                glow = f"text-shadow: 0 0 {5*intensity}px {cor_titulo}; color: {cor_titulo};"
                styles.append(glow)
        else:
            styles.append("")
    return styles

st.dataframe(df_display.style.apply(neon_pulse_style, axis=1), hide_index=True)

# ----------------------------
# Botão de exportação Excel
# ----------------------------
if ajuste is not None and vazao_lh is not None:
    st.markdown("### Exportar resultados")
    excel_bytes = gerar_excel(df_display, ajuste, vazao_lh)
    st.download_button(
        label="📥 Baixar Excel",
        data=excel_bytes,
        file_name="valvula_resultado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ---------------------------
# Função para rodapé e fundo
# ---------------------------
def add_footer_and_background(canvas, doc):
    # Fundo preto
    canvas.setFillColor(colors.black)
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], stroke=0, fill=1)

    # Texto do rodapé (data e hora)
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(doc.pagesize[0] - 1 * cm, 1 * cm, f"Gerado em: {data_hora}")

# ---------------------------
# Função para gerar PDF
# ---------------------------
def gerar_pdf_multiplos(dn_list, df_valvulas, observacao):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        'Titulo',
        parent=styles['Heading1'],
        textColor=colors.white,
        alignment=1,  # centralizado
        fontSize=16,
        spaceAfter=20
    )
    texto_style = ParagraphStyle(
        'Texto',
        parent=styles['Normal'],
        textColor=colors.white,
        fontSize=11
    )

    for dn_choice in dn_list:
        # Gera gráfico Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_valvulas["Setting (%)"],
            y=df_valvulas[dn_choice],
            mode='lines+markers',
            name=f"DN {dn_choice}"
        ))
        fig.update_layout(
            title=f"Curva de Vazão - DN {dn_choice}",
            xaxis_title="Setting (%)",
            yaxis_title="Vazão (L/h)",
            template="plotly_dark"
        )

        # Exporta gráfico como PNG
        img_bytes = pio.to_image(fig, format="png", width=800, height=500)

        # Adiciona ao PDF
        story.append(Paragraph(f"Relatório da Válvula DN {dn_choice}", titulo_style))
        if observacao:
            story.append(Paragraph(f"Observações: {observacao}", texto_style))
            story.append(Spacer(1, 12))
        story.append(Image(BytesIO(img_bytes), width=16*cm, height=10*cm))
        story.append(PageBreak())

    doc.build(story, onFirstPage=add_footer_and_background, onLaterPages=add_footer_and_background)
    buffer.seek(0)
    return buffer

# ---------------------------
# Streamlit
# ---------------------------
st.sidebar.header("Exportação")

# Campo de observação no APP
observacao = st.sidebar.text_area("Observações para incluir no PDF:")

if st.sidebar.button("📄 Exportar PDF"):
    if "dn_comparar" in st.session_state and st.session_state["dn_comparar"]:
        pdf_bytes = gerar_pdf_multiplos(st.session_state["dn_comparar"], df_valvulas, observacao)
        st.download_button(
            "📥 Baixar PDF",
            data=pdf_bytes,
            file_name="relatorio_valvulas.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("Selecione ao menos um DN para gerar o PDF.")









