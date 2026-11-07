from i18n import tr
"""Render allocation snapshots independently of viewport and scroll position."""
import math
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from chart_palette import COLORS
from average_cost import number
import dashboard_theme as theme
from allocation_media import hatch_sector


def render(data, extra, capital, rows, results, basis, palette, theme_name):
    p = palette
    width = 1600
    basis = 'evaluation'
    key = 'evaluation'
    total = sum(row[key] for row in rows)
    shortage = next((r.get('funding',0) for r in rows if r['key']==('cash',)),0)
    capital = next((r.get('funded_capital',capital) for r in rows if r['key']==('cash',)),capital)
    current = {('holding', i): dict(purchase=number(h.get('krw')), evaluation=number(h.get('evaluation_krw')))
               for i, h in enumerate(data.get('holdings', []))}
    current[('cash',)] = dict(purchase=number(data.get('cash')), evaluation=number(data.get('cash')))
    current_total = sum(r['evaluation'] for r in current.values())
    target_total = sum(r['evaluation'] for r in rows if r['key']!=('funding',))
    current_chart_total = sum(r[key] for r in current.values())
    projected = {r['key']: r for r in rows}
    def original(row):
        return current.get(row['key'], dict(purchase=number(0), evaluation=number(0)))
    def comparison(result):
        before = original(result)['evaluation']
        after = projected[result['key']]['evaluation']
        old_weight = before / current_total * 100 if current_total else 0
        new_weight = after / target_total * 100 if target_total else 0
        return f"{tr('기존 평가 ')}{before:,.0f}{tr('원 (')}{old_weight:.2f}{tr('%) > 목표 평가 ')}{after:,.0f}{tr('원 (')}{new_weight:.2f}%)"
    font_cache = {}

    def font(size, bold=False):
        cache_key = (size, bold)
        if cache_key not in font_cache:
            font_cache[cache_key] = ImageFont.truetype('C:/Windows/Fonts/' + ('malgunbd.ttf' if bold else 'malgun.ttf'), size)
        return font_cache[cache_key]

    def wrap(text, limit, size=24):
        lines, line = [], ''
        for char in str(text):
            if line and font(size).getlength(line + char) > limit:
                lines.append(line); line = ''
            line += char
        return lines + [line]

    targets = [(r, wrap(r['name'] + (f" ({r['symbol']})" if r['symbol'] else ''), 650)) for r in results]
    comparisons = [wrap(comparison(r), 680, 23) for r, _ in targets]
    target_height = max(95, sum(46 + 32 * (len(lines) + len(detail)) for (_, lines), detail in zip(targets, comparisons)))
    legend = [(r, wrap(r['name'], 350)) for r in rows]
    legend_height = sum(max(60, 20 + 32 * len(lines)) for _, lines in legend)
    summary_bottom = max(820, 390 + target_height)
    height = summary_bottom + 155 + legend_height + 145
    image = Image.new('RGB', (width, height), p['page'])
    d = ImageDraw.Draw(image)

    def text(x, y, value, size=24, bold=False, color=None, anchor=None):
        d.text((x, y), str(value), font=font(size, bold), fill=color or p['text'], anchor=anchor)

    def card(box):
        d.rounded_rectangle(box, radius=24, fill=p['card'])

    text(44, 32, tr('비중계산 · 예상 포트폴리오'), 38, True)
    text(1556, 47, datetime.now().strftime('%Y.%m.%d %H:%M'), 21, color=p['muted'], anchor='ra')
    card((32, 108, 1568, 250))
    text(60, 130, f"{tr('현재 평가자산 + 현금  ')}{current_total:,.0f}{tr('원')}", 26)
    text(60, 180, f"{tr('예수금 조정  ')}{extra:+,.0f}{tr('원')}" if extra else tr('예수금 조정  0원'), 24, color='#159C65' if extra > 0 else '#E5484D' if extra < 0 else p['muted'])
    text(910, 130, tr('목표 평가자산 + 현금'), 24, color=p['muted'])
    text(910, 175, f"{capital:,.0f}{tr('원')}", 32, True)
    card((32, 274, 790, summary_bottom))
    card((814, 274, 1568, summary_bottom))
    text(60, 295, tr('추가한 목표 설정'), 28, True)
    y = 350
    if not targets:
        text(60, y, tr('추가한 목표 없음 · 현재 포트폴리오'), color=p['muted'])
    for (r, lines), detail in zip(targets, comparisons):
        for line in lines:
            text(60, y, line); y += 32
        for line in detail:
            text(60, y, line, 23); y += 32
        delta = r['delta']
        action = tr('추가할 금액') if delta > 0 else tr('줄일 금액') if delta < 0 else tr('변경 없음')
        text(60, y, f"{action}  {abs(delta):,.0f}{tr('원')}", 23,
             color='#159C65' if delta > 0 else '#E5484D' if delta < 0 else p['muted'])
        y += 46
    text(845, 295, tr('목표비중 차트 · ') + (tr('매입차트') if basis == 'purchase' else tr('평가차트')), 28, True)
    # Supersample only the donut; the exported text is rendered at final resolution.
    scale, size = 3, 400
    tile = Image.new('RGB', (size * scale, size * scale), p['card'])
    brush = ImageDraw.Draw(tile)
    bounds = (6, 6, size * scale - 6, size * scale - 6)
    start = -90
    labels = []
    colors = [theme.chart_color(i, r['key'] == ('cash',), COLORS[i % len(COLORS)], theme_name) for i, r in enumerate(rows)]
    for r, color in zip(rows, colors):
        if r[key] <= 0 or total <= 0:continue
        extent = float(r[key] / total * 360)
        if extent >= 359.999999:brush.ellipse(bounds, fill=color)
        else:brush.pieslice(bounds, start=start, end=start + extent, fill=color, outline=p['card'], width=scale)
        if extent >= 18:
            angle = math.radians(start + extent / 2)
            labels.append((1190 + 146 * math.cos(angle), 555 + 146 * math.sin(angle), f"{r['weight']:.0f}%", color))
        missing=min(r[key],r.get('shortfall',0))
        if missing>0:
            hatch_extent=float(missing/total*360)
            hatch_sector(tile,bounds,start+extent-hatch_extent,hatch_extent,scale)
        start += extent
    brush.ellipse((size * scale * .29, size * scale * .29, size * scale * .71, size * scale * .71), fill=p['card'])
    image.paste(tile.resize((size, size), Image.Resampling.LANCZOS), (990, 355));tile.close()
    for x, y, label, color in labels:
        rgb = [int(color[i:i+2], 16) for i in (1,3,5)]
        ink = '#172332' if sum(a*b for a,b in zip(rgb,(.299,.587,.114))) > 145 else '#FFFFFF'
        text(x, y, label, 23, color=ink, anchor='mm')
    text(1190, 540, tr('목표 비중'), 24, True, anchor='mm')
    text(1190, 575, tr('매입 기준') if basis == 'purchase' else tr('평가 기준'), 21, color=p['muted'], anchor='mm')
    text(845, 775, tr('추가 입금만으로 목표 유지 불가') if shortage is None else f"{tr('목표비중 유지 필요 입금 ')}{shortage:,.0f}{tr('원')}" if shortage else f"{tr('차트 합계 ')}{total:,.0f}{tr('원')}", 21, color='#E99083' if shortage is None or shortage else p['muted'])
    y = summary_bottom + 24
    card((32, y, 1568, height - 125))
    text(60, y + 18, tr('목표비중 세부내역'), 26, True)
    y += 70
    for x, label, anchor in ((135,tr('종목코드'),'ma'),(225,tr('종목명'),None),(790,tr('매입금액'),'ra'),(1000,tr('평가금액'),'ra'),(1210,tr('목표금액'),'ra'),(1370,tr('목표비중'),'ra'),(1530,tr('조정률'),'ra')):
        text(x, y, label, 22, color=p['muted'], anchor=anchor)
    y += 42
    for (r, lines), color in zip(legend, colors):
        row_height = max(60, 20 + 32 * len(lines))
        if r['changed']:d.rounded_rectangle((48,y,1552,y+row_height-3), radius=10, fill=p['soft'])
        d.ellipse((60,y+22,72,y+34),fill=color)
        text(135,y+16,r['symbol'] or '—',22,anchor='ma')
        for n,line in enumerate(lines):text(225,y+12+n*32,line)
        old = original(r)
        target = r[key]
        before = old[key]
        old_weight = before / current_chart_total * 100 if current_chart_total else 0
        adjustment = r['weight'] - old_weight
        adjustment_text = '—' if r['key']==('funding',) else f'{adjustment:+.2f}%p'
        text(790,y+16,f"{old['purchase']:,.0f}{tr('원')}",21,anchor='ra')
        text(1000,y+16,f"{old['evaluation']:,.0f}{tr('원')}",21,anchor='ra')
        text(1210,y+16,f"{target:,.0f}{tr('원')}",21,anchor='ra')
        text(1370,y+16,f"{r['weight']:.2f}%",21,anchor='ra')
        text(1530,y+16,adjustment_text,21,anchor='ra',
             color='#159C65' if adjustment > 0 else '#E5484D' if adjustment < 0 else p['muted'])
        y += row_height
    text(44,height-102,tr('현재 매입·평가금액은 조정 전 원본 · 목표금액/목표비중/조정률은 평가금액 기준 · 신규 종목의 기존 비중은 0%'),20,color=p['muted'])
    text(44,height-66,tr('부족 시 필요 입금 반영 후 예상 포트폴리오 · 필요 입금액은 자산에 중복 합산하지 않음 · 수수료/세금 제외'),20,color=p['muted'])
    return image
