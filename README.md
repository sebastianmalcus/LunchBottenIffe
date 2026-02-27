# 🍴 LunchBottenIffe

En automatiserad lunch-bot för Telegram som levererar dagens menyer från **Nya Etage** och **Södra Porten** i Mölndal direkt till din kanal.

## 🚀 Funktioner
* **Automatisk skrapning:** Hämtar menyer varje vardag morgon via GitHub Actions.
* **Smart formatering:** Sorterar rätter och lägger vegetariska alternativ längst ner för bättre läsbarhet.
* **Direktlänkar:** Snabbåtkomst till restaurangernas egna sidor via inbäddade länkar.
* **Dagens Visdomsord:** Varje meddelande avslutas med ett internationellt citat som automatiskt översätts till svenska.
* **Felhantering:** Inbyggda fallbacks för att hantera API-ändringar eller nätverksproblem utan att boten dör.

## 🛠 Teknisk lösning
Projektet har utvecklats genom en iterativ process för att övervinna utmaningar med dynamiskt innehåll:

1.  **Web Scraping (BeautifulSoup4):** För Nya Etage läser boten av HTML-strukturen direkt från hemsidan.
2.  **Mashie/Matilda API-integration:** Södra Portens meny visade sig ligga i en skyddad `iframe`. Boten har konfigurerats för att prata direkt med Matilda Platforms API för att hämta JSON-data på ett stabilt sätt.
3.  **Översättnings-motor:** Använder *ZenQuotes API* kombinerat med *MyMemory Translation API* för att leverera dagliga citat på svenska.
4.  **GitHub Actions:** Boten körs helt serverlöst via ett schemalagt "Cron-jobb" (måndag-fredag kl 08:30).

## 📦 Installation & Konfiguration

### Förutsättningar
* Python 3.9+
* En Telegram-bot (skapad via BotFather)
* Ett GitHub-repo för hosting

### Miljövariabler (Secrets)
För att köra boten krävs följande `Repository Secrets` i ditt GitHub-repo:
* `TELEGRAM_TOKEN`: Din bots unika token.
* `TELEGRAM_CHAT_ID`: ID för den kanal/chatt dit menyn ska skickas.

### Installation
1. Klona repot:
   ```bash
   git clone [https://github.com/DITT-ANVÄNDARNAMN/LunchBottenIffe.git](https://github.com/DITT-ANVÄNDARNAMN/LunchBottenIffe.git)
