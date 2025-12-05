import streamlit as st
import streamlit.components.v1 as components
import json
import os
import textwrap
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

def calcular_saldo_final(abatimentos: List[Dict], direitos: List[Dict]) -> Dict:
    """
    Calcula o saldo final entre direitos e abatimentos.
    """
    total_valor_abatimentos = sum(p['valor'] for p in abatimentos)
    total_valor_direitos = sum(p['valor'] for p in direitos)

    saldo_final = total_valor_direitos - total_valor_abatimentos

    return {
        'total_valor_abatimentos': total_valor_abatimentos,
        'total_valor_direitos': total_valor_direitos,
        'saldo_final': saldo_final
    }

def formatar_real(valor: float) -> str:
    """Formata número no padrão brasileiro R$ 1.234,56"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ============================================================================
# FUNÇÕES DE RELATÓRIO
# ============================================================================

def gerar_html_relatorio(calculos: list) -> str:
    """Gera o relatório completo em HTML."""

    # CSS e Cabeçalho
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Relatório de Acerto Financeiro</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                max-width: 900px;
                margin: 20px auto;
                background: #fff;
                color: #333;
            }
            .relatorio {
                margin-bottom: 50px;
                border: 1px solid #ccc;
                background: #fff;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 0;
            }
            th, td {
                border: 1px solid #000;
                padding: 5px 10px;
                font-size: 14px;
            }
            .header-abatidos {
                background-color: red;
                color: white;
                text-align: center;
                font-weight: bold;
                text-transform: uppercase;
                padding: 5px;
            }
            .header-direitos {
                background-color: #002060; /* Dark blue */
                color: white;
                text-align: center;
                font-weight: bold;
                text-transform: uppercase;
                padding: 5px;
            }
            .valor-col {
                text-align: right;
                width: 120px;
                white-space: nowrap;
            }
            .desc-col {
                text-align: left;
            }
            .detalhe-col {
                text-align: center;
            }
            .subtotal-row td {
                text-align: right;
                font-weight: bold;
                color: red;
            }
            .subtotal-row-direito td {
                text-align: right;
                font-weight: bold;
                color: #000;
            }
            .saldo-final-row td {
                text-align: right;
                font-weight: bold;
                background-color: #f9f9f9;
            }
            .info-header {
                padding: 10px;
                background: #eee;
                border-bottom: 1px solid #ccc;
            }
        </style>
    </head>
    <body>
    """

    for calc in calculos:
        html += f"""
        <div class="relatorio">
            <div class="info-header">
                <strong>Funcionário:</strong> {calc['nome_funcionario'].upper()}<br>
                <strong>Empresa:</strong> {calc['empresa']}
            </div>

            <table>
                <!-- ABATIMENTOS -->
                <thead>
                    <tr>
                        <th colspan="3" class="header-abatidos">VALORES COMPRADOS A SEREM ABATIDOS</th>
                    </tr>
                </thead>
                <tbody>
        """

        for item in calc['abatimentos']:
            html += f"""
                <tr>
                    <td class="desc-col">{item['descricao']}</td>
                    <td class="detalhe-col">{item['detalhes']}</td>
                    <td class="valor-col" style="color: red;">{formatar_real(item['valor'])}</td>
                </tr>
            """

        html += f"""
                <tr class="subtotal-row">
                    <td colspan="2"></td>
                    <td class="valor-col">{formatar_real(calc['totais']['total_valor_abatimentos'])}</td>
                </tr>
                </tbody>
            </table>

            <table>
                <!-- DIREITOS -->
                <thead>
                    <tr>
                        <th colspan="3" class="header-direitos">VALORES QUE TEM DIREITO</th>
                    </tr>
                </thead>
                <tbody>
        """

        for item in calc['direitos']:
            html += f"""
                <tr>
                    <td class="desc-col">{item['descricao']}</td>
                    <td class="detalhe-col">{item['dias']} dias de trabalho</td>
                    <td class="valor-col">{formatar_real(item['valor'])}</td>
                </tr>
            """

        html += f"""
                <tr class="subtotal-row-direito">
                    <td colspan="2"></td>
                    <td class="valor-col">{formatar_real(calc['totais']['total_valor_direitos'])}</td>
                </tr>
                <tr class="saldo-final-row">
                    <td colspan="2">Valor de direito abatendo o valor pago a maior</td>
                    <td class="valor-col">{formatar_real(calc['totais']['saldo_final'])}</td>
                </tr>
                <tr>
                    <td colspan="2" style="text-align: right;">Data de reembolso na conta bancária</td>
                    <td class="valor-col">{calc.get('data_reembolso', '')}</td>
                </tr>
                </tbody>
            </table>

            {f'<div style="padding: 10px; font-style: italic;">Obs: {calc["observacao"]}</div>' if calc.get('observacao') else ''}
        </div>
        """

    html += """
    </body>
    </html>
    """

    return textwrap.dedent(html)

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
            dias_base = st.number_input("Dias-Base (Apenas referência)",
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
            st.text(f"• {nome} — {formatar_real(dados['valor_diario'])}/dia")

def renderizar_calculo_individual(empresas: Dict):
    """Renderiza a seção de cálculo individual."""
    st.subheader("Cálculo Individual")

    if not empresas:
        st.warning("Cadastre pelo menos uma empresa antes de fazer cálculos")
        return

    # Inicializar listas no session_state
    if 'abatimentos_temp' not in st.session_state:
        st.session_state.abatimentos_temp = []
    if 'direitos_temp' not in st.session_state:
        st.session_state.direitos_temp = []

    col1, col2 = st.columns(2)

    with col1:
        nome_funcionario = st.text_input("Nome do Funcionário", placeholder="Ex: João Silva")

    with col2:
        empresa_selecionada = st.selectbox("Empresa", options=list(empresas.keys()))

    if empresa_selecionada:
        dados_empresa = empresas[empresa_selecionada]
        valor_diario = dados_empresa['valor_diario']

        st.info(f"Usando Valor Diário: {formatar_real(valor_diario)}")

        # ===== SEÇÃO 1: ABATIMENTOS (VERMELHO) =====
        st.markdown("---")
        st.markdown("<h3 style='color: red;'>1. Valores Comprados a Serem Abatidos</h3>", unsafe_allow_html=True)

        with st.expander("Adicionar Item de Abatimento", expanded=True):
            with st.form("form_abatimento", clear_on_submit=True):
                col_ab1, col_ab2, col_ab3 = st.columns([2, 1, 1])
                with col_ab1:
                    desc_abatimento = st.text_input("Descrição", placeholder="Ex: Descontar Referente a Julho")
                with col_ab2:
                    dias_trab_abat = st.number_input("Dias Atuou/Trabalhou", min_value=0, value=0, step=1, help="Dias que a pessoa trabalhou neste período")
                with col_ab3:
                    dias_afast_abat = st.number_input("Dias a Abater/Afastamento", min_value=0, value=0, step=1, help="Dias que serão descontados")

                submitted_abat = st.form_submit_button("Adicionar Abatimento")

                if submitted_abat:
                    if desc_abatimento:
                        # Lógica do detalhe
                        if dias_trab_abat > 0:
                            detalhe = f"Atuou {dias_trab_abat} dias - sendo abatido o restante ({dias_afast_abat} dias)"
                        else:
                            detalhe = f"Não atuou nenhum dia - sendo abatido todo o valor ({dias_afast_abat} dias)"

                        item = {
                            'descricao': desc_abatimento,
                            'dias_trabalhados': dias_trab_abat,
                            'dias_afastamento': dias_afast_abat,
                            'detalhes': detalhe,
                            'valor': dias_afast_abat * valor_diario
                        }
                        st.session_state.abatimentos_temp.append(item)
                        st.success("Item adicionado!")
                        st.rerun()
                    else:
                        st.error("Preencha a descrição")

        if st.session_state.abatimentos_temp:
            st.table(st.session_state.abatimentos_temp)
            if st.button("Limpar Abatimentos"):
                st.session_state.abatimentos_temp = []
                st.rerun()

        # ===== SEÇÃO 2: DIREITOS (AZUL) =====
        st.markdown("---")
        st.markdown("<h3 style='color: blue;'>2. Valores que Tem Direito</h3>", unsafe_allow_html=True)

        with st.expander("Adicionar Item de Direito", expanded=True):
            with st.form("form_direito", clear_on_submit=True):
                col_dir1, col_dir2, col_dir3 = st.columns([2, 1, 1])
                with col_dir1:
                    desc_direito = st.text_input("Mês/Período", placeholder="Ex: Outubro")
                with col_dir2:
                    dias_direito = st.number_input("Dias de Trabalho", min_value=0, value=21, step=1)

                submitted_dir = st.form_submit_button("Adicionar Direito")

                if submitted_dir:
                    if desc_direito and dias_direito > 0:
                        item = {
                            'descricao': desc_direito,
                            'dias': dias_direito,
                            'valor': dias_direito * valor_diario
                        }
                        st.session_state.direitos_temp.append(item)
                        st.success("Item adicionado!")
                        st.rerun()
                    else:
                        st.error("Preencha a descrição e dias")

        if st.session_state.direitos_temp:
            st.table(st.session_state.direitos_temp)
            if st.button("Limpar Direitos"):
                st.session_state.direitos_temp = []
                st.rerun()

        # ===== RESULTADO E DATA =====
        st.markdown("---")
        st.subheader("Finalização")

        col_res1, col_res2 = st.columns(2)
        with col_res1:
            observacao = st.text_area("Observação (opcional)")
        with col_res2:
            data_reembolso = st.date_input("Data de Reembolso na Conta", value=date.today())

        col_act1, col_act2, col_act3 = st.columns(3)

        with col_act1:
            if st.button("Calcular Saldo", type="primary", use_container_width=True):
                if not nome_funcionario:
                    st.error("Preencha o nome do funcionário")
                else:
                    totais = calcular_saldo_final(
                        st.session_state.abatimentos_temp,
                        st.session_state.direitos_temp
                    )

                    st.session_state._ultimo_calculo = {
                        'nome_funcionario': nome_funcionario,
                        'empresa': empresa_selecionada,
                        'valor_diario': valor_diario,
                        'abatimentos': st.session_state.abatimentos_temp.copy(),
                        'direitos': st.session_state.direitos_temp.copy(),
                        'totais': totais,
                        'observacao': observacao,
                        'data_reembolso': data_reembolso.strftime('%d/%m/%Y')
                    }
                    st.success("Calculado!")

        with col_act2:
            if st.button("Adicionar ao Relatório Final", use_container_width=True):
                if '_ultimo_calculo' in st.session_state:
                    if 'calculos' not in st.session_state:
                        st.session_state.calculos = []
                    st.session_state.calculos.append(st.session_state._ultimo_calculo)

                    # Limpar temporários
                    st.session_state.abatimentos_temp = []
                    st.session_state.direitos_temp = []
                    del st.session_state._ultimo_calculo

                    st.success("Adicionado ao relatório!")
                    st.rerun()
                else:
                    st.warning("Calcule primeiro.")

        with col_act3:
             if st.button("Resetar Tudo", use_container_width=True):
                st.session_state.abatimentos_temp = []
                st.session_state.direitos_temp = []
                st.session_state.calculos = []
                if '_ultimo_calculo' in st.session_state:
                    del st.session_state._ultimo_calculo
                st.rerun()

        # Mostrar resumo do cálculo atual
        if '_ultimo_calculo' in st.session_state:
            res = st.session_state._ultimo_calculo['totais']
            st.metric("Saldo Final (Direitos - Abatimentos)", formatar_real(res['saldo_final']),
                      delta=formatar_real(res['total_valor_direitos']) + " (Créditos)",
                      delta_color="normal")
            st.caption(f"Abatimentos: {formatar_real(res['total_valor_abatimentos'])}")

def gerar_relatorio():
    """Gera e exibe o relatório final."""
    st.subheader("Relatório Final")

    if 'calculos' not in st.session_state or not st.session_state.calculos:
        st.info("Nenhum cálculo adicionado ao relatório")
        return

    html_relatorio = gerar_html_relatorio(st.session_state.calculos)

    # Exibir usando componente HTML isolado para garantir renderização correta
    components.html(html_relatorio, height=600, scrolling=True)

    arquivo_html = Path("relatorio_descontos.html")
    arquivo_html.write_text(html_relatorio, encoding='utf-8')

    with open(arquivo_html, 'rb') as f:
        st.download_button(
            label="Baixar Relatório (HTML)",
            data=f,
            file_name=f"relatorio_acerto_{date.today().strftime('%Y%m%d')}.html",
            mime="text/html",
            use_container_width=True
        )

# ============================================================================
# APLICAÇÃO PRINCIPAL
# ============================================================================

def main():
    st.set_page_config(
        page_title="Cálculo de Acertos",
        page_icon="💰",
        layout="wide"
    )

    st.title("Sistema de Cálculo de Acertos/Descontos")

    empresas = carregar_empresas()

    with st.sidebar:
        st.header("Menu")
        opcao = st.radio(
            "Navegação",
            ["Cadastro de Empresas", "Cálculo Individual", "Relatório Final"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.caption("v2.1 - Acertos e Abatimentos")

    if opcao == "Cadastro de Empresas":
        renderizar_cadastro_empresas(empresas)
    elif opcao == "Cálculo Individual":
        renderizar_calculo_individual(empresas)
    else:
        gerar_relatorio()

if __name__ == "__main__":
    main()