# Exchange — Piattaforma di Trading BTC Simulato

🇬🇧 [Read in English](README.md)

Applicazione web full-stack sviluppata con Django che simula una piattaforma di trading Bitcoin, con MongoDB come database. Ogni utente ha un wallet con un saldo BTC simulato e un saldo fiat separato, può inserire ordini di acquisto/vendita, e gli ordini vengono incrociati tra loro da un motore di order-matching personalizzato.

## Funzionalità
- Registrazione e autenticazione utenti (login/logout)
- Portafoglio utente con saldo BTC e saldo fiat separati
- Inserimento ordini di acquisto e vendita BTC
- Order book con storico degli ordini
- Sezione di monitoraggio profitti/perdite
- Pannello di amministrazione Django

## Tecnologie utilizzate
- Python 3
- Django 3.0
- MongoDB (tramite djongo)
- Bootstrap 3, HTML/CSS

## Struttura del progetto
```
exchange/    → configurazione del progetto Django
app/         → logica applicativa
  models.py  → modelli Profile e Order
  views.py   → logica di business, incluso il motore di order-matching
  forms.py   → form di registrazione e ordini
  urls.py    → routing
  templates/ → interfaccia HTML
```

## Configurazione

1. Assicurati che sia in esecuzione un'istanza MongoDB locale (default: `localhost:27017`, senza autenticazione).
2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```
   > **Nota di compatibilità**: `djongo` è strettamente legato a versioni specifiche di Django/pymongo. Se `pip install` fallisce o le migrazioni danno errore, controlla la documentazione di djongo per la combinazione corretta rispetto alla tua versione di Python — è un punto di attrito noto del progetto djongo stesso, non specifico di questo codice.
3. Copia `.env.example` in `.env` e inserisci la tua secret key (e le credenziali MongoDB, se la tua istanza richiede autenticazione):
   ```bash
   cp .env.example .env
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
4. Esegui le migrazioni e avvia il server:
   ```bash
   python manage.py makemigrations app
   python manage.py migrate
   python manage.py createsuperuser   # opzionale, per il pannello admin
   python manage.py runserver
   ```

I nuovi utenti ricevono un piccolo saldo BTC casuale (1-10 BTC) alla registrazione, così hanno subito qualcosa da scambiare.

## Note di sicurezza

- La secret key di Django e i parametri di connessione a MongoDB **non sono mai** scritti direttamente nel codice: vengono caricati da un file `.env` locale, escluso dal controllo di versione tramite `.gitignore`.
- Questo progetto non ha alcuna integrazione con exchange, wallet o blockchain reali — tutti i saldi e gli scambi sono interamente simulati all'interno del database dell'app. Non ci sono fondi reali, API key o chiavi private in nessun punto di questo codice.

## Una nota sul motore di order-matching

Il cuore di questo progetto — l'incrocio tra ordini di acquisto e vendita in `app/views.py` — è implementato come una sequenza piuttosto lunga di condizioni annidate in profondità, che gestisce riempimenti parziali, corrispondenze esatte e frazionamento degli ordini su entrambi i lati (buy e sell). Funziona, ma è denso e presenta una discreta duplicazione tra i due rami.

Ho scelto deliberatamente di non toccare questa logica durante la preparazione del repository per la pubblicazione, invece di refactorizzarla, perché ristrutturare una logica di order-matching comporta un rischio reale di modificarne silenziosamente il comportamento — e sbagliare in un pezzo di codice che movimenta (seppur simulato) denaro è peggio che lasciarlo verboso. Se dovessi riprendere in mano questo progetto, estrarre un'unica funzione condivisa `match_order()` parametrizzata sul lato dell'ordine sarebbe il passo naturale per ridurre la duplicazione in modo sicuro, supportato da test che fissino prima il comportamento attuale.

## Scopo

Progetto personale realizzato per approfondire lo sviluppo web full-stack con Django, l'utilizzo di un database NoSQL (MongoDB) e la simulazione di logiche finanziarie/di trading.
