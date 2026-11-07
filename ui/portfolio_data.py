from i18n import tr
"""Native currency prices; KRW projections are always derived from quantity and FX."""
from decimal import Decimal
from datetime import datetime
from average_cost import number
from quantity import shares

def validate(raw):
    cash=number(raw.get('cash','0'))
    fx_text=str(raw.get('fx','')).strip().replace(',','')
    fx=number(fx_text) if fx_text else None
    if fx is not None and fx<=0:raise ValueError(tr('환율은 0보다 커야 합니다.'))
    holdings=[]
    for source in raw.get('holdings',[]):
        name=str(source.get('name','')).strip()
        if not name:raise ValueError(tr('종목명을 입력해 주세요.'))
        q=shares(source.get('quantity',0))
        market=source.get('market','kr')
        if market not in ('kr','us'):raise ValueError(tr('국내 또는 해외 자산을 선택해 주세요.'))
        if 'buy_price' in source:
            buy=number(source['buy_price']);current=number(source['current_price'])
            purchase=buy*q;value=current*q
        else:
            purchase=number(source.get('purchase',source.get('krw',0)))
            value=number(source.get('evaluation_krw',0))
            buy=purchase/q if q else Decimal(0);current=value/q if q else Decimal(0)
            if not q and (purchase or value):raise ValueError(f"{name}{tr(': 금액이 있는 자산은 보유수량을 입력해 주세요.')}")
        rate=Decimal(1) if market=='kr' else fx
        holdings.append(dict(name=name,symbol=str(source.get('symbol','')).strip(),quantity=str(q),
            market=market,currency='USD' if market=='us' else 'KRW',broker='local',buy_price=str(buy),current_price=str(current),
            purchase=str(purchase),krw=str(purchase*rate) if rate else '0',
            evaluation_krw=str(value*rate) if rate else '0',at=source.get('at') or datetime.now().isoformat()))
    missing=fx is None and any(h['market']=='us' for h in holdings)
    return dict(schema=2,cash=str(cash),fx=fx_text,fx_missing=missing,holdings=holdings,
        capital=str(cash+sum((Decimal(h['evaluation_krw']) for h in holdings),Decimal(0))))
