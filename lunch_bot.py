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
        
        # Detta är magin som fixar "hÃ¶grevsburger"
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
        
        # 'stripped_strings' drar ut ALL text i boxen, oavsett vilka dolda taggar de ligger i
        for text in items_container.stripped_strings:
            text = text.lstrip('>').lstrip('•').strip()
            
            if len(text) > 5 and text.lower() != "idag":
                if "veg/" in text.lower() or "vegan" in text.lower():
                    if text not in veggo: # Förhindra dubbletter
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
        res = requests.get(url, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
        today = days[datetime.now().weekday()]
        
        menu_div = soup.find('div', class_='menu_perc_div')
        if not menu_div:
            return "⚠️ Hittade inte menyn på sidan."
            
        # Vi gör om hela deras meny till en ren textlista
        lines = list(menu_div.stripped_strings)
        
        today_menu = []
        capture = False
        # Ord vi vill rensa bort så att de inte dyker upp som "maträtter"
        ignore_words = ["grönt och gott", "dagens husman", "sallad", "action", "fresh market", "betala efter vikt"]
        
        for line in lines:
            # Börja kopiera rader när vi ser dagens namn
            if line.lower() == today.lower():
                capture = True
                continue
            
            # Sluta kopiera om vi stöter på en annan veckodag
            if capture and any(line.lower() == d.lower() for d in days if d.lower() != today.lower()):
                break
                
            if capture and len(line) > 5:
                # Skippa Kvartersmenyns egna underrubriker
                if not any(line.lower().startswith(iw) for iw in ignore_words):
                    if f"• {line}" not in today_menu:
                        today_menu.append(f"• {line}")
                        
        return "\n".join(today_menu) if today_menu else "⚠️ Menyn ej uppdaterad än."
    except Exception as e:
        return f"❌ Fel: {str(e)}"

async def main():
    if datetime.now().weekday() >= 5: return 
    
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
