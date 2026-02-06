import os
import json
import requests
import smtplib
import gspread
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- CONFIGURAÇÕES ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE", "").strip()
SENHA_APP = os.getenv("SENHA_APP", "").strip()
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
LOGO_URL = "https://raw.githubusercontent.com/emillysc04-oss/Sentinela-3.0/main/Logo3.png"

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

def notificar_erro_admin(erro_msg):
    """Envia um e-mail de alerta para você caso o sistema falhe."""
    print(f"❌ ERRO CRÍTICO: {erro_msg}. Notificando admin...")
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_REMETENTE # Envia para você mesma
    msg['Subject'] = f"🚨 FALHA NO SENTINELA - {datetime.now().strftime('%d/%m')}"
    
    corpo = f"""
    <h3>Ocorreu um erro na execução do Sentinela</h3>
    <p>O sistema não conseguiu enviar os e-mails para a lista.</p>
    <p><strong>Erro detalhado:</strong> {erro_msg}</p>
    """
    msg.attach(MIMEText(corpo, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_APP)
        server.sendmail(EMAIL_REMETENTE, EMAIL_REMETENTE, msg.as_string())
        server.quit()
    except:
        pass # Se falhar o envio de erro, não há muito o que fazer.

def buscar_google_elite():
    query_base = '(edital OR chamada OR "call for papers" OR bolsa OR grant) ("física médica" OR radioterapia OR "medical physics")'
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    
    resultados = []
    tamanho_bloco = 10
    blocos = [SITES_ALVO[i:i + tamanho_bloco] for i in range(0, len(SITES_ALVO), tamanho_bloco)]

    for bloco in blocos:
        filtro_sites = " OR ".join(bloco)
        query_final = f"{query_base} ({filtro_sites})"
        payload = json.dumps({"q": query_final, "tbs": "qdr:m", "gl": "br"})
        
        try:
            response = requests.post(url, headers=headers, data=payload)
            items = response.json().get("organic", [])
            for item in items:
                resultados.append(f"- Título: {item.get('title')}\n  Link: {item.get('link')}\n  Snippet: {item.get('snippet')}\n")
            time.sleep(0.5)
        except:
            continue
            
    return "\n".join(resultados)

def formatar_html(conteudo_ia):
    if not conteudo_ia: return None
    
    # CSS EXATO QUE VOCÊ ENVIOU
    estilos_css = """
        body { margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .container { max-width: 600px; margin: 0 auto; padding: 10px; }
        .header-content { text-align: center; margin-bottom: 30px; }
        .logo { max-width: 180px; margin-bottom: 10px; }
        .title { color: #009688; margin: 0; font-size: 24px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }
        .subtitle { color: #555; font-size: 13px; margin-top: 5px; letter-spacing: 1px; text-transform: uppercase; }
        .header-bar { height: 3px; background: linear-gradient(90deg, #004d40 0%, #009688 50%, #80cbc4 100%); width: 100%; border-radius: 4px; margin-bottom: 30px;}
        h3 { color: #00796b; margin-top: 40px; font-size: 18px; border-bottom: 2px solid #e0e0e0; padding-bottom: 5px; text-transform: uppercase; }
        ul { list-style-type: none; padding: 0; margin: 0; }
        li { margin-bottom: 20px; background-color: transparent; padding: 15px; border: 1px solid #e0e0e0; border-left: 5px solid #009688; border-radius: 4px; }
        strong { color: #004d40; font-size: 16px; display: block; margin-bottom: 6px; }
        .resumo { color: #555555; font-size: 14px; display: block; margin-bottom: 12px; line-height: 1.4; }
        .prazo { color: #d84315; font-size: 12px; font-weight: bold; text-transform: uppercase; background-color: #fbe9e7; padding: 4px 8px; border-radius: 4px; display: inline-block; }
        a { background-color: #009688; color: #ffffff !important; text-decoration: none; font-weight: bold; font-size: 12px; float: right; padding: 5px 12px; border-radius: 4px; margin-top: -5px; }
        a:hover { background-color: #00796b; }
        .footer { padding: 30px; text-align: center; font-size: 11px; color: #888; margin-top: 40px; border-top: 1px solid #eee; }
    """

    return f"""
    <!DOCTYPE html>
    <html>
    <head><style>{estilos_css}</style></head>
    <body>
        <div class="container">
            <div class="header-content">
                <img src="{LOGO_URL}" alt="HCPA" class="logo">
                <h1 class="title">Sistema de monitoramento Sentinela</h1>
                <div class="subtitle">Editais de Pesquisa</div>
            </div>
            <div class="header-bar"></div>
            <div class="content">{conteudo_ia}</div>
            <div class="footer">
                Serviço de Física Médica e Radioproteção<br>
                Hospital de Clínicas de Porto Alegre<br>
                Gerado automaticamente via Inteligência Artificial
            </div>
        </div>
    </body>
    </html>
    """

def processar_ia(texto_bruto):
    if not texto_bruto: return None
    
    prompt = f"""
    Você é um Assistente do HCPA. Analise os dados e encontre oportunidades de Física Médica.
    PARA CADA ITEM, ENCONTRE O PRAZO (OBRIGATÓRIO).
    
    FORMATO HTML (LIMPO, sem <html>):
    Agrupe por temas (ex: <h3>Editais</h3>).
    Use esta estrutura para CADA item:
    <li>
        <a href="LINK">ACESSAR ➜</a>
        <strong>TÍTULO</strong>
        <span class="resumo">Resumo curto.</span><br>
        <span class="prazo">📅 Prazo: DATA</span>
    </li>
    Se sem data: <span class="prazo">⚠️ Prazo: Verificar Edital</span>
    DADOS: {texto_bruto}
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, headers={'Content-Type': 'application/json'})
        if resp.status_code == 200:
            raw_text = resp.json()['candidates'][0]['content']['parts'][0]['text']
            return formatar_html(raw_text.replace("```html", "").replace("```", ""))
        else:
            raise Exception(f"Erro Gemini: {resp.text}")
    except Exception as e:
        raise e

def obter_emails():
    if not GOOGLE_CREDENTIALS: return [EMAIL_REMETENTE]
    lista = [EMAIL_REMETENTE]
    try:
        gc = gspread.service_account_from_dict(json.loads(GOOGLE_CREDENTIALS))
        raw = gc.open("Sentinela Emails").sheet1.col_values(3)
        for e in raw:
            if "@" in e and "email" not in e.lower() and e.strip() not in lista:
                lista.append(e.strip())
        return lista
    except:
        return lista # Retorna pelo menos o admin se a planilha falhar

def enviar(html, destinos):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_APP)
        
        for email in destinos:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_REMETENTE
            msg['To'] = email
            msg['Subject'] = f"Sentinela Física Médica - {datetime.now().strftime('%d/%m')}"
            msg.attach(MIMEText(html, 'html'))
            server.sendmail(EMAIL_REMETENTE, email, msg.as_string())
            print(f"📤 Enviado: {email}")
            
        server.quit()
    except Exception as e:
        raise e

if __name__ == "__main__":
    print("🚀 Sentinela Iniciado.")
    try:
        # 1. Busca
        dados = buscar_google_elite()
        if not dados: raise Exception("Nenhum dado encontrado no Google Search.")
        
        # 2. IA e Layout
        email_html = processar_ia(dados)
        
        # 3. Lista de Emails
        destinatarios = obter_emails()
        
        # 4. Envio
        enviar(email_html, destinatarios)
        print("🏁 Finalizado com sucesso.")
        
    except Exception as e:
        notificar_erro_admin(str(e))
