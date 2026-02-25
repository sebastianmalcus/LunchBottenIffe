import asyncio
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_swedish_day():
    days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"]
    return days[datetime.now().weekday()]

def scrape_sodra_porten():
    try:
        url = "https://sodraporten.kvartersmenyn.se/"
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        day_name = get_swedish_day()
        
        # Vi letar efter rubriken oavsett om det är h3, h4 eller strong
        target = soup.find(lambda t: t.name in ['h3', 'h4', 'strong'] and day_name.lower() in t.get_text().lower())
        
        if target:
            menu_items = []
            # Vi tittar på allt som kommer efter rubriken fram till nästa dag
            current = target.find_next()
            while current:
                if current.name in ['h3', 'h4', 'strong'] and any(d in current.get_text() for d in ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]) and day_name.lower() not in current.get_text().lower():
                    break
                
                txt = current.get_text(strip=True)
                # Vi vill bara ha rader som ser ut som faktiska maträtter (längre än 10 tecken)
                if len(txt) > 10 and day_name.lower() not in txt.lower():
                    # Undvik dubbletter
                    clean_txt = f"• {txt}"
                    if clean_txt not in menu_items:
                        menu_items.append(clean_txt)
                current = current.find_next()
            
            if menu_items: return "\n".join(menu_items[:6]) # Max 6 rätter för att hålla det snyggt
            
        return "⚠️ Hittade rubriken men kunde inte läsa rätterna."
    except Exception as e:
        return f"❌ Fel: {str(e)}"

def scrape_nya_etage():
    try:
        url = "https://nyaetage.se/"
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        day_name = get_swedish_day()
        
        # Hittar rubriken (t.ex. Onsdag) oavsett "IDAG"-bubblan
        header = soup.find(lambda t: t.name == 'h3' and day_name.lower() in t.get_text().lower())
        
        if header:
            # Gå till föräldra-boxen som innehåller all mat för den dagen
            box = header.find_parent('div')
            if box:
                # Plocka alla p-taggar och li-taggar
                lines = box.find_all(['p', 'li'])
                menu = []
                for l in lines:
                    t = l.get_text(strip=True).lstrip('>').strip()
                    # Rensa bort rubriken och korta ord
                    if len(t) > 5 and day_name.lower() not in t.lower() and "idag" not in t.lower():
                        menu.append(f"• {t}")
                if menu: return "\n".join(menu)

        return "⚠️ Hittade inte maten i boxen."
    except Exception as e:
        return f"❌ Fel: {str(e)}"

async def main():
    if get_swedish_day() in ["Lördag", "Söndag"]: return
    bot = Bot(token=TOKEN)
    
    # Hämta och skicka
    sodra = scrape_sodra_porten()
    etage = scrape_nya_etage()
    
    msg = (
        f"🍴 *LUNCH {get_swedish_day().upper()}* 🍴\n\n"
        f"📍 *Södra Porten*\n{sodra}\n\n"
        f"📍 *Nya Etage*\n{etage}\n\n"
        "Smaklig måltid!"
    )
    
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())
