#!/usr/bin/env python3
"""Generate SEO-friendly static product pages, index links and sitemap safely.
Run from repository root: python3 generate_seo.py
"""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace

ROOT = Path(__file__).resolve().parent
BASE = 'https://sunet0204.github.io/black-thunder/'
FOLDERS = {'index': ('json', ''), 'thun2': ('json2', '-2'), 'thun3': ('json3', '-3'), 'thun4': ('json4', '-4')}
CSS = '''body{max-width:900px;margin:auto;padding:20px;font-family:system-ui,sans-serif;line-height:1.6}
#backLink{display:inline-block;margin-bottom:20px}
#productImages{display:flex;flex-wrap:wrap;gap:20px;margin:20px 0}
#productImages img{display:block;max-width:min(400px,100%);width:auto;height:auto}
.info{margin:10px 0}.label{font-weight:bold}
#descriptionArea{margin-top:30px}#description{white-space:pre-wrap;line-height:1.8}
#officialArea,#referenceArea{margin-top:30px}
.linkList{margin:0;padding-left:25px}.linkList li{margin-bottom:8px}'''
MANAGED_FILE = re.compile(r'^(?:index|thun2|thun3|thun4)-\d{4}-.+\.html$')
STATIC_START = '<!-- STATIC_PRODUCT_LINKS_START -->'
STATIC_END = '<!-- STATIC_PRODUCT_LINKS_END -->'

def esc(value):
    return html.escape(str(value if value is not None else ''), quote=True)

def as_list(value):
    return [] if value is None or value == '' else (value if isinstance(value, list) else [value])

def clean_text(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()

def info(area, label, value, field):
    if not value:
        return ''
    return f'<div class="info" id="{area}"><span class="label">{esc(label)}：</span><span id="{field}">{esc(value)}</span></div>'

def link_section(area, list_id, heading, links, text):
    urls = [x for x in as_list(links) if isinstance(x, str) and urlsplit(x).scheme in ('https', 'http') and urlsplit(x).netloc]
    if not urls:
        return ''
    rows = ''.join(f'<li><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(text if len(urls)==1 else f"{text} {i}")}</a></li>' for i, url in enumerate(urls, 1))
    return f'<section id="{area}"><h2>{esc(heading)}</h2><ul id="{list_id}" class="linkList">{rows}</ul></section>'

def image_url(image):
    image = image.strip()
    if urlsplit(image).scheme in ('https', 'http'):
        return image
    # The source JSON uses paths relative to the site root, e.g. imag/...
    return urljoin(BASE, quote(image.lstrip('/'), safe='/'))

def generate_doc(kind, year, item, filename):
    name = clean_text(item.get('name')) or '商品詳細'
    images = [x for x in as_list(item.get('images') if item.get('images') is not None else item.get('image')) if isinstance(x, str) and x.strip()]
    image_html = ''.join(f'<img src="{esc(image_url(img))}" alt="{esc(name if len(images)==1 else f"{name} {i}")}" loading="{"eager" if i==1 else "lazy"}" decoding="async">' for i, img in enumerate(images, 1))
    release = item.get('releaseDate') or '不明'
    bits = [f'<h1 id="productName">{esc(name)}</h1>']
    if image_html:
        bits.append(f'<div id="productImages">{image_html}</div>')
    bits.append(info('releaseDateArea', '発売日', release, 'releaseDate'))
    bits.append(info('nicknameArea', '二つ名', item.get('nickname'), 'nickname'))
    bits.append(info('sizeArea', 'コラボ先' if kind=='thun3' else 'サイズ', item.get('collab') if kind=='thun3' else item.get('size'), 'size'))
    if kind == 'index':
        for area, label, key, field in [('flavorArea','味','flavors','flavor'), ('seriesArea','シリーズ区分','series','series')]:
            bits.append(info(area, label, '・'.join(str(x) for x in as_list(item.get(key)) if x is not None), field))
    desc = str(item.get('description') or '')
    if desc.strip():
        bits.append(f'<section id="descriptionArea"><h2>商品紹介</h2><p id="description">{esc(desc)}</p></section>')
    bits.append(link_section('officialArea','officialLinks','公式記事',item.get('officialLinks'),'公式記事を見る'))
    bits.append(link_section('referenceArea','referenceLinks','参考リンク',item.get('referenceLinks'),'参考ページを見る'))
    canonical = BASE + 'products/' + quote(filename, safe='')
    summary = clean_text(desc)[:150] or f'{name}の発売情報や画像を掲載した非公式データベースです。'
    structured = {'@context':'https://schema.org','@type':'Product','name':name,'description':clean_text(desc) or summary,'url':canonical,'sku':str(item['id'])}
    if images:
        structured['image'] = [image_url(img) for img in images]
    # Escape '<' so user-controlled text cannot terminate a script tag.
    json_ld = json.dumps(structured, ensure_ascii=False).replace('<', '\\u003c')
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(name)}（{esc(year)}年） | ブラックサンダー商品データベース</title>
<meta name="description" content="{esc(summary)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{esc(canonical)}">
<script type="application/ld+json">{json_ld}</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-99P2MSR5QT"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-99P2MSR5QT');</script>
<style>{CSS}</style>
</head>
<body>
<a id="backLink" href="../index.html">← 商品一覧へ戻る</a>
<main id="productArea">{''.join(bits)}</main>
<script>
// Return through browser history when arriving from this site's index.
// This preserves the list's existing sessionStorage-based filters and scroll restoration.
document.getElementById('backLink').addEventListener('click', function(event) {{
  try {{
    const previous = new URL(document.referrer);
    const index = new URL('../index.html', location.href);
    if (previous.origin === location.origin &&
        (previous.pathname === index.pathname || previous.pathname === index.pathname.replace(/index\\.html$/, '')) &&
        history.length > 1) {{
      event.preventDefault();
      history.back();
    }}
  }} catch (_) {{ /* Direct visits use the normal index link. */ }}
}});
</script>
</body>
</html>
'''

def update_index(index_path, products):
    original = index_path.read_text(encoding='utf-8')
    if original.count(STATIC_START) != 1 or original.count(STATIC_END) != 1:
        raise ValueError('index.html must contain exactly one pair of static link markers')
    start = original.index(STATIC_START) + len(STATIC_START)
    end = original.index(STATIC_END)
    if start > end:
        raise ValueError('Invalid marker order in index.html')
    lines = ['<nav id="staticProductLinks" aria-label="全商品へのリンク">', '<h2>全商品のリンク</h2>', '<ul>']
    lines.extend(f'<li><a href="products/{esc(quote(filename, safe=""))}">{esc(name)}</a></li>' for name, filename in products)
    lines.extend(['</ul>', '</nav>'])
    return original[:start] + '\n' + '\n'.join(lines) + '\n' + original[end:]

def main():
    pending, links, errors = {}, [], []
    urls = [BASE]
    for kind, (folder, suffix) in FOLDERS.items():
        directory = ROOT / folder
        if not directory.is_dir():
            errors.append(f'Missing directory: {directory}')
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
                for number, item in enumerate(items, 1):
                    if not isinstance(item, dict) or not item.get('id'):
                        raise ValueError(f'Item {number}: missing object/id')
                    pid = str(item['id'])
                    if not re.fullmatch(r'[A-Za-z0-9_-]+', pid):
                        raise ValueError(f'Item {number}: unsupported ID {pid!r}')
                    filename = f'{kind}-{year}-{pid}.html'
                    if filename in pending:
                        raise ValueError(f'Duplicate ID: {filename}')
                    pending[filename] = generate_doc(kind, year, item, filename)
                    links.append((str(item.get('name') or '商品詳細'), filename))
                    urls.append(BASE + 'products/' + quote(filename, safe=''))
            except (ValueError, OSError, TypeError) as exc:
                errors.append(f'{path}: {exc}')
    if errors or not pending:
        for error in errors:
            print('ERROR:', error, file=sys.stderr)
        if not pending:
            print('ERROR: No product pages found.', file=sys.stderr)
        raise SystemExit('Generation cancelled; existing files were not changed.')
    try:
        updated_index = update_index(ROOT / 'index.html', links)
    except (OSError, ValueError) as exc:
        raise SystemExit(f'Generation cancelled; existing files were not changed: {exc}')
    register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    root = Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
    for url in urls:
        entry = SubElement(root, '{http://www.sitemaps.org/schemas/sitemap/0.9}url')
        SubElement(entry, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text = url
    out = ROOT / 'products'
    out.mkdir(exist_ok=True)
    for filename, document in pending.items():
        (out / filename).write_text(document, encoding='utf-8')
    removed = 0
    for path in out.glob('*.html'):
        if MANAGED_FILE.fullmatch(path.name) and path.name not in pending:
            path.unlink()
            removed += 1
    ElementTree(root).write(ROOT / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
    (ROOT / 'index.html').write_text(updated_index, encoding='utf-8')
    print(f'Generated {len(pending)} product pages, removed {removed} obsolete pages, sitemap.xml ({len(urls)} URLs)')

if __name__ == '__main__':
    main()
