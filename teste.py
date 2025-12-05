import streamlit as st
import json
import os
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, Tuple, List

# ============================================================================
# CONFIGURAÇÕES E CONSTANTES
# ============================================================================

ARQUIVO_EMPRESAS = "empresas_cadastradas.json"

# ============================================================================
# FUNÇÕES DE PERSISTÊNCIA
# ============================================================================

def carregar_empresas() -> Dict:
    """Carrega as empresas cadastradas do arquivo JSON."""
    if os.path.exists(ARQUIVO_EMPRESAS):
        try:
            with open(ARQUIVO_EMPRESAS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erro ao carregar empresas: {e}")
            return {}
    return {}

def salvar_empresas(empresas: Dict) -> bool:
    """Salva as empresas no arquivo JSON."""
    try:
        with open(ARQUIVO_EMPRESAS, 'w', encoding='utf-8') as f:
            json.dump(empresas, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar empresas: {e}")
        return False

# ============================================================================
# FUNÇÕES DE CÁLCULO
# ============================================================================

def contar_dias_uteis(data_inicio: date, data_fim: date) -> int:
    """
    Conta dias úteis entre duas datas.
    Ignora apenas sábados e domingos.
    Feriados são considerados dias normais de trabalho.
    """
    if data_inicio > data_fim:
        return 0
    
    dias_uteis = 0
    data_atual = data_inicio
    
    while data_atual <= data_fim:
        if data_atual.weekday() < 5:  # Segunda a Sexta
            dias_uteis += 1
        data_atual += timedelta(days=1)
    
    return dias_uteis

def calcular_desconto_total(periodos_direito: List[Dict], periodos_afastamento: List[Dict], 
                           dias_base: int, valor_diario: float) -> Dict:
    """
    Calcula o desconto total baseado em múltiplos períodos.
    
    Args:
        periodos_direito: Lista de dicts com {mes, valor, dias}
        periodos_afastamento: Lista de dicts com {descricao, data_inicio, data_fim, dias}
        dias_base: Dias base da empresa
        valor_diario: Valor diário da empresa
    
    Returns:
        Dict com os totais calculados
    """
    total_dias_direito = sum(p['dias'] for p in periodos_direito)
    total_valor_direito = sum(p['valor'] for p in periodos_direito)
    total_dias_ausentes = sum(p['dias'] for p in periodos_afastamento)
    
    dias_trabalhados = total_dias_direito - total_dias_ausentes
    
    if dias_trabalhados >= dias_base:
        dias_a_descontar = 0
    else:
        dias_a_descontar = dias_base - dias_trabalhados
    
    dias_a_descontar = max(0, dias_a_descontar)
    valor_a_descontar = dias_a_descontar * valor_diario
    valor_final = total_valor_direito - valor_a_descontar
    
    return {
        'total_dias_direito': total_dias_direito,
        'total_valor_direito': total_valor_direito,
        'total_dias_ausentes': total_dias_ausentes,
        'dias_trabalhados': dias_trabalhados,
        'dias_a_descontar': dias_a_descontar,
        'valor_a_descontar': valor_a_descontar,
        'valor_final': valor_final
    }

def formatar_real(valor: float) -> str:
    """Formata número no padrão brasileiro R$ 1.234,56"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ============================================================================
# FUNÇÕES DE RELATÓRIO
# ============================================================================

def gerar_html_relatorio(calculos: list) -> str:
    """Gera o relatório completo em HTML."""
    
    html_completo = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Relatório de Descontos</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 900px;
                margin: 40px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .relatorio {
                background: white;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .cabecalho {
                background: #2c3e50;
                color: white;
                padding: 15px;
                margin: -30px -30px 20px -30px;
                text-align: center;
            }
            .secao-titulo {
                background: #34495e;
                color: white;
                padding: 10px 15px;
                margin: 20px 0 15px 0;
                font-weight: bold;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 15px;
            }
            td, th {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
                text-align: left;
            }
            .valor {
                text-align: right;
                font-weight: bold;
            }
            .total {
                background: #e74c3c;
                color: white;
                padding: 12px 15px;
                text-align: right;
                font-weight: bold;
                font-size: 1.1em;
                margin: 15px 0;
            }
            .total-direito {
                background: #27ae60;
                color: white;
                padding: 12px 15px;
                text-align: right;
                font-weight: bold;
                font-size: 1.1em;
                margin: 15px 0;
            }
            .observacao {
                background: #ecf0f1;
                padding: 15px;
                margin: 15px 0;
                font-style: italic;
                color: #555;
            }
            .info-reembolso {
                background: #3498db;
                color: white;
                padding: 12px 15px;
                margin: 15px 0;
            }
            .resumo-item {
                padding: 10px;
                background: #f8f9fa;
                margin-bottom: 8px;
                border-left: 4px solid #3498db;
            }
        </style>
    </head>
    <body>
    """
    
    for calc in calculos:
        html_completo += f"""
        <div class="relatorio">
            <div class="cabecalho">
                <h2>{calc['nome_funcionario'].upper()}</h2>
                <p style="margin: 5px 0 0 0;">Empresa: {calc['empresa']}</p>
            </div>
        """
        
        # Seção de DESCONTOS
        html_completo += """
            <div class="secao-titulo">PERÍODOS DE AFASTAMENTO</div>
            <table>
                <thead>
                    <tr>
                        <th>Descrição/Período</th>
                        <th style="text-align: center;">Dias</th>
                        <th style="text-align: right;">Valor Diário</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for periodo in calc['periodos_afastamento']:
            descricao = periodo['descricao']
            if periodo.get('data_inicio') and periodo.get('data_fim'):
                descricao += f" ({periodo['data_inicio']} a {periodo['data_fim']})"
            
            html_completo += f"""
                <tr>
                    <td>{descricao}</td>
                    <td style="text-align: center;">{periodo['dias']} dias</td>
                    <td class="valor">{formatar_real(calc['valor_diario'])}</td>
                </tr>
            """
        
        html_completo += "</tbody></table>"
        
        if calc.get('observacao'):
            html_completo += f"""
                <div class="observacao">
                    <strong>Observação:</strong> {calc['observacao']}
                </div>
            """
        
        html_completo += f"""
            <div class="total">
                SUBTOTAL DE DESCONTO: {calc['totais']['total_dias_ausentes']} dias = {formatar_real(calc['totais']['valor_a_descontar'])}
            </div>
        """
        
        # Seção VALORES QUE TEM DIREITO
        html_completo += """
            <div class="secao-titulo">VALORES QUE TEM DIREITO</div>
            <table>
                <thead>
                    <tr>
                        <th>Mês/Período</th>
                        <th style="text-align: center;">Dias</th>
                        <th style="text-align: right;">Valor</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for periodo in calc['periodos_direito']:
            html_completo += f"""
                <tr>
                    <td>{periodo['mes']}</td>
                    <td style="text-align: center;">{periodo['dias']} dias</td>
                    <td class="valor">{formatar_real(periodo['valor'])}</td>
                </tr>
            """
        
        html_completo += f"""
                </tbody>
            </table>
            
            <div class="total-direito">
                Total de direito: {formatar_real(calc['totais']['total_valor_direito'])}
            </div>
            
            <div class="info-reembolso">
                <strong>Valor de direito abatendo o valor descontado:</strong> {formatar_real(calc['totais']['valor_final'])}<br>
                <strong>Data de reembolso:</strong> {calc.get('data_reembolso', date.today().strftime('%d/%m/%Y'))}
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-left: 4px solid #2c3e50;">
                <strong>Resumo do Cálculo:</strong><br>
                • Total de dias de direito: {calc['totais']['total_dias_direito']} dias<br>
                • Total de dias ausentes: {calc['totais']['total_dias_ausentes']} dias<br>
                • Dias trabalhados: {calc['totais']['dias_trabalhados']} dias<br>
                • Dias-base da empresa: {calc['dias_base']} dias<br>
                • Dias a descontar: {calc['totais']['dias_a_descontar']} dias<br>
                • Valor diário: {formatar_real(calc['valor_diario'])}
            </div>
        </div>
        """
    
    html_completo += """
    </body>
    </html>
    """
    
    return html_completo

# ============================================================================
# INTERFACE
# ============================================================================

def renderizar_cadastro_empresas(empresas: Dict):
    """Renderiza a seção de cadastro de empresas."""
    st.subheader("Cadastro de Empresas")
    
    with st.form("form_empresa"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            nome_empresa = st.text_input("Nome da Empresa", placeholder="Ex: Empresa X")
        with col2:
            valor_diario = st.number_input("Valor Diário (R$)", 
                                          min_value=0.0, 
                                          value=79.24, 
                                          step=0.01,
                                          format="%.2f")
        with col3:
            dias_base = st.number_input("Dias-Base", 
                                       min_value=1, 
                                       value=21, 
                                       step=1)
        
        col_save, col_del = st.columns([1, 1])
        
        with col_save:
            submit = st.form_submit_button("Salvar/Atualizar", use_container_width=True)
        with col_del:
            delete = st.form_submit_button("Excluir", use_container_width=True, type="secondary")
        
        if submit:
            if not nome_empresa.strip():
                st.error("Nome da empresa é obrigatório")
            else:
                empresas[nome_empresa] = {
                    "valor_diario": valor_diario,
                    "dias_base": dias_base
                }
                if salvar_empresas(empresas):
                    st.success(f"Empresa '{nome_empresa}' salva com sucesso")
                    st.rerun()
        
        if delete:
            if nome_empresa in empresas:
                del empresas[nome_empresa]
                salvar_empresas(empresas)
                st.success(f"Empresa '{nome_empresa}' removida")
                st.rerun()
    
    if empresas:
        st.write("**Empresas cadastradas:**")
        for nome, dados in empresas.items():
            st.text(f"• {nome} — {formatar_real(dados['valor_diario'])}/dia — Base: {dados['dias_base']} dias")

def renderizar_calculo_individual(empresas: Dict):
    """Renderiza a seção de cálculo individual."""
    st.subheader("Cálculo Individual")
    
    if not empresas:
        st.warning("Cadastre pelo menos uma empresa antes de fazer cálculos")
        return
    
    # Inicializar listas no session_state
    if 'periodos_direito_temp' not in st.session_state:
        st.session_state.periodos_direito_temp = []
    if 'periodos_afastamento_temp' not in st.session_state:
        st.session_state.periodos_afastamento_temp = []
    
    col1, col2 = st.columns(2)
    
    with col1:
        nome_funcionario = st.text_input("Nome do Funcionário", placeholder="Ex: João Silva")
    
    with col2:
        empresa_selecionada = st.selectbox("Empresa", options=list(empresas.keys()))
    
    if empresa_selecionada:
        dados_empresa = empresas[empresa_selecionada]
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Valor Diário: {formatar_real(dados_empresa['valor_diario'])}")
        with col2:
            st.info(f"Dias-Base: {dados_empresa['dias_base']} dias")
        
        # ===== SEÇÃO: PERÍODOS DE DIREITO =====
        st.markdown("---")
        st.subheader("Períodos de Direito")
        
        with st.form("form_periodo_direito", clear_on_submit=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                mes_direito = st.text_input("Mês/Período", placeholder="Ex: Novembro/2024")
            
            with col2:
                metodo_calc_direito = st.selectbox("Cálculo", ["Manual", "Por Data"])
            
            with col3:
                if metodo_calc_direito == "Manual":
                    dias_direito = st.number_input("Dias", min_value=0, value=21, step=1, key="dias_dir_manual")
                    valor_direito = st.number_input("Valor (R$)", min_value=0.0, value=100.0, step=10.0, key="valor_dir")
                    data_inicio_dir = None
                    data_fim_dir = None
                else:
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        data_inicio_dir = st.date_input("Data Início", key="data_inicio_dir")
                    with col_d2:
                        data_fim_dir = st.date_input("Data Fim", key="data_fim_dir")
                    
                    if data_inicio_dir and data_fim_dir:
                        dias_direito = contar_dias_uteis(data_inicio_dir, data_fim_dir)
                        valor_direito = dias_direito * dados_empresa['valor_diario']
                        st.info(f"Dias: {dias_direito} | Valor: {formatar_real(valor_direito)}")
                    else:
                        dias_direito = 0
                        valor_direito = 0.0
            
            if st.form_submit_button("Adicionar Período de Direito", use_container_width=True):
                if mes_direito and dias_direito > 0:
                    periodo = {
                        'mes': mes_direito,
                        'dias': dias_direito,
                        'valor': valor_direito,
                        'data_inicio': str(data_inicio_dir) if data_inicio_dir else None,
                        'data_fim': str(data_fim_dir) if data_fim_dir else None
                    }
                    st.session_state.periodos_direito_temp.append(periodo)
                    st.success(f"Período '{mes_direito}' adicionado")
                    st.rerun()
        
        # Exibir períodos de direito adicionados
        if st.session_state.periodos_direito_temp:
            st.write("**Períodos de Direito Adicionados:**")
            for idx, p in enumerate(st.session_state.periodos_direito_temp):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.text(f"• {p['mes']} — {p['dias']} dias — {formatar_real(p['valor'])}")
                with col2:
                    if st.button("Remover", key=f"rem_dir_{idx}"):
                        st.session_state.periodos_direito_temp.pop(idx)
                        st.rerun()
        
        # ===== SEÇÃO: PERÍODOS DE AFASTAMENTO =====
        st.markdown("---")
        st.subheader("Períodos de Afastamento (Atestados/Faltas)")
        
        with st.form("form_periodo_afastamento", clear_on_submit=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                descricao_afastamento = st.text_input("Descrição", placeholder="Ex: Atestado médico")
            
            with col2:
                metodo_calc_afastamento = st.selectbox("Cálculo", ["Manual", "Por Data"], key="metodo_afas")
            
            if metodo_calc_afastamento == "Manual":
                dias_afastamento = st.number_input("Dias de Afastamento", min_value=0, value=1, step=1, key="dias_afas_manual")
                data_inicio_afas = None
                data_fim_afas = None
            else:
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    data_inicio_afas = st.date_input("Data Início", key="data_inicio_afas")
                with col_a2:
                    data_fim_afas = st.date_input("Data Fim", key="data_fim_afas")
                
                if data_inicio_afas and data_fim_afas:
                    dias_afastamento = contar_dias_uteis(data_inicio_afas, data_fim_afas)
                    st.info(f"Dias calculados: {dias_afastamento}")
                else:
                    dias_afastamento = 0
            
            if st.form_submit_button("Adicionar Período de Afastamento", use_container_width=True):
                if descricao_afastamento and dias_afastamento > 0:
                    periodo = {
                        'descricao': descricao_afastamento,
                        'dias': dias_afastamento,
                        'data_inicio': str(data_inicio_afas) if data_inicio_afas else None,
                        'data_fim': str(data_fim_afas) if data_fim_afas else None
                    }
                    st.session_state.periodos_afastamento_temp.append(periodo)
                    st.success(f"Afastamento '{descricao_afastamento}' adicionado")
                    st.rerun()
        
        # Exibir períodos de afastamento adicionados
        if st.session_state.periodos_afastamento_temp:
            st.write("**Períodos de Afastamento Adicionados:**")
            for idx, p in enumerate(st.session_state.periodos_afastamento_temp):
                col1, col2 = st.columns([5, 1])
                with col1:
                    periodo_txt = f"• {p['descricao']} — {p['dias']} dias"
                    if p.get('data_inicio') and p.get('data_fim'):
                        periodo_txt += f" ({p['data_inicio']} a {p['data_fim']})"
                    st.text(periodo_txt)
                with col2:
                    if st.button("Remover", key=f"rem_afas_{idx}"):
                        st.session_state.periodos_afastamento_temp.pop(idx)
                        st.rerun()
        
        # ===== OBSERVAÇÃO E FINALIZAÇÃO =====
        st.markdown("---")
        observacao = st.text_area("Observação (opcional)")
        data_reembolso = st.date_input("Data de Reembolso", value=date.today())
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Calcular", type="primary", use_container_width=True):
                if not nome_funcionario.strip():
                    st.error("Nome do funcionário é obrigatório")
                elif not st.session_state.periodos_direito_temp:
                    st.error("Adicione pelo menos um período de direito")
                elif not st.session_state.periodos_afastamento_temp:
                    st.error("Adicione pelo menos um período de afastamento")
                else:
                    totais = calcular_desconto_total(
                        st.session_state.periodos_direito_temp,
                        st.session_state.periodos_afastamento_temp,
                        dados_empresa['dias_base'],
                        dados_empresa['valor_diario']
                    )
                    
                    st.session_state._ultimo_calculo = {
                        'nome_funcionario': nome_funcionario,
                        'empresa': empresa_selecionada,
                        'valor_diario': dados_empresa['valor_diario'],
                        'dias_base': dados_empresa['dias_base'],
                        'periodos_direito': st.session_state.periodos_direito_temp.copy(),
                        'periodos_afastamento': st.session_state.periodos_afastamento_temp.copy(),
                        'totais': totais,
                        'observacao': observacao,
                        'data_reembolso': data_reembolso.strftime('%d/%m/%Y')
                    }
                    
                    st.success("Cálculo realizado com sucesso")
        
        with col2:
            if st.button("Adicionar ao Relatório", use_container_width=True):
                if '_ultimo_calculo' not in st.session_state:
                    st.warning("Calcule primeiro antes de adicionar")
                else:
                    if 'calculos' not in st.session_state:
                        st.session_state.calculos = []
                    st.session_state.calculos.append(st.session_state._ultimo_calculo)
                    st.session_state.periodos_direito_temp = []
                    st.session_state.periodos_afastamento_temp = []
                    st.success("Adicionado ao relatório")
                    st.rerun()
        
        with col3:
            if st.button("Limpar Tudo", use_container_width=True):
                st.session_state.periodos_direito_temp = []
                st.session_state.periodos_afastamento_temp = []
                st.session_state.calculos = []
                if '_ultimo_calculo' in st.session_state:
                    del st.session_state._ultimo_calculo
                st.success("Tudo limpo")
                st.rerun()
        
        # Exibir resultado do último cálculo
        if '_ultimo_calculo' in st.session_state:
            st.markdown("---")
            st.subheader("Resultado do Cálculo")
            calc = st.session_state._ultimo_calculo
            totais = calc['totais']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Dias de Direito", totais['total_dias_direito'])
            with col2:
                st.metric("Dias Ausentes", totais['total_dias_ausentes'])
            with col3:
                st.metric("Dias a Descontar", totais['dias_a_descontar'])
            with col4:
                st.metric("Valor Final", formatar_real(totais['valor_final']))

def gerar_relatorio():
    """Gera e exibe o relatório final."""
    st.subheader("Relatório Final")
    
    if 'calculos' not in st.session_state or not st.session_state.calculos:
        st.info("Nenhum cálculo adicionado ao relatório")
        return
    
    html_relatorio = gerar_html_relatorio(st.session_state.calculos)
    
    st.markdown(html_relatorio, unsafe_allow_html=True)
    
    arquivo_html = Path("relatorio_descontos.html")
    arquivo_html.write_text(html_relatorio, encoding='utf-8')
    
    with open(arquivo_html, 'rb') as f:
        st.download_button(
            label="Baixar Relatório (HTML)",
            data=f,
            file_name=f"relatorio_descontos_{date.today().strftime('%Y%m%d')}.html",
            mime="text/html",
            use_container_width=True
        )

# ============================================================================
# APLICAÇÃO PRINCIPAL
# ============================================================================

def main():
    st.set_page_config(
        page_title="Cálculo de Descontos",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("Sistema de Cálculo de Descontos")
    
    empresas = carregar_empresas()
    
    with st.sidebar:
        st.header("Menu")
        opcao = st.radio(
            "Navegação",
            ["Cadastro de Empresas", "Cálculo Individual", "Relatório Final"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.caption("Sistema de cálculo de descontos por ausência")
    
    if opcao == "Cadastro de Empresas":
        renderizar_cadastro_empresas(empresas)
    elif opcao == "Cálculo Individual":
        renderizar_calculo_individual(empresas)
    else:
        gerar_relatorio()

if __name__ == "__main__":
    main()