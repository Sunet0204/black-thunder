#!/usr/bin/env python3
"""Generate static product pages matching product.html's design and a sitemap."""
import html
import json
import re
from pathlib import Path
from urllib.parse import quote
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace

ROOT = Path(__file__).resolve().parent
BASE = 'https://sunet0204.github.io/black-thunder/'
FOLDERS = {'index': ('json', ''), 'thun2': ('json2', '-2'), 'thun3': ('json3', '-3'), 'thun4': ('json4', '-4')}
CSS = '''body{max-width:900px;margin:auto;padding:20px}
#backLink{display:inline-block;margin-bottom:20px}
#productImages{display:flex;flex-wrap:wrap;gap:20px;margin:20px 0}
#productImages img{display:block;max-width:400px;width:100%;height:auto}
.info{margin:10px 0}.label{font-weight:bold}
#descriptionArea{margin-top:30px}#description{white-space:pre-wrap;line-height:1.8}
#officialArea,#referenceArea{margin-top:30px}
.linkList{margin:0;padding-left:25px}.linkList li{margin-bottom:8px}
#error{color:red}'''

def esc(v):
    return html.escape(str(v if v is not None else ''), quote=True)

def as_list(v):
    return [] if v is None or v == '' else (v if isinstance(v, list) else [v])

def info(area, label, value, field):
    if not value:
        return ''
    return f'<div class="info" id="{area}"><span class="label">{esc(label)}：</span><span id="{field}">{esc(value)}</span></div>'

def link_section(area, list_id, heading, links, text):
    urls = [x for x in as_list(links) if isinstance(x, str) and x.startswith(('https://', 'http://'))]
    if not urls:
        return ''
    rows = ''.join(f'<li><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(text if len(urls)==1 else f"{text} {i}")}</a></li>' for i, url in enumerate(urls, 1))
    return f'<section id="{area}"><h2>{heading}</h2><ul id="{list_id}" class="linkList">{rows}</ul></section>'

def generate_doc(kind, year, item, filename):
    name = str(item.get('name') or '商品詳細')
    pid = str(item['id'])
    images = [x for x in as_list(item.get('images') if item.get('images') is not None else item.get('image')) if isinstance(x, str) and x.strip()]
    image_html = ''.join(f'<img src="../{esc(img.lstrip("/"))}" alt="{esc(name if len(images)==1 else f"{name} {i}")}" loading="{"eager" if i==1 else "lazy"}">' for i, img in enumerate(images, 1))
    release = item.get('releaseDate') or '不明'
    bits = [f'<h1 id="productName">{esc(name)}</h1>']
    if image_html:
        bits.append(f'<div id="productImages">{image_html}</div>')
    bits.append(info('releaseDateArea', '発売日', release, 'releaseDate'))
    bits.append(info('nicknameArea', '二つ名', item.get('nickname'), 'nickname'))
    bits.append(info('sizeArea', 'コラボ先' if kind=='thun3' else 'サイズ', item.get('collab') if kind=='thun3' else item.get('size'), 'size'))
    if kind == 'index':
        for area, label, key, field in [('flavorArea','味','flavors','flavor'), ('seriesArea','シリーズ区分','series','series')]:
            value = '・'.join(str(x) for x in as_list(item.get(key)))
            bits.append(info(area,label,value,field))
    desc = item.get('description') or ''
    if desc:
        bits.append(f'<section id="descriptionArea"><h2>商品紹介</h2><p id="description">{esc(desc)}</p></section>')
    bits.append(link_section('officialArea','officialLinks','公式記事',item.get('officialLinks'),'公式記事を見る'))
    bits.append(link_section('referenceArea','referenceLinks','参考リンク',item.get('referenceLinks'),'参考ページを見る'))
    canonical = BASE + 'products/' + quote(filename)
    summary = f'{name}の発売日や商品情報を掲載した非公式データベースです。'
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-99P2MSR5QT"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-99P2MSR5QT');</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(name)} | ブラックサンダー</title>
<meta name="description" content="{esc(summary)}">
<link rel="canonical" href="{esc(canonical)}">
<style>{CSS}</style>
</head>
<body>
<a id="backLink" href="../index.html">← 商品一覧へ戻る</a>
<main id="productArea">
{''.join(bits)}
</main>
<p id="error"></p>
</body>
</html>
'''

def main():
    out = ROOT / 'products'
    out.mkdir(exist_ok=True)
    urls = [BASE]
    count = 0
    seen = set()
    for kind, (folder, suffix) in FOLDERS.items():
        directory = ROOT / folder
        if not directory.is_dir():
            print(f'WARNING: missing directory {directory}')
            continue
        for path in sorted(directory.glob('*.json')):
            stem = path.stem
            if suffix and not stem.endswith(suffix):
                continue
            year = stem[:-len(suffix)] if suffix else stem
            if not re.fullmatch(r'\d{4}', year):
                continue
            try:
                items = json.loads(path.read_text(encoding='utf-8-sig'))
                if not isinstance(items, list):
                    raise ValueError('JSON root must be an array')
            except (ValueError, OSError) as ex:
                print(f'SKIP {path}: {ex}')
                continue
            for item in items:
                if not isinstance(item, dict) or not item.get('id'):
                    continue
                pid = str(item['id'])
                filename = f'{kind}-{year}-{quote(pid, safe="")}.html'
                if filename in seen:
                    print(f'WARNING duplicate ID: {filename}')
                    continue
                seen.add(filename)
                (out / filename).write_text(generate_doc(kind,year,item,filename),encoding='utf-8')
                urls.append(BASE + 'products/' + quote(filename))
                count += 1
    register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    root = Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
    for url in urls:
        entry = SubElement(root, '{http://www.sitemaps.org/schemas/sitemap/0.9}url')
        SubElement(entry, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text = url
    sitemap = ROOT / 'sitemap.xml'
    if count:
        ElementTree(root).write(sitemap, encoding='utf-8', xml_declaration=True)
    else:
        print('WARNING: no product pages generated; sitemap.xml was not overwritten')
    print(f'Generated {count} product pages' + (f' and sitemap.xml ({len(urls)} URLs)' if count else ''))

if __name__ == '__main__':
    main()
