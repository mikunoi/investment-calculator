"""Explicit UI translation; never translates user-entered names or values."""
import json
import os
import sys
from pathlib import Path

LANGUAGE = 'ko'
try:
    config = json.loads((Path(os.environ['LOCALAPPDATA']) / 'IndependentInvestmentCalculator/settings.json').read_text(encoding='utf-8'))
    LANGUAGE = config.get('language', 'ko') if config.get('language') in ('ko', 'en') else 'ko'
except (OSError, ValueError, AttributeError, KeyError):
    pass
_path = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'translations.json'
CATALOG = json.loads(_path.read_text(encoding='utf-8'))


def select(language):
    global LANGUAGE
    LANGUAGE = language if language in ('ko', 'en') else 'ko'


def tr(text):
    value=CATALOG.get(text,text) if LANGUAGE=='en' else text
    return value.replace('투자계산기','mikunoi_Stock_Calculator')
