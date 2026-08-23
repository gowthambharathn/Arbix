"""
ArbiX Position Management

Tracks asset balances and positions across cryptocurrency exchanges.

The position manager is responsible for local portfolio state. It does
not submit or cancel orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class AssetPosition:
    """
    Represents the balance of one asset on one exchange.
    """

    exchange: str
    asset: str

    available: Decimal = Decimal("0")
    locked: Decimal = Decimal("0")

    @property
    def total(self) -> Decimal:
        """Return available + locked balance."""

        return self.available + self.locked

    def __post_init__(self) -> None:
        """Validate the position."""

        if not self.exchange:
            raise ValueError(
                "Exchange cannot be empty."
            )

        if not self.asset:
            raise ValueError(
                "Asset cannot be empty."
            )

        if self.available < 0:
            raise ValueError(
                "Available balance cannot be negative."
            )

        if self.locked < 0:
            raise ValueError(
                "Locked balance cannot be negative."
            )


class PositionManager:
    """
    Maintains balances across multiple exchanges.

    Positions are stored using:

        exchange -> asset -> AssetPosition

    Example:

        Binance
            BTC -> 0.5
            USDT -> 5000

        Kraken
            BTC -> 0.2
            USDT -> 7000
    """

    def __init__(self) -> None:
        self._positions: dict[
            str,
            dict[str, AssetPosition],
        ] = {}

    def set_position(
        self,
        exchange: str,
        asset: str,
        available: Decimal,
        locked: Decimal = Decimal("0"),
    ) -> AssetPosition:
        """
        Create or replace a position.

        Args:
            exchange: Exchange name.
            asset: Asset symbol.
            available: Available balance.
            locked: Balance currently locked by orders.

        Returns:
            Updated AssetPosition.
        """

        self._validate_balance(
            available=available,
            locked=locked,
        )

        position = AssetPosition(
            exchange=exchange,
            asset=asset,
            available=available,
            locked=locked,
        )

        self._positions.setdefault(
            exchange,
            {},
        )[asset] = position

        return position

    def get_position(
        self,
        exchange: str,
        asset: str,
    ) -> AssetPosition | None:
        """Return a position if it exists."""

        return (
            self._positions
            .get(exchange, {})
            .get(asset)
        )

    def get_required_position(
        self,
        exchange: str,
        asset: str,
    ) -> AssetPosition:
        """
        Return a position or raise KeyError.
        """

        position = self.get_position(
            exchange=exchange,
            asset=asset,
        )

        if position is None:
            raise KeyError(
                f"Position not found: "
                f"{exchange}/{asset}"
            )

        return position

    def available_balance(
        self,
        exchange: str,
        asset: str,
    ) -> Decimal:
        """Return available balance for an asset."""

        position = self.get_position(
            exchange=exchange,
            asset=asset,
        )

        if position is None:
            return Decimal("0")

        return position.available

    def locked_balance(
        self,
        exchange: str,
        asset: str,
    ) -> Decimal:
        """Return locked balance for an asset."""

        position = self.get_position(
            exchange=exchange,
            asset=asset,
        )

        if position is None:
            return Decimal("0")

        return position.locked

    def total_balance(
        self,
        exchange: str,
        asset: str,
    ) -> Decimal:
        """Return total balance for an asset."""

        position = self.get_position(
            exchange=exchange,
            asset=asset,
        )

        if position is None:
            return Decimal("0")

        return position.total

    def increase_available(
        self,
        exchange: str,
        asset: str,
        amount: Decimal,
    ) -> AssetPosition:
        """Increase available balance."""

        if amount < 0:
            raise ValueError(
                "Amount cannot be negative."
            )

        position = self._get_or_create_position(
            exchange=exchange,
            asset=asset,
        )

        position.available += amount

        return position

    def decrease_available(
        self,
        exchange: str,
        asset: str,
        amount: Decimal,
    ) -> AssetPosition:
        """Decrease available balance."""

        if amount < 0:
            raise ValueError(
                "Amount cannot be negative."
            )

        position = self._get_or_create_position(
            exchange=exchange,
            asset=asset,
        )

        if amount > position.available:
            raise ValueError(
                f"Insufficient available {asset} "
                f"balance on {exchange}."
            )

        position.available -= amount

        return position

    def lock(
        self,
        exchange: str,
        asset: str,
        amount: Decimal,
    ) -> AssetPosition:
        """
        Move balance from available to locked.

        Locked balance is normally associated with an open order.
        """

        if amount <= 0:
            raise ValueError(
                "Lock amount must be greater than zero."
            )

        position = self._get_or_create_position(
            exchange=exchange,
            asset=asset,
        )

        if amount > position.available:
            raise ValueError(
                f"Insufficient available {asset} "
                f"balance to lock."
            )

        position.available -= amount
        position.locked += amount

        return position

    def unlock(
        self,
        exchange: str,
        asset: str,
        amount: Decimal,
    ) -> AssetPosition:
        """
        Move balance from locked back to available.
        """

        if amount <= 0:
            raise ValueError(
                "Unlock amount must be greater than zero."
            )

        position = self._get_or_create_position(
            exchange=exchange,
            asset=asset,
        )

        if amount > position.locked:
            raise ValueError(
                f"Cannot unlock more {asset} "
                f"than currently locked."
            )

        position.locked -= amount
        position.available += amount

        return position

    def apply_trade(
        self,
        exchange: str,
        base_asset: str,
        quote_asset: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal = Decimal("0"),
    ) -> None:
        """
        Apply a completed trade to local balances.

        BUY:

            Quote currency decreases.
            Base asset increases.

        SELL:

            Base asset decreases.
            Quote currency increases.

        Args:
            exchange: Exchange where the trade occurred.
            base_asset: Asset being bought/sold.
            quote_asset: Asset used for payment.
            side: "buy" or "sell".
            quantity: Filled base-asset quantity.
            price: Average execution price.
            fee: Fee paid in quote currency.

        Note:
            The exact fee currency can differ between exchanges.
            This method assumes the fee is paid in quote currency.
        """

        if quantity <= 0:
            raise ValueError(
                "Trade quantity must be greater than zero."
            )

        if price <= 0:
            raise ValueError(
                "Trade price must be greater than zero."
            )

        if fee < 0:
            raise ValueError(
                "Trade fee cannot be negative."
            )

        normalized_side = side.lower()

        trade_value = quantity * price

        if normalized_side == "buy":
            total_quote_cost = trade_value + fee

            self.decrease_available(
                exchange=exchange,
                asset=quote_asset,
                amount=total_quote_cost,
            )

            self.increase_available(
                exchange=exchange,
                asset=base_asset,
                amount=quantity,
            )

        elif normalized_side == "sell":
            self.decrease_available(
                exchange=exchange,
                asset=base_asset,
                amount=quantity,
            )

            self.increase_available(
                exchange=exchange,
                asset=quote_asset,
                amount=trade_value - fee,
            )

        else:
            raise ValueError(
                f"Unsupported order side: {side}"
            )

    def get_exchange_positions(
        self,
        exchange: str,
    ) -> list[AssetPosition]:
        """Return all positions belonging to an exchange."""

        return list(
            self._positions
            .get(exchange, {})
            .values()
        )

    def get_all_positions(self) -> list[AssetPosition]:
        """Return every tracked position."""

        positions: list[AssetPosition] = []

        for exchange_positions in self._positions.values():
            positions.extend(
                exchange_positions.values()
            )

        return positions

    def get_exchange_balances(
        self,
        exchange: str,
    ) -> dict[str, Decimal]:
        """
        Return total balances for an exchange.
        """

        return {
            position.asset: position.total
            for position in self.get_exchange_positions(
                exchange
            )
        }

    def _get_or_create_position(
        self,
        exchange: str,
        asset: str,
    ) -> AssetPosition:
        """Return an existing position or create an empty one."""

        position = self.get_position(
            exchange=exchange,
            asset=asset,
        )

        if position is not None:
            return position

        return self.set_position(
            exchange=exchange,
            asset=asset,
            available=Decimal("0"),
        )

    @staticmethod
    def _validate_balance(
        available: Decimal,
        locked: Decimal,
    ) -> None:
        """Validate balance values."""

        if available < 0:
            raise ValueError(
                "Available balance cannot be negative."
            )

        if locked < 0:
            raise ValueError(
                "Locked balance cannot be negative."
            )