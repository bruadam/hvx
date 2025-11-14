"""
Energy Pricing Models

Provides data structures for tracking energy prices with period and currency support.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from .enums import EnergyCarrier


class Currency(str):
    """Currency code (ISO 4217)."""
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"
    DKK = "DKK"
    SEK = "SEK"
    NOK = "NOK"
    CHF = "CHF"


class PricingPeriod(str):
    """Period granularity for energy pricing."""
    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class EnergyPrice(BaseModel):
    """
    Energy price for a specific carrier, period, and currency.
    """
    carrier: EnergyCarrier
    price_per_kwh: float = Field(..., description="Price per kWh")
    currency: str = Field(default="EUR", description="ISO 4217 currency code")

    valid_from: date
    valid_to: Optional[date] = None

    period: str = Field(default="yearly", description="Pricing period: hourly, daily, monthly, yearly")

    # Additional pricing components
    distribution_fee_per_kwh: Optional[float] = Field(default=None, ge=0)
    transmission_fee_per_kwh: Optional[float] = Field(default=None, ge=0)
    taxes_per_kwh: Optional[float] = Field(default=None, ge=0)
    fixed_fee_per_month: Optional[float] = Field(default=None, ge=0)

    country_code: Optional[str] = None
    region: Optional[str] = None
    tariff_name: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def total_price_per_kwh(self) -> float:
        """Calculate total price including all fees."""
        total = self.price_per_kwh
        if self.distribution_fee_per_kwh:
            total += self.distribution_fee_per_kwh
        if self.transmission_fee_per_kwh:
            total += self.transmission_fee_per_kwh
        if self.taxes_per_kwh:
            total += self.taxes_per_kwh
        return total


class MonthlyEnergyPrice(EnergyPrice):
    """Monthly average energy price."""
    period: str = "monthly"
    year: int
    month: int


class YearlyEnergyPrice(EnergyPrice):
    """Yearly average energy price."""
    period: str = "yearly"
    year: int


class EnergyPriceRegistry(BaseModel):
    """
    Registry of energy prices for different carriers and periods.
    """
    prices: List[EnergyPrice] = Field(default_factory=list)

    def add_price(self, price: EnergyPrice) -> None:
        """Add or update an energy price."""
        # Remove existing price for same carrier and period if it exists
        self.prices = [
            p for p in self.prices
            if not (
                p.carrier == price.carrier
                and p.valid_from == price.valid_from
                and p.currency == price.currency
            )
        ]
        self.prices.append(price)

    def get_price(
        self,
        carrier: EnergyCarrier,
        date_: date,
        currency: str = "EUR",
    ) -> Optional[EnergyPrice]:
        """
        Get the applicable energy price for a specific date.

        Args:
            carrier: Energy carrier
            date_: Date to get price for
            currency: Currency code

        Returns:
            Applicable EnergyPrice or None if not found
        """
        applicable_prices = [
            p for p in self.prices
            if (
                p.carrier == carrier
                and p.currency == currency
                and p.valid_from <= date_
                and (p.valid_to is None or p.valid_to >= date_)
            )
        ]

        if not applicable_prices:
            return None

        # Return the most specific period price
        # Priority: hourly > daily > monthly > yearly
        period_priority = {"hourly": 4, "daily": 3, "monthly": 2, "yearly": 1}
        return max(
            applicable_prices,
            key=lambda p: period_priority.get(p.period, 0)
        )

    def calculate_energy_cost(
        self,
        carrier: EnergyCarrier,
        kwh: float,
        start_date: date,
        end_date: Optional[date] = None,
        currency: str = "EUR",
    ) -> Optional[float]:
        """
        Calculate energy cost for a given consumption.

        Args:
            carrier: Energy carrier
            kwh: Energy consumption in kWh
            start_date: Start date of consumption period
            end_date: End date of consumption period (optional)
            currency: Currency code

        Returns:
            Total cost in specified currency or None if no price found
        """
        price = self.get_price(carrier, start_date, currency)
        if not price:
            return None

        return kwh * price.total_price_per_kwh


class EnergyCostSummary(BaseModel):
    """
    Summary of energy costs by carrier.
    """
    period_start: date
    period_end: date
    currency: str = "EUR"

    costs_by_carrier: Dict[str, float] = Field(default_factory=dict)
    consumption_by_carrier: Dict[str, float] = Field(default_factory=dict)

    total_cost: float = 0.0
    total_consumption_kwh: float = 0.0

    average_price_per_kwh: Optional[float] = None

    def add_carrier_cost(
        self,
        carrier: EnergyCarrier,
        consumption_kwh: float,
        cost: float,
    ) -> None:
        """Add cost for a specific carrier."""
        carrier_str = carrier.value
        self.costs_by_carrier[carrier_str] = self.costs_by_carrier.get(carrier_str, 0.0) + cost
        self.consumption_by_carrier[carrier_str] = self.consumption_by_carrier.get(carrier_str, 0.0) + consumption_kwh

        self.total_cost += cost
        self.total_consumption_kwh += consumption_kwh

        if self.total_consumption_kwh > 0:
            self.average_price_per_kwh = self.total_cost / self.total_consumption_kwh


__all__ = [
    "Currency",
    "PricingPeriod",
    "EnergyPrice",
    "MonthlyEnergyPrice",
    "YearlyEnergyPrice",
    "EnergyPriceRegistry",
    "EnergyCostSummary",
]
