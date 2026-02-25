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
        html_content = ""
        
        # Försök 1: Direkt anrop med ordentlig förklädnad
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'sv,en-US;q=0.7,en;q=0.3'
        }
        
        res = requests.get(target_url, timeout=10, headers=headers)
        if res.status_code == 200:
            res.encoding = 'utf-8'
            html_content = res.text
        else:
            # Försök 2: Använd CodeTabs som en ny, starkare tunnel
            proxy_url = f"https://api.codetabs.com/v1/proxy?quest={target_url}"
            res_proxy = requests.get(proxy_url, timeout=20)
            
            if res_proxy.status_code == 200:
                html_content = res_proxy.text
            else:
                return f"⚠️ Både direktlänk (Fel {res.status_code}) och tunnel (Fel {res_proxy.status_code}) blockerades."

        soup = BeautifulSoup(html_content, 'html.parser')
        
        days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
        today_str = days[datetime.now().weekday()].lower()
        
        # 1. Hitta menylådan
        menu_div = soup.find('div', class_='meny') or soup.find('div', class_='menu_perc_div')
        
        if not menu_div:
            # Reservplan
            day_tag = soup.find(lambda t: t.name in ['strong', 'b', 'h3', 'h4'] and today_str.lower() in t.get_text().lower())
            if day_tag:
                menu_div = day_tag.parent
                
        if not menu_div:
            return "⚠️ Hittade inte meny-containern på sidan."

        # 2. Platta till <br>-taggarna till riktiga radbrytningar
        for br in menu_div.find_all('br'):
            br.replace_with('\n')
            
        text_content = menu_div.get_text(separator='\n')
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        menu_items = []
        capture = False
        ignore_words = ["grönt", "dagens", "sallad", "action", "fresh", "betala", "pris", "inkl", "öppet", "***", "husmanskost", "pogre"]
        
        # 3. Filtrera raderna
        for line in lines:
            lower_line = line.lower()
            
            is_day = False
            for d in days:
                if lower_line == d.lower() or lower_line.startswith(d.lower() + ":"):
                    is_day = True
                    if d.lower() == today_str.lower():
                        capture = True
                    else:
                        capture = False
                    break
                    
            if is_day:
                continue
                
            if capture:
                if "inkl" in lower_line or "öppet" in lower_line or "pris fr" in lower_line:
                    break
                    
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
