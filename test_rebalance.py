import unittest
from portfolio import Portfolio, Asset
from rebalance import full_rebalance, minimal_rebalance, value_preserving_rebalance

class TestRebalance(unittest.TestCase):
    def setUp(self):
        self.portfolio = Portfolio()
        
        # Create assets
        # Asset(ticker, shares, currency, target_allocation)
        self.a1 = Asset("AAPL", 10, "USD", 60)
        self.a1.group = "Equities"
        self.a1.adjust = 1
        
        self.a2 = Asset("MSFT", 5, "USD", 40)
        self.a2.group = "Equities"
        self.a2.adjust = 1
        
        self.portfolio.add_asset(self.a1)
        self.portfolio.add_asset(self.a2)
        
        self.prices = {
            "AAPL": 100.0, # Value: 1000
            "MSFT": 200.0  # Value: 1000, Total Value: 2000
        }

    def test_full_rebalance_no_action_needed(self):
        # Target allocation is 60 AAPL, 40 MSFT.
        # Current is 50/50. So rebalance IS needed! Wait.
        # Let's change target to match current for this test
        self.a1.target_allocation = 50
        self.a2.target_allocation = 50
        
        suggestions = full_rebalance(
            self.portfolio, self.prices, "USD", distribute_across_adjustables=True
        )
        self.assertEqual(len(suggestions), 0)
        
    def test_full_rebalance_needs_action(self):
        # Total value = 2000
        # Targets: AAPL 60% (1200), MSFT 40% (800)
        # AAPL target shares = 1200 / 100 = 12 (needs +2)
        # MSFT target shares = 800 / 200 = 4 (needs -1)
        
        suggestions = full_rebalance(
            self.portfolio, self.prices, "USD", distribute_across_adjustables=True
        )
        
        self.assertEqual(len(suggestions), 2)
        
        buy_aapl = next((s for s in suggestions if s["ticker"] == "AAPL"), None)
        self.assertIsNotNone(buy_aapl)
        self.assertEqual(buy_aapl["action"], "BUY")
        self.assertEqual(buy_aapl["shares"], 2)

        sell_msft = next((s for s in suggestions if s["ticker"] == "MSFT"), None)
        self.assertIsNotNone(sell_msft)
        self.assertEqual(sell_msft["action"], "SELL")
        self.assertEqual(sell_msft["shares"], 1)

    def test_minimal_rebalance_under_threshold(self):
        # Use separate groups to evaluate individual drift
        self.a1.group = "G1"
        self.a2.group = "G2"
        # Targets: AAPL 52% (1040), MSFT 48% (960)
        # Current is 50/50. Drift is 2% = 0.02
        self.a1.target_allocation = 52
        self.a2.target_allocation = 48
        
        # With threshold 0.05, 0.02 is under threshold, no suggestions
        suggestions = minimal_rebalance(
            self.portfolio, self.prices, "USD", threshold=0.05, distribute_across_adjustables=False
        )
        self.assertEqual(len(suggestions), 0)

    def test_minimal_rebalance_over_threshold(self):
        # Drift is > 5%
        self.a1.group = "G1"
        self.a2.group = "G2"
        # Targets: AAPL 60% (1200), MSFT 40% (800)
        # Current: 50/50. Drift is 10%.
        suggestions = minimal_rebalance(
            self.portfolio, self.prices, "USD", threshold=0.05, distribute_across_adjustables=False
        )
        self.assertTrue(len(suggestions) > 0)

    def test_non_adjustable_assets(self):
        self.a2.adjust = 0 # MSFT is non-adjustable
        
        # Targets: AAPL 50%, MSFT 50%
        # Current: AAPL 1000, MSFT 1000
        self.a1.target_allocation = 50
        self.a2.target_allocation = 50
        
        # Change price of AAPL to 50. Total value = 500 + 1000 = 1500
        # Target for Equities group = 1500
        # Non-adjust value = 1000
        # Adjust value = 1500 - 1000 = 500
        # Target shares for AAPL = 500 / 50 = 10 (no change)
        prices = {"AAPL": 50.0, "MSFT": 200.0}
        
        suggestions = full_rebalance(self.portfolio, prices, "USD")
        self.assertEqual(len(suggestions), 0)

    def test_value_preserving_rebalance(self):
        # Value preserving rebalancing
        self.a1.target_allocation = 60
        self.a2.target_allocation = 40
        
        # In value_preserving_rebalance, only the FIRST adjust_asset is adjusted.
        # Let's specify explicitly that a2 is 0 or it might error if distribute is not used (it doesn't have distribute)
        # Wait, value_preserving_rebalance only adjusts one asset per group: adjust_assets[0]
        # Let's make a1 the only adjust asset.
        self.a2.adjust = 0
        
        # Target for Equities group = 2000
        # Non adjust = 1000
        # Adjust value = 1000. Price of AAPL = 100. Target shares = 10.
        suggestions = value_preserving_rebalance(self.portfolio, self.prices, "USD")
        # should be 0 since target shares 10 == current 10
        self.assertEqual(len(suggestions), 0)
        
        # What if adjust value is 900?
        self.a2.shares = 5.5 # Value = 1100
        # Total value = 2100. Non adjust = 1100. Adjust value = 1000. Price = 100. Target shares = 10.
        suggestions = value_preserving_rebalance(self.portfolio, self.prices, "USD")
        self.assertEqual(len(suggestions), 0)

if __name__ == '__main__':
    unittest.main()
