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

def scrape_nya_etage():
    try:
        url = "https://nyaetage.se/"
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        res.encoding = 'utf-8' 
        soup = BeautifulSoup(res.text, 'html.parser')
        
        day_num = get_day_number()
        day_card = soup.find('div', attrs={'data-day': str(day_num)})
        
        if not day_card:
            return "⚠️ Hittade inte dagens meny-kort."

        items_container = day_card.find('div', class_='menu-items')
        if not items_container:
            return "⚠️ Hittade inte rätterna i boxen."

        dagens = []
        veggo = ""
        
        for text in items_container.stripped_strings:
            text = text.lstrip('>').lstrip('•').strip().replace('*', '').replace('_', '')
            if len(text) > 5 and text.lower() != "idag":
                if "veg/" in text.lower() or "vegan" in text.lower():
                    if text not in veggo:
                        veggo = f"\n🥗 *Vegetariskt*\n• {text}"
                else:
                    if f"• {text}" not in dagens:
                        dagens.append(f"• {text}")

        meny = "\n".join(dagens)
        if veggo:
            meny += veggo
            
        return meny if meny else "⚠️ Inga rätter hittades."
    except Exception as e:
        return f"❌ Fel vid skrapning: {str(e)}"

def scrape_sodra_porten():
    try:
        url = "https://sodraporten.kvartersmenyn.se/"
        
        # Försök 1: Vanlig webbläsare
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        
        # Försök 2: Om vi är blockerade, prova helt utan förklädnad
        if res.status_code == 403:
            res = requests.get(url, timeout=15)
            
        if res.status_code != 200:
            return f"⚠️ Sidan blockerar oss just nu (Felkod {res.status_code})."
            
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
        today_str = days[datetime.now().weekday()].lower()
        
        # Vi struntar helt i deras rutor och drar ut ALL text från hemsidan
        text_content = soup.get_text(separator='\n')
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        menu_items = []
        capture = False
        ignore_words = ["grönt", "dagens", "sallad", "action", "fresh", "betala", "pris", "inkl", "öppet", "husmanskost", "pogre"]
        
        for line in lines:
            lower_line = line.lower()
            
            # Kollar om raden BARA innehåller ett dagnamn
            if any(lower_line == d.lower() for d in days):
                if lower_line == today_str:
                    capture = True
                else:
                    capture = False
                continue
                
            if capture:
                # Sluta läsa om vi når slutet på menyn
                if "inkl" in lower_line or "öppet" in lower_line or "pris fr" in lower_line:
                    break
                    
                # Plocka maten
                if len(line) > 10:
                    if not any(lower_line.startswith(iw) for iw in ignore_words) and lower_line not in ignore_words:
                        clean_line = line.replace('*', '').replace('_', '').replace('"', '').strip()
                        if f"• {clean_line}" not in menu_items:
                            menu_items.append(f"• {clean_line}")
                            
        return "\n".join(menu_items) if menu_items else "⚠️ Sidan lästes, men inga maträtter matchade."
    except Exception as e:
        return f"❌ Fel: {str(e)}"

async def main():
    if datetime.now().weekday() >= 5: 
        return 
    
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
