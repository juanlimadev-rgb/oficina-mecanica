from fpdf import FPDF
from flask import current_app
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "pdfs")


# Caminho do arquivo de logo (opcional). Coloque o arquivo em static/logo.png
LOGO_PATH = os.path.join(BASE_DIR, "static", "logo.png")

NOME_OFICINA = "JOANDERSON MOTO PEÇAS"
ENDERECO_OFICINA = "AV. HILDETE FALCAO BATISTA, 199 - DIVINEIA"
CIDADE_OFICINA = "49071-172 - SAO CRISTOVAO SERGIPE"
CNPJ_OFICINA = "CNPJ 52.485.390/0001-30"

# Número mínimo de linhas em branco na tabela de itens (para preencher como no recibo)
MIN_LINHAS_TABELA = 12


def _moeda(valor):
    """Formata valor como R$ 1.234,56"""
    txt = f"{valor:,.2f}"
    txt = txt.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {txt}"


class PDFOrdemServico(FPDF):
    def header(self):
        # Logo (se existir o arquivo)
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=10, y=8, w=45)

        # Cabeçalho com dados da oficina, centralizado
        self.set_xy(0, 10)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 6, NOME_OFICINA, align="C", ln=True)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 5, ENDERECO_OFICINA, align="C", ln=True)
        self.cell(0, 5, CIDADE_OFICINA, align="C", ln=True)
        self.cell(0, 5, CNPJ_OFICINA, align="C", ln=True)

        self.set_y(35)


def _linha_dado(pdf, label, valor, largura_total=190):
    """Desenha 'LABEL: valor' com uma linha sublinhada até o fim da largura."""
    pdf.set_font("Helvetica", "B", 9)
    label_txt = f"{label}: "
    pdf.cell(pdf.get_string_width(label_txt) + 1, 6, label_txt, border=0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, valor or "", border="B", ln=True)


def gerar_pdf_ordem(ordem, cliente):
    """
    ordem: instância de OrdemServico (com itens carregados)
    cliente: instância de Cliente
    Retorna o caminho do arquivo PDF gerado.
    """
    pdf = PDFOrdemServico()
    pdf.add_page()
    pdf.set_margins(10, 10, 10)

    # --- Dados do cliente / OS ---
    _linha_dado(pdf, "NOME", cliente.nome)
    _linha_dado(pdf, "ENDEREÇO", cliente.endereco or "")

    # CONTATO + DATA na mesma linha
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(20, 6, "CONTATO:", border=0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(95, 6, cliente.telefone or "", border="B")

    data_str = ordem.data.strftime("%d/%m/%Y") if ordem.data else ""
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(20, 6, "DATA:", border=0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, data_str, border="B", ln=True)

    # VEICULO + PLACA na mesma linha
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(20, 6, "VEICULO:", border=0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(95, 6, cliente.moto or "", border="B")

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(20, 6, "PLACA:", border=0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, cliente.placa or "", border="B", ln=True)

    pdf.ln(4)

    # --- Tabela de itens ---
    col_qtd = 20
    col_desc = 95
    col_unit = 37.5
    col_total = 37.5

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(col_qtd, 7, "QUANT", border=1, align="C")
    pdf.cell(col_desc, 7, "SERVIÇOS/PEÇAS", border=1, align="C")
    pdf.cell(col_unit, 7, "VL. UNIDADE", border=1, align="C")
    pdf.cell(col_total, 7, "VL. TOTAL", border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    linhas_usadas = 0
    for item in ordem.itens:
        subtotal = item.quantidade * item.valor_unitario
        qtd_str = f"{item.quantidade:g}"
        pdf.cell(col_qtd, 7, qtd_str, border=1, align="C")
        pdf.cell(col_desc, 7, item.descricao, border=1, align="C")
        pdf.cell(col_unit, 7, _moeda(item.valor_unitario), border=1, align="C")
        pdf.cell(col_total, 7, _moeda(subtotal), border=1, align="C")
        pdf.ln()
        linhas_usadas += 1

    # Linhas em branco para completar a tabela (visual do recibo)
    for _ in range(max(0, MIN_LINHAS_TABELA - linhas_usadas)):
        pdf.cell(col_qtd, 7, "", border=1)
        pdf.cell(col_desc, 7, "", border=1)
        pdf.cell(col_unit, 7, "", border=1)
        pdf.cell(col_total, 7, _moeda(0) if linhas_usadas == 0 else "", border=1, align="C")
        pdf.ln()

    # Total
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_qtd + col_desc + col_unit, 8, "TOTAL", border=1, align="C")
    pdf.cell(col_total, 8, _moeda(ordem.valor_total), border=1, align="C")
    pdf.ln(12)

    # --- Observação ---
    pdf.set_font("Helvetica", "B", 9)
    obs_txt = "OBSERVAÇÃO: "
    pdf.cell(pdf.get_string_width(obs_txt) + 1, 6, obs_txt, border=0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, ordem.descricao or "", border="B", ln=True)
    pdf.ln(10)

    # --- Forma de pagamento ---
    pdf.set_font("Helvetica", "B", 9)
    fp_txt = "FORMA DE PAGAMENTO: "
    pdf.cell(pdf.get_string_width(fp_txt) + 1, 6, fp_txt, border=0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, ordem.forma_pagamento or "", border="B", ln=True)

    pdf_dir = current_app.config["PDF_DIR"]
    os.makedirs(pdf_dir, exist_ok=True)
    filename = f"OS_{ordem.id}.pdf"
    filepath = os.path.join(pdf_dir, filename)
    pdf.output(filepath)
    return filepath
