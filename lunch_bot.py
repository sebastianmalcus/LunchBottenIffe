import asyncio
import requests
import os
import random
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_day_number():
    return datetime.now().weekday() + 1 # Returnerar dagens index (1-5)

def get_swedish_wisdom():
    try:
        # Hämtar dagens citat på engelska
        res = requests.get("https://zenquotes.io/api/today", timeout=5)
        if res.status_code == 200:
            data = res.json()[0]
            eng_quote = data['q']
            author = data['a']
            
            # Översätter till svenska via MyMemory API
            trans_url = f"https://api.mymemory.translated.net/get?q={eng_quote}&langpair=en|sv"
            trans_res = requests.get(trans_url, timeout=5)
            if trans_res.status_code == 200:
                swe_quote = trans_res.json()['responseData']['translatedText']
                return f"_{swe_quote}_ \n— *{author}*"
        return "Ät lunch, annars blir du hungrig."
    except:
        return "En mätt mage är en glad mage."

def scrape_nya_etage():
    try:
        url = "https://nyaetage.se/"
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        res.encoding = 'utf-8' 
        soup = BeautifulSoup(res.text, 'html.parser')
        
        day_num = get_day_number()
        day_card = soup.find('div', attrs={'data-day': str(day_num)})
        
        if not day_card: return "⚠️ Hittade inte dagens meny."

        dagens = []
        veggo = ""
        items_container = day_card.find('div', class_='menu-items')
        
        for text in items_container.stripped_strings:
            text = text.lstrip('>• ').strip().replace('*', '')
            if len(text) > 5 and text.lower() != "idag":
                if "veg/" in text.lower() or "vegan" in text.lower():
                    veggo = f"\n🥗 *Vegetariskt*\n• {text}"
                else:
                    dagens.append(f"• {text}")

        meny = "\n".join(dagens)
        if veggo: meny += f"\n{veggo}"
        return meny
    except Exception as e:
        return f"❌ Fel Etage: {str(e)}"

def scrape_sodra_porten():
    try:
        url = "https://compass.mashie.matildaplatform.com/public/app/s%C3%B6dra+porten/e64c2893?country=se"
        res = requests.get(url, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        today_date = datetime.now().strftime('%d %b').lower()
        day_panel = None
        for p in soup.find_all('div', class_='panel'):
            header = p.find('div', class_='panel-heading')
            if header and today_date in header.get_text().lower():
                day_panel = p
                break
        
        if not day_panel: day_panel = soup.find('div', class_='panel-primary')
        if not day_panel: return "⚠️ Hittade inte dagens meny."

        dagens, veggo = [], ""
        for item in day_panel.find_all('div', class_='list-group-item-menu'):
            cat = item.find('strong', class_='app-alternative-name')
            dish = item.find('div', class_='app-daymenu-name')
            if dish:
                dish_text = dish.get_text(strip=True)
                if cat and "grönt" in cat.get_text().lower():
                    veggo = f"\n🥗 *Vegetariskt*\n• {dish_text}"
                else:
                    dagens.append(f"• {dish_text}")
                    
        meny = "\n".join(dagens)
        if veggo: meny += f"\n{veggo}"
        return meny
    except Exception as e:
        return f"❌ Fel Södra Porten: {str(e)}"

async def main():
    if datetime.now().weekday() >= 5: return 
    
    bot = Bot(token=TOKEN)
    etage = scrape_nya_etage()
    sodra = scrape_sodra_porten()
    wisdom = get_swedish_wisdom()
    
    dag = ["MÅNDAG", "TISDAG", "ONSDAG", "TORSDAG", "FREDAG"][datetime.now().weekday()]
    
    msg = (
        f"🍴 *LUNCH {dag}* 🍴\n\n\n"
        f"📍 *Nya Etage* [[LÄNK](https://nyaetage.se/)]\n{etage}\n\n\n"
        f"📍 *Södra Porten* [[LÄNK](https://www.compass-group.se/restauranger-och-menyer/ovriga-restauranger/sodra-porten/)]\n{sodra}\n\n\n"
        f"💡 *Dagens visdomsord:*\n{wisdom}\n\n"
        "--- \n"
        "Smaklig måltid!"
    )
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown', disable_web_page_preview=True)
    except:
        await bot.send_message(chat_id=CHAT_ID, text=msg.replace('*', '').replace('_', ''))

if __name__ == "__main__":
    asyncio.run(main())
