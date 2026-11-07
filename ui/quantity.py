from i18n import tr
"""Exact fractional share validation and display."""
from decimal import Decimal

def shares(raw):
    value=Decimal(str(raw).replace(',', '').strip())
    if not value.is_finite() or value<0:
        raise ValueError(tr('수량은 0 이상의 유한한 숫자여야 합니다.'))
    if value != value.quantize(Decimal('0.00000001')):
        raise ValueError(tr('수량은 소수점 8자리까지 입력해 주세요.'))
    return value

def display_shares(raw):
    s=format(Decimal(str(raw)), ',.8f').rstrip('0').rstrip('.')
    return s or '0'
