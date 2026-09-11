import streamlit as st
import pysus
import pandas as pd
import os

st.set_page_config(
    page_title="TRANSITA // DATASUS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# ESTILIZAÇÃO CSS (DARK NEON)
# -------------------------------------------------------------
st.markdown("""
    <style>
    .stApp, header[data-testid="stHeader"] { background-color: #0b0f19 !important; }
    .main { background-color: #0b0f19 !important; }
    section[data-testid="stSidebar"] { background-color: #111625 !important; border-right: 1px solid #1e293b !important; }
    label, p, span, div { color: #e0e6ed !important; }
    .stSelectbox label, .stNumberInput label, .stMultiSelect label { color: #94a3b8 !important; font-weight: 700 !important; font-size: 0.8rem !important; text-transform: uppercase !important; }
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, input { background-color: #131b2e !important; border-color: #1e293b !important; color: #ffffff !important; border-radius: 6px !important; }
    span[data-baseweb="tag"] { background-color: #f43f5e !important; border-radius: 4px !important; }
    span[data-baseweb="tag"] span { color: #ffffff !important; }
    ul[data-baseweb="menu"] { background-color: #131b2e !important; border: 1px solid #1e293b !important; }
    li[data-baseweb="option"] { background-color: #131b2e !important; color: #e0e6ed !important; }
    li[data-baseweb="option"]:hover { background-color: #1e293b !important; }
    .transita-title { font-size: 2.2rem; font-weight: 900; letter-spacing: 2px; color: #00d8ff !important; text-transform: uppercase; }
    .transita-title span { color: #ffffff !important; }
    .transita-subtitle { font-size: 0.85rem; letter-spacing: 1.5px; color: #64748b !important; text-transform: uppercase; margin-bottom: 12px; }
    .transita-bar { height: 3px; width: 140px; background: linear-gradient(90deg, #00d8ff 0%, #f472b6 100%); margin-bottom: 25px; border-radius: 2px; }
    .transita-card { background-color: #131b2e; border: 1px solid #1e293b; border-radius: 8px; padding: 18px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4); margin-bottom: 15px; }
    .transita-metric-label { font-size: 0.75rem; color: #f43f5e !important; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
    .transita-metric-value { font-size: 1.8rem; color: #00d8ff !important; font-weight: 800; margin-top: 5px; }
    div.stButton > button { background: linear-gradient(90deg, #38bdf8 0%, #f472b6 100%) !important; color: #0b0f19 !important; font-weight: 800 !important; text-transform: uppercase !important; border: none !important; border-radius: 6px !important; padding: 12px 28px !important; }
    .section-title { color: #00d8ff !important; font-size: 1rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-top: 15px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# CABEÇALHO
st.markdown("""
    <div class="transita-title">TRANSITA <span>// DATASUS</span></div>
    <div class="transita-subtitle">SISTEMA DE CONSULTA DE DADOS ABERTOS DA SAÚDE</div>
    <div class="transita-bar"></div>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.markdown('<div class="section-title">CONFIGURAÇÕES</div>', unsafe_allow_html=True)
    base = st.selectbox("BASE DE DADOS:", ["sinasc", "sih", "sia", "sim", "sinan", "cnes"])
    uf = st.selectbox("ESTADO (UF):", ["RS", "SP", "RJ", "MG", "PR", "SC", "BA", "PE", "CE"])
    ano = st.number_input("ANO:", min_value=2010, max_value=2026, value=2023)
    
    bases_mensais = ["sih", "sia", "cnes"]
    usa_mes = base in bases_mensais
    mes = st.number_input("MÊS:", min_value=1, max_value=12, value=1, disabled=not usa_mes)
    
    cod_municipio = st.text_input("CÓDIGO IBGE DO MUNICÍPIO (OPCIONAL):", placeholder="Ex: 431490 para Porto Alegre")

    # FILTRO DE QUADRIMESTRE
    quadrimestre_sel = st.selectbox("QUADRIMESTRE:", ["Todos", "1º Quadrimestre (Jan-Abr)", "2º Quadrimestre (Mai-Ago)", "3º Quadrimestre (Set-Dez)"])

# FUNÇÃO AUXILIAR PARA DOWNLOAD E LEITURA (COMPATÍVEL COM PYSUS ATUAL)
def carregar_dados_pysus_mod(nome_base, estado, ano_val, mes_val=None):
    try:
        # Tenta a chamada dinâmica via módulo raiz (ex: pysus.sinasc ou pysus.sim)
        funcao_base = getattr(pysus, nome_base.lower())
        kwargs = {"state": estado, "year": ano_val}
        if mes_val and nome_base.lower() in bases_mensais: 
            kwargs["month"] = mes_val

        res = funcao_base(**kwargs)
        
        # Tratamento de retorno flexível (Objeto PySUS, lista de caminhos ou Dataframe)
        if isinstance(res, pd.DataFrame):
            return res

        paths = [res] if isinstance(res, str) else [p for p in res if isinstance(p, str)] if isinstance(res, list) else [res.path] if hasattr(res, 'path') else []
        df_list = []
        for path in paths:
            if os.path.exists(path):
                if path.endswith('.parquet'): 
                    df_list.append(pd.read_parquet(path))
                elif path.endswith('.csv') or path.endswith('.dbc'): 
                    df_list.append(pd.read_csv(path, low_memory=False))

        return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()
    except Exception as e:
        st.warning(f"Aviso ao carregar {nome_base.upper()}: {e}")
        return pd.DataFrame()

# FILTROS E ESTRATIFICAÇÃO SINASC
filtros_sinasc = {}
if base == "sinasc":
    st.markdown('<div class="section-title">FILTROS DE BUSCA // SINASC</div>', unsafe_allow_html=True)
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    
    with f_col1:
        sexo_sel = st.selectbox("SEXO DO NASCIDO:", ["Todos", "Masculino", "Feminino", "Ignorado"])
        if sexo_sel == "Masculino": filtros_sinasc["SEXO"] = ["1", 1]
        elif sexo_sel == "Feminino": filtros_sinasc["SEXO"] = ["2", 2]
        elif sexo_sel == "Ignorado": filtros_sinasc["SEXO"] = ["0", "9", 0, 9]

    with f_col2:
        parto_sel = st.selectbox("TIPO DE PARTO:", ["Todos", "Vaginal", "Cesáreo", "Ignorado"])
        if parto_sel == "Vaginal": filtros_sinasc["PARTO"] = ["1", 1]
        elif parto_sel == "Cesáreo": filtros_sinasc["PARTO"] = ["2", 2]
        elif parto_sel == "Ignorado": filtros_sinasc["PARTO"] = ["9", 9]

    with f_col3:
        gravidez_sel = st.selectbox("TIPO DE GRAVIDEZ:", ["Todos", "Única", "Dupla", "Tripla ou mais"])
        if gravidez_sel == "Única": filtros_sinasc["GRAVIDEZ"] = ["1", 1]
        elif gravidez_sel == "Dupla": filtros_sinasc["GRAVIDEZ"] = ["2", 2]
        elif gravidez_sel == "Tripla ou mais": filtros_sinasc["GRAVIDEZ"] = ["3", 3]

    with f_col4:
        raca_sel = st.multiselect("RAÇA/COR DA MÃE:", ["Branca", "Preta", "Amarela", "Parda", "Indígena"])
        mapa_raca = {"Branca": ["1", 1], "Preta": ["2", 2], "Amarela": ["3", 3], "Parda": ["4", 4], "Indígena": ["5", 5]}
        
        if raca_sel:
            codigos_raca = []
            for r in raca_sel:
                codigos_raca.extend(mapa_raca[r])
            filtros_sinasc["RACACOR"] = codigos_raca

# EXECUÇÃO E ESTRATIFICAÇÃO
st.markdown("<br>", unsafe_allow_html=True)
if st.button("FILTRAR E ESTRATIFICAR"):
    st.info(f"Buscando no servidor DATASUS // Base {base.upper()} ({uf} - {ano})...")
    try:
        df = carregar_dados_pysus_mod(base, uf, ano, mes if usa_mes else None)

        if not df.empty:
            # ESTRATIFICAÇÃO E FILTRO POR QUADRIMESTRE VIA DTNASC (DDMMAAAA)
            if "DTNASC" in df.columns:
                df["DTNASC_STR"] = df["DTNASC"].astype(str).str.zfill(8)
                df["MES_NASC"] = pd.to_numeric(df["DTNASC_STR"].str[2:4], errors="coerce")
                
                def extrair_quadrimestre(mes_val):
                    if pd.isna(mes_val): return "Não Informado"
                    if 1 <= mes_val <= 4: return "1º Quadrimestre"
                    elif 5 <= mes_val <= 8: return "2º Quadrimestre"
                    elif 9 <= mes_val <= 12: return "3º Quadrimestre"
                    return "Não Informado"

                df["QUADRIMESTRE"] = df["MES_NASC"].apply(extrair_quadrimestre)

                if quadrimestre_sel.startswith("1º"):
                    df = df[df["QUADRIMESTRE"] == "1º Quadrimestre"]
                elif quadrimestre_sel.startswith("2º"):
                    df = df[df["QUADRIMESTRE"] == "2º Quadrimestre"]
                elif quadrimestre_sel.startswith("3º"):
                    df = df[df["QUADRIMESTRE"] == "3º Quadrimestre"]

            # FILTRO POR MUNICÍPIO DE RESIDÊNCIA
            if cod_municipio.strip():
                col_mun = next((col for col in ["CODMUNRES", "CODMUNOCOR", "MUNICIP"] if col in df.columns), None)
                if col_mun:
                    df = df[df[col_mun].astype(str).str.contains(cod_municipio.strip())]

            if base == "sinasc":
                col_raca = "RACACORMAE" if "RACACORMAE" in df.columns else "RACACOR"

                # CÁLCULO DOS INDICADORES DE SAÚDE DA POPULAÇÃO NEGRA
                taxa_baixo_prenatal = None
                cmm_negras = None
                
                if col_raca in df.columns:
                    # Nascidos Vivos de Mães Negras (Preta = 2, Parda = 4)
                    df_negras = df[df[col_raca].astype(str).isin(["2", "4"])]
                    total_nascidos_vivos_negras = len(df_negras)
                    
                    # 1. % Baixo Pré-Natal (<4 consultas)
                    if "CONSULTAS" in df.columns and total_nascidos_vivos_negras > 0:
                        negras_baixo_prenatal = len(df_negras[df_negras["CONSULTAS"].astype(str).isin(["1", "2"])])
                        taxa_baixo_prenatal = (negras_baixo_prenatal / total_nascidos_vivos_negras) * 100

                    # 2. COEFICIENTE DE MORTALIDADE MATERNA NEGRA (Óbitos via SIM)
                    df_sim = carregar_dados_pysus_mod("sim", uf, ano)
                    if not df_sim.empty:
                        if cod_municipio.strip():
                            col_mun_sim = next((c for c in ["CODMUNRES", "CODMUNOCOR"] if c in df_sim.columns), None)
                            if col_mun_sim:
                                df_sim = df_sim[df_sim[col_mun_sim].astype(str).str.contains(cod_municipio.strip())]

                        col_raca_sim = "RACACOR" if "RACACOR" in df_sim.columns else "RACACORMAE"
                        df_sim_negras = df_sim[df_sim[col_raca_sim].astype(str).isin(["2", "4"])] if col_raca_sim in df_sim.columns else df_sim

                        # Identifica óbito materno na gestação/puerpério (OBITOMAT em ['1', '2'] ou CID-10 iniciada em 'O')
                        if "OBITOMAT" in df_sim_negras.columns:
                            obitos_maternos_negras = len(df_sim_negras[df_sim_negras["OBITOMAT"].astype(str).isin(["1", "2"])])
                        elif "CAUSABAS" in df_sim_negras.columns:
                            obitos_maternos_negras = len(df_sim_negras[df_sim_negras["CAUSABAS"].astype(str).str.startswith("O", na=False)])
                        else:
                            obitos_maternos_negras = 0

                        if total_nascidos_vivos_negras > 0:
                            cmm_negras = (obitos_maternos_negras / total_nascidos_vivos_negras) * 100000

                # Aplicação dos Filtros Selecionados pelo usuário no SINASC
                for coluna, valores in filtros_sinasc.items():
                    col_alvo = col_raca if coluna == "RACACOR" else coluna
                    if col_alvo in df.columns:
                        df = df[df[col_alvo].astype(str).isin([str(v) for v in valores])]

                # EXIBIÇÃO DOS CARDS DE MÉTRICAS
                st.markdown('<div class="section-title">INDICADORES SOCIOEPIDEMIOLÓGICOS</div>', unsafe_allow_html=True)
                m_col1, m_col2, m_col3 = st.columns(3)
                
                with m_col1:
                    val_prenatal = f"{taxa_baixo_prenatal:.2f}%" if taxa_baixo_prenatal is not None else "N/A"
                    st.markdown(f"""
                        <div class="transita-card">
                            <div class="transita-metric-label">% Mães Negras com < 4 Consultas Pré-Natal</div>
                            <div class="transita-metric-value">{val_prenatal}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                with m_col2:
                    val_cmm = f"{cmm_negras:.1f}" if cmm_negras is not None else "N/A"
                    st.markdown(f"""
                        <div class="transita-card">
                            <div class="transita-metric-label">Coef. Mortalidade Materna Negra</div>
                            <div class="transita-metric-value">{val_cmm} <span style="font-size:0.8rem; color:#64748b;">/ 100k</span></div>
                        </div>
                    """, unsafe_allow_html=True)

                with m_col3:
                    st.markdown(f"""
                        <div class="transita-card">
                            <div class="transita-metric-label">Total de Registros Analisados</div>
                            <div class="transita-metric-value">{len(df):,}</div>
                        </div>
                    """, unsafe_allow_html=True)

                # MÓDULO DE ESTRATIFICAÇÃO VISUAL
                st.markdown('<div class="section-title">ESTRATIFICAÇÃO DOS DADOS</div>', unsafe_allow_html=True)
                
                if "IDADEMAE" in df.columns:
                    df["IDADEMAE_NUM"] = pd.to_numeric(df["IDADEMAE"], errors="coerce")
                    bins = [0, 19, 29, 39, 100]
                    labels = ["Adolescente (<20)", "Jovem Adulta (20-29)", "Adulta (30-39)", "Maturidade (40+)"]
                    df["ESTRATO_IDADE"] = pd.cut(df["IDADEMAE_NUM"], bins=bins, labels=labels)

                col_est1, col_est2, col_est3, col_est4 = st.columns(4)
                
                with col_est1:
                    if "ESTRATO_IDADE" in df.columns:
                        st.markdown("**Faixa Etária da Mãe**")
                        estrato_idade = df["ESTRATO_IDADE"].value_counts().sort_index()
                        st.bar_chart(estrato_idade, color="#00d8ff")

                with col_est2:
                    if col_raca in df.columns:
                        st.markdown("**Distribuição por Raça/Cor**")
                        mapa_labels = {"1": "Branca", "2": "Preta", "3": "Amarela", "4": "Parda", "5": "Indígena"}
                        df_raca_plot = df[col_raca].astype(str).map(mapa_labels).value_counts()
                        st.bar_chart(df_raca_plot, color="#38bdf8")

                with col_est3:
                    if "QUADRIMESTRE" in df.columns:
                        st.markdown("**Nascimentos por Quadrimestre**")
                        df_quad_plot = df["QUADRIMESTRE"].value_counts()
                        st.bar_chart(df_quad_plot, color="#a855f7")

                with col_est4:
                    if "ESTRATO_IDADE" in df.columns and "PARTO" in df.columns:
                        st.markdown("**Taxa de Cesárea por Idade (%)**")
                        df_cesarea = df[df["PARTO"].astype(str) == "2"]
                        estrato_cesarea = (df_cesarea["ESTRATO_IDADE"].value_counts() / df["ESTRATO_IDADE"].value_counts()) * 100
                        st.bar_chart(estrato_cesarea, color="#f43f5e")

            st.markdown('<div class="section-title">REGISTROS LOCALIZADOS</div>', unsafe_allow_html=True)
            st.dataframe(df.head(10), use_container_width=True)

        else:
            st.warning("Nenhum dado retornado para os parâmetros selecionados.")
    except Exception as e:
        st.error(f"ERRO DE EXECUÇÃO: {e}")
