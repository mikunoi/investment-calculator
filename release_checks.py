"""Isolated regression checks: never load the user's saved portfolio."""
import os,sys,tempfile,unittest,json,time
from pathlib import Path
from decimal import Decimal as D
from types import SimpleNamespace
from unittest.mock import patch

ISOLATED=tempfile.TemporaryDirectory()
os.environ['LOCALAPPDATA']=ISOLATED.name
sys.path.insert(0,str(Path(__file__).parent/'ui'))
from portfolio_data import validate
from allocation_tool import scenario,AllocationView
from average_cost import calculate,AverageCostView,PALETTES
from asset_files import export_file,import_file
from main import App,DATA_FILE
import goal_history

def sample(fx='1400'):
    return validate(dict(cash='100000',fx=fx,holdings=[dict(name='국내',symbol='001234',market='kr',quantity=10,buy_price=1000,current_price=1200),dict(name='미국',symbol='ABC',market='us',quantity=2,buy_price=50,current_price=60)]))

def find(w,cls):
    if isinstance(w,cls):return w
    for child in w.winfo_children():
        result=find(child,cls)
        if result:return result

class ReleaseChecks(unittest.TestCase):
    def setUp(self):
        import i18n
        i18n.select('ko')
        from main import SETTINGS_FILE
        if SETTINGS_FILE.exists():SETTINGS_FILE.unlink()

    def test_fractional_precision(self):
        from quantity import display_shares
        q,cost,avg,added=calculate('0.125','100',[('200','0.375')])
        self.assertEqual((q,cost,avg,added),(D('.5'),D('87.5'),D('175'),D('75')))
        self.assertEqual(display_shares('10.00000000'),'10')
        self.assertEqual(display_shares('.00000001'),'0.00000001')
        for bad in ('-1','NaN','Infinity','0.000000001'):
            with self.assertRaises((ValueError,ArithmeticError)):calculate(bad,'1',[])
        for language in ('ko','en'):
            import i18n
            i18n.select(language)
            data=validate(dict(cash='100',fx='1400',holdings=[dict(name='User 한글 name',symbol='000001',market='us',quantity='12345678.12345678',buy_price='1',current_price='2')]))
            for ext in ('xlsx','csv','json'):
                path=Path(ISOLATED.name)/('fractional.'+ext)
                export_file(path,data)
                loaded=validate(import_file(path))
                self.assertEqual(loaded['holdings'][0]['quantity'],'12345678.12345678')
                self.assertEqual(loaded['capital'],data['capital'])
                self.assertEqual(loaded['holdings'][0]['name'],'User 한글 name')

    def test_language_and_preferences(self):
        import i18n
        from main import SETTINGS_FILE
        app=App();app.withdraw()
        try:
            app.persist(validate(dict(cash='10000',fx='1400',holdings=[dict(name='Custom 이름',symbol='ABC',market='us',quantity='.125',buy_price='20',current_price='25')])))
            app.show('average');view=find(app,AverageCostView)
            view.choices.current(1);view.load_holding();self.assertEqual(view.quantity.get(),'0.125')
            app.show('allocation');view=find(app,AllocationView)
            view.plans=[dict(key=('holding',0),name='Custom 이름',symbol='ABC',kind='percent',value=D(20))]
            view.extra.set('123')
            app.mode.set('메트릭스');app.change_theme()
            # Set a target after the theme rebuild, then change language.
            view=find(app,AllocationView);view.plans=[dict(key=('holding',0),name='Custom 이름',symbol='ABC',kind='percent',value=D(20))]
            app.language.set('US');app.change_language()
            view=find(app,AllocationView)
            self.assertEqual(len(view.plans),1)
            self.assertEqual(i18n.tr('내 자산'),'My assets')
            saved=json.loads(SETTINGS_FILE.read_text())
            self.assertEqual(saved,{'mode':'matrix','language':'en'})
            app.show('assets');app.update_idletasks()
            self.assertEqual(app.title(),'mikunoi_Stock_Calculator')
        finally:app.close()
        app=App();app.withdraw()
        try:
            self.assertEqual(app.language.get(),'US');self.assertEqual(app.mode.get(),'Matrix')
            app.language.set('한글');app.change_language()
            self.assertEqual(app.mode.get(),'메트릭스')
        finally:app.close()


    def test_fx_and_withdrawal(self):
        self.assertEqual(scenario(sample(),[],'-10,000')[0],D(270000))
        self.assertEqual(scenario(sample(),[],'-10,000')[1],D(90000))
        with self.assertRaises(ValueError):scenario(sample(''),[],'')
        for invalid in ('NaN','Infinity','-1'):
            with self.assertRaises((ValueError,ArithmeticError)):sample(invalid)

    def test_funding_invariants(self):
        for percent in (10,60,80,99):
            plan=dict(key=('holding',0),name='A',symbol='A',kind='percent',value=D(percent))
            _,_,rows,_=scenario(sample(),[plan],'')
            total=sum(r['evaluation'] for r in rows)
            self.assertAlmostEqual(rows[0]['evaluation']/total*100,D(percent),places=12)
            self.assertAlmostEqual(sum(r.get('weight',r['evaluation']/total*100) for r in rows),D(100),places=12)

    def test_english_ui_and_export_coverage(self):
        import i18n,re,ast
        i18n.select('en')
        for source in (Path(__file__).parent/'ui').glob('*.py'):
            if source.name=='i18n.py':continue
            for node in ast.walk(ast.parse(source.read_text(encoding='utf-8'))):
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='tr' and node.args and isinstance(node.args[0],ast.Constant):
                    text=node.args[0].value
                    if isinstance(text,str):self.assertFalse(re.search('[가-힣]',i18n.tr(text)),(source.name,text))
        # Set startup preferences in the isolated user directory.
        from main import SETTINGS_FILE
        SETTINGS_FILE.parent.mkdir(parents=True,exist_ok=True)
        SETTINGS_FILE.write_text('{"mode":"default","language":"en"}')
        app=App();app.withdraw()
        try:
            app.persist(validate(dict(cash='10000',fx='1400',holdings=[dict(name='Custom ETF',symbol='ABC',market='us',quantity='.125',buy_price='20',current_price='25')])))
            def walk(w):
                yield w
                for c in w.winfo_children():yield from walk(c)
            for page in ('assets','average','allocation'):
                app.show(page);app.update_idletasks()
                for w in walk(app.pages[page][0]):
                    try:text=str(w.cget('text'))
                    except Exception:continue
                    self.assertFalse(re.search('[가-힣]',text),text)
            from allocation_export import render
            from PIL import ImageDraw
            drawn=[];original=ImageDraw.ImageDraw.text
            def capture(draw,xy,text,*args,**kwargs):
                drawn.append(str(text));return original(draw,xy,text,*args,**kwargs)
            data=app.data;capital,_,rows,results=scenario(data,[],'')
            with patch.object(ImageDraw.ImageDraw,'text',capture):
                image=render(data,D(0),capital,rows,results,'evaluation',PALETTES['default'],'default')
                image.close()
            self.assertTrue(drawn)
            self.assertFalse(any(re.search('[가-힣]',t) for t in drawn))
        finally:app.close()

    def test_update_snooze_and_reopen(self):
        import app_update as u
        app=App();app.withdraw();errors=[];app.report_callback_exception=lambda *e:errors.append(e)
        updater=u.StartupUpdate(app);app.updater=updater
        app.after_cancel(updater.job);updater.job=None
        info={'tag':'v9.0.0','notes':'## 한국어\n- 변경사항\n## English\n- Improvements'}
        try:
            updater.show(info);app.update()
            self.assertFalse(updater.progress.winfo_ismapped())
            updater.dismiss(snooze=True)
            self.assertGreater(u.snoozed_until(),time.time()+6.99*86400)
            self.assertTrue(updater.header_button.winfo_exists())
            updater.open_pending();app.update();self.assertTrue(updater.dialog.winfo_exists())
            self.assertFalse(updater.cancel.is_set())
            updater.dismiss()
            app.language.set('US');app.change_language();app.update()
            self.assertTrue(updater.header_button.winfo_exists())
            updater.open_pending();app.update();updater.dismiss()
            # A new app session must suppress the automatic popup but retain access.
            second=u.StartupUpdate(app);app.after_cancel(second.job);second.job=None
            second.messages.put(('release',info));second.poll()
            self.assertIsNone(second.dialog);self.assertTrue(second.header_button.winfo_exists())
            second.stop()
            self.assertFalse(errors)
            self.assertNotIn('##',u.notes_for_language(info['notes']))
        finally:app.close()

    def test_update_card_resize_and_retry(self):
        import app_update as u
        app=App();errors=[];app.report_callback_exception=lambda *e:errors.append(e)
        updater=u.StartupUpdate(app);app.updater=updater
        app.after_cancel(updater.job);updater.job=None
        try:
            updater.show({'tag':'v9.0.0','notes':'• A short change'});app.update()
            before=updater.art_size
            updater.progress['value']=77
            with patch.object(u,'download',side_effect=OSError('offline')):
                updater.begin_download()
                self.assertEqual(float(updater.progress['value']),0)
                until=time.monotonic()+2
                while updater.downloading and time.monotonic()<until:app.update();time.sleep(.01)
            app.update()
            self.assertGreater(updater.art_size[1],before[1])
            self.assertFalse(updater.update_button.disabled)
            updater.dismiss();app.update();self.assertIsNone(updater.art_job)
            self.assertFalse(errors)
        finally:app.close()

    def test_snooze_invalid_and_expired(self):
        import app_update as u
        path=u.DATA/'update-preferences.json';path.parent.mkdir(parents=True,exist_ok=True)
        for text in ('broken','[]','{"snoozed_until":"NaN"}','{"snoozed_until":-1}'):
            path.write_text(text,encoding='utf-8');self.assertEqual(u.snoozed_until(),0)
        u.save_snooze(time.time()-1);self.assertLess(u.snoozed_until(),time.time())

    def test_update_release_validation(self):
        import app_update as u,io,hashlib
        payload=b'installer bytes'
        info={'tag_name':'v1.8.2','body':'## 한국어\n수정\n## English\nFix','assets':[{'name':'mikunoi_Stock_Calculator-Setup-1.8.2-x64.exe','state':'uploaded','size':len(payload),'digest':'sha256:'+hashlib.sha256(payload).hexdigest(),'browser_download_url':'https://github.com/mikunoi/investment-calculator/releases/download/v1.8.2/mikunoi_Stock_Calculator-Setup-1.8.2-x64.exe'}]}
        def check():
            with patch.object(u,'VERSION','1.8.0'), patch.object(u,'urlopen',return_value=io.BytesIO(json.dumps(info).encode())):return u.release()
        self.assertIsNotNone(check())
        info['draft']=True;self.assertIsNone(check());info['draft']=False
        info['assets'][0]['browser_download_url']='https://example.com/setup.exe';self.assertIsNone(check())
        self.assertGreater(u.version('v1.10.0'),u.version('1.9.9'))
        self.assertIsNone(u.version('v1.9.0-beta'))

    def test_update_download_integrity_cancel(self):
        import app_update as u,io,hashlib,queue,threading
        payload=b'complete installer'
        class Response(io.BytesIO):
            def geturl(self):return 'https://release-assets.githubusercontent.com/example'
        info={'url':'https://github.com/mikunoi/investment-calculator/releases/download/v1.8.2/setup.exe','name':'setup.exe','size':len(payload),'digest':hashlib.sha256(payload).hexdigest()}
        q=queue.Queue();cancel=threading.Event()
        with patch.object(u,'urlopen',return_value=Response(payload)):u.download(info,cancel,q)
        events=list(q.queue);path=next(v for k,v in events if k=='downloaded')
        self.assertEqual(path.read_bytes(),payload)
        info['digest']='0'*64
        with patch.object(u,'urlopen',return_value=Response(payload)),self.assertRaises(ValueError):u.download(info,cancel,queue.Queue())
        self.assertFalse(list((u.DATA/'update-cache').glob('*.part')))
        cancel.set();q=queue.Queue()
        with patch.object(u,'urlopen',return_value=Response(payload)):u.download(info,cancel,q)
        self.assertTrue(q.empty())

    def test_legend_original_and_targets(self):
        app=App();app.withdraw()
        try:
            app.persist(sample());app.show('allocation');app.update_idletasks();v=find(app,AllocationView)
            v.plans=[dict(key=('holding',0),name='국내',symbol='001234',kind='percent',value=D(20))]
            v.extra.set('-10000');app.update_idletasks()
            item=next(i for i,k in v.legend_keys.items() if k==('holding',0))
            self.assertEqual(v.legend.set(item,'evaluation'),'12,000')
            self.assertEqual(v.legend.set(item,'target'),'54,000')
            self.assertEqual(v.legend_cell_colors[item],'#159C65')
            v.plans[0]['value']=D(1);v.update_all();app.update_idletasks()
            item=next(i for i,k in v.legend_keys.items() if k==('holding',0))
            self.assertEqual(v.legend_cell_colors[item],'#E5484D')
        finally:app.close()

    def test_pending_callbacks_cleanup(self):
        app=App();app.withdraw()
        app.show('assets')
        app.language.set('US');app.change_language()
        self.assertEqual(app.current,'assets')
        app.show_initial_page();self.assertEqual(app.current,'assets')
        app.close()
        self.assertIsNone(app.screen_fit.job)
        self.assertIsNone(app.screen_fit.initial_job)
        self.assertFalse(app.screen_fit.map_jobs)

    def test_popup_topmost_drag_and_owner_close(self):
        import app_update as u
        app=App();app.update()
        updater=u.StartupUpdate(app);app.updater=updater
        app.after_cancel(updater.job);updater.job=None
        updater.show({'tag':'v9.0.0','notes':'Release notes'})
        app.update()
        self.assertTrue(updater.dialog.attributes('-topmost'))
        self.assertIsNone(app.grab_current())
        updater.activate_dialog();app.update()
        self.assertEqual(app.focus_get().winfo_toplevel(),updater.dialog)
        app.close()
        self.assertTrue(updater.cancel.is_set())
        self.assertFalse(updater.owner_bindings)

    def test_average(self):
        quantity,cost,average,added=calculate('40','2500',[('2000','40')])
        self.assertEqual((quantity,cost,average,added),(D(80),D(180000),D(2250),D(80000)))
        self.assertEqual(calculate('1.5','2',[])[0],D('1.5'))

    def test_legacy_and_files(self):
        old=validate(dict(holdings=[dict(name='old',quantity=40,krw='100000',evaluation_krw='120000')]))
        self.assertEqual(old['holdings'][0]['buy_price'],'2500')
        for ext in ('xlsx','csv','json'):
            p=Path(ISOLATED.name)/('roundtrip.'+ext);export_file(p,sample())
            restored=validate(import_file(p))
            self.assertEqual(D(restored['capital']),D(280000))
            self.assertEqual(restored['holdings'][0]['symbol'],'001234')

    def test_goals_five(self):
        view=SimpleNamespace(plans=[dict(key=('holding',0),name='A',symbol='',kind='percent',value=D(20))],data=sample(),extra=SimpleNamespace(get=lambda:''),winfo_toplevel=lambda:None)
        with patch.object(goal_history.simpledialog,'askstring',side_effect=[f'goal{i}' for i in range(6)]),patch.object(goal_history.messagebox,'showinfo'),patch.object(goal_history.messagebox,'showerror') as error:
            for _ in range(6):goal_history.save(view)
            error.assert_not_called()
        items=goal_history.read();self.assertEqual(len(items),5)
        self.assertEqual([i['name'] for i in items],['goal5','goal4','goal3','goal2','goal1'])
        for item in items:
            plans=[dict(p,key=tuple(p['key']),value=D(p['value'])) for p in item['plans']]
            scenario(item['data'],plans,item['extra'])

    def test_ui_cache_fx_chart_and_close(self):
        app=App();app.withdraw();errors=[]
        app.report_callback_exception=lambda *args:errors.append(args)
        try:
            app.persist(sample());app.show('allocation');app.update_idletasks()
            view=find(app,AllocationView)
            view.snapshot=True;view.fx.set('1500');view.apply_fx()
            self.assertEqual(app.data['fx'],'1400')
            self.assertEqual(view.data['fx'],'1500')
            view.snapshot=False;view.fx.set('1600');view.apply_fx()
            self.assertEqual(app.data['fx'],'1600')
            w,h=view.chart.winfo_width(),view.chart.winfo_height();size=max(40,min(w-28,h-22))
            view.chart_click(SimpleNamespace(x=w/2+size*.35,y=h/2))
            self.assertTrue(view.legend.selection());view.clear_chart_selection();self.assertFalse(view.legend.selection())
            app.show('average');app.update_idletasks();av=find(app,AverageCostView)
            av.choices.current(2);av.load_holding();av.currency.set('원')
            self.assertEqual(D(av.average.get().replace(',','')),D(80000))
            av.currency.set('USD');self.assertEqual(D(av.average.get().replace(',','')),D(50))
            app.show('assets');initial={k:id(v[0]) for k,v in app.pages.items()}
            start=time.perf_counter()
            for _ in range(100):
                for tab in ('average','allocation','assets'):app.show(tab)
            app.update_idletasks()
            self.assertEqual(initial,{k:id(v[0]) for k,v in app.pages.items()})
            print(f'300 cached tab switches: {(time.perf_counter()-start)*1000:.1f} ms (hidden Tk)')
            self.assertFalse(errors)
            self.assertEqual(json.loads(DATA_FILE.read_text(encoding="utf-8"))['fx'],'1600')
        finally:app.close()

    def test_export_image(self):
        from allocation_export import render
        data=sample();capital,cash,rows,results=scenario(data,[],'-10000')
        image=render(data,D(-10000),capital,rows,results,'evaluation',PALETTES['default'],'default')
        try:
            self.assertEqual(image.width,1600)
            image.save(Path(ISOLATED.name)/'preview.png')
        finally:image.close()

if __name__=='__main__':unittest.main(verbosity=2)

