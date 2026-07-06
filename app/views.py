from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
import random

from .forms import RegistrationForm, OrderForm
from .models import Profile, Order
from .matching import match_order, SELL, BUY

TYPE_SELL = 'Sell'
TYPE_BUY = 'Buy'


def _message_redirect(request, text, error=False):
    """Shared helper for the extremely common 'show a message, go home' pattern."""
    if error:
        messages.error(request, text)
    else:
        messages.success(request, text)
    return redirect('home')


def _as_profile_dict(cache, profile_model):
    """Builds (and caches) the plain-dict view of a Profile used by the
    matching engine, so multiple orders belonging to the same profile
    within a single matching run share and accumulate the same dict."""
    if profile_model.id not in cache:
        cache[profile_model.id] = {
            "id": profile_model.id,
            "BTC": profile_model.BTC,
            "fiatMoney": profile_model.fiatMoney,
            "profit": profile_model.profit,
            "_model": profile_model,
        }
    return cache[profile_model.id]


def _execute_market_order(taker_profile, side, quantity, price):
    """
    Creates the incoming order, matches it as a market order against the
    resting book on the opposite side (see app/matching.py for the
    matching rules), and persists every resulting change: fills, resting
    order updates, and profile balance updates.

    Returns True if the book had at least one resting order to match
    against (regardless of whether the incoming order was fully filled),
    False if the opposite book was completely empty.
    """
    opposite_type = TYPE_BUY if side == TYPE_SELL else TYPE_SELL
    engine_side = SELL if side == TYPE_SELL else BUY

    incoming_order = Order.objects.create(
        profile=taker_profile, price=price, quantity=quantity, type=side
    )

    profile_cache = {}
    taker_dict = _as_profile_dict(profile_cache, taker_profile)

    resting_models = list(Order.objects.filter(type=opposite_type, complete=False))
    book = []
    order_models_by_id = {}
    for resting_model in resting_models:
        maker_dict = _as_profile_dict(profile_cache, resting_model.profile)
        entry = {
            "id": resting_model._id,
            "profile": maker_dict,
            "price": resting_model.price,
            "quantity": resting_model.quantity,
            "complete": resting_model.complete,
        }
        book.append(entry)
        order_models_by_id[resting_model._id] = (entry, resting_model)

    book_was_empty = len(book) == 0

    result = match_order(
        engine_side,
        taker_dict,
        quantity=float(quantity),
        price=float(price),
        book=book,
        new_order_id=incoming_order._id,
    )

    # Persist changes to every resting order touched by the match.
    for entry, model in order_models_by_id.values():
        if entry["quantity"] != model.quantity or entry["complete"] != model.complete:
            model.quantity = entry["quantity"]
            model.complete = entry["complete"]
            model.save()

    # Persist balance changes for every profile touched (taker + any makers).
    for pdict in profile_cache.values():
        model = pdict["_model"]
        if (
            model.BTC != pdict["BTC"]
            or model.fiatMoney != pdict["fiatMoney"]
            or model.profit != pdict["profit"]
        ):
            model.BTC = pdict["BTC"]
            model.fiatMoney = pdict["fiatMoney"]
            model.profit = pdict["profit"]
            model.save()

    # The incoming order itself: fully filled -> complete; otherwise it
    # rests in the book with only the unfilled quantity left, at the
    # trader's originally submitted price.
    if result["remaining_quantity"] <= 0:
        incoming_order.complete = True
    else:
        incoming_order.quantity = result["remaining_quantity"]
    incoming_order.save()

    return not book_was_empty


@login_required(login_url='login')
def home(request):
    user = User.objects.get(username=request.user)
    profile = Profile.objects.get(user=user)
    BTC = round(profile.BTC, 8)
    fiatMoney = round(profile.fiatMoney, 2)

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            quantity = float(request.POST['quantity'])
            price = float(request.POST['price'])

            if quantity == 0 or price == 0:
                return _message_redirect(
                    request,
                    'Impossible to perform the operation! Price or Quantity is equal to zero!',
                )

            elif 'sell' in request.POST:
                if profile.BTC >= quantity:
                    matched = _execute_market_order(profile, TYPE_SELL, quantity, price)
                    if not matched:
                        return _message_redirect(request, 'Registered Sale Order. Pending a Purchase Order!')
                    return _message_redirect(request, 'Registered Order!')
                else:
                    return _message_redirect(request, 'Impossible to perform the operation! Insufficient BTC!', error=True)

            elif 'buy' in request.POST:
                # Total cost is price * quantity, not price alone — this
                # pre-check was fixed to match that (see project README).
                if profile.fiatMoney >= price * quantity:
                    matched = _execute_market_order(profile, TYPE_BUY, quantity, price)
                    if not matched:
                        return _message_redirect(request, 'Registered Purchase Order. Pending a Sale Order!')
                    return _message_redirect(request, 'Registered Order!')
                else:
                    return _message_redirect(request, 'Impossible to perform the operation! Insufficient Funds!', error=True)
    else:
        form = OrderForm()

    return render(request, 'app/home.html', {'form': form, 'BTC': BTC, 'fiatMoney': fiatMoney})


@login_required(login_url='login')
def orderBook(request):
    response = []
    activeOrders = Order.objects.filter(complete=False)
    for order in activeOrders:
        response.append(
            {
                'Order ID': str(order._id),
                'Typology': order.type,
                'Datetime': order.datetime,
                'Price': round((order.price), 2),
                'Quantity': round((order.quantity), 8),
            }
        )
    return JsonResponse(response, safe=False)


@login_required(login_url='login')
def profit(request):
    response = []
    user = User.objects.get(username=request.user)
    profile = Profile.objects.get(user=user)
    response.append(
            {
                'User ID': str(profile._id),
                'Name': profile.user.first_name,
                'Surname': profile.user.last_name,
                'Balance': round((profile.fiatMoney), 2),
                'BTC': round((profile.BTC), 8),
                'Profit': round((profile.profit), 2),
            }
        )
    return JsonResponse(response, safe=False)


def registerView(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = Profile.objects.create(user=user)
            profile.BTC = round(random.uniform(1, 10), 8)
            profile.save()
            messages.success(request, 'Congratulations! Your new account has been successfully created!')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'app/register.html', {'form': form})


def loginView(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == "POST":
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Username or Password is incorrect!')
        return render(request, 'app/login.html')


def logoutView(request):
    logout(request)
    return redirect('login')
