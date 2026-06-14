import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Painel Energético - Bar XYZ", layout="wide")

st.title("📊 Painel Energético - Bar XYZ")


uploaded_file = st.file_uploader("Carregar 'Dados_Consumo.xlsx'", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    cols = ['Valor Total Faturado', 'Valor ICMS', 'Valor PIS', 'Valor COFINS', 'Valor CIP/COSIP', 'Valor kwh medido', 'Valor Bandeira']
    df_grouped = df.groupby('Data da Fatura')[cols].sum().reset_index()
    df_grouped['Valor energia'] = df_grouped['Valor Total Faturado'] - (df_grouped['Valor ICMS'] + df_grouped['Valor PIS'] + df_grouped['Valor COFINS'] + df_grouped['Valor CIP/COSIP'] + df_grouped['Valor Bandeira'])
    
    media_historica = df_grouped['Valor Total Faturado'].mean()
    
    st.sidebar.header("⚙️ Simulador ")
    tempo_ligado = st.sidebar.slider('Tempo de Compressor Ligado (minutos por hora)', 0, 60, 30)
    fator_ciclo = tempo_ligado / 60
    horas_fritadeira = st.sidebar.slider("Horas Fritadeira/dia", 0, 12, 4)
    potencia_fritadeira = st.sidebar.slider("Potência Fritadeira (W)", 1000, 5000, 2500)
    dias_faturados = st.sidebar.slider("Número de dias faturados", 27 , 33, 30)
    bandeira = st.sidebar.selectbox("Bandeira Tarifária (R$)", ["Verde (0.00)", "Amarela (0.018)", "Vermelha P1 (0.039)", "Vermelha P2 (0.094)"])
    st.sidebar.info("**Tempo de Compressor:** Representa quantos minutos, dentro de uma hora, o motor da geladeira fica efetivamente ligado para manter a temperatura. O calor e a abertura frequente de portas fazem esse tempo aumentar.")
    st.sidebar.info("**Bandeira Tarifária:** Reflete o custo de geração de energia (uso de térmicas vs hidrelétricas). O valor adicional é aplicado por kWh consumido. É um fator externo que impacta a fatura independentemente da eficiência dos seus aparelhos.")
    
    adicional = float(bandeira.split("(")[1].replace(")", ""))
    
    # Cálculo Consumo Simulado (kWh/mês)

    qtd_lâmpadas = 15 # 15 Lâmpadas (20W cada) 8h de uso cada
    qtd_estufa_fria = 1 # 1 Estufa Fria (400W) 24h ligado
    hr_estufa_quente = 12 # 1 estufa quente (700W) 12h de uso
    qtd_geladeiras_tipo1 = 3 # 3 Geladeiras expositoras (400W cada)
    qtd_geladeiras_tipo2 = 1 # 1 Geladeira vertical (130W)
    qtd_freezer =  1 # 1 freezer horizontal (220W)
    hr_fritadeira = 4 # 1 Fritadeira (3.000W): 4 horas de uso
    hr_microondas = 2 # 1 Micro-ondas (1.200W): Estimado em 100W médios/hora, uso de 2 horas
    qtd_ventiladores = 4 # 4 Ventiladores (100W cada) 15h de uso cada
    qtd_tvs = 2 # 2 TVs (150W cada): 10 horas de uso cada


    consumo_diario = ((qtd_lâmpadas*20*8) + (qtd_geladeiras_tipo1*400*24*fator_ciclo+qtd_geladeiras_tipo2*130*24*fator_ciclo+qtd_freezer*220*24*fator_ciclo) + (qtd_ventiladores*100*15) + (qtd_estufa_fria*400*24) + (700*hr_estufa_quente) + (potencia_fritadeira*horas_fritadeira) + (100*hr_microondas) + (qtd_tvs*150*10)) / 1000
    consumo_mensal = consumo_diario * dias_faturados
    fatura_simulada = consumo_mensal * (0.85 + adicional) * 1.3 # Estimativa com impostos
    

    col1, col2, col3 = st.columns(3)
    col1.metric("Consumo mensal", f"{consumo_mensal:.2f} kWh")
    col2.metric("Fatura Simulada", f"R$ {fatura_simulada:.2f}")
    col3.metric("Média Histórica", f"R$ {media_historica:.2f}")


    def gerar_curva():
        horas = np.arange(24)
    # Refrigeração (Base)
        refrig = (5 * 300 * fator_ciclo) + 400
    # Cozinha (Picos)
        cozinha = np.where(((horas >= 11) & (horas < 14)) | ((horas >= 18) & (horas < 22)), potencia_fritadeira, 0) # fritadeira
        cozinha += np.where((horas >= 11) & (horas < 23), 1500, 0) # Estufa Quente
    # Iluminação e Conforto
        ilum = np.where((horas >= 17) | (horas < 1), 15 * 15, 0)
        conf = np.where((horas >= 10) | (horas < 1), 4 * 100, 0) + np.where((horas >= 12) | (horas < 1), 2 * 150, 0)
    
        return pd.DataFrame({'Hora': horas, 'Refrigeração': refrig, 'Cozinha': cozinha, 'Iluminação/Conforto': ilum + conf})

    df_sim = gerar_curva()
    st.subheader("Curva de Carga Simulada (W)")
    fig_sim = px.area(df_sim, x='Hora', y=['Refrigeração', 'Cozinha', 'Iluminação/Conforto'], 
                 labels={'value': 'Potência (W)'})
    st.plotly_chart(fig_sim, use_container_width=True)

    st.subheader("Carga diária estimada por categoria (kWh)")
    data_carga = pd.DataFrame({
        'Categoria': ['Refrigeração', 'Cozinha', 'Iluminação/Conforto'],
        'Consumo (kWh)': [(qtd_geladeiras_tipo1*400*24*fator_ciclo+qtd_geladeiras_tipo2*130*24*fator_ciclo+qtd_freezer*220*24*fator_ciclo)/1000, (potencia_fritadeira*horas_fritadeira + 700*hr_estufa_quente + 100*hr_microondas)/1000, (qtd_lâmpadas*20*8 + qtd_ventiladores*100*15 + qtd_tvs*150*10 + qtd_estufa_fria*400*24)/1000]
    })
    fig1 = px.pie(data_carga, values='Consumo (kWh)', names='Categoria', hole=0.4, color= 'Categoria')
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("histórico das faturas por composição (R$)")
    fig2 = px.bar(df_grouped.melt(id_vars='Data da Fatura', value_vars=['Valor energia', 'Valor ICMS', 'Valor PIS', 'Valor COFINS', 'Valor CIP/COSIP', 'Valor Bandeira']), 
                  x='Data da Fatura', y='value', color='variable', labels={'value': 'valor (R$)'})
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Por favor, importe o arquivo Excel para iniciar.")