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
            meny += f"\n{veggo}"
            
        return meny if meny else "⚠️ Inga rätter hittades."
    except Exception as e:
        return f"❌ Fel vid skrapning: {str(e)}"

def scrape_sodra_porten():
    try:
        url = "https://compass.mashie.matildaplatform.com/public/app/s%C3%B6dra+porten/e64c2893?country=se"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
        
        res = requests.get(url, headers=headers, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        today_date_str = datetime.now().strftime('%d %b').lower()
        panels = soup.find_all('div', class_='panel')
        day_panel = None
        
        for p in panels:
            header = p.find('div', class_='panel-heading')
            if header and today_date_str in header.get_text().lower():
                day_panel = p
                break
        
        if not day_panel:
            day_panel = soup.find('div', class_='panel-primary')

        if not day_panel:
            return "⚠️ Hittade inte dagens meny."

        dagens = []
        veggo = ""
        items = day_panel.find_all('div', class_='list-group-item-menu')
        
        for item in items:
            cat_tag = item.find('strong', class_='app-alternative-name')
            dish_tag = item.find('div', class_='app-daymenu-name')
            
            if dish_tag:
                dish_text = dish_tag.get_text(strip=True)
                cat_text = cat_tag.get_text(strip=True) if cat_tag else ""
                
                # Sorterar vegetariskt till egen variabel för att lägga den sist
                if "grönt" in cat_text.lower():
                    veggo = f"\n🥗 *Vegetariskt*\n• {dish_text}"
                else:
                    dagens.append(f"• {dish_text}")
                    
        meny = "\n".join(dagens)
        if veggo:
            meny += f"\n{veggo}"
            
        return meny if meny else "⚠️ Inga rätter hittades."
        
    except Exception as e:
        return f"❌ Fel Södra Porten: {str(e)}"

async def main():
    if datetime.now().weekday() >= 5: 
        return 
    
    bot = Bot(token=TOKEN)
    etage = scrape_nya_etage()
    sodra = scrape_sodra_porten()
    
    dag = ["MÅNDAG", "TISDAG", "ONSDAG", "TORSDAG", "FREDAG"][datetime.now().weekday()]
    
    # Skapar extra luft med dubbla radbrytningar mellan sektionerna
    msg = (
        f"🍴 *LUNCH {dag}* 🍴\n\n\n"
        f"📍 *Nya Etage*\n{etage}\n\n\n"
        f"📍 *Södra Porten*\n{sodra}\n\n\n"
        "_Smaklig måltid!_"
    )
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
    except Exception:
        await bot.send_message(chat_id=CHAT_ID, text=msg.replace('*', '').replace('_', ''))

if __name__ == "__main__":
    asyncio.run(main())
