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

## Il motore di order-matching

La logica di matching vive in `app/matching.py`, come funzione autonoma e senza dipendenze (`match_order`) — non richiede né Django né MongoDB per essere usata o testata. `app/views.py` gestisce la parte Django/database (creazione ordini, persistenza dei saldi), e delega tutta la logica di matching a questo modulo.

**Come funziona**: gli ordini in ingresso vengono eseguiti come veri ordini di mercato, senza protezione di prezzo (slippage senza limite). Il motore scorre il book degli ordini in attesa dando priorità al miglior prezzo — una vendita in ingresso incrocia prima il prezzo di acquisto più alto, un acquisto in ingresso incrocia prima il prezzo di vendita più basso — consumando gli ordini uno alla volta, **ciascuno al proprio prezzo**, fino a soddisfare la quantità richiesta o esaurire il book. Qualsiasi residuo non eseguito diventa un nuovo ordine in attesa al prezzo originariamente inserito dal trader. Un self-trade (un ordine che incrocia un proprio ordine in attesa) chiude entrambi i lati senza alcun movimento di saldo.

**Perché questo design**: l'implementazione originale aveva qui un bug reale — quando un ordine grande si incrociava con ordini in attesa di *più utenti diversi*, ogni esecuzione veniva accreditata al saldo del primo utente incrociato, indipendentemente da chi possedesse realmente ciascun ordine. Il bug è stato individuato con una riproduzione in Python puro (vedi `app/test_matching.py`, `test_sell_spans_multiple_buyers_at_their_own_prices`) prima di scrivere qualsiasi correzione, proprio per confermarlo con numeri reali e non solo per ispezione visiva del codice.

**Una seconda correzione, più piccola**: il controllo preliminare per piazzare un ordine di acquisto confrontava il saldo fiat del trader con il solo prezzo unitario dell'ordine (`fiatMoney >= price`), invece del costo totale reale (`price × quantity`) — questo avrebbe permesso a un trader di piazzare un ordine di acquisto ben più grande di quanto potesse realmente permettersi. Ora viene controllato correttamente.

**Per eseguire i test** (senza MongoDB, senza configurazione Django):
```bash
pip install pytest
pytest app/test_matching.py -v
```

## Scopo

Progetto personale realizzato per approfondire lo sviluppo web full-stack con Django, l'utilizzo di un database NoSQL (MongoDB) e la simulazione di logiche finanziarie/di trading.

