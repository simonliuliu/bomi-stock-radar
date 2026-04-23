#!/usr/bin/env python3
import json, re, requests, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parents[1]
DATA_PATH = BASE / 'data' / 'stocks.json'
HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json, text/plain, */*',
    'Origin': 'https://www.nasdaq.com',
    'Referer': 'https://www.nasdaq.com/'
}
SESSION = requests.Session()
SESSION.headers.update({'User-Agent': 'Mozilla/5.0'})


def pct(a, b):
    if b in (0, None):
        return None
    return round((a / b - 1) * 100, 2)


def parse_money(s):
    return float(re.sub(r'[$,]', '', str(s)))


def nearest(rows, target_date):
    for r in reversed(rows):
        if r['date'] <= target_date:
            return r['close']
    return rows[0]['close']


def fetch_us_metrics(symbol):
    fr = (dt.date.today() - dt.timedelta(days=420)).isoformat()
    to = dt.date.today().isoformat()
    url = f'https://api.nasdaq.com/api/quote/{symbol}/historical?assetclass=stocks&fromdate={fr}&limit=500&todate={to}'
    data = SESSION.get(url, headers=HEADERS, timeout=25).json()['data']['tradesTable']['rows']
    rows = []
    for r in data:
        rows.append({
            'date': dt.datetime.strptime(r['date'], '%m/%d/%Y').date().isoformat(),
            'close': parse_money(r['close']),
            'high': parse_money(r['high']),
            'low': parse_money(r['low'])
        })
    rows.sort(key=lambda x: x['date'])
    last = rows[-1]
    d = dt.date.fromisoformat(last['date'])
    m1 = nearest(rows, (d - dt.timedelta(days=30)).isoformat())
    y1 = nearest(rows, (d - dt.timedelta(days=365)).isoformat())
    ytd = nearest(rows, f'{d.year}-01-02')
    return {
        'date': last['date'],
        'price': round(last['close'], 2),
        'm1': pct(last['close'], m1),
        'ytd': pct(last['close'], ytd),
        'y1': pct(last['close'], y1),
        'high52': round(max(r['high'] for r in rows[-252:]), 2),
        'low52': round(min(r['low'] for r in rows[-252:]), 2),
        'drawdown': pct(last['close'], max(r['high'] for r in rows))
    }


def secid(ticker):
    return ('1.' if ticker.startswith(('6', '5')) else '0.') + ticker


def fetch_cn_metrics(ticker):
    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    params = {
        'secid': secid(ticker),
        'fields1': 'f1,f2,f3,f4,f5,f6',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
        'klt': '101',
        'fqt': '1',
        'beg': '20200101',
        'end': '20500101'
    }
    data = SESSION.get(url, params=params, timeout=25).json()['data']['klines']
    rows = []
    for line in data:
        p = line.split(',')
        rows.append({'date': p[0], 'close': float(p[2]), 'high': float(p[3]), 'low': float(p[4])})
    rows.sort(key=lambda x: x['date'])
    last = rows[-1]
    d = dt.date.fromisoformat(last['date'])
    m1 = nearest(rows, (d - dt.timedelta(days=30)).isoformat())
    y1 = nearest(rows, (d - dt.timedelta(days=365)).isoformat())
    ytd = nearest(rows, f'{d.year}-01-02')
    return {
        'date': last['date'],
        'price': round(last['close'], 2),
        'm1': pct(last['close'], m1),
        'ytd': pct(last['close'], ytd),
        'y1': pct(last['close'], y1),
        'high52': round(max(r['high'] for r in rows[-252:]), 2),
        'low52': round(min(r['low'] for r in rows[-252:]), 2),
        'drawdown': pct(last['close'], max(r['high'] for r in rows))
    }


def main():
    data = json.loads(DATA_PATH.read_text())
    refreshed = []
    for stock in data['stocks']:
        try:
            if stock['region'] == 'US':
                metrics = fetch_us_metrics(stock['ticker'])
            else:
                metrics = fetch_cn_metrics(stock['ticker'])
            stock.update(metrics)
            refreshed.append(stock['ticker'])
        except Exception as e:
            stock['events'] = [f'自动刷新失败，保留旧数据：{e}'] + stock.get('events', [])[:2]
    now = dt.datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M %Z')
    data['meta']['updated_at'] = now
    data['meta']['notes'] = '价格、涨幅、区间位置已由自动脚本刷新；事件摘要仍为人工整理版。'
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(json.dumps({'ok': True, 'updated_at': now, 'refreshed': refreshed, 'count': len(refreshed)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
