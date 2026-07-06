# Exchange — Simulated BTC Trading Platform

🇮🇹 [Leggi in italiano](README.it.md)

A full-stack Django web application simulating a Bitcoin trading platform, backed by MongoDB. Users get a wallet with a simulated BTC balance and a fiat balance, can place buy/sell orders, and orders are matched against each other by a custom order-matching engine.

## Features
- User registration and authentication (login/logout)
- User wallet with separate BTC and fiat balances
- Placing buy and sell BTC orders
- Order book with order history
- Profit/loss tracking section
- Django admin panel

## Tech Stack
- Python 3
- Django 3.0
- MongoDB (via djongo)
- Bootstrap 3, HTML/CSS

## Project structure
```
exchange/    → Django project configuration
app/         → application logic
  models.py  → Profile and Order models
  views.py   → business logic, including the order-matching engine
  forms.py   → registration and order forms
  urls.py    → routing
  templates/ → HTML interface
```

## Setup

1. Make sure a local MongoDB instance is running (default: `localhost:27017`, no auth).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   > **Compatibility note**: `djongo` is tightly coupled to specific Django/pymongo versions. If `pip install` fails or migrations error out, check djongo's documentation for the combination that matches your Python version — this is a known friction point of the djongo project, not specific to this codebase.
3. Copy `.env.example` to `.env` and fill in your own secret key (and MongoDB credentials, if your instance requires auth):
   ```bash
   cp .env.example .env
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
4. Run migrations and start the server:
   ```bash
   python manage.py makemigrations app
   python manage.py migrate
   python manage.py createsuperuser   # optional, for the admin panel
   python manage.py runserver
   ```

New users are seeded with a small random BTC balance (1–10 BTC) on registration, so there's something to trade with immediately.

## Security notes

- The Django secret key and MongoDB connection details are **never** hardcoded — they're loaded from a local `.env` file, excluded from version control via `.gitignore`.
- This project has no integration with any real cryptocurrency exchange, wallet, or blockchain — all balances and trades are entirely simulated inside the app's own database. There are no real funds, API keys, or private keys involved anywhere in this codebase.

## The order-matching engine

Order matching lives in `app/matching.py`, as a standalone, dependency-free function (`match_order`) — no Django, no MongoDB required to use or test it. `app/views.py` handles the Django/database side (creating orders, persisting balances), and delegates all matching logic to this module.

**How it works**: incoming orders execute as true market orders, with no price limit protection (unlimited slippage). The engine walks the resting order book in best-price-first order — an incoming sell matches the highest bid first, an incoming buy matches the lowest ask first — consuming resting orders one at a time, **each at its own price**, until either the requested quantity is fully filled or the book runs out. Any unfilled remainder becomes a new resting order at the trader's originally submitted price. A self-trade (an order matching against the same profile's own resting order) closes both sides with no balance change.

**Why this design**: the original implementation had a real bug here — when a large order matched against resting orders from *multiple different users*, every fill was credited to the very first matched user's balance, regardless of who actually owned each order. This was caught with a plain-Python reproduction (see `app/test_matching.py`, `test_sell_spans_multiple_buyers_at_their_own_prices`) before writing any fix, specifically to confirm the bug with real numbers rather than by inspection alone.

**A second, smaller fix**: the original pre-check for placing a buy order compared the trader's fiat balance against the order's unit price alone (`fiatMoney >= price`), rather than the actual total cost (`price × quantity`) — meaning a trader could place a buy order far larger than they could actually afford. This is now checked correctly.

**Running the tests** (no MongoDB, no Django setup needed):
```bash
pip install pytest
pytest app/test_matching.py -v
```

## Purpose

Personal project built to explore full-stack web development with Django, working with a NoSQL database (MongoDB), and simulating financial/trading logic.

