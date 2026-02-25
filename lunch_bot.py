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
        target_url = "https://sodraporten.kvartersmenyn.se/"
        # Vi använder AllOrigins som en tunnel för att komma runt IP-blockeringen!
        proxy_url = f"https://api.allorigins.win/get?url={target_url}"
        
        res = requests.get(proxy_url, timeout=20)
        
        if res.status_code != 200:
            return f"⚠️ Tunneln svarade inte (Felkod {res.status_code})."
            
        # Packa upp den gömda webbsidan
        data = res.json()
        html_content = data.get('contents', '')
        
        if not html_content:
            return "⚠️ Kunde inte hämta sidan genom tunneln."
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
        today_str = days[datetime.now().weekday()].lower()
        
        # 1. Hitta menylådan
        menu_div = soup.find('div', class_='meny') or soup.find('div', class_='menu_perc_div')
        
        if not menu_div:
            # Reservplan: Leta efter rubriken och ta dess låda
            day_tag = soup.find(lambda t: t.name in ['strong', 'b', 'h3', 'h4'] and today_str.lower() in t.get_text().lower())
            if day_tag:
                menu_div = day_tag.parent
                
        if not menu_div:
            return "⚠️ Hittade inte meny-containern på sidan."

        # 2. Den platta metoden: Gör om <br> till radbrytningar
        for br in menu_div.find_all('br'):
            br.replace_with('\n')
            
        text_content = menu_div.get_text(separator='\n')
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        menu_items = []
        capture = False
        ignore_words = ["grönt", "dagens", "sallad", "action", "fresh", "betala", "pris", "inkl", "öppet", "***", "husmanskost", "pogre"]
        
        # 3. Läs rad för rad
        for line in lines:
            lower_line = line.lower()
            
            # Kolla om raden är en veckodag
            is_day = False
            for d in days:
                if lower_line == d.lower() or lower_line.startswith(d.lower() + ":"):
                    is_day = True
                    if d.lower() == today_str.lower():
                        capture = True # Dagens meny startar!
                    else:
                        capture = False # Vi nådde nästa dag!
                    break
                    
            if is_day:
                continue
                
            if capture:
                # Kolla om vi nått botten av menyn
                if "inkl" in lower_line or "öppet" in lower_line or "pris fr" in lower_line:
                    break
                    
                # Rensa och spara rätterna
                if len(line) > 8:
                    if not any(lower_line.startswith(iw) for iw in ignore_words) and lower_line not in ignore_words:
                        clean_line = line.replace('*', '').replace('_', '').replace('"', '').strip()
                        if f"• {clean_line}" not in menu_items:
                            menu_items.append(f"• {clean_line}")
                            
        return "\n".join(menu_items) if menu_items else "⚠️ Koden läste rutan men hittade inga rätter."
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
