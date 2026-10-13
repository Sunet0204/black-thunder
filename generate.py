#!/usr/bin/env python3
"""Generate crawlable product pages and sitemap from Black Thunder JSON files."""
import json
import html
from pathlib import Path
from urllib.parse import quote
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace

ROOT = Path(__file__).resolve().parent
BASE = 'https://sunet0204.github.io/black-thunder/'
FOLDERS = {'index': ('json', ''), 'thun2': ('json2', '-2'), 'thun3': ('json3', '-3'), 'thun4': ('json4', '-4')}

def esc(value):
    return html.escape(str(value or ''), quote=True)

def as_list(value):
    if value is None or value == '': return []
    return value if isinstance(value, list) else [value]

def main():
    out = ROOT / 'products'
    out.mkdir(exist_ok=True)
    urls = [BASE]
    count = 0
    for kind, (folder, suffix) in FOLDERS.items():
        for path in sorted((ROOT / folder).glob('*.json')):
            year = path.stem.removesuffix(suffix)
            try:
                items = json.loads(path.read_text(encoding='utf-8-sig'))
                if not isinstance(items, list): raise ValueError('JSON root must be an array')
            except (ValueError, OSError) as ex:
                print(f'SKIP {path}: {ex}')
                continue
            for item in items:
                if not isinstance(item, dict) or not item.get('id'): continue
                pid = str(item['id'])
                filename = f'{kind}-{year}-{quote(pid, safe="")}.html'
                name = str(item.get('name') or '商品詳細')
                images = as_list(item.get('images', item.get('image')))
                images = [i for i in images if isinstance(i, str) and i.strip()]
                lines = []
                for label, key in [('発売日','releaseDate'), ('二つ名','nickname'), ('コラボ先' if kind == 'thun3' else 'サイズ', 'collab' if kind == 'thun3' else 'size'), ('味','flavors'), ('シリーズ区分','series')]:
                    val = item.get(key)
                    if val:
                        display = '・'.join(map(str, as_list(val)))
                        lines.append(f'<p><strong>{esc(label)}：</strong>{esc(display)}</p>')
                desc = item.get('description') or ''
                if desc: lines.append(f'<section><h2>商品紹介</h2><p class="description">{esc(desc)}</p></section>')
                for label, key in [('公式記事','officialLinks'), ('参考リンク','referenceLinks')]:
                    links = [u for u in as_list(item.get(key)) if isinstance(u,str) and u.startswith(('http://','https://'))]
                    if links:
                        anchors = ''.join(f'<li><a href="{esc(u)}" rel="noopener noreferrer">{esc(label)} {n}</a></li>' for n,u in enumerate(links,1))
                        lines.append(f'<section><h2>{esc(label)}</h2><ul>{anchors}</ul></section>')
                image_html = ''.join(f'<img src="../{esc(img.lstrip("/"))}" alt="{esc(name)}" loading="lazy">' for img in images)
                original = f'../product.html?type={quote(kind)}&amp;year={quote(year)}&amp;id={quote(pid)}'
                doc = f'''<!doctype html>
<html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(name)} | ブラックサンダー</title>
<meta name="description" content="{esc(name)}の発売日や商品情報を掲載した非公式データベースです。">
<link rel="canonical" href="{esc(BASE + 'products/' + filename)}">
<style>body{{max-width:900px;margin:auto;padding:20px;font-family:sans-serif}}.images{{display:flex;flex-wrap:wrap;gap:20px;margin:20px 0}}.images img{{max-width:400px;width:100%;height:auto}}.description{{white-space:pre-wrap;line-height:1.8}}section{{margin-top:30px}}</style>
</head><body><a href="../index.html">← 商品一覧へ戻る</a>
<main><h1>{esc(name)}</h1><div class="images">{image_html}</div>{''.join(lines)}</main>
<p><a href="{original}">従来の商品ページを開く</a></p></body></html>'''
                (out / filename).write_text(doc, encoding='utf-8')
                urls.append(BASE + 'products/' + filename)
                count += 1
    register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    root = Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
    for url in urls:
        entry = SubElement(root, '{http://www.sitemaps.org/schemas/sitemap/0.9}url')
        SubElement(entry, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text = url
    ElementTree(root).write(ROOT / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
    print(f'Generated {count} product pages and sitemap.xml ({len(urls)} URLs)')

if __name__ == '__main__': main()
