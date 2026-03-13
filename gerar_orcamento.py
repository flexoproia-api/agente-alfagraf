from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import os

PRECOS_M2 = {
    1:  {"Vinil": 120,  "BOPP Branco": 140, "BOPP Metalizado": 150, "BOPP Transparente": 150},
    2:  {"Vinil": 77,   "BOPP Branco": 100, "BOPP Metalizado": 120, "BOPP Transparente": 120},
    3:  {"Vinil": 64,   "BOPP Branco": 85,  "BOPP Metalizado": 100, "BOPP Transparente": 100},
    4:  {"Vinil": 60,   "BOPP Branco": 78,  "BOPP Metalizado": 92.5,"BOPP Transparente": 92.5},
    5:  {"Vinil": 56,   "BOPP Branco": 75,  "BOPP Metalizado": 90,  "BOPP Transparente": 90},
    6:  {"Vinil": 53,   "BOPP Branco": 72,  "BOPP Metalizado": 85,  "BOPP Transparente": 85},
    7:  {"Vinil": 51,   "BOPP Branco": 66,  "BOPP Metalizado": 83,  "BOPP Transparente": 83},
    8:  {"Vinil": 49,   "BOPP Branco": 63,  "BOPP Metalizado": 81,  "BOPP Transparente": 81},
    9:  {"Vinil": 48,   "BOPP Branco": 60,  "BOPP Metalizado": 79,  "BOPP Transparente": 79},
    10: {"Vinil": 47,   "BOPP Branco": 57,  "BOPP Metalizado": 76,  "BOPP Transparente": 76},
}

ESTADOS_FRETE_FIXO = ["PR", "SP", "SC", "RS"]
VALOR_FRETE = 50.0

AZUL_ALFAGRAF = colors.HexColor("#1a237e")
AZUL_CLARO    = colors.HexColor("#e8eaf6")
CINZA_LINHA   = colors.HexColor("#eeeeee")

def calcular_preco_m2(material, metros2):
    import math
    m2_int = min(10, max(1, math.ceil(metros2)))
    tabela = PRECOS_M2.get(m2_int)
    if not tabela:
        return None
    return tabela.get(material)

def calcular_item(material, largura_mm, altura_mm, quantidade):
    area_unitaria = (largura_mm / 1000) * (altura_mm / 1000)
    area_total    = area_unitaria * quantidade
    preco_m2      = calcular_preco_m2(material, area_total)
    if preco_m2 is None:
        return None
    return round(area_total * preco_m2, 2), round(area_total, 4), preco_m2

def gerar_pdf(dados, caminho_saida):
    doc = SimpleDocTemplate(
        caminho_saida,
        pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=10*mm,   bottomMargin=15*mm
    )

    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle("titulo", fontSize=18, textColor=AZUL_ALFAGRAF,
        fontName="Helvetica-Bold", spaceAfter=2)
    h1 = ParagraphStyle("h1", fontSize=10, textColor=AZUL_ALFAGRAF,
        fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=4)
    normal = ParagraphStyle("normal", fontSize=9, textColor=colors.black,
        fontName="Helvetica", spaceAfter=2)
    obs = ParagraphStyle("obs", fontSize=8, textColor=colors.HexColor("#777777"),
        fontName="Helvetica-Oblique")
    celula = ParagraphStyle("celula", fontSize=8, textColor=colors.black,
        fontName="Helvetica", leading=11)
    rodape = ParagraphStyle("rodape", fontSize=7.5, textColor=colors.HexColor("#888888"),
        fontName="Helvetica", alignment=TA_CENTER)

    story = []

    # CABEÇALHO
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_alfagraf.png")
    logo = Image(logo_path, width=45*mm, height=18*mm)
    numero_orcamento = datetime.now().strftime("%Y%m%d%H%M")
    data_formatada   = datetime.now().strftime("%d/%m/%Y")

    cabecalho_dados = [[logo,
        Paragraph(f"<b>ORÇAMENTO Nº {numero_orcamento}</b>", estilo_titulo),
        Paragraph(f"Data: {data_formatada}", normal)]]
    tabela_cab = Table(cabecalho_dados, colWidths=[50*mm, 100*mm, 35*mm])
    tabela_cab.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",  (2,0), (2,0),  "RIGHT"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(tabela_cab)
    story.append(HRFlowable(width="100%", thickness=2, color=AZUL_ALFAGRAF, spaceAfter=6))

    # DADOS DO CLIENTE
    story.append(Paragraph("DADOS DO CLIENTE", h1))
    empresa_linha = f"<b>Empresa:</b> {dados['empresa']}" if dados.get("empresa") else "<b>Pessoa Física</b>"
    info_cliente = [
        [Paragraph(f"<b>Cliente:</b> {dados['cliente']}", normal),
         Paragraph(empresa_linha, normal)],
        [Paragraph(f"<b>Cidade/UF:</b> {dados['cidade']} / {dados['estado']}", normal),
         Paragraph(f"<b>Telefone:</b> {dados['telefone']}", normal)],
    ]
    tab_cliente = Table(info_cliente, colWidths=[93*mm, 93*mm])
    tab_cliente.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [AZUL_CLARO, colors.white]),
        ("GRID",       (0,0), (-1,-1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("LEFTPADDING",(0,0),(-1,-1), 6),
    ]))
    story.append(tab_cliente)
    story.append(Spacer(1, 6*mm))

    # ITENS
    story.append(Paragraph("ITENS DO ORÇAMENTO", h1))

    cabecalho_itens = ["#", "Descrição", "Material", "Tamanho", "Qtd", "Total (R$)"]
    linhas = [cabecalho_itens]

    subtotal     = 0.0
    itens_humano = []

    for i, item in enumerate(dados["itens"], 1):
        material = item.get("material", "")
        mat_auto = ["Vinil", "BOPP Branco", "BOPP Metalizado", "BOPP Transparente"]

        if material in mat_auto:
            resultado = calcular_item(material, item["largura_mm"], item["altura_mm"], item["quantidade"])
            if resultado:
                valor_total, area_total, preco_m2 = resultado
                subtotal += valor_total
                linhas.append([
                    str(i),
                    Paragraph(item.get("descricao", material), celula),
                    Paragraph(material, celula),
                    f"{item['largura_mm']}x{item['altura_mm']} mm",
                    str(item["quantidade"]),
                    f"R$ {valor_total:.2f}",
                ])
            else:
                itens_humano.append(i)
                linhas.append([str(i), Paragraph(item.get("descricao", material), celula),
                    Paragraph(material, celula),
                    f"{item['largura_mm']}x{item['altura_mm']} mm",
                    str(item["quantidade"]), "A consultar"])
        else:
            itens_humano.append(i)
            linhas.append([str(i), Paragraph(item.get("descricao", material), celula),
                Paragraph(material, celula),
                f"{item.get('largura_mm','-')}x{item.get('altura_mm','-')} mm",
                str(item.get("quantidade","-")), "A consultar"])

    col_widths = [8*mm, 58*mm, 35*mm, 28*mm, 14*mm, 33*mm]
    tab_itens = Table(linhas, colWidths=col_widths, repeatRows=1)
    tab_itens.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  AZUL_ALFAGRAF),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, CINZA_LINHA]),
        ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#cccccc")),
        ("ALIGN",         (4,0), (4,-1),  "CENTER"),
        ("ALIGN",         (5,0), (5,-1),  "RIGHT"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
    ]))
    story.append(tab_itens)
    story.append(Spacer(1, 4*mm))

    # TOTAIS
    estado = dados.get("estado", "").upper()
    frete  = VALOR_FRETE if estado in ESTADOS_FRETE_FIXO else None
    total  = subtotal + (frete or 0)

    linhas_totais = []
    if subtotal > 0:
        linhas_totais.append(["", "Subtotal dos itens:", f"R$ {subtotal:.2f}"])
    if frete is not None:
        linhas_totais.append(["", f"Frete ({estado}):", f"R$ {frete:.2f}"])
    elif estado:
        linhas_totais.append(["", "Frete:", "A consultar"])
    if subtotal > 0:
        linhas_totais.append(["", "TOTAL GERAL:", f"R$ {total:.2f}"])

    if linhas_totais:
        tab_totais = Table(linhas_totais, colWidths=[118*mm, 40*mm, 28*mm])
        estilo_totais = [
            ("ALIGN",   (1,0), (-1,-1), "RIGHT"),
            ("FONTSIZE",(0,0), (-1,-1), 9),
            ("TOPPADDING",    (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ]
        ultima = len(linhas_totais) - 1
        if subtotal > 0:
            estilo_totais += [
                ("FONTNAME",  (1,ultima), (-1,ultima), "Helvetica-Bold"),
                ("TEXTCOLOR", (1,ultima), (-1,ultima), AZUL_ALFAGRAF),
                ("FONTSIZE",  (1,ultima), (-1,ultima), 10),
                ("LINEABOVE", (1,ultima), (-1,ultima), 1, AZUL_ALFAGRAF),
            ]
        tab_totais.setStyle(TableStyle(estilo_totais))
        story.append(tab_totais)

    # OBSERVAÇÕES
    story.append(Spacer(1, 4*mm))
    obs_linhas = [
        "• Orçamento válido por 7 dias.",
        "• Prazo de entrega a combinar após aprovação.",
        "• Aceitamos cartão de crédito.",
        "• Esta é uma proposta preliminar elaborada com base nas informações fornecidas. Após a aprovação, realizaremos as confirmações técnicas necessárias para garantir a melhor solução para o seu projeto.",
    ]
    if itens_humano:
        nums = ", ".join(str(n) for n in itens_humano)
        obs_linhas.append(f"• Os itens {nums} marcados como 'A consultar' serão orçados manualmente pela equipe comercial.")
    if frete is None and estado:
        obs_linhas.append("• Frete para o seu estado será calculado pela equipe comercial.")

    for o in obs_linhas:
        story.append(Paragraph(o, obs))

    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc"), spaceAfter=4))
    story.append(Paragraph(
        "Alfagraf — R. Dep. João Ribeiro Júnior, 220 - Cidade Industrial de Curitiba, Curitiba - PR, 81350-220  |  (41) 3014-4002  |  comercial@alfagraf.com.br",
        rodape))

    doc.build(story)

if __name__ == "__main__":
    dados_teste = {
        "cliente": "Carlos Mendes", "empresa": "Distribuidora Mendes Ltda",
        "cidade": "Curitiba", "estado": "PR", "telefone": "41998887766",
        "itens": [
            {"descricao": "Etiqueta BOPP Branco para rotulagem de produtos alimentícios",
             "material": "BOPP Branco", "largura_mm": 100, "altura_mm": 50, "quantidade": 500},
            {"descricao": "Adesivo Vinil externo",
             "material": "Vinil", "largura_mm": 200, "altura_mm": 150, "quantidade": 200},
        ]
    }
    gerar_pdf(dados_teste, "/mnt/user-data/outputs/orcamento_teste_alfagraf.pdf")
    print("OK")
