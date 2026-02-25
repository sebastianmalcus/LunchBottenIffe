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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, timeout=15, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
        today = days[datetime.now().weekday()].lower()
        
        menu_div = soup.find('div', class_='meny') or soup.find('div', class_='menu_perc_div')
        if not menu_div:
            return "⚠️ Hittade inte meny-containern på sidan."

        menu_items = []
        capture = False
        
        # Aggressiv rensning av deras tråkiga underrubriker
        ignore_words = ["grönt", "dagens", "sallad", "action", "fresh market", "betala", "pris", "pogre"]
        
        for text in menu_div.stripped_strings:
            clean_text = text.strip().replace('*', '').replace('_', '')
            lower_text = clean_text.lower()
            
            # Kolla om raden BÖRJAR med en veckodag (fångar även "Onsdag:" etc.)
            matched_day = False
            for d in days:
                if lower_text.startswith(d.lower()):
                    matched_day = True
                    if d.lower() == today:
                        capture = True
                    elif capture:
                        capture = False # Vi har nått nästa dag, stäng av!
                    break
                    
            if matched_day:
                continue # Hoppa över själva dagnamnet
                
            if capture and len(clean_text) > 8: # En riktig maträtt är alltid längre än 8 tecken
                # Stoppa helt om vi når Kvartersmenyns sidfot
                if "inkl. smör" in lower_text or "öppet:" in lower_text:
                    break
                    
                # Rensa bort skräp-rubrikerna (och ***Husman***)
                if not any(lower_text.startswith(iw) for iw in ignore_words) and "***" not in lower_text:
                    item = f"• {clean_text}"
                    if item not in menu_items:
                        menu_items.append(item)
                        
        return "\n".join(menu_items) if menu_items else "⚠️ Inga rätter hittades för idag."
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
