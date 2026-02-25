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
        # Låtsas vara en riktig webbläsare för att undvika att bli blockerad
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, timeout=15, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
        today = days[datetime.now().weekday()].lower()
        
        menu_items = []
        capture = False
        
        # Städa bort deras rubriker och skräpord
        ignore_words = ["grönt och gott", "dagens husman", "sallad", "action", "fresh market", "betala efter", "***husmanskostens", "pogre", "pris fr"]
        
        # Vi läser all text på hela webbsidan som en bok, uppifrån och ner
        for text in soup.stripped_strings:
            text_clean = text.strip()
            text_lower = text_clean.lower()
            
            # Kollar om vi stöter på en ensam veckodag
            if text_lower in [d.lower() for d in days]:
                if text_lower == today:
                    capture = True  # Nu börjar dagens meny!
                    continue
                elif capture:
                    break  # Vi nådde nästa dags meny, sluta kopiera!
                else:
                    continue  # En gammal dag, ignorera
                    
            if capture and len(text_clean) > 4:
                # Kolla om vi nått botten av menyn (t.ex. på fredagar)
                if "inkl. smör" in text_lower or "öppet:" in text_lower or "pris fr" in text_lower:
                    break
                    
                # Ta bort deras rubriker
                if not any(text_lower.startswith(iw) for iw in ignore_words) and text_lower not in ignore_words:
                    if f"• {text_clean}" not in menu_items:
                        menu_items.append(f"• {text_clean}")
                        
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
