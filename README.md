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

## A note on the order-matching engine

The core of this project — matching buy and sell orders in `app/views.py` — is implemented as a fairly long, deeply nested set of conditionals handling partial fills, exact matches, and order splitting across both the buy and sell sides. It works, but it's dense and has a fair amount of duplication between the buy and sell branches.

I've deliberately left this logic untouched while preparing the repository for publication, rather than refactoring it, because restructuring order-matching logic carries a real risk of silently changing its behavior — and getting it wrong in a piece of code that moves (simulated) money is worse than leaving it verbose. If I were to revisit this project, extracting a single shared `match_order()` function parameterized by order side would be the natural next step to reduce duplication safely, backed by tests that pin down the current behavior first.

## Purpose

Personal project built to explore full-stack web development with Django, working with a NoSQL database (MongoDB), and simulating financial/trading logic.
