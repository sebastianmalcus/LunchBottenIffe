import asyncio
import requests
import os
from bs4 import BeautifulSoup, NavigableString, Tag
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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36'}
        res = requests.get(url, timeout=15, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]
        today = days[datetime.now().weekday()].lower()
        
        # 1. Hitta taggen för dagens namn, VAR DEN ÄN ÄR på hela sidan
        day_tag = None
        for tag in soup.find_all(['strong', 'b', 'h3', 'h4', 'div', 'p']):
            if tag.get_text(strip=True).lower() == today:
                day_tag = tag
                break
                
        # Fallback om de skrivit typ "Onsdag 25/2"
        if not day_tag:
            for tag in soup.find_all(['strong', 'b', 'h3', 'h4']):
                if tag.get_text(strip=True).lower().startswith(today):
                    day_tag = tag
                    break

        if not day_tag:
            return "⚠️ Hittade inte dagens rubrik på sidan."

        menu_items = []
        ignore_words = ["grönt", "dagens", "sallad", "action", "fresh", "betala", "pris", "inkl", "öppet", "***", "husmanskost", "pogre"]
        
        # 2. Gå igenom all text och alla taggar som ligger DIREKT EFTER rubriken
        for sibling in day_tag.next_siblings:
            text = ""
            
            if isinstance(sibling, NavigableString):
                text = str(sibling).strip()
            elif isinstance(sibling, Tag):
                # Om vi stöter på en tjock rubrik med NÄSTA dags namn, då är vi klara!
                if sibling.name in ['strong', 'b', 'h3', 'h4']:
                    sibling_text = sibling.get_text(strip=True).lower()
                    if any(d.lower() in sibling_text for d in days if d.lower() != today):
                        break 
                
                # Plocka text från vanliga taggar, strunta i <br> och <i>
                if sibling.name not in ['br', 'i', 'hr']:
                    text = sibling.get_text(strip=True)
                    
            if not text:
                continue
                
            clean_text = text.replace('*', '').replace('_', '').replace('"', '')
            lower_clean = clean_text.lower()
            
            # För säkerhets skull: Om texten i sig är ett dagnamn, sluta leta
            if any(lower_clean == d.lower() for d in days if d.lower() != today):
                break
                
            # 3. Sortera ut rätterna från skräpet
            if len(clean_text) > 8:
                if not any(lower_clean.startswith(iw) for iw in ignore_words) and lower_clean not in ignore_words:
                    item = f"• {clean_text}"
                    if item not in menu_items:
                        menu_items.append(item)
                        
        return "\n".join(menu_items) if menu_items else "⚠️ Inga rätter hittades under rubriken."
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
