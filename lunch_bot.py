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
        # Vi går direkt mot Compass Groups API istället för att skrapa hemsidan
        # Detta är mycket mer stabilt och blockeras inte
        api_url = "https://eu-central-1.aws.data.mongodb-api.com/app/compass-gastronomy-restaurants-puvoc/endpoint/get_menu"
        params = {
            'restaurant_id': '650974892c556b6b3e700a89', # ID för Södra Porten
            'language': 'sv'
        }
        
        res = requests.get(api_url, params=params, timeout=15)
        if res.status_code != 200:
            return "⚠️ Kunde inte hämta menyn från Södra Porten."
            
        data = res.json()
        if not data or 'days' not in data:
            return "⚠️ Ingen meny tillgänglig."
            
        # Hitta dagens meny i JSON-datan
        today_idx = datetime.now().weekday()
        if today_idx >= 5: return "Helg!"
        
        # Compass API returnerar ofta menyer per vecka
        day_data = data['days'][today_idx]
        menu_items = []
        
        for menu in day_data.get('menus', []):
            dish = menu.get('menu_item_name', '')
            if dish:
                # Rensa bort onödig text och lägg till punkt
                clean_dish = dish.strip().replace('*', '').replace('_', '')
                menu_items.append(f"• {clean_dish}")
                
        return "\n".join(menu_items) if menu_items else "⚠️ Inga rätter hittades för idag."
        
    except Exception as e:
        return f"❌ Fel Södra Porten: {str(e)}"

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
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
    except Exception as e:
        print(f"Telegram fel: {e}")

if __name__ == "__main__":
    asyncio.run(main())
