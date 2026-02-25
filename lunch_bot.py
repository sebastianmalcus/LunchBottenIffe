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
        # Detta är den stabila API-vägen för Matilda Platform (Mashie)
        # ID:t e648ad20... är det som styr Södra Porten
        url = "https://menu.matildaplatform.com/api/v1/public/menus/e648ad20-80fd-4f24-a7b2-0f2d67d2b44d/days?range=0"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
            'Accept': 'application/json'
        }
        
        res = requests.get(url, headers=headers, timeout=15)
        
        if res.status_code != 200:
            return f"⚠️ Södra Porten svarade inte (Kod {res.status_code})"
            
        data = res.json()
        today_str = datetime.now().strftime('%Y-%m-%d')
        menu_items = []
        
        # Leta upp dagens datum i listan från API:et
        for day in data:
            if day.get('date', '').split('T')[0] == today_str:
                for menu in day.get('menus', []):
                    dish = menu.get('description', '')
                    category = menu.get('name', '')
                    
                    if dish:
                        clean_dish = dish.strip().replace('\r', '').replace('\n', ' ').replace('  ', ' ')
                        # Snygga till vegetariskt baserat på kategori eller innehåll
                        if "grönt" in category.lower() or "vegetarisk" in clean_dish.lower():
                            menu_items.append(f"🥗 *Veg:* {clean_dish}")
                        else:
                            menu_items.append(f"• {clean_dish}")
                break
        
        return "\n".join(menu_items) if menu_items else "⚠️ Inga rätter hittades i systemet för idag."
        
    except Exception as e:
        return f"❌ Tekniskt fel: {str(e)}"

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
    except Exception:
        # Fallback utan Markdown-stjärnor om texten innehåller tecken som krockar
        await bot.send_message(chat_id=CHAT_ID, text=msg.replace('*', ''))

if __name__ == "__main__":
    asyncio.run(main())
