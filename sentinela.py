import os
import json
import requests
import smtplib
import time
import gspread
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- CONFIGURAÇÕES ---
# ✅ MODO SEGURO: Puxa a chave dos Secrets do GitHub
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE", "").strip()
SENHA_APP = os.getenv("SENHA_APP", "").strip()
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

# Link do Logo Oficial do HCPA (Público)
LOGO_URL = "https://www.hcpa.edu.br/images/logo_hcpa.png"

# Lista de Sites
SITES_ALVO = [
    "site:gov.br", "site:edu.br", "site:org.br", "site:b.br",
    "site:fapergs.rs.gov.br", "site:hcpa.edu.br", "site:ufrgs.br", "site:ufcspa.edu.br",
    "site:afimrs.com.br", "site:sgr.org.br", "site:amrigs.org.br",
    "site:fapesc.sc.gov.br", "site:fara.pr.gov.br", "site:fapesp.br",
    "site:iaea.org", "site:who.int", "site:nih.gov", "site:europa.eu", "site:nsf.gov",
    "site:aapm.org", "site:estro.org", "site:astro.org", "site:rsna.org",
    "site:iomp.org", "site:efomp.org", "site:snmmi.org",
    "site:edu", "site:ac.uk", "site:arxiv.org",
    "site:ieee.org", "site:nature.com", "site:science.org", "site:sciencedirect.com",
    "site:iop.org", "site:frontiersin.org", "site:mdpi.com", "site:wiley.com",
    "site:springer.com", "site:thelancet.com",
    "site:einstein.br", "site:hospitalsiriolibanes.org.br", "site:moinhosdevento.org.br"
]

def buscar_google_elite():
    """Etapa 1: Busca os links brutos"""
    print("🚀 1. INICIANDO VARREDURA (SERPER)...")
    
    query_base = '(edital OR chamada OR "call for papers" OR bolsa OR grant) ("física médica" OR radioterapia OR "medical physics")'
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    
    resultados_texto = []
    tamanho_bloco = 8
    blocos = [SITES_ALVO[i:i + tamanho_bloco] for i in range(0, len(SITES_ALVO), tamanho_bloco)]

    for bloco in blocos:
        filtro_sites = " OR ".join(bloco)
        query_final = f"{query_base} ({filtro_sites})"
        payload = json.dumps({"q": query_final, "tbs": "qdr:m", "gl": "br"})
        
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            dados = response.json()
            items = dados.get("organic", [])
            for item in items:
                linha = f"- Título: {item.get('title')}\n  Link: {item.get('link')}\n  Snippet: {item.get('snippet')}\n  Data: {item.get('date', 'N/A')}\n"
                resultados_texto.append(linha)
            time.sleep(1.0)
        except Exception as e:
            print(f"❌ Erro num bloco: {e}")

    print(f"✅ Busca concluída. {len(resultados_texto)} itens para análise.\n")
    return "\n".join(resultados_texto)

def aplicar_template_profissional(conteudo_ia):
    """Envelopa o texto da IA no design HCPA Dark Mode"""
    
    if not conteudo_ia:
        conteudo_ia = "<p style='text-align:center; color:#777;'>Nenhuma oportunidade relevante encontrada hoje.</p>"

    # Cores baseadas no Manual do HCPA (Verde Turquesa)
    # HCPA Green Principal: #009688
    # HCPA Light Accent: #80cbc4
    
    estilos_css = """
        body { margin: 0; padding: 0; background-color: #121212; font-family: 'Segoe UI', Helvetica, Arial, sans-serif; }
        .container { max-width: 600px; margin: 0 auto; background-color: #1e1e1e; color: #e0e0e0; border-radius: 8px; overflow: hidden; }
        .header-bar { height: 6px; background: linear-gradient(90deg, #00695c 0%, #009688 50%, #80cbc4 100%); width: 100%; }
        .header-content { padding: 35px 20px; text-align: center; border-bottom: 1px solid #333; background-color: #232323; }
        .logo { max-width: 150px; margin-bottom: 15px; filter: brightness(0) invert(1); opacity: 0.9; } /* Logo branco para fundo escuro */
        .title { color: #4db6ac; margin: 0; font-size: 26px; font-weight: 300; letter-spacing: 0.5px; text-transform: uppercase; }
        .subtitle { color: #b2dfdb; font-size: 13px; margin-top: 5px; text-transform: uppercase; letter-spacing: 2px; }
        .content { padding: 30px 25px; line-height: 1.6; }
        
        /* Estilização dos Itens da IA */
        h3 { color: #80cbc4; border-left: 4px solid #009688; padding-left: 12px; margin-top: 30px; font-size: 18px; font-weight: 600; text-transform: uppercase; }
        ul { list-style-type: none; padding: 0; margin: 0; }
        li { margin-bottom: 25px; background-color: #262626; padding: 15px; border-radius: 6px; border-left: 2px solid #333; transition: border-left 0.3s; }
        li:hover { border-left: 2px solid #4db6ac; }
        
        strong { color: #fff; font-size: 16px; display: block; margin-bottom: 4px; }
        .resumo { color: #b0bec5; font-size: 14px; display: block; margin-bottom: 8px; line-height: 1.4; }
        .prazo { color: #ffab91; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; display: inline-block; background: #3e2723; padding: 2px 8px; border-radius: 4px; }
        
        a { color: #4db6ac; text-decoration: none; font-weight: bold; font-size: 14px; }
        a:hover { text-decoration: underline; color: #80cbc4; }
        
        .footer { padding: 30px; text-align: center; font-size: 11px; color: #666; border-top: 1px solid #333; background-color: #181818; }
    """

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        {estilos_css}
    </style>
    </head>
    <body>
        <div class="container">
            <div class="header-bar"></div>
            
            <div class="header-content">
                <img src="{LOGO_URL}" alt="HCPA" class="logo">
                <h1 class="title">Sistema Sentinela</h1>
                <div class="subtitle">Serviço de Física Médica e Radioproteção</div>
            </div>
            
            <div class="content">
                {conteudo_ia}
            </div>
            
            <div class="footer">
                <strong>Hospital de Clínicas de Porto Alegre</strong><br>
                Rua Ramiro Barcelos, 2350 - Porto Alegre / RS<br>
                <br>
                <em>Este é um informativo automático gerado por Inteligência Artificial.<br>
                Verifique sempre os editais originais.</em>
            </div>
        </div>
    </body>
    </html>
    """
    return html_template

def gerar_html_manual(texto_bruto):
    """Backup manual"""
    print("⚠️ Usando formatador manual...")
    linhas = texto_bruto.split("- Título: ")
    html_items = ""
    for item in linhas:
        if "Link: " in item:
            partes = item.split("\n")
            titulo = partes[0].strip()
            link = ""
            for p in partes:
                if "Link: " in p: link = p.replace("Link: ", "").strip()
            if link:
                html_items += f"<li><strong><a href='{link}'>{titulo}</a></strong><span class='resumo'>Link direto identificado.</span></li>"
    
    return aplicar_template_profissional(f"<h3>Resultados (Modo Manual)</h3><ul>{html_items}</ul>")

def analisar_com_gemini(texto_bruto):
    """Etapa 2: Inteligência Artificial (Modelo 2.5 Flash)"""
    print("🧠 2. ACIONANDO GEMINI 2.5 FLASH...")
    
    if not texto_bruto: return None

    modelo = "gemini-2.5-flash"
    
    # --- PROMPT ATUALIZADO PARA RESUMO E PRAZO ---
    prompt = f"""
    Você é um Assistente de Pesquisa do Serviço de Física Médica do HCPA.
    Analise os dados brutos abaixo e selecione APENAS oportunidades reais (Editais, Bolsas, Eventos, Chamadas).
    
    REGRAS DE FORMATAÇÃO (HTML PURO):
    1. NÃO use tags <html>, <head> ou <body>. Retorne apenas o conteúdo.
    2. Agrupe por categorias (ex: <h3>Editais e Fomento</h3>).
    3. Para cada item, use a seguinte estrutura exata dentro de um <ul>:
    
    <li>
        <strong>Título da Oportunidade</strong> - <a href="LINK_AQUI">ACESSAR</a><br>
        <span class="resumo">Resumo: Escreva aqui um resumo de 1 ou 2 linhas sobre o objetivo.</span><br>
        <span class="prazo">📅 Prazo: Data ou "Fluxo Contínuo" (Encontre essa info no texto)</span>
    </li>
    
    DADOS PARA ANÁLISE:
    {texto_bruto}
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("   ✅ SUCESSO! A IA gerou o conteúdo.")
            resultado = response.json()
            texto_cru_ia = resultado['candidates'][0]['content']['parts'][0]['text']
            
            # Limpa marcadores
            texto_limpo = texto_cru_ia.replace("```html", "").replace("```", "")
            
            # Aplica o layout
            return aplicar_template_profissional(texto_limpo)
        else:
            print(f"   ❌ Erro na API ({response.status_code}): {response.text}")
            return gerar_html_manual(texto_bruto)

    except Exception as e:
        print(f"   ❌ Erro de conexão: {e}")
        return gerar_html_manual(texto_bruto)

def obter_lista_emails():
    """Etapa Extra: Pega os e-mails da Planilha"""
    print("📋 Lendo lista de contatos da COLUNA 3...")
    
    lista_final = []
    if EMAIL_REMETENTE: lista_final.append(EMAIL_REMETENTE)
    
    if not GOOGLE_CREDENTIALS: 
        return lista_final

    try:
        creds_dict = json.loads(GOOGLE_CREDENTIALS)
        gc = gspread.service_account_from_dict(creds_dict)
        sh = gc.open("Sentinela Emails")
        ws = sh.sheet1
        
        emails_raw = ws.col_values(3)
        
        for e in emails_raw:
            email_limpo = e.strip()
            if "@" in email_limpo and "email" not in email_limpo.lower():
                if email_limpo not in lista_final:
                    lista_final.append(email_limpo)
        
        print(f"✅ Destinatários válidos: {len(lista_final)}")
        return lista_final
        
    except Exception as e:
        print(f"❌ Erro na planilha: {e}")
        return lista_final

def enviar_email(corpo_html, destinatario):
    """Etapa 3: Dispara o e-mail"""
    if not destinatario: return

    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = destinatario
    msg['Subject'] = f"Sentinela Física Médica - {datetime.now().strftime('%d/%m')}"
    msg.attach(MIMEText(corpo_html, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_APP)
        server.sendmail(EMAIL_REMETENTE, destinatario, msg.as_string())
        server.quit()
        print(f"   📤 Enviado para: {destinatario}")
    except Exception as e:
        print(f"   ❌ Falha ao enviar para {destinatario}: {e}")

if __name__ == "__main__":
    dados = buscar_google_elite()
    relatorio = analisar_com_gemini(dados)
    
    if relatorio:
        lista_vip = obter_lista_emails()
        print(f"\n📧 Iniciando disparos para {len(lista_vip)} pessoas...")
        for email in lista_vip:
            enviar_email(relatorio, email)
        print("🏁 FIM.")
    else:
        print("📭 Nada encontrado.")
