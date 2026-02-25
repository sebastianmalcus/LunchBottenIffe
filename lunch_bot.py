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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0'}
        html = ""
        
        try:
            res = requests.get(url, timeout=10, headers=headers)
            if res.status_code == 200: 
                res.encoding = 'utf-8'
                html = res.text
        except: pass
        
        if not html:
            try:
                res = requests.get(f"https://api.allorigins.win/get?url={url}", timeout=10)
                if res.status_code == 200: 
                    html = res.json().get('contents', '')
            except: pass

        if not html:
            return "⚠️ Kunde inte hämta menyn (Blockerad av Kvartersmenyn)."

        soup = BeautifulSoup(html, 'html.parser')
        
        menu_div = soup.find('div', class_='meny') or soup.find('div', class_='menu_perc_div')
        if not menu_div:
            return "⚠️ Hittade inte meny-rutan på sidan."

        for br in menu_div.find_all('br'):
            br.replace_with('\n')

        lines = [line.strip() for line in menu_div.get_text(separator='\n').split('\n') if line.strip()]
        
        days = ["måndag", "tisdag", "onsdag", "torsdag", "fredag"]
        today_idx = datetime.now().weekday()
        if today_idx >= 5: return "Helg!"
        today_str = days[today_idx]

        menu_items = []
        capture = False
        
        ignore_words = ["grönt", "dagens", "sallad", "action", "fresh", "betala", "pris", "inkl", "husmanskost", "lunchmeny", "pogre"]

        for line in lines:
            clean_line = line.replace('pogre', '').replace('*', '').replace('_', '').strip()
            low = clean_line.lower()
            
            is_day = False
            for d in days:
                if low == d or low.startswith(d + ":"):
                    is_day = True
                    capture = (d == today_str)
                    break
            
            if is_day:
                continue

            if capture:
                if "öppet" in low or "pris fr" in low or "inkl" in low or "restaurang" in low:
                    break
                
                if len(clean_line) > 8:
                    if not any(low.startswith(iw) for iw in ignore_words) and low not in ignore_words:
                        item = f"• {clean_line}"
                        if item not in menu_items:
                            menu_items.append(item)

        return "\n".join(menu_items) if menu_items else "⚠️ Hittade rutan men inga rätter för idag."
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
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
    except Exception as e:
        print(f"Telegram fel: {e}")

if __name__ == "__main__":
    asyncio.run(main())
