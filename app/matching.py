"""
Market-style order-matching engine (pure Python, no Django/MongoDB).

Design:
- The incoming order always executes as a true market order: no price
  limit protection, unlimited slippage. It walks the resting book on the
  opposite side, best price first, consuming orders until either the
  requested quantity is fully filled or the book is exhausted.
- Each matched resting order is executed at ITS OWN price, not at the
  incoming order's price — this is what "slippage" means in practice:
  the effective average price the trader gets can be worse than what
  they typed in, if the top of the book alone isn't enough.
- Book ordering follows standard market convention:
    - an incoming SELL walks the BUY book best-price-first, i.e. highest
      price first (best bid).
    - an incoming BUY walks the SELL book best-price-first, i.e. lowest
      price first (best ask).
- If the incoming order's own profile happens to own a resting order it
  would otherwise match against (a self-trade), that resting order is
  simply closed with no balance movement — no money changes hands
  between a trader and themselves.
- Any quantity left unmatched after the whole book is exhausted becomes
  a new resting order for the incoming trader, at their originally
  submitted price.

Orders and profiles are plain dicts:
  profile = {"id": ..., "BTC": ..., "fiatMoney": ..., "profit": ...}
  order   = {"id": ..., "profile": profile, "price": ..., "quantity": ..., "complete": False}
"""

SELL = "sell"
BUY = "buy"


def _apply_fill(taker_side, taker_profile, maker_profile, price, quantity):
    """Applies the balance changes for one executed fill to both sides.

    taker_side is the side of the INCOMING order ('sell' or 'buy').
    The maker is the owner of the resting book order being consumed.
    """
    cost = price * quantity  # Note: in this model each unit's "price" already represents the total for that order's priced quantity, consistent with the original app's convention of treating `price` as a lump amount tied to `quantity` rather than a strict per-unit rate.

    if taker_side == SELL:
        # Taker is selling BTC for fiat; maker is the resting buyer.
        taker_profile["BTC"] -= quantity
        taker_profile["fiatMoney"] += cost
        taker_profile["profit"] += cost

        maker_profile["BTC"] += quantity
        maker_profile["fiatMoney"] -= cost
        maker_profile["profit"] -= cost
    else:
        # Taker is buying BTC with fiat; maker is the resting seller.
        taker_profile["BTC"] += quantity
        taker_profile["fiatMoney"] -= cost
        taker_profile["profit"] -= cost

        maker_profile["BTC"] -= quantity
        maker_profile["fiatMoney"] += cost
        maker_profile["profit"] += cost


def match_order(side, profile, quantity, price, book, new_order_id="new"):
    """
    Executes an incoming market order against a resting order book.

    Parameters
    ----------
    side : 'sell' or 'buy' — the side of the incoming order.
    profile : dict — the profile placing the incoming order (mutated in place).
    quantity : float — requested quantity.
    price : float — the price the trader typed in; only used if a remainder
            ends up resting in the book (no limit protection otherwise).
    book : list[dict] — resting orders on the OPPOSITE side. Mutated in place
           (quantities reduced and/or `complete` flags set on filled orders).
           Only orders with complete == False are considered.
    new_order_id : identifier for the incoming order, used in the returned fills.

    Returns
    -------
    dict with:
      - "fills": list of {"resting_order_id", "profile_id", "quantity", "price"}
                 describing every execution that happened, in order.
      - "remaining_quantity": quantity still unfilled after exhausting the book.
      - "new_resting_order": None, or a dict describing the new resting order
        created for the leftover quantity (at the trader's original price).
    """
    if side not in (SELL, BUY):
        raise ValueError("side must be 'sell' or 'buy'")

    # Best-price-first ordering, per standard market convention.
    reverse = (side == SELL)  # selling wants the highest bid first
    resting_orders = sorted(
        (o for o in book if not o["complete"]),
        key=lambda o: o["price"],
        reverse=reverse,
    )

    remaining = quantity
    fills = []

    for resting in resting_orders:
        if remaining <= 0:
            break

        is_self_trade = resting["profile"]["id"] == profile["id"]
        take_qty = min(remaining, resting["quantity"])

        if is_self_trade:
            # No money changes hands when trading with yourself; just
            # consume the resting order's quantity as if it were filled.
            pass
        else:
            _apply_fill(side, profile, resting["profile"], resting["price"], take_qty)
            fills.append({
                "resting_order_id": resting["id"],
                "profile_id": resting["profile"]["id"],
                "quantity": take_qty,
                "price": resting["price"],
            })

        resting["quantity"] = round(resting["quantity"] - take_qty, 8)
        remaining = round(remaining - take_qty, 8)

        if resting["quantity"] <= 0:
            resting["complete"] = True

    new_resting_order = None
    if remaining > 0:
        new_resting_order = {
            "id": new_order_id,
            "profile": profile,
            "price": price,
            "quantity": remaining,
            "complete": False,
        }

    return {
        "fills": fills,
        "remaining_quantity": remaining,
        "new_resting_order": new_resting_order,
    }
