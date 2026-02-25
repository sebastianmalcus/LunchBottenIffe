import asyncio
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_day_number():
    return datetime.now().weekday() + 1

def fix_encoding(text):
    # En rejäl tvätt för att tvinga fram ÅÄÖ om requests misslyckas
    try:
        return text.encode('latin1').decode('utf-8')
    except:
        return text

def scrape_nya_etage():
    try:
        url = "https://nyaetage.se/"
        # Vi använder en session för att vara mer stabila
        session = requests.Session()
        res = session.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        
        # Tvinga UTF-8 direkt på innehållet
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.content, 'html.parser', from_encoding='utf-8')
        
        day_num = get_day_number()
        day_card = soup.find('div', attrs={'data-day': str(day_num)})
        
        if not day_card:
            return "⚠️ Hittade inte dagens meny-kort."

        items_container = day_card.find('div', class_='menu-items')
        if not items_container:
            return "⚠️ Hittade inte rätterna i boxen."

        # Hitta alla rader med mat
        rows = items_container.find_all('p')
        dagens = []
        veggo = ""

        for row in rows:
            text = row.get_text(strip=True).lstrip('>').strip()
            if not text or len(text) < 3:
                continue
            
            # Sortera Veg/Vegan
            if "veg/" in text.lower() or "vegan" in text.lower():
                veggo = f"\n🥗 *Veg/Vegan*\n• {text}"
            else:
                dagens.append(f"• {text}")

        if not dagens and not veggo:
            return "⚠️ Tomt i containern."

        return "\n".join(dagens) + veggo

    except Exception as e:
        return f"❌ Fel: {str(e)}"

def scrape_sodra_porten():
    try:
        url = "https://sodraporten.kvartersmenyn.se/"
        res = requests.get(url, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
        current_day = days[datetime.now().weekday()]
        
        # Letar efter rubriken
        header = soup.find(lambda t: t.name in ["h3", "h4"] and current_day.lower() in t.get_text().lower())
        if header:
            menu_div = header.find_next_sibling('div')
            if menu_div:
                items = []
                for p in menu_div.find_all('p'):
                    txt = p.get_text(strip=True)
                    if len(txt) > 5:
                        items.append(f"• {txt}")
                return "\n".join(items) if items else "Hittade inga rätter."
        return "Menyn inte uppdaterad än."
    except:
        return "Kunde inte hämta menyn."

async def main():
    if datetime.now().weekday() >= 5: return 
    
    bot = Bot(token=TOKEN)
    etage = scrape_nya_etage()
    sodra = scrape_sodra_porten()
    
    dag = ["MÅNDAG", "TISDAG", "ONSDAG", "TORSDAG", "FREDAG"][datetime.now().weekday()]
    
    msg = (
        f"🍴 *LUNCH {dag}* 🍴\n\n"
        f"📍 *Nya Etage*\n{etage}\n\n"
        f"📍 *Södra Porten*\n{sodra}\n\n"
        "Smaklig måltid!"
    )
    
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())
