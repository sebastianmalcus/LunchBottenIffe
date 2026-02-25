import asyncio
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_day_number():
    # Måndag=1, Tisdag=2, osv.
    return datetime.now().weekday() + 1

def scrape_nya_etage():
    try:
        url = "https://nyaetage.se/"
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        
        day_num = get_day_number()
        
        # Baserat på din bild: Vi letar efter kortet med rätt data-day attribut
        day_card = soup.find('div', attrs={'data-day': str(day_num)})
        
        if not day_card:
            return f"⚠️ Hittade inte kortet för dag {day_num}."

        # Din bild visar: <div class="menu-items"> innehåller rätterna
        items_container = day_card.find('div', class_='menu-items')
        
        if not items_container:
            return "⚠️ Hittade kortet men inte containern 'menu-items'."

        # Varje rätt verkar ligga i en p-tagg eller span enligt sajten
        rows = items_container.find_all(['p', 'span', 'div'], recursive=True)
        
        menu_items = []
        for row in rows:
            text = row.get_text(strip=True).lstrip('>').strip()
            # Filtrera bort tomma rader och dubbletter
            if len(text) > 5 and text not in menu_items:
                # Vi vill inte ha med kategorier som "Veg/Vegan" som egna rader om de ligger i samma
                menu_items.append(text)
        
        # Rensa bort eventuellt skräp (vi tar de unika raderna)
        final_menu = []
        for item in menu_items:
            # Undvik att lägga till samma text om den redan finns som del av en annan sträng
            if not any(item in existing for existing in final_menu):
                final_menu.append(f"• {item}")

        return "\n".join(final_menu) if final_menu else "⚠️ Inga rätter hittades i boxen."

    except Exception as e:
        return f"❌ Fel vid skrapning: {str(e)}"

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
    
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())
