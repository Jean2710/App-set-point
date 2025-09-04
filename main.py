# ----------------------------
# Inicialização e instalação condicional
# ----------------------------
import streamlit as st
import sys
import subprocess

# Tenta importar plotly; se não estiver instalado, instala automaticamente
try:
    import plotly.express as px
    import plotly.graph_objects as go
    import plotly.io as pio
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly==6.3.0"])
    import plotly.express as px
    import plotly.graph_objects as go
    import plotly.io as pio

# ----------------------------
# Imports principais
# ----------------------------
st.set_page_config(page_title="Valve Calibration AB-QM", layout="wide")

import pandas as pd
import base64
from io import BytesIO
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from datetime import datetime
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
df_valvulas = pd.read_excel("tabela_valvulas.xlsx")
df_maquinas = pd.read_excel("Relação de capacidade das máquinas.xlsx")

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

# ----------------------------
# Seleção de capacidade
# ----------------------------
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
    10000: "DN 15 L/h",
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

# ----------------------------
# Setup de cores (fixo)
cor_titulo = "#ff0000"
cor_hover_logo = "#ff0000"
# ----------------------------
# Cabeçalho futurista
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
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px; background-color: #111; padding: 10px 15px; border-radius: 10px;">
    <img src="data:image/png;base64,{logo_base64}" class="logo-hover" style="max-height: 75px; width: auto; background: linear-gradient(135deg, #ffffff, #dddddd); padding: 5px; border-radius: 8px;" />
    <h1 style="margin: 0; font-size: 2.0rem; line-height: 1.2; animation: glow 3s infinite; font-family: 'Orbitron', monospace;">Valve Calibration AB-QM</h1>
</div>
""", unsafe_allow_html=True)

# ----------------------------
# Seleção de DN e vazão
col1_dn, col2_vaz = st.columns(2)
dn_choice = None  # valor padrão

with col1_dn:
    if selecao_cap != "Selecione...":
        wanted_dn_label = capacidade_to_dn.get(int(selecao_cap))
        
        # Ignora automaticamente DN que contenha "LF"
        if wanted_dn_label and "LF" not in wanted_dn_label:
            dn_choice_auto = find_matching_dn_column(wanted_dn_label, dn_options)
            if dn_choice_auto:
                dn_choice = dn_choice_auto
                st.success(f"DN selecionado automaticamente: **{dn_choice}**")
            else:
                dn_choice = st.selectbox("Escolha o DN", dn_options, key="dn_escolhido")
        else:
            dn_choice = st.selectbox("Escolha o DN", dn_options, key="dn_escolhido")
    else:
        dn_choice = st.selectbox("Escolha o DN", dn_options, key="dn_escolhido")

if dn_choice == "Selecione...":
    dn_choice = None

with col2_vaz:
    flow_m3h = st.number_input("Digite a vazão de projeto (m³/h):", min_value=0.0, step=0.01, key="flow_m3h")

# ----------------------------
# Multiselect para comparar DNs
# ----------------------------
with st.expander("Comparar múltiplos DNs"):
    dn_comparar = st.multiselect(
        "Comparar múltiplos DNs",
        options=dn_options,
        key="dn_comparativo"
    )

# ----------------------------
# Cálculo do ajuste
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
if ajuste and vazao_lh:
    st.markdown("### Resultado")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"💧 Vazão em m³/h: {vazao_m3h:.2f}")
    with col2:
        st.write(f"🔧 Ajuste recomendado: **{ajuste}%** → ({vazao_lh:.0f} L/h)")

# ----------------------------
# Gráfico interativo
# ----------------------------
with st.expander("📊 Visualizar curvas das válvulas"):
    if dn_choice:
        df_plot = df_valvulas[['Setting (%)', dn_choice]].copy()
        fig = px.line(df_plot, x='Setting (%)', y=dn_choice, markers=True,
                      labels={'Setting (%)':'Setting (%)', dn_choice:'Vazão (L/h)'},
                      title=f"Curva de ajuste {dn_choice}")
        # Ponto recomendado
        if ajuste and vazao_lh:
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
            if dn in df_valvulas.columns:
                df_tmp = df_valvulas[['Setting (%)', dn]].copy()
                fig.add_scatter(x=df_tmp['Setting (%)'], y=df_tmp[dn], mode='lines+markers', name=f"DN {dn}")
        fig.update_layout(template='plotly_dark', title_font=dict(family='Orbitron, monospace', size=22, color=cor_titulo),
                          legend=dict(title='Legenda', font=dict(family='Orbitron, monospace', size=12)),
                          xaxis=dict(title='Setting (%)', showgrid=True, gridcolor='#333'),
                          yaxis=dict(title='Vazão (L/h)', showgrid=True, gridcolor='#333'),
                          plot_bgcolor='#111111', paper_bgcolor='#111111')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Selecione um DN para visualizar o gráfico.")

# ----------------------------
# Tabela Neon
# ----------------------------
logo_base64_fab = carregar_logo_base64("logo_fabricante.png")
titulo_com_logo("Tabela de referência Danfoss (L/h)", logo_base64_fab, largura=70)
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
                styles.append(f"text-shadow: 0 0 {5*intensity}px {cor_titulo}; color: {cor_titulo};")
        else:
            styles.append("")
    return styles
st.dataframe(df_display.style.apply(neon_pulse_style, axis=1), hide_index=True)

# ----------------------------
# Exportação Excel
# ----------------------------
if ajuste and vazao_lh:
    excel_bytes = gerar_excel(df_display, ajuste, vazao_lh)
    st.download_button(
        label="📥 Baixar Excel",
        data=excel_bytes,
        file_name="valvula_resultado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ----------------------------
# Função PDF premium
# ----------------------------
def gerar_pdf_premium(dn_list, df_valvulas, observacao, ajuste=None, vazao_lh=None, logo_path="logo_fabricante.png"):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    story = []

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle('Titulo', parent=styles['Heading1'], textColor=colors.white,
                                  alignment=1, fontSize=18, spaceAfter=12)
    texto_style = ParagraphStyle('Texto', parent=styles['Normal'], textColor=colors.white, fontSize=10)

    # Logo no topo
    try:
        logo_bytes = open(logo_path, "rb").read()
        story.append(Image(BytesIO(logo_bytes), width=6*cm, height=3*cm))
        story.append(Spacer(1,12))
    except:
        story.append(Paragraph("⚠️ Logo não encontrada", texto_style))
        story.append(Spacer(1,12))

    # Título
    story.append(Paragraph("Relatório de Válvulas AB-QM", titulo_style))
    story.append(Spacer(1,12))

    # Gráfico
    if dn_list:
        fig = go.Figure()
        for dn_choice in dn_list:
            if dn_choice in df_valvulas.columns:
                fig.add_trace(go.Scatter(
                    x=df_valvulas["Setting (%)"], y=df_valvulas[dn_choice],
                    mode='lines+markers', name=f"DN {dn_choice}"
                ))
        # Ponto recomendado
        if ajuste and vazao_lh:
            for dn_choice in dn_list:
                if dn_choice in df_valvulas.columns:
                    idx = (df_valvulas[dn_choice] - vazao_lh).abs().idxmin()
                    fig.add_scatter(
                        x=[df_valvulas.loc[idx, 'Setting (%)']],
                        y=[df_valvulas.loc[idx, dn_choice]],
                        mode='markers+text',
                        marker=dict(color='red', size=14, symbol='star'),
                        text=[f"💧 {vazao_lh:.0f} L/h"],
                        textposition='top center',
                        name='Ponto recomendado'
                    )
        fig.update_layout(template="plotly_dark", width=800, height=400,
                          xaxis_title="Setting (%)", yaxis_title="Vazão (L/h)")
        try:
            img_bytes = pio.to_image(fig, format="png")
            story.append(Image(BytesIO(img_bytes), width=16*cm, height=10*cm))
            story.append(Spacer(1,12))
        except:
            story.append(Paragraph("⚠️ Gráfico não pôde ser gerado", texto_style))
            story.append(Spacer(1,12))

    # Tabela de DNs
    if dn_list:
        df_pdf = df_valvulas[['Setting (%)'] + [dn for dn in dn_list if dn in df_valvulas.columns]].copy()
        data_table = [df_pdf.columns.tolist()] + df_pdf.values.tolist()
        table = Table(data_table, repeatRows=1)
        # Estilo tabela
        styles_table = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#222222')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.gray),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#111111')),
            ('TEXTCOLOR', (0,1), (-1,-1), colors.white)
        ])
        # Destaque do ponto recomendado
        if ajuste and vazao_lh:
            for dn_choice in dn_list:
                if dn_choice in df_pdf.columns:
                    col_idx = df_pdf.columns.get_loc(dn_choice)
                    row_idx = (df_pdf[dn_choice] - vazao_lh).abs().idxmin() + 1
                    styles_table.add('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#00ffea'))
                    styles_table.add('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), colors.black)
        table.setStyle(styles_table)
        story.append(table)
        story.append(Spacer(1,12))

    # Observações
    if observacao:
        story.append(Paragraph(f"Observações: {observacao}", texto_style))
        story.append(Spacer(1,12))

    # Rodapé e fundo
    def add_footer(canvas, doc):
        canvas.setFillColor(colors.black)
        canvas.rect(0,0,doc.pagesize[0],doc.pagesize[1], stroke=0, fill=1)
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(doc.pagesize[0]-1*cm, 1*cm, f"Gerado em: {data_hora}")

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return buffer.getvalue()

# ----------------------------
# Exportação PDF com fallback DN
# ----------------------------
st.sidebar.header("Exportação")
observacao = st.sidebar.text_area("Observações para incluir no PDF:")

if st.sidebar.button("📄 Exportar PDF"):
    dn_para_pdf = st.session_state["dn_comparativo"].copy()
    
    if not dn_para_pdf:
        dn_para_pdf = [dn_choice] if dn_choice else []
    
    if dn_para_pdf:
        pdf_bytes = gerar_pdf_premium(dn_para_pdf, df_valvulas, observacao, ajuste, vazao_lh)
        st.download_button(
            label="📥 Baixar PDF",
            data=pdf_bytes,
            file_name="relatorio_valvulas.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("Nenhum DN disponível para gerar o PDF.")
# ----------------------------

# Botão para limpar seleções
def limpar_selecoes():
    st.session_state["selecao_cap"] = "Selecione..."
    st.session_state["dn_escolhido"] = "Selecione..."
    st.session_state["dn_comparativo"] = []
    st.session_state["flow_m3h"] = 0.0

st.sidebar.button("🧹 Limpar seleções", on_click=limpar_selecoes)


