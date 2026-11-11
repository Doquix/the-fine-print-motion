from .phone import PhoneTap
from .cards import NotifChat, TaskCarousel, CounterClimb, WalletSend, StampReveal, SourceCard
from .multi import TrustPayment, MoneyFlow, CoinRequest
from .alert import BlockModal
from .text import KineticLine, LogoOutro

REGISTRY = {c.name: c for c in (PhoneTap, NotifChat, TaskCarousel, CounterClimb, TrustPayment, CoinRequest, WalletSend,
                                StampReveal, MoneyFlow, SourceCard, BlockModal, KineticLine, LogoOutro)}
