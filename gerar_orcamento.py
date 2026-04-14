from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import os

MATERIAIS_VALIDOS = [
    "Vinil",
    "BOPP Branco",
    "BOPP Metalizado",
    "BOPP Transparente",
    "Etiqueta Patrimônio",
    "Troca de Óleo Vinil Transparente",
    "Chapa de PS 1mm",
]

PRECOS_M2 = {
    1:  {"Vinil": 120, "BOPP Branco": 140, "BOPP Metalizado": 150, "BOPP Transparente": 150, "Etiqueta Patrimônio": 280, "Troca de Óleo Vinil Transparente": 200},
    2:  {"Vinil": 77,  "BOPP Branco": 100, "BOPP Metalizado": 120, "BOPP Transparente": 120, "Etiqueta Patrimônio": 240, "Troca de Óleo Vinil Transparente": 140},
    3:  {"Vinil": 64,  "BOPP Branco": 85,  "BOPP Metalizado": 100, "BOPP Transparente": 100, "Etiqueta Patrimônio": 220, "Troca de Óleo Vinil Transparente": 110},
    4:  {"Vinil": 60,  "BOPP Branco": 78,  "BOPP Metalizado": 92.5,"BOPP Transparente": 92.5,"Etiqueta Patrimônio": 210, "Troca de Óleo Vinil Transparente": 97.5},
    5:  {"Vinil": 56,  "BOPP Branco": 75,  "BOPP Metalizado": 90,  "BOPP Transparente": 90,  "Etiqueta Patrimônio": 200, "Troca de Óleo Vinil Transparente": 90},
    6:  {"Vinil": 53,  "BOPP Branco": 72,  "BOPP Metalizado": 85,  "BOPP Transparente": 85,  "Etiqueta Patrimônio": 200, "Troca de Óleo Vinil Transparente": 90},
    7:  {"Vinil": 51,  "BOPP Branco": 66,  "BOPP Metalizado": 83,  "BOPP Transparente": 83,  "Etiqueta Patrimônio": 200, "Troca de Óleo Vinil Transparente": 90},
    8:  {"Vinil": 49,  "BOPP Branco": 63,  "BOPP Metalizado": 81,  "BOPP Transparente": 81,  "Etiqueta Patrimônio": 200, "Troca de Óleo Vinil Transparente": 90},
    9:  {"Vinil": 48,  "BOPP Branco": 60,  "BOPP Metalizado": 79,  "BOPP Transparente": 79,  "Etiqueta Patrimônio": 200, "Troca de Óleo Vinil Transparente": 90},
    10: {"Vinil": 47,  "BOPP Branco": 57,  "BOPP Metalizado": 76,  "BOPP Transparente": 76,  "Etiqueta Patrimônio": 200, "Troca de Óleo Vinil Transparente": 90},
}

# Chapa de PS: preço por faixa de 2 m² (chave = metros quadrados cobertos, sempre par)
PRECOS_CHAPA_PS = {
    2:  200,
    4:  360,
    6:  480,
    8:  560,
    10: 650,
    12: 650,
    14: 650,
}

ESTADOS_FRETE_FIXO = ["PR", "SP", "SC", "RS"]
VALOR_FRETE = 50.0

AZUL_CLICKECOLA  = colors.HexColor("#1a4fb5")
LARANJA_CLICKECOLA = colors.HexColor("#f5a000")
AZUL_CLARO       = colors.HexColor("#e8f0fb")
CINZA_LINHA      = colors.HexColor("#eeeeee")

def calcular_preco_m2(material, metros2):
    import math
    # Mínimo de 1 m² cobrado — mesmo que a área real seja menor
    area_cobrada = max(1.0, metros2)
    m2_int = min(10, max(1, math.ceil(area_cobrada)))
    tabela = PRECOS_M2.get(m2_int)
    if not tabela:
        return None, None
    preco = tabela.get(material)
    return preco, area_cobrada

def calcular_item_chapa_ps(largura_mm, altura_mm, quantidade):
    """Chapa de PS: mínimo 2 m², incrementos de 2 em 2."""
    import math
    area_unitaria = (largura_mm / 1000) * (altura_mm / 1000)
    area_total    = area_unitaria * quantidade
    faixas     = max(1, math.ceil(area_total / 2))
    m2_coberto = faixas * 2
    preco_total = PRECOS_CHAPA_PS.get(min(m2_coberto, max(PRECOS_CHAPA_PS)))
    if preco_total is None:
        return None
    return round(preco_total, 2), round(area_total, 4), m2_coberto

def calcular_item(material, largura_mm, altura_mm, quantidade):
    # Trava de segurança — material não reconhecido lança exceção
    if material not in MATERIAIS_VALIDOS:
        raise ValueError(f"Material '{material}' não disponível para orçamento automático. Encaminhar para atendente humano.")

    if material == "Chapa de PS 1mm":
        resultado = calcular_item_chapa_ps(largura_mm, altura_mm, quantidade)
        if resultado is None:
            return None
        valor_total, area_total, m2_coberto = resultado
        return valor_total, area_total, f"preço fixo/{m2_coberto}m²"

    area_unitaria = (largura_mm / 1000) * (altura_mm / 1000)
    area_total    = area_unitaria * quantidade

    preco_m2, area_cobrada = calcular_preco_m2(material, area_total)
    if preco_m2 is None:
        return None

    # Cobra pela área mínima de 1 m² se a área real for menor
    valor_total = round(area_cobrada * preco_m2, 2)
    return valor_total, round(area_total, 4), preco_m2

def gerar_pdf(dados, caminho_saida):
    # Valida todos os materiais antes de gerar o PDF
    for item in dados.get("itens", []):
        material = item.get("material", "")
        if material not in MATERIAIS_VALIDOS:
            raise ValueError(f"Material '{material}' não disponível para orçamento automático. Encaminhar para atendente humano.")

    doc = SimpleDocTemplate(
        caminho_saida,
        pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=10*mm,   bottomMargin=15*mm
    )

    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle("titulo", fontSize=18, textColor=AZUL_CLICKECOLA,
        fontName="Helvetica-Bold", spaceAfter=2)
    h1 = ParagraphStyle("h1", fontSize=10, textColor=AZUL_CLICKECOLA,
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
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Logo_Click_e_Cola.jpeg")
    logo_w = 70*mm
    logo_h = logo_w / 3.4
    logo = Image(logo_path, width=logo_w, height=logo_h)
    numero_orcamento = datetime.now().strftime("%Y%m%d%H%M")
    data_formatada   = datetime.now().strftime("%d/%m/%Y")

    estilo_orcamento = ParagraphStyle("orcamento", fontSize=11, textColor=AZUL_CLICKECOLA,
        fontName="Helvetica-Bold", spaceAfter=0)
    estilo_data = ParagraphStyle("data", fontSize=9, textColor=colors.black,
        fontName="Helvetica", alignment=TA_CENTER)

    cabecalho_dados = [[
        logo,
        Paragraph(f"ORÇAMENTO Nº<br/>{numero_orcamento}", estilo_orcamento),
        Paragraph(f"Data: {data_formatada}", estilo_data),
    ]]
    tabela_cab = Table(cabecalho_dados, colWidths=[72*mm, 80*mm, 36*mm])
    tabela_cab.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",  (1,0), (1,0),  "LEFT"),
        ("ALIGN",  (2,0), (2,0),  "RIGHT"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
    ]))
    story.append(tabela_cab)
    story.append(HRFlowable(width="100%", thickness=2, color=LARANJA_CLICKECOLA, spaceAfter=2))
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL_CLICKECOLA, spaceAfter=6))

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

    subtotal = 0.0

    for i, item in enumerate(dados["itens"], 1):
        material = item.get("material", "")
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

    col_widths = [8*mm, 58*mm, 35*mm, 28*mm, 14*mm, 33*mm]
    tab_itens = Table(linhas, colWidths=col_widths, repeatRows=1)
    tab_itens.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  AZUL_CLICKECOLA),
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
                ("TEXTCOLOR", (1,ultima), (-1,ultima), AZUL_CLICKECOLA),
                ("FONTSIZE",  (1,ultima), (-1,ultima), 10),
                ("LINEABOVE", (1,ultima), (-1,ultima), 1, LARANJA_CLICKECOLA),
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
    if frete is None and estado:
        obs_linhas.append("• Frete para o seu estado será calculado pela equipe comercial.")

    for o in obs_linhas:
        story.append(Paragraph(o, obs))

    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=LARANJA_CLICKECOLA, spaceAfter=2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=AZUL_CLICKECOLA, spaceAfter=4))
    story.append(Paragraph(
        "Click e Cola Soluções Gráficas — R. Dep. João Ribeiro Júnior, 220 - Cidade Industrial de Curitiba, Curitiba - PR, 81350-220  |  (41) 3014-4002  |  comercial@alfagraf.com.br",
        rodape))

    doc.build(story)

if __name__ == "__main__":
    dados_teste = {
        "cliente": "Carlos Mendes", "empresa": "Distribuidora Mendes Ltda",
        "cidade": "Curitiba", "estado": "PR", "telefone": "41998887766",
        "itens": [
            {"descricao": "Etiqueta BOPP Branco para rotulagem",
             "material": "BOPP Branco", "largura_mm": 100, "altura_mm": 50, "quantidade": 500},
            {"descricao": "Adesivo Vinil externo",
             "material": "Vinil", "largura_mm": 200, "altura_mm": 150, "quantidade": 200},
            {"descricao": "Etiqueta de Patrimônio em Poliéster",
             "material": "Etiqueta Patrimônio", "largura_mm": 80, "altura_mm": 40, "quantidade": 300},
            {"descricao": "Etiqueta Troca de Óleo Vinil Transparente",
             "material": "Troca de Óleo Vinil Transparente", "largura_mm": 60, "altura_mm": 40, "quantidade": 100},
            {"descricao": "Placa de Sinalização Chapa PS 1mm",
             "material": "Chapa de PS 1mm", "largura_mm": 300, "altura_mm": 200, "quantidade": 15},
        ]
    }
    gerar_pdf(dados_teste, "/tmp/orcamento_teste.pdf")
    print("PDF gerado com sucesso!")
