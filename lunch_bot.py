import asyncio
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_day_number():
    # Returnerar 1 för måndag, 2 för tisdag... upp till 5 för fredag
    return datetime.now().weekday() + 1

def scrape_nya_etage():
    try:
        url = "https://nyaetage.se/"
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Hämta rätt dag-nummer (1-5)
        day_num = get_day_number()
        
        # Hitta rätt kort med hjälp av data-day attributet
        # Ex: <div class="menu-card" data-day="3"> för onsdag
        day_card = soup.find('div', class_='menu-card', attrs={'data-day': str(day_num)})
        
        if not day_card:
            return f"⚠️ Hittade inte kortet för dag {day_num} (Nya Etage)."

        # Hämta containern för rätterna
        menu_container = day_card.find('div', class_='menu-items')
        if not menu_container:
            return "⚠️ Hittade kortet men inte rätterna (menu-items saknas)."

        # Plocka alla p-taggar (rätterna)
        rows = menu_container.find_all('p')
        menu_items = []
        for row in rows:
            text = row.get_text(strip=True).lstrip('>').strip()
            if text and len(text) > 2:
                menu_items.append(f"• {text}")
        
        return "\n".join(menu_items) if menu_items else "⚠️ Inga rätter hittades i containern."

    except Exception as e:
        return f"❌ Fel vid skrapning: {str(e)}"

def scrape_sodra_porten():
    # Vi behåller en förenklad version för Södra Porten
    try:
        url = "https://sodraporten.kvartersmenyn.se/"
        res = requests.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
        current_day = days[datetime.now().weekday()]
        
        header = soup.find(lambda t: t.name in ["h3", "h4"] and current_day.lower() in t.get_text().lower())
        if header:
            div = header.find_next_sibling('div')
            if div:
                items = [f"• {p.get_text(strip=True)}" for p in div.find_all('p') if len(p.get_text()) > 5]
                if items: return "\n".join(items)
        return "⚠️ Kunde inte läsa dagens meny."
    except:
        return "❌ Tekniskt fel."

async def main():
    if datetime.now().weekday() >= 5: return # Helg-check
    
    bot = Bot(token=TOKEN)
    msg = (
        f"🍴 *LUNCH {['MÅNDAG','TISDAG','ONSDAG','TORSDAG','FREDAG'][datetime.now().weekday()]}* 🍴\n\n"
        f"📍 *Nya Etage*\n{scrape_nya_etage()}\n\n"
        f"📍 *Södra Porten*\n{scrape_sodra_porten()}\n\n"
        "Smaklig måltid!"
    )
    
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())
