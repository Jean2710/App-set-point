import streamlit as st
import math

st.set_page_config(page_title="Cálculo de Vazão", layout="wide")

st.title("💧 Cálculo de Vazão")

st.markdown("### Insira os parâmetros para calcular a vazão:")

# Entradas do usuário
diametro = st.number_input("Diâmetro interno do tubo (mm)", min_value=1.0, step=0.1)
velocidade = st.number_input("Velocidade do fluido (m/s)", min_value=0.0, step=0.1)
densidade = st.number_input("Densidade do fluido (kg/m³)", min_value=0.0, step=0.1, value=1000.0)

# Cálculo da área da seção transversal
if diametro > 0 and velocidade > 0:
    area = math.pi * (diametro/1000 / 2) ** 2  # área em m²
    vazao_m3h = area * velocidade * 3600       # m³/h
    vazao_lh = vazao_m3h * 1000                # L/h
    massa_kg_h = vazao_m3h * densidade         # kg/h

    st.markdown("### 🔎 Resultados")
    st.write(f"Área da seção: **{area:.6f} m²**")
    st.write(f"Vazão volumétrica: **{vazao_m3h:.2f} m³/h**  |  **{vazao_lh:.0f} L/h**")
    st.write(f"Vazão mássica: **{massa_kg_h:.2f} kg/h**")
else:
    st.info("Informe diâmetro e velocidade maiores que zero para calcular.")
