import asyncio
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot

# --- INSTÄLLNINGAR ---
TOKEN = '8750781160:AAEUIEtY7B4ADcH4ZCnius2NEk_zzgs9C-I'
CHAT_ID = '5284259078'

def get_swedish_day():
    days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"]
    return days[datetime.now().weekday()]

def scrape_sodra_porten():
    try:
        url = "https://sodraporten.kvartersmenyn.se/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        day_name = get_swedish_day()
        
        # Hitta rätt dag i Kvartersmenyns struktur
        day_header = soup.find('h3', string=day_name)
        if not day_header: return "Kunde inte hitta menyn för idag."
        
        menu_div = day_header.find_next_sibling('div', class_='menu_perc_div')
        items = menu_div.find_all('p')
        
        menu_text = ""
        for item in items:
            # Rensar bort extra mellanslag och radbrytningar
            txt = item.get_text(strip=True).replace('\n', ' ')
            if txt: menu_text += f"• {txt}\n"
        return menu_text
    except Exception as e:
        return f"Fel vid hämtning: {e}"

def scrape_nya_etage():
    try:
        url = "https://nyaetage.se/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        day_name = get_swedish_day()
        
        # Nya Etage använder ofta h4 eller strong för dagarna
        day_tag = soup.find(['h4', 'strong'], string=lambda t: t and day_name in t)
        if not day_tag: return "Kunde inte hitta menyn för idag."
        
        # Hämta rätterna fram till nästa dag
        menu_items = []
        current = day_tag.find_next('p')
        while current and not any(d in current.get_text() for d in ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"]):
            text = current.get_text(strip=True)
            if text: menu_items.append(f"• {text}")
            current = current.find_next('p')
            
        return "\n".join(menu_items)
    except Exception as e:
        return f"Fel vid hämtning: {e}"

async def skicka_lunch_rapport():
    day = get_swedish_day()
    if day in ["Lördag", "Söndag"]:
        print("Det är helg!")
        return

    bot = Bot(token=TOKEN)
    
    print("Hämtar menyer...")
    sodra = scrape_sodra_porten()
    etage = scrape_nya_etage()
    
    meddelande = (
        f"🍴 *LUNCH {day.upper()}* 🍴\n\n"
        f"📍 *Restaurang Södra Porten*\n{sodra}\n\n"
        f"📍 *Restaurang Nya Etage*\n{etage}\n\n"
        "Smaklig måltid!"
    )
    
    await bot.send_message(chat_id=CHAT_ID, text=meddelande, parse_mode='Markdown')
    print("Skickat!")

if __name__ == "__main__":
    asyncio.run(skicka_lunch_rapport())
