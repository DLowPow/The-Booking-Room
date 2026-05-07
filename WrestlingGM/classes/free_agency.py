"""
Free Agency System - Browse and sign available wrestlers
Manages tiered free agent listings, contract negotiations, signing logic
Integrates with WrestlerPool for talent generation and AI rivals for competition

PRICING NOTE:
- All booking fees come from wrestler.booking_fee (set by WrestlerPool generation)
- Signing bonuses use LEVEL_FEE_MULTIPLIER from wrestler_pool.py
- This ensures ONE pricing source of truth across the codebase
"""
import random
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from classes.wrestler import (
    Wrestler, WrestlerLevel, ContractType, Alignment,
    LEVEL_INFO, LEVEL_REPUTATION_THRESHOLDS
)


# ==================== FREE AGENT TIERS ====================
class FreeAgentTier(Enum):
    """Tiers used for browsing/filtering the free agent pool"""
    ROOKIE = "Rookie"           # Show Ready / Indy Wrestler
    PROSPECT = "Prospect"       # Indy Star / Indy Darling
    RISING = "Rising"           # Rising Star / Established
    PROVEN = "Proven"           # Main Eventer / Top Star
    ELITE = "Elite"             # Legend / Icon
    INDY_GOD = "Indy God"       # Released wrestlers (premium tier)


# Map wrestler levels to free agent tiers
LEVEL_TO_TIER = {
    WrestlerLevel.SHOW_READY: FreeAgentTier.ROOKIE,
    WrestlerLevel.INDY_WRESTLER: FreeAgentTier.ROOKIE,
    WrestlerLevel.INDY_STAR: FreeAgentTier.PROSPECT,
    WrestlerLevel.INDY_DARLING: FreeAgentTier.PROSPECT,
    WrestlerLevel.RISING_STAR: FreeAgentTier.RISING,
    WrestlerLevel.ESTABLISHED: FreeAgentTier.RISING,
    WrestlerLevel.MAIN_EVENTER: FreeAgentTier.PROVEN,
    WrestlerLevel.TOP_STAR: FreeAgentTier.PROVEN,
    WrestlerLevel.LEGEND: FreeAgentTier.ELITE,
    WrestlerLevel.ICON: FreeAgentTier.ELITE,
    WrestlerLevel.INDY_GOD: FreeAgentTier.INDY_GOD,
}

TIER_INFO = {
    FreeAgentTier.ROOKIE: {
        "name": "Rookie", "icon": "🎫", "color": "#6b7280",
        "description": "Just starting out. Cheap and hungry.",
        "filter_order": 1,
    },
    FreeAgentTier.PROSPECT: {
        "name": "Prospect", "icon": "⭐", "color": "#3b82f6",
        "description": "Buzz building on the indies.",
        "filter_order": 2,
    },
    FreeAgentTier.RISING: {
        "name": "Rising Talent", "icon": "📈", "color": "#a855f7",
        "description": "On the verge of stardom.",
        "filter_order": 3,
    },
    FreeAgentTier.PROVEN: {
        "name": "Proven Talent", "icon": "🎤", "color": "#ec4899",
        "description": "Main event caliber. Major investment.",
        "filter_order": 4,
    },
    FreeAgentTier.ELITE: {
        "name": "Elite", "icon": "🏆", "color": "#fbbf24",
        "description": "Legendary names. Maximum prestige.",
        "filter_order": 5,
    },
    FreeAgentTier.INDY_GOD: {
        "name": "Indy God", "icon": "😈", "color": "#dc2626",
        "description": "Released from a major promotion. Cult following.",
        "filter_order": 6,
    },
}


# ==================== AGENT LISTING ====================
@dataclass
class AgentListing:
    """A free agent listing with contract details and AI competition tracking"""
    wrestler: Wrestler
    tier: FreeAgentTier
    listing_week: int = 0
    listing_year: int = 1
    weeks_listed: int = 0

    # Contract terms
    contract_type: ContractType = ContractType.PER_APPEARANCE
    asking_per_show: int = 50        # Per-appearance fee (defaults LOW for safety)
    asking_weekly_salary: int = 0    # Only for exclusive contracts (Phase B)
    signing_bonus: int = 0           # One-time signing fee
    contract_length_weeks: int = 26  # Default 6-month contract
    is_exclusive_offer: bool = False

    # AI Rival competition
    rival_interested: bool = False
    rival_promotion_name: str = ""
    rival_offer_deadline: int = 0   # Week when rival signs them if you don't act
    is_locked_in_negotiations: bool = False

    # Display flags
    is_hot_prospect: bool = False
    is_indy_god: bool = False
    is_licensed: bool = False

    # ==================== PROPERTY HELPERS ====================
    @property
    def has_contracts(self) -> bool:
        """Backwards compat — old template checks this"""
        return self.is_exclusive_offer

    @property
    def per_show_rate(self) -> int:
        """Backwards compat alias"""
        return self.asking_per_show

    @property
    def asking_salary(self) -> int:
        """Backwards compat alias"""
        return self.asking_weekly_salary

    @property
    def tier_name(self) -> str:
        """Tier display name for old template"""
        return TIER_INFO.get(self.tier, {}).get("name", "Unknown")

    # ==================== UI HELPERS ====================
    def get_tier_icon(self) -> str:
        return TIER_INFO.get(self.tier, {}).get("icon", "🤼")

    def get_tier_color(self) -> str:
        return TIER_INFO.get(self.tier, {}).get("color", "#6b7280")

    def get_total_first_payment(self) -> int:
        """Total upfront cost to sign this wrestler"""
        if self.is_exclusive_offer:
            return self.signing_bonus
        return 0  # Per-appearance has no upfront

    def get_weeks_remaining(self) -> int:
        """Weeks left before they leave the free agent pool"""
        return max(0, 4 - self.weeks_listed)

    def get_status_label(self) -> str:
        """Human-readable status"""
        if self.is_locked_in_negotiations:
            return f"🤝 Negotiating with {self.rival_promotion_name}"
        if self.rival_interested:
            return f"⚠️ {self.rival_promotion_name} interested"
        if self.is_hot_prospect:
            return "🔥 Hot Prospect"
        if self.is_indy_god:
            return "😈 Released Star"
        if self.is_licensed:
            return "🌟 Licensed Talent"
        return ""

    def get_summary(self) -> Dict:
        """Get summary dict for UI display"""
        w = self.wrestler
        return {
            "name": w.name,
            "nickname": getattr(w, 'nickname', None),
            "age": getattr(w, 'age', 0),
            "gender": w.gender.value if hasattr(w, 'gender') and w.gender else 'Unknown',
            "hometown": getattr(w, 'hometown', ''),
            "level": w.wrestler_level.value if hasattr(w, 'wrestler_level') and w.wrestler_level else 'Show Ready',
            "level_icon": w.get_level_icon() if hasattr(w, 'get_level_icon') else '🎫',
            "level_color": w.get_level_color() if hasattr(w, 'get_level_color') else '#6b7280',
            "alignment": w.alignment.value if hasattr(w, 'alignment') and w.alignment else 'Tweener',
            "alignment_icon": w.get_alignment_icon() if hasattr(w, 'get_alignment_icon') else '😐',
            "primary_style": w.primary_style.value if hasattr(w, 'primary_style') and w.primary_style else 'Unknown',
            "secondary_style": (
                w.secondary_style.value
                if hasattr(w, 'secondary_style') and w.secondary_style
                else None
            ),
            "overall_rating": getattr(w, 'overall_rating', 50),
            "popularity": getattr(w, 'popularity', 30),
            "reputation": getattr(w, 'reputation', 0),
            "tier": self.tier.value,
            "tier_name": self.tier_name,
            "tier_icon": self.get_tier_icon(),
            "tier_color": self.get_tier_color(),
            "asking_per_show": self.asking_per_show,
            "signing_bonus": self.signing_bonus,
            "contract_length_weeks": self.contract_length_weeks,
            "is_exclusive_offer": self.is_exclusive_offer,
            "weeks_listed": self.weeks_listed,
            "weeks_remaining": self.get_weeks_remaining(),
            "rival_interested": self.rival_interested,
            "rival_promotion_name": self.rival_promotion_name,
            "is_hot_prospect": self.is_hot_prospect,
            "is_indy_god": self.is_indy_god,
            "is_licensed": self.is_licensed,
            "status_label": self.get_status_label(),
        }

    # ==================== SERIALIZATION ====================
    def to_dict(self) -> dict:
        return {
            "wrestler": self.wrestler.to_dict(),
            "tier": self.tier.value,
            "listing_week": self.listing_week,
            "listing_year": self.listing_year,
            "weeks_listed": self.weeks_listed,
            "contract_type": self.contract_type.value,
            "asking_per_show": self.asking_per_show,
            "asking_weekly_salary": self.asking_weekly_salary,
            "signing_bonus": self.signing_bonus,
            "contract_length_weeks": self.contract_length_weeks,
            "is_exclusive_offer": self.is_exclusive_offer,
            "rival_interested": self.rival_interested,
            "rival_promotion_name": self.rival_promotion_name,
            "rival_offer_deadline": self.rival_offer_deadline,
            "is_locked_in_negotiations": self.is_locked_in_negotiations,
            "is_hot_prospect": self.is_hot_prospect,
            "is_indy_god": self.is_indy_god,
            "is_licensed": self.is_licensed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentListing":
        try:
            tier = FreeAgentTier(data.get("tier", "Rookie"))
        except ValueError:
            tier = FreeAgentTier.ROOKIE
        try:
            ct = ContractType(data.get("contract_type", "Per Appearance"))
        except ValueError:
            ct = ContractType.PER_APPEARANCE

        return cls(
            wrestler=Wrestler.from_dict(data["wrestler"]),
            tier=tier,
            listing_week=data.get("listing_week", 0),
            listing_year=data.get("listing_year", 1),
            weeks_listed=data.get("weeks_listed", 0),
            contract_type=ct,
            asking_per_show=data.get("asking_per_show", 50),
            asking_weekly_salary=data.get("asking_weekly_salary", 0),
            signing_bonus=data.get("signing_bonus", 0),
            contract_length_weeks=data.get("contract_length_weeks", 26),
            is_exclusive_offer=data.get("is_exclusive_offer", False),
            rival_interested=data.get("rival_interested", False),
            rival_promotion_name=data.get("rival_promotion_name", ""),
            rival_offer_deadline=data.get("rival_offer_deadline", 0),
            is_locked_in_negotiations=data.get("is_locked_in_negotiations", False),
            is_hot_prospect=data.get("is_hot_prospect", False),
            is_indy_god=data.get("is_indy_god", False),
            is_licensed=data.get("is_licensed", False),
        )


# ==================== FREE AGENCY MANAGER ====================
class FreeAgencyManager:
    """Manages the entire free agency system - listings, signings, AI competition"""

    def __init__(self):
        # FIX: was `def **init**(self):` — markdown bold corruption
        self.listings: List[AgentListing] = []
        self.signed_count: int = 0
        self.lost_to_rivals: int = 0
        self.weeks_active: int = 0

    # ==================== SETUP / SEEDING ====================
    def seed_initial_pool(
        self,
        target_size: int = 80,
        include_licensed: bool = True,
        current_week: int = 0,
        current_year: int = 1,
    ):
        """Generate the initial free agent pool when the game starts"""
        from data.wrestler_pool import WrestlerPool
        pool = WrestlerPool()
        wrestlers = pool.generate_starter_pool(
            target_size=target_size,
            include_licensed=include_licensed,
        )
        for wrestler in wrestlers:
            listing = self._create_listing_for_wrestler(
                wrestler, current_week, current_year
            )
            if listing:
                self.listings.append(listing)

    def _create_listing_for_wrestler(
        self,
        wrestler: Wrestler,
        current_week: int,
        current_year: int,
    ) -> Optional[AgentListing]:
        """Build an AgentListing from a Wrestler"""
        tier = LEVEL_TO_TIER.get(wrestler.wrestler_level, FreeAgentTier.ROOKIE)

        # Calculate contract terms based on wrestler level
        per_show, signing_bonus, contract_length, is_exclusive = self._calculate_contract_terms(wrestler)

        # Determine special flags
        is_indy_god = getattr(wrestler, 'is_indy_god', False)
        is_licensed = wrestler.has_trait("Licensed Talent") if hasattr(wrestler, 'has_trait') else False
        is_hot = self._is_hot_prospect(wrestler)

        listing = AgentListing(
            wrestler=wrestler,
            tier=tier,
            listing_week=current_week,
            listing_year=current_year,
            weeks_listed=0,
            asking_per_show=per_show,
            signing_bonus=signing_bonus,
            contract_length_weeks=contract_length,
            is_exclusive_offer=is_exclusive,
            contract_type=ContractType.EXCLUSIVE if is_exclusive else ContractType.PER_APPEARANCE,
            is_hot_prospect=is_hot,
            is_indy_god=is_indy_god,
            is_licensed=is_licensed,
        )
        return listing

    def _calculate_contract_terms(self, wrestler: Wrestler) -> Tuple[int, int, int, bool]:
        """
        Calculate (per_show, signing_bonus, contract_length, is_exclusive) for a wrestler.

        FIX HISTORY:
        - Was calling wrestler.calculate_booking_fee() which doesn't exist (caused bad prices)
        - Was using markdown-corrupted `_level_mult_` operator
        - Now uses wrestler.booking_fee directly + LEVEL_FEE_MULTIPLIER from wrestler_pool
        """
        # Use the wrestler's pre-calculated booking_fee (set by WrestlerPool)
        # This is the SINGLE SOURCE OF TRUTH for per-show pricing.
        base_fee = getattr(wrestler, 'booking_fee', 50)

        # If somehow booking_fee is missing/zero, recalculate it as a safety net
        if base_fee <= 0:
            try:
                from data.wrestler_pool import calculate_booking_fee
                base_fee = calculate_booking_fee(
                    level=wrestler.wrestler_level,
                    popularity=getattr(wrestler, 'popularity', 30),
                    overall_rating=getattr(wrestler, 'overall_rating', 50),
                )
            except Exception:
                base_fee = 50  # Hard floor fallback

        # Top stars demand exclusive contracts
        is_exclusive = wrestler.wrestler_level in [
            WrestlerLevel.MAIN_EVENTER, WrestlerLevel.TOP_STAR,
            WrestlerLevel.LEGEND, WrestlerLevel.ICON,
        ]

        # Indy Gods sometimes prefer per-show (cult appeal)
        if getattr(wrestler, 'is_indy_god', False) and random.random() < 0.5:
            is_exclusive = False

        per_show = base_fee
        signing_bonus = 0
        contract_length = 26

        if is_exclusive:
            # Get fee multiplier from wrestler_pool (single source of truth)
            try:
                from data.wrestler_pool import LEVEL_FEE_MULTIPLIER
                level_mult = LEVEL_FEE_MULTIPLIER.get(wrestler.wrestler_level, 1.0)
            except Exception:
                level_mult = 1.0

            # FIX: was `int(base_fee _level_mult_ 4)` — markdown corruption
            # Signing bonus = ~4 weeks of base fee, scaled by tier multiplier
            signing_bonus = int(base_fee * level_mult * 4)

            # Cap signing bonus at sane levels (we don't want $40k bonuses for indy stars)
            signing_bonus = min(signing_bonus, base_fee * 20)  # Max 20x weekly

            contract_length = random.choice([26, 39, 52])  # 6mo / 9mo / 1yr

        return per_show, signing_bonus, contract_length, is_exclusive

    def _is_hot_prospect(self, wrestler: Wrestler) -> bool:
        """Determine if wrestler should be flagged as a hot prospect"""
        age = getattr(wrestler, 'age', 30)
        popularity = getattr(wrestler, 'popularity', 30)
        overall_rating = getattr(wrestler, 'overall_rating', 50)

        # High popularity + low age + decent stats = hot
        if age <= 28 and popularity >= 60 and overall_rating >= 65:
            return True
        # Recent reputation gains
        if wrestler.wrestler_level in [WrestlerLevel.RISING_STAR, WrestlerLevel.INDY_DARLING]:
            if popularity >= 55:
                return True
        return False

    # ==================== QUERIES ====================
    def get_all_listings(self) -> List[AgentListing]:
        """Get all current free agent listings"""
        return list(self.listings)

    def get_listings_by_tier(self, tier: FreeAgentTier) -> List[AgentListing]:
        """Filter listings by tier"""
        return [l for l in self.listings if l.tier == tier]

    def get_listing_by_name(self, wrestler_name: str) -> Optional[AgentListing]:
        """Find a specific listing by wrestler name"""
        for listing in self.listings:
            if listing.wrestler.name == wrestler_name:
                return listing
        return None

    def get_hot_prospects(self) -> List[AgentListing]:
        """Get only hot prospect listings"""
        return [l for l in self.listings if l.is_hot_prospect]

    def get_indy_gods(self) -> List[AgentListing]:
        """Get only Indy God listings"""
        return [l for l in self.listings if l.is_indy_god]

    def get_licensed_talent(self) -> List[AgentListing]:
        """Get only licensed real-world talent listings"""
        return [l for l in self.listings if l.is_licensed]

    def get_total_count(self) -> int:
        return len(self.listings)

    def get_count_by_tier(self) -> Dict[str, int]:
        """Get count of listings per tier for UI tabs"""
        counts = {}
        for tier in FreeAgentTier:
            counts[tier.value] = len(self.get_listings_by_tier(tier))
        return counts

    # ==================== SIGNING ====================
    def can_sign(
        self,
        wrestler_name: str,
        budget: int,
        roster_count: int,
        roster_limit: int,
    ) -> Tuple[bool, str]:
        """Check if a wrestler can be signed. Returns (can_sign, reason)"""
        listing = self.get_listing_by_name(wrestler_name)
        if not listing:
            return (False, "Wrestler not found in free agency")

        if roster_count >= roster_limit:
            return (False, f"Roster full ({roster_count}/{roster_limit})")

        upfront_cost = listing.get_total_first_payment()
        if budget < upfront_cost:
            return (False, f"Insufficient funds (need ${upfront_cost:,})")

        if listing.is_locked_in_negotiations:
            return (False, f"In negotiations with {listing.rival_promotion_name}")

        return (True, "Can sign")

    def sign_wrestler(
        self,
        wrestler_name: str,
        budget: int,
        roster_count: int,
        roster_limit: int,
    ) -> Tuple[bool, str, Optional[Wrestler], int]:
        """
        Sign a wrestler from free agency.
        Returns: (success, message, wrestler_or_None, cost_paid)
        """
        can_sign, reason = self.can_sign(wrestler_name, budget, roster_count, roster_limit)
        if not can_sign:
            return (False, reason, None, 0)

        listing = self.get_listing_by_name(wrestler_name)
        if not listing:
            return (False, "Listing not found", None, 0)

        wrestler = listing.wrestler

        # Apply contract terms to wrestler (using listing values - the source of truth)
        wrestler.booking_fee = listing.asking_per_show
        wrestler.contract_type = listing.contract_type
        wrestler.contract_length = listing.contract_length_weeks
        wrestler.is_exclusive = listing.is_exclusive_offer
        wrestler.is_signed = True

        # Boost morale on signing
        if hasattr(wrestler, 'adjust_morale'):
            wrestler.adjust_morale(15)

        cost_paid = listing.get_total_first_payment()

        # Remove from listings
        self.listings.remove(listing)
        self.signed_count += 1

        msg = f"Signed {wrestler.name} ({listing.tier_name})"
        if cost_paid > 0:
            msg += f" for ${cost_paid:,} signing bonus"
        else:
            msg += f" — ${listing.asking_per_show}/show"

        return (True, msg, wrestler, cost_paid)

    def remove_listing(self, wrestler_name: str) -> bool:
        """Remove a listing without signing (e.g. they retired or signed elsewhere)"""
        listing = self.get_listing_by_name(wrestler_name)
        if listing:
            self.listings.remove(listing)
            return True
        return False

    # ==================== WEEKLY UPDATE ====================
    def weekly_update(
        self,
        current_week: int,
        current_year: int,
        ai_director=None,
        rival_promotions=None,
    ) -> Dict:
        """Process weekly free agency operations"""
        result = {
            "expired": [],
            "rival_signings": [],
            "new_arrivals": [],
            "rival_interest_added": [],
        }

        self.weeks_active += 1

        # Age existing listings & remove expired
        for listing in self.listings[:]:
            listing.weeks_listed += 1

            # Check rival signing deadline
            if listing.rival_interested and current_week >= listing.rival_offer_deadline:
                # Rival signs them
                self.listings.remove(listing)
                self.lost_to_rivals += 1
                result["rival_signings"].append({
                    "wrestler": listing.wrestler.name,
                    "rival": listing.rival_promotion_name,
                })
                continue

            # Auto-expire after 4 weeks
            if listing.weeks_listed >= 4:
                self.listings.remove(listing)
                result["expired"].append(listing.wrestler.name)

        # Generate new listings to refresh pool
        new_listings = self._generate_weekly_refresh(current_week, current_year)
        result["new_arrivals"] = [l.wrestler.name for l in new_listings]

        # AI rivals show interest in some listings
        if rival_promotions:
            interest_added = self._process_rival_interest(
                current_week, rival_promotions
            )
            result["rival_interest_added"] = interest_added

        return result

    def _generate_weekly_refresh(
        self,
        current_week: int,
        current_year: int,
    ) -> List[AgentListing]:
        """Generate new free agents to keep the pool fresh"""
        from data.wrestler_pool import WrestlerPool
        target_size = 80
        current_size = len(self.listings)

        if current_size >= target_size:
            return []

        pool = WrestlerPool()

        # Track existing names to avoid duplicates
        for listing in self.listings:
            pool.used_names.add(listing.wrestler.name)

        new_wrestlers = pool.generate_weekly_refresh(
            current_pool_size=current_size,
            target_pool_size=target_size,
        )

        new_listings = []
        for wrestler in new_wrestlers:
            listing = self._create_listing_for_wrestler(
                wrestler, current_week, current_year
            )
            if listing:
                self.listings.append(listing)
                new_listings.append(listing)

        return new_listings

    def _process_rival_interest(
        self,
        current_week: int,
        rival_promotions,
    ) -> List[Dict]:
        """AI rival promotions show interest in select free agents"""
        added = []
        try:
            active_rivals = (
                rival_promotions.get_all_rivals()
                if hasattr(rival_promotions, 'get_all_rivals')
                else []
            )
        except Exception:
            active_rivals = []

        if not active_rivals:
            return added

        # 15% chance per week that a rival shows interest in a wrestler
        for listing in self.listings:
            if listing.rival_interested:
                continue

            if random.random() < 0.15:
                rival = random.choice(active_rivals)
                rival_name = getattr(rival, 'name', 'A rival promotion')

                listing.rival_interested = True
                listing.rival_promotion_name = rival_name
                # Rival will sign in 1-2 weeks if you don't act
                listing.rival_offer_deadline = current_week + random.randint(1, 2)
                added.append({
                    "wrestler": listing.wrestler.name,
                    "rival": rival_name,
                    "deadline": listing.rival_offer_deadline,
                })

        return added

    # ==================== INDY GOD CONVERSION ====================
    def add_released_wrestler(
        self,
        wrestler: Wrestler,
        current_week: int,
        current_year: int,
    ):
        """Add a recently released wrestler as an Indy God free agent"""
        # Convert to Indy God if not already
        if not getattr(wrestler, 'is_indy_god', False):
            if hasattr(wrestler, 'become_indy_god'):
                wrestler.become_indy_god()

        listing = self._create_listing_for_wrestler(wrestler, current_week, current_year)
        if listing:
            listing.is_indy_god = True
            self.listings.append(listing)
            return listing
        return None

    # ==================== UI HELPERS ====================
    def get_filter_summary(self) -> Dict:
        """Get summary for UI filter tabs"""
        counts = self.get_count_by_tier()
        return {
            "total": len(self.listings),
            "by_tier": counts,
            "hot_prospects": len(self.get_hot_prospects()),
            "indy_gods": len(self.get_indy_gods()),
            "licensed": len(self.get_licensed_talent()),
            "rival_interest_count": len([l for l in self.listings if l.rival_interested]),
        }

    # ==================== SERIALIZATION ====================
    def to_dict(self) -> dict:
        return {
            "listings": [l.to_dict() for l in self.listings],
            "signed_count": self.signed_count,
            "lost_to_rivals": self.lost_to_rivals,
            "weeks_active": self.weeks_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FreeAgencyManager":
        manager = cls()
        manager.signed_count = data.get("signed_count", 0)
        manager.lost_to_rivals = data.get("lost_to_rivals", 0)
        manager.weeks_active = data.get("weeks_active", 0)
        for ld in data.get("listings", []):
            try:
                manager.listings.append(AgentListing.from_dict(ld))
            except Exception:
                pass
        return manager
