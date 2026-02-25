import asyncio
import requests
import os
from bs4 import BeautifulSoup, NavigableString
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
            text = text.lstrip('>').lstrip('•').strip()
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
        res = requests.get(url, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
        today = days[datetime.now().weekday()]
        
        # 1. Hitta <strong> med dagens namn (precis som på din bild)
        day_tag = soup.find(lambda t: t.name in ['strong', 'b', 'h3'] and today.lower() in t.get_text(strip=True).lower())
        
        if not day_tag:
            return "⚠️ Hittade inte dagens rubrik på sidan."

        menu_items = []
        # Ord vi ska rensa bort
        ignore_words = ["grönt och gott", "dagens husman", "sallad", "action", "fresh market", "betala efter", "***husmanskostens"]
        
        # 2. Stega igenom allt som kommer EFTER <strong>-taggen
        current = day_tag.next_sibling
        
        while current:
            # Avbryt om vi plötsligt stöter på nästa dags rubrik
            if current.name in ['strong', 'b', 'h3']:
                break
                
            # NavigableString = Bara den rena texten (ignorerar <br> och osynliga <i>-taggar)
            if isinstance(current, NavigableString):
                text = current.strip()
                
                # Om texten i sig är ett annat dagsnamn, avbryt
                if any(d.lower() == text.lower() for d in days if d.lower() != today.lower()):
                    break
                    
                if len(text) > 5 and not any(text.lower().startswith(iw) for iw in ignore_words):
                    if f"• {text}" not in menu_items:
                        menu_items.append(f"• {text}")
                        
            current = current.next_sibling
            
        return "\n".join(menu_items) if menu_items else "⚠️ Inga rätter hittades under dagen."
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
