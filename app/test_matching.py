import unittest
from .matching import match_order, SELL, BUY


def make_profile(id, BTC=0.0, fiatMoney=0.0, profit=0.0):
    return {"id": id, "BTC": BTC, "fiatMoney": fiatMoney, "profit": profit}


def make_order(id, profile, price, quantity, complete=False):
    return {"id": id, "profile": profile, "price": price, "quantity": quantity, "complete": complete}


class TestExactMatch(unittest.TestCase):
    def test_sell_exact_match_different_profiles(self):
        seller = make_profile("seller", BTC=1.0, fiatMoney=0.0, profit=0.0)
        buyer = make_profile("buyer", BTC=0.0, fiatMoney=500.0, profit=0.0)
        buy_order = make_order("b1", buyer, price=100, quantity=1.0)

        result = match_order(SELL, seller, quantity=1.0, price=90, book=[buy_order])

        self.assertEqual(result["remaining_quantity"], 0)
        self.assertIsNone(result["new_resting_order"])
        self.assertTrue(buy_order["complete"])
        self.assertEqual(seller["BTC"], 0.0)
        self.assertEqual(seller["fiatMoney"], 100.0)
        self.assertEqual(buyer["BTC"], 1.0)
        self.assertEqual(buyer["fiatMoney"], 400.0)

    def test_buy_exact_match_different_profiles(self):
        buyer = make_profile("buyer", BTC=0.0, fiatMoney=500.0, profit=0.0)
        seller = make_profile("seller", BTC=1.0, fiatMoney=0.0, profit=0.0)
        sell_order = make_order("s1", seller, price=100, quantity=1.0)

        result = match_order(BUY, buyer, quantity=1.0, price=120, book=[sell_order])

        self.assertEqual(result["remaining_quantity"], 0)
        self.assertTrue(sell_order["complete"])
        self.assertEqual(buyer["BTC"], 1.0)
        self.assertEqual(buyer["fiatMoney"], 400.0)
        self.assertEqual(seller["BTC"], 0.0)
        self.assertEqual(seller["fiatMoney"], 100.0)


class TestBestPriceOrdering(unittest.TestCase):
    def test_sell_matches_highest_bid_first(self):
        seller = make_profile("seller", BTC=5.0)
        low_bidder = make_profile("low", fiatMoney=1000.0)
        high_bidder = make_profile("high", fiatMoney=1000.0)
        low_order = make_order("low_order", low_bidder, price=90, quantity=1.0)
        high_order = make_order("high_order", high_bidder, price=110, quantity=1.0)

        # Deliberately listed with the lower bid first in the book list,
        # to prove sorting -- not list order -- determines match priority.
        result = match_order(SELL, seller, quantity=1.0, price=0, book=[low_order, high_order])

        self.assertEqual(result["fills"][0]["resting_order_id"], "high_order")
        self.assertTrue(high_order["complete"])
        self.assertFalse(low_order["complete"])
        self.assertEqual(seller["fiatMoney"], 110.0)

    def test_buy_matches_lowest_ask_first(self):
        buyer = make_profile("buyer", fiatMoney=1000.0)
        cheap_seller = make_profile("cheap", BTC=5.0)
        pricey_seller = make_profile("pricey", BTC=5.0)
        cheap_order = make_order("cheap_order", cheap_seller, price=90, quantity=1.0)
        pricey_order = make_order("pricey_order", pricey_seller, price=110, quantity=1.0)

        result = match_order(BUY, buyer, quantity=1.0, price=999, book=[pricey_order, cheap_order])

        self.assertEqual(result["fills"][0]["resting_order_id"], "cheap_order")
        self.assertTrue(cheap_order["complete"])
        self.assertFalse(pricey_order["complete"])
        self.assertEqual(buyer["fiatMoney"], 1000.0 - 90.0)


class TestMultiOrderSlippage(unittest.TestCase):
    def test_sell_spans_multiple_buyers_at_their_own_prices(self):
        """This is the scenario that reproduced the original fund-misattribution bug."""
        seller = make_profile("seller", BTC=3.0, fiatMoney=0.0, profit=0.0)
        buyer_a = make_profile("buyer_a", fiatMoney=1000.0)  # best bid
        buyer_b = make_profile("buyer_b", fiatMoney=1000.0)  # second-best bid
        order_a = make_order("order_a", buyer_a, price=110, quantity=1.0)
        order_b = make_order("order_b", buyer_b, price=100, quantity=2.0)

        result = match_order(SELL, seller, quantity=3.0, price=0, book=[order_a, order_b])

        self.assertEqual(result["remaining_quantity"], 0)
        self.assertTrue(order_a["complete"])
        self.assertTrue(order_b["complete"])

        # Seller sold 1 BTC @110 and 2 BTC @100 => 110 + 200 = 310 total,
        # an average effective price of ~103.33 — worse than the top bid
        # alone, which is exactly what slippage means.
        self.assertEqual(seller["fiatMoney"], 310.0)
        self.assertEqual(seller["BTC"], 0.0)

        # Each buyer pays/receives based on THEIR OWN order — the bug fix.
        self.assertEqual(buyer_a["BTC"], 1.0)
        self.assertEqual(buyer_a["fiatMoney"], 1000.0 - 110.0)
        self.assertEqual(buyer_b["BTC"], 2.0)
        self.assertEqual(buyer_b["fiatMoney"], 1000.0 - 200.0)

    def test_partial_fill_of_top_order_leaves_remainder_resting(self):
        seller = make_profile("seller", BTC=5.0)
        buyer = make_profile("buyer", fiatMoney=1000.0)
        buy_order = make_order("b1", buyer, price=100, quantity=2.0)

        result = match_order(SELL, seller, quantity=0.5, price=0, book=[buy_order])

        self.assertEqual(result["remaining_quantity"], 0)
        self.assertFalse(buy_order["complete"])
        self.assertAlmostEqual(buy_order["quantity"], 1.5)
        self.assertEqual(seller["fiatMoney"], 50.0)  # 0.5 units at price 100/unit
        self.assertEqual(buyer["BTC"], 0.5)


class TestSelfTrade(unittest.TestCase):
    def test_self_trade_closes_order_without_moving_money(self):
        trader_profile = make_profile("trader", BTC=2.0, fiatMoney=500.0, profit=0.0)
        own_buy_order = make_order("own_order", trader_profile, price=100, quantity=1.0)

        result = match_order(SELL, trader_profile, quantity=1.0, price=90, book=[own_buy_order])

        self.assertTrue(own_buy_order["complete"])
        self.assertEqual(result["fills"], [])  # no fills recorded — no money moved
        # Balances are untouched by the trade itself.
        self.assertEqual(trader_profile["BTC"], 2.0)
        self.assertEqual(trader_profile["fiatMoney"], 500.0)


class TestInsufficientLiquidity(unittest.TestCase):
    def test_remainder_becomes_new_resting_order_at_original_price(self):
        seller = make_profile("seller", BTC=10.0)
        buyer = make_profile("buyer", fiatMoney=1000.0)
        buy_order = make_order("b1", buyer, price=100, quantity=1.0)

        result = match_order(SELL, seller, quantity=5.0, price=95, book=[buy_order])

        self.assertEqual(result["remaining_quantity"], 4.0)
        self.assertIsNotNone(result["new_resting_order"])
        self.assertEqual(result["new_resting_order"]["quantity"], 4.0)
        self.assertEqual(result["new_resting_order"]["price"], 95)
        self.assertTrue(buy_order["complete"])
        self.assertEqual(seller["fiatMoney"], 100.0)
        self.assertEqual(seller["BTC"], 10.0 - 1.0)

    def test_empty_book_rests_entire_order(self):
        seller = make_profile("seller", BTC=10.0)
        result = match_order(SELL, seller, quantity=2.0, price=95, book=[])
        self.assertEqual(result["remaining_quantity"], 2.0)
        self.assertEqual(result["new_resting_order"]["quantity"], 2.0)
        self.assertEqual(seller["BTC"], 10.0)  # untouched, nothing executed


if __name__ == "__main__":
    unittest.main(verbosity=2)
