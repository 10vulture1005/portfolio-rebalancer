# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    rebalance.py                                       :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: Time Money Code <->                        +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2025/06/05 18:42:24 by Time Money        #+#    #+#              #
#    Updated: 2025/06/05 18:42:24 by Time Money       ###   ########.fr        #
#                                                                              #
# **************************************************************************** #


import math
from collections import defaultdict


def get_group_adjust_data(assets, prices, total_value, scaling):
    """
    Helper to compute group target value, non-adjustable value, and adjustable/non-adjustable asset lists.
    Raises ValueError if price is missing.
    """
    group_target_pct = sum(a.target_allocation for a in assets) * scaling
    group_target_value = total_value * (group_target_pct / 100)
    adjust_assets = [a for a in assets if getattr(a, "adjust", 1) == 1]
    non_adjust_assets = [a for a in assets if getattr(a, "adjust", 1) == 0]
    for a in assets:
        if a.ticker not in prices:
            raise ValueError(f"Missing price for {a.ticker}")
    non_adjust_value = sum(prices[a.ticker] * a.shares for a in non_adjust_assets)
    return group_target_value, non_adjust_value, adjust_assets, non_adjust_assets


def full_rebalance(
    portfolio,
    prices,
    base_currency,
    use_ceil=False,
    distribute_across_adjustables=False,
):
    """
    Suggest trades to fully rebalance the portfolio to target allocations.
    If distribute_across_adjustables is True, split adjustment across all adjust==1 assets in a group.
    """
    groups = defaultdict(list)
    for asset in portfolio.get_assets():
        group = getattr(asset, "group", asset.ticker) or asset.ticker
        groups[group].append(asset)
    suggestions = []
    total_value = sum(prices[a.ticker] * a.shares for a in portfolio.get_assets())
    total_target_pct = sum(a.target_allocation for a in portfolio.get_assets())
    scaling = 100.0 / total_target_pct if total_target_pct > 0 else 1.0
    for group, assets in groups.items():
        (
            group_target_value,
            non_adjust_value,
            adjust_assets,
            non_adjust_assets,
        ) = get_group_adjust_data(assets, prices, total_value, scaling)
        if not adjust_assets:
            raise ValueError(
                f"No adjustable ETF in group '{group}'. Please set Adjust=1 for at least one ETF in this group."
            )
        adjust_value = group_target_value - non_adjust_value
        if distribute_across_adjustables and len(adjust_assets) > 1:
            # Proportional by target allocation, or equally if all zero
            total_targets = sum(a.target_allocation for a in adjust_assets)
            if total_targets > 0:
                weights = [a.target_allocation / total_targets for a in adjust_assets]
            else:
                weights = [1.0 / len(adjust_assets)] * len(adjust_assets)
            for i, asset in enumerate(adjust_assets):
                price = prices[asset.ticker]
                asset_adjust_value = adjust_value * weights[i]
                target_shares = asset_adjust_value / price
                diff_shares = target_shares - asset.shares
                if diff_shares > 0:
                    diff_shares_rounded = (
                        math.ceil(diff_shares) if use_ceil else math.floor(diff_shares)
                    )
                else:
                    diff_shares_rounded = math.floor(diff_shares)
                if diff_shares_rounded != 0:
                    action = "BUY" if diff_shares_rounded > 0 else "SELL"
                    suggestions.append(
                        {
                            "ticker": asset.ticker,
                            "action": action,
                            "shares": abs(diff_shares_rounded),
                            "from": asset.shares,
                            "to": target_shares,
                        }
                    )
        else:
            asset = adjust_assets[0]
            price = prices[asset.ticker]
            target_shares = adjust_value / price
            diff_shares = target_shares - asset.shares
            if diff_shares > 0:
                diff_shares_rounded = (
                    math.ceil(diff_shares) if use_ceil else math.floor(diff_shares)
                )
            else:
                diff_shares_rounded = math.floor(diff_shares)
            if diff_shares_rounded != 0:
                action = "BUY" if diff_shares_rounded > 0 else "SELL"
                suggestions.append(
                    {
                        "ticker": asset.ticker,
                        "action": action,
                        "shares": abs(diff_shares_rounded),
                        "from": asset.shares,
                        "to": target_shares,
                    }
                )
    return suggestions


def minimal_rebalance(
    portfolio,
    prices,
    base_currency,
    threshold=0.05,
    use_ceil=False,
    distribute_across_adjustables=False,
):
    """
    Suggest trades only for assets where allocation drift exceeds threshold.
    If distribute_across_adjustables is True, split adjustment across all adjust==1 assets in a group.
    """
    groups = defaultdict(list)
    for asset in portfolio.get_assets():
        group = getattr(asset, "group", asset.ticker) or asset.ticker
        groups[group].append(asset)
    suggestions = []
    total_value = sum(prices[a.ticker] * a.shares for a in portfolio.get_assets())
    total_target_pct = sum(a.target_allocation for a in portfolio.get_assets())
    scaling = 100.0 / total_target_pct if total_target_pct > 0 else 1.0
    for group, assets in groups.items():
        (
            group_target_value,
            non_adjust_value,
            adjust_assets,
            non_adjust_assets,
        ) = get_group_adjust_data(assets, prices, total_value, scaling)
        if not adjust_assets:
            raise ValueError(
                f"No adjustable ETF in group '{group}'. Please set Adjust=1 for at least one ETF in this group."
            )
        group_value = sum(prices[a.ticker] * a.shares for a in assets)
        group_target_pct = sum(a.target_allocation for a in assets) * scaling
        group_current_pct = group_value / total_value if total_value > 0 else 0
        group_target_pct_decimal = group_target_pct / 100
        drift = group_current_pct - group_target_pct_decimal
        if abs(drift) <= threshold:
            continue
        adjust_value = group_target_value - non_adjust_value
        if distribute_across_adjustables and len(adjust_assets) > 1:
            total_targets = sum(a.target_allocation for a in adjust_assets)
            if total_targets > 0:
                weights = [a.target_allocation / total_targets for a in adjust_assets]
            else:
                weights = [1.0 / len(adjust_assets)] * len(adjust_assets)
            for i, asset in enumerate(adjust_assets):
                price = prices[asset.ticker]
                asset_adjust_value = adjust_value * weights[i]
                target_shares = asset_adjust_value / price
                diff_shares = target_shares - asset.shares
                if diff_shares > 0:
                    diff_shares_rounded = (
                        math.ceil(diff_shares) if use_ceil else math.floor(diff_shares)
                    )
                else:
                    diff_shares_rounded = math.floor(diff_shares)
                if diff_shares_rounded != 0:
                    action = "BUY" if diff_shares_rounded > 0 else "SELL"
                    suggestions.append(
                        {
                            "ticker": asset.ticker,
                            "action": action,
                            "shares": abs(diff_shares_rounded),
                            "from": asset.shares,
                            "to": target_shares,
                        }
                    )
        else:
            asset = adjust_assets[0]
            price = prices[asset.ticker]
            target_shares = adjust_value / price
            diff_shares = target_shares - asset.shares
            if diff_shares > 0:
                diff_shares_rounded = (
                    math.ceil(diff_shares) if use_ceil else math.floor(diff_shares)
                )
            else:
                diff_shares_rounded = math.floor(diff_shares)
            if diff_shares_rounded != 0:
                action = "BUY" if diff_shares_rounded > 0 else "SELL"
                suggestions.append(
                    {
                        "ticker": asset.ticker,
                        "action": action,
                        "shares": abs(diff_shares_rounded),
                        "from": asset.shares,
                        "to": target_shares,
                    }
                )
    return suggestions


def value_preserving_rebalance(portfolio, prices, base_currency, use_ceil=False):
    """
    Suggest trades to rebalance the portfolio so that the total value before and after rebalancing is the same.
    Only adjusts shares for assets with adjust==1 in each group.
    The sum of all group target values is forced to match the current total portfolio value.
    Rounding is handled so that the closest integer number of shares is chosen to minimize value drift.
    """
    groups = defaultdict(list)
    for asset in portfolio.get_assets():
        group = getattr(asset, "group", asset.ticker) or asset.ticker
        groups[group].append(asset)
    suggestions = []
    total_value = sum(prices[a.ticker] * a.shares for a in portfolio.get_assets())
    total_target_pct = sum(a.target_allocation for a in portfolio.get_assets())
    scaling = 100.0 / total_target_pct if total_target_pct > 0 else 1.0
    for group, assets in groups.items():
        (
            group_target_value,
            non_adjust_value,
            adjust_assets,
            non_adjust_assets,
        ) = get_group_adjust_data(assets, prices, total_value, scaling)
        if not adjust_assets:
            raise ValueError(
                f"No adjustable ETF in group '{group}'. Please set Adjust=1 for at least one ETF in this group."
            )
        adjust_value = group_target_value - non_adjust_value
        asset = adjust_assets[0]
        price = prices[asset.ticker]
        target_shares = adjust_value / price
        floor_shares = math.floor(target_shares)
        ceil_shares = math.ceil(target_shares)
        floor_value = floor_shares * price + non_adjust_value
        ceil_value = ceil_shares * price + non_adjust_value
        if abs(floor_value - group_target_value) <= abs(
            ceil_value - group_target_value
        ):
            best_shares = floor_shares
        else:
            best_shares = ceil_shares
        diff_shares = best_shares - asset.shares
        if diff_shares != 0:
            action = "BUY" if diff_shares > 0 else "SELL"
            suggestions.append(
                {
                    "ticker": asset.ticker,
                    "action": action,
                    "shares": abs(diff_shares),
                    "from": asset.shares,
                    "to": best_shares,
                }
            )
    return suggestions
