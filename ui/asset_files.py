from i18n import tr, CATALOG
"""Local Excel/CSV interchange. No online spreadsheet connection."""
import csv
import json
from pathlib import Path
from decimal import Decimal
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

LEGACY_HEADERS=['구분','종목명','종목코드','보유수량','매입금액','평가금액']
HEADERS=['구분','종목명','종목코드','보유수량','매입가','현재가']
GUIDE='''엑셀(.xlsx), UTF-8 CSV, JSON을 지원합니다.
첫 행: 구분 | 종목명 | 종목코드 | 보유수량 | 매입가 | 현재가
구분: 국내 / 해외 / 예수금 / 환율
국내 가격은 주당 원, 해외 가격은 주당 USD입니다. 수량은 소수점 8자리까지 입력할 수 있습니다.
예수금 행은 현재가 열에 원화 예수금, 환율 행은 현재가 열에 1 USD당 원을 적습니다.
환율 공란은 해외자산 비중계산을 중단하고 경고합니다.
예: 해외 | 예시 ETF | ABC | 10 | 25.50 | 27.00
예: 환율 | USD/KRW | (공란) | 0 | 0 | 1400
예: 예수금 | 예수금 | (공란) | 0 | 0 | 50000
종목코드는 텍스트로 입력하세요. 숫자는 쉼표를 포함할 수 있습니다.
수식 대신 숫자 값을 입력하세요. 자산 시트를 읽습니다.
기존 매입금액/평가금액 양식도 국내 자산으로 불러옵니다.
Google 스프레드시트는 xlsx 또는 CSV로 내려받아 가져오세요.
가져오기 전 전체 검증과 교체 확인을 거칩니다.'''

def export_file(path,data):
    path=Path(path)
    if path.suffix.lower()=='.json':
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');return
    from portfolio_data import validate
    data=validate(data)
    rows=[[tr(h) for h in HEADERS],[tr('예수금'),tr('예수금'),'',0,0,data['cash']],[tr('환율'),'USD/KRW','',0,0,data.get('fx','')]]
    for r in data['holdings']:rows.append([tr('해외') if r['market']=='us' else tr('국내'),r['name'],r['symbol'],r['quantity'],r['buy_price'],r['current_price']])
    if path.suffix.lower()=='.csv':
        # Prefix formula-like text for spreadsheet safety; importer removes this prefix.
        with path.open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.writer(stream)
            for row in rows:
                writer.writerow(["'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v for v in row])
        return
    wb=Workbook();ws=wb.active;ws.title=tr('자산')
    for ri,row in enumerate(rows,1):
        for ci,value in enumerate(row,1):
            cell=ws.cell(ri,ci)
            if ri>1 and ci>=4:
                cell.value=str(value) if ci==4 else float(Decimal(str(value))) if str(value) else None
                cell.number_format='@' if ci==4 else '#,##0.00'
            else:
                cell.value=str(value);cell.data_type='s'
                if ci==3:cell.number_format='@'
            if ri==1:
                cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='244363')
    for col,width in zip('ABCDEF',[12,36,18,16,22,22]):ws.column_dimensions[col].width=width
    ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
    notes=wb.create_sheet(tr('형식 안내'))
    for i,line in enumerate(tr(GUIDE).splitlines(),1):notes.cell(i,1,line)
    notes.column_dimensions['A'].width=110
    wb.save(path);wb.close()

def import_file(path):
    path=Path(path)
    if path.suffix.lower()=='.json':return json.loads(path.read_text(encoding='utf-8-sig'))
    if path.suffix.lower()=='.xlsx':
        wb=load_workbook(path,read_only=True,data_only=False)
        try:
            ws=wb['자산'] if '자산' in wb.sheetnames else wb.worksheets[0]
            rows=[]
            for row in ws.iter_rows():
                if any(c.data_type=='f' for c in row):raise ValueError(tr('수식 셀이 있습니다. 숫자 값으로 바꾼 뒤 가져와 주세요.'))
                rows.append([c.value for c in row])
        finally:wb.close()
    elif path.suffix.lower()=='.csv':
        with path.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.reader(stream))
    else:raise ValueError(tr('xlsx, CSV 또는 기존 JSON 파일을 선택해 주세요.'))
    header=[str(v or '').strip() for v in rows[0][:6]] if rows else []
    aliases={CATALOG.get(h,h):h for h in HEADERS+LEGACY_HEADERS}
    header=[aliases.get(h,h) for h in header]
    if header not in (HEADERS,LEGACY_HEADERS):raise ValueError(tr('열 제목이 맞지 않습니다. 형식 안내를 확인해 주세요.'))
    legacy=header==LEGACY_HEADERS
    data={'cash':'0','holdings':[]};cash_seen=False;fx_seen=False
    def txt(value):
        s='' if value is None else str(value).strip()
        return s[1:] if s.startswith("'") else s
    for lineno,row in enumerate(rows[1:],2):
        if not any(v is not None and str(v).strip() for v in row):continue
        row=list(row)+[None]*max(0,6-len(row))
        kind=txt(row[0])
        kind={CATALOG.get(k,k):k for k in ('국내','해외','예수금','환율','종목')}.get(kind,kind)
        if kind=='예수금':
            if cash_seen:raise ValueError(tr('예수금 행은 하나만 입력해 주세요.'))
            cash_seen=True;data['cash']=txt(row[5]) or '0'
        elif kind=='환율' and not legacy:
            if fx_seen:raise ValueError(tr('환율 행은 하나만 입력해 주세요.'))
            fx_seen=True;data['fx']=txt(row[5])
        elif kind in (('종목',) if legacy else ('국내','해외')):
            symbol=txt(row[2])
            if kind!='해외' and isinstance(row[2],(int,float)) and float(row[2]).is_integer():symbol=str(int(row[2])).zfill(6)
            item=dict(name=txt(row[1]),symbol=symbol,quantity=txt(row[3]) or '0',market='us' if kind=='해외' else 'kr')
            item.update({('krw' if legacy else 'buy_price'):txt(row[4]) or '0',('evaluation_krw' if legacy else 'current_price'):txt(row[5]) or '0'})
            data['holdings'].append(item)
        else:raise ValueError(f"{lineno}{tr('행 구분을 확인해 주세요(국내/해외/예수금/환율).')}")
    return data
