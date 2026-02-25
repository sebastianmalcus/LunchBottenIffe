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
        # En extremt robust User-Agent så Kvartersmenyn tror vi är Chrome på Windows
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
        res = requests.get(url, timeout=15, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        if not soup.body:
            return "⚠️ Kunde inte ladda sidan (blockerad?)."

        days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
        today = days[datetime.now().weekday()].lower()
        
        # Hämta ALL text från hela sidan och dela upp den rad för rad
        all_text = soup.body.get_text(separator='\n', strip=True)
        lines = all_text.split('\n')
        
        menu_items = []
        capture = False
        
        # Ord vi vill kasta i papperskorgen
        ignore_words = ["grönt", "dagens", "sallad", "action", "fresh market", "betala", "pris", "pogre", "inkl.", "öppet:", "husmanskost"]
        
        for line in lines:
            clean_line = line.strip().replace('*', '').replace('_', '')
            lower_line = clean_line.lower()
            
            # Kolla om raden är en veckodag (ex "Onsdag" eller "Onsdag:")
            is_day_header = False
            for d in days:
                if lower_line == d.lower() or lower_line.startswith(d.lower() + ":"):
                    is_day_header = True
                    if lower_line.startswith(today):
                        capture = True
                    else:
                        capture = False
                    break
            
            if is_day_header:
                continue # Gå till nästa rad så vi inte skriver ut själva ordet "Onsdag"
                
            if capture and len(clean_line) > 8:
                # Kolla om vi nått botten av sidan/menyn
                if "inkl. smör" in lower_line or "öppet:" in lower_line or "pris fr" in lower_line:
                    break
                    
                # Rensa bort skräp-rubrikerna
                if not any(lower_line.startswith(iw) for iw in ignore_words) and lower_line not in ignore_words:
                    item = f"• {clean_line}"
                    if item not in menu_items:
                        menu_items.append(item)
                        
        return "\n".join(menu_items) if menu_items else "⚠️ Hittade text men inga maträtter för idag."
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
