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
        
        # FIX: Tvinga rätt teckenkodning (UTF-8) så ÅÄÖ ser bra ut
        res.encoding = 'utf-8' 
        
        soup = BeautifulSoup(res.text, 'html.parser')
        day_num = get_day_number()
        
        day_card = soup.find('div', attrs={'data-day': str(day_num)})
        if not day_card:
            return "⚠️ Hittade inte dagens kort."

        items_container = day_card.find('div', class_='menu-items')
        if not items_container:
            return "⚠️ Hittade inte menu-items."

        # Vi plockar alla rader och delar upp dem
        rows = items_container.find_all('p')
        dagens_ratter = []
        veg_vegan = ""

        for row in rows:
            text = row.get_text(strip=True).lstrip('>').strip()
            if not text:
                continue
            
            # Sortera ut Vegetariskt/Veganskt
            if "veg/" in text.lower() or "vegan" in text.lower():
                veg_vegan = f"\n🥗 *Vegetariskt/Vegan*\n• {text}"
            else:
                dagens_ratter.append(f"• {text}")

        # Sätt ihop texten snyggt
        meny_output = "\n".join(dagens_ratter)
        if veg_vegan:
            meny_output += veg_vegan
            
        return meny_output if dagens_ratter else "⚠️ Inga rätter hittades."

    except Exception as e:
        return f"❌ Fel: {str(e)}"

async def main():
    if datetime.now().weekday() >= 5: return 
    
    bot = Bot(token=TOKEN)
    etage_meny = scrape_nya_etage()
    
    dag_namn = ["MÅNDAG", "TISDAG", "ONSDAG", "TORSDAG", "FREDAG"][datetime.now().weekday()]
    
    msg = (
        f"🍴 *LUNCH {dag_namn}* 🍴\n\n"
        f"📍 *Nya Etage*\n{etage_meny}\n\n"
        "Smaklig måltid!"
    )
    
    try:
        # MarkdownV2 kan vara petigt, vi kör vanlig Markdown här för stabilitet
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
    except Exception as e:
        print(f"Telegram fel: {e}")

if __name__ == "__main__":
    asyncio.run(main())
