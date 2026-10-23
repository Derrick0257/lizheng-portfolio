"""Build the curated print portfolio from the current website content.
Requires Python, Pillow, reportlab, PyMuPDF, and Playwright with Chromium.
"""
from pathlib import Path
from html import escape
import base64, io, json, re
import fitz
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from PIL import Image
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics import renderSVG
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'portfolio'
BUILD = Path('/tmp/lizheng-portfolio-pdf')
BUILD.mkdir(exist_ok=True)
SITE = 'https://derrick0257.github.io/lizheng-portfolio/'
EMAIL = 'lizheng25lz@163.com'
source = (ROOT / 'index.html').read_text()
decoder = json.JSONDecoder()
start = source.index('const caseData = ') + len('const caseData = ')
cases, _ = decoder.raw_decode(source[start:])
for match in re.finditer(r'Object\.assign\(caseData,\s*', source):
    extra, _ = decoder.raw_decode(source[match.end():]); cases.update(extra)
start = source.index('const evidenceAssets = ') + len('const evidenceAssets = ')
assets, _ = decoder.raw_decode(source[start:])
optimized = {}

def image(key, cls='', alt=''):
    if key not in optimized:
        data = assets[key]
        if not key.startswith('logo-'):
            im = Image.open(io.BytesIO(base64.b64decode(data.split(',', 1)[1]))).convert('RGB')
            im.thumbnail((1600, 1600))
            stream = io.BytesIO(); im.save(stream, 'JPEG', quality=88, optimize=True)
            data = 'data:image/jpeg;base64,' + base64.b64encode(stream.getvalue()).decode()
        optimized[key] = data
    return f'<img class="{cls}" src="{optimized[key]}" alt="{escape(alt)}">'

def qr(url):
    d = Drawing(120, 120); d.add(Rect(0, 0, 120, 120, fillColor=__import__('reportlab.lib.colors', fromlist=['white']).white, strokeColor=None))
    widget = QrCodeWidget(url, barLevel='M', barBorder=4, barWidth=110, barHeight=110, x=5, y=5)
    d.add(widget)
    data = base64.b64encode(renderSVG.drawToString(d).encode()).decode()
    return f'<img class="qr" src="data:image/svg+xml;base64,{data}" alt="完整作品观看二维码">'

def header(section):
    return f'<header class="page-header"><span class="identity"><b class="mark">LZ</b> LI ZHENG <span class="muted">/ 作品集</span></span><span class="eyebrow muted">{escape(section)}</span></header>'

def footer(n):
    return f'<footer><a href="{SITE}">derrick0257.github.io/lizheng-portfolio/ ↗</a><span>LI ZHENG · {n:02d} / 12</span></footer>'

def page(n, title, content, cls=''):
    return f'<section class="page {cls}" id="p{n}">{header(title)}{content}{footer(n)}</section>'

def title(eyebrow, heading, deck=''):
    return f'<div class="heading"><p class="eyebrow muted">{escape(eyebrow)}</p><h1>{escape(heading)}</h1>' + (f'<p class="deck">{escape(deck)}</p>' if deck else '') + '</div>'

def meta(data):
    items = ''.join(f'<div><span>{escape(k.split(" / ")[0])}</span><strong>{escape(v)}</strong></div>' for k, v in data['meta'])
    return f'<div class="meta">{items}</div>'

def metrics(data):
    return '<div class="metrics">' + ''.join(f'<div><strong>{escape(v)}</strong><span>{escape(label)}</span><small>{escape(scope)}</small></div>' for v, label, scope in data.get('metrics', [])) + '</div>'

def stories(data, cls=''):
    result = []
    for i, (heading, text) in enumerate(data['sections']):
        if isinstance(text, list): continue
        result.append(f'<article class="story"><h3><span>{i+1:02d}</span> {escape(heading)}</h3><p>{escape(text)}</p></article>')
    return f'<div class="stories {cls}">' + ''.join(result) + '</div>'

def figure(key, caption, cls=''):
    return f'<figure class="{cls}">{image(key, alt=caption)}<figcaption>{escape(caption)}</figcaption></figure>'

pages = []
cover = '''<div class="cover-top"><div><p class="eyebrow muted">Content · Culture · Connection</p><p class="name">李政 <span>Li Zheng</span></p><h1>让好想法，<br>成为被看见的故事。</h1><p class="cover-copy">在品牌内容、新闻影像与文化现场之间，<br>把需求梳理成叙事，把创意推进到交付。</p></div><aside class="cover-panel"><span class="star">✳</span><span class="eyebrow">Selected work / 2026</span><div><b>内容策划</b><b>视频制作</b><b>活动执行</b></div><small>从选题与创意，<br>到制作与现场。</small></aside></div>'''
cover += '<div class="cover-photos">' + figure('internship-onsite-1', '《快乐哆唻咪》新疆外拍现场') + figure('gold-onsite', '《小芒种花夜》舞台与制作团队') + '</div>'
cover += f'<div class="contact-strip"><div><span class="eyebrow muted">Contact</span><a href="mailto:{EMAIL}">{EMAIL}</a></div><div><span class="eyebrow muted">Online portfolio</span><a href="{SITE}">访问个人作品集 ↗</a></div></div>'
pages.append(page(1, 'Selected work · 2026', cover, 'cover'))

brands = [('金典','logo-satine'),('美团','logo-meituan'),('三星','logo-samsung'),('德芙','logo-dove'),('奥利奥','logo-oreo'),('纽瑞滋','logo-nouriz'),('唯品会','logo-vipshop'),('你拍一','logo-yipai'),('Soul','logo-soul'),('乐堡啤酒','logo-tuborg'),('豆本豆','logo-doubendou'),('雪天盐','logo-snowsky'),('李锦记','logo-leekumkee'),('sevennights','logo-sevennights')]
contents = [
    (3,'03—04','新闻影像','《为确定性买单》 / 《超市消费之困》'),
    (5,'05—07','综艺品牌内容','你拍一 / 纽瑞滋 / 金典'),
    (8,'08','节目现场制作','《说唱听我的》置景与道具执行'),
    (9,'09—10','湖南卫视制片实习','量化项目经历与现场记录'),
    (11,'11','芒果青年说','《芒芒剧综厅》团队创意提案'),
    (12,'12','学联与文化交流','国际文化节 / 苏格兰春晚 / 游园会 / 茶会'),
]
overview = title('About & contents', '作品与项目实践。', '内容策划 · 英文采写 · 视频制作 · 现场执行')
overview += '<div class="overview-intro"><p>参与综艺商业内容执行、新闻短片制作与文化活动策划，推进选题研究、跨团队沟通、拍摄执行及内容交付。</p><p class="muted">制作工具：Premiere Pro / 剪映 / ChatGPT</p></div>'
overview += '<nav class="contents">' + ''.join(f'<a href="#p{p}"><span class="contents-no">{num}</span><div><strong>{name}</strong><small>{detail}</small></div><span>↗</span></a>' for p,num,name,detail in contents) + '</nav>'
overview += '<div class="section-label"><h2>服务过的品牌</h2><span class="eyebrow muted">Brand collaborations</span></div><div class="brand-grid">' + ''.join(f'<div>{image(key, alt=name)}<span>{name}</span></div>' for name,key in brands) + '</div>'
overview += '<div class="experience-note"><b>商业内容执行 · 2019.10—2021.11</b><p>参与《妻子的浪漫旅行5》《小芒种花夜》《我们的滚烫人生》等节目，衔接品牌需求、制作沟通与内容交付。</p></div>'
pages.append(page(2,'About & contents',overview,'overview'))

for n,key,heading,question in [
    (3,'film','为确定性买单。','学生是否在为租房的便利与确定性支付溢价？'),
    (4,'supermarket','超市消费之困。','学生如何应对不断上涨的超市价格？'),
]:
    data=cases[key]
    body=title('Journalism / 0'+str(n-2),heading,data['deck'])+meta(data)
    body+=f'<div class="question-panel"><span class="eyebrow">The question</span><p>{escape(question)}</p><small>'+('格拉斯哥国际学生的住房选择' if key=='film' else '生活成本与学生的日常消费')+'</small></div>'
    body+=stories(data)
    body+=f'<a class="watch" href="{escape(data["watchUrl"],quote=True)}"><div><span class="eyebrow muted">Full film / 完整作品</span><strong>观看完整新闻片 ↗</strong><span>点击此处或扫描二维码 · OneDrive</span></div>{qr(data["watchUrl"])}</a>'
    pages.append(page(n,'News & visual storytelling',body,'news'))

for n,key,heading,visual,caption in [
    (5,'yipai','你拍一 × 妻子的浪漫旅行5','yp-22','内容植入｜由“辅导孩子”的生活话题切入，在嘉宾交流中呈现产品体验。'),
    (6,'nuriz','纽瑞滋 × 妻子的浪漫旅行5','nr-25','内容植入｜以嘉宾交流育儿经验的情境，承接品牌与产品出现。'),
    (7,'gold','金典 × 小芒种花夜','gold-16','现场执行｜衔接嘉宾口播、观众互动和品牌产品露出。'),
    (8,'rap','说唱听我的 · 置景与道具','rap-onsite','节目现场｜舞台与制作团队合影。'),
]:
    data=cases[key]
    body=title('Brand & production / 0'+str(n-4),heading,data['deck'])+meta(data)+metrics(data)+stories(data)
    body+=figure(visual,caption,'case-visual')
    pages.append(page(n,'Brand content & production',body,'brand-case'))

internship=cases['internship']
body=title('TV production / Hunan TV','湖南卫视制片实习。',internship['deck'])+meta(internship)+metrics(internship)
body+=stories(internship,'internship-stories')
projects=internship['sections'][-1][1]
body+='<div class="projects-box"><h3>参与项目</h3><div class="project-tags">'+''.join(f'<span>{escape(p)}</span>' for p in projects)+'</div></div>'
body+='<a class="next-gallery" href="#p10"><span>从外拍统筹，到彩排与正式直播。</span><b>查看现场记录 →</b></a>'
pages.append(page(9,'Hunan TV · Production internship',body,'internship'))
body=title('On set / 2018—2019','现场记录。','《快乐哆唻咪》 / 中国航天日晚会 / 2018芒果小镇')
body+='<div class="onsite-grid">'+''.join(figure(asset,caption.rstrip('。')) for asset,caption in internship['gallery'])+'</div>'
pages.append(page(10,'Hunan TV · On set',body,'onsite'))

pitch=cases['pitch']
body=title('Mango youth / Team proposal','芒芒剧综厅。',pitch['deck'])+meta(pitch)+metrics(pitch)+stories(pitch)
body+=figure('pitch-8','功能框架｜明星带看、兴趣圈层、自由组队三类房间，结合互动玩法与等级机制。','case-visual')
pages.append(page(11,'Creative concept & proposal',body,'pitch'))

culture=cases['culture']
body=title('Glasgow CSSA / Culture & community','把文化，变成可以参与的现场。',culture['deck'])+meta(culture)
body+='<div class="culture-story"><h3>文化展示与现场执行</h3><p>'+escape(culture['sections'][1][1])+'</p><p>'+escape(culture['sections'][2][1])+'</p></div>'
body+='<div class="culture-scale"><span><b>100+</b> 相关文化活动单场参与人数</span><span><b>300+</b> 苏格兰春晚参与人数</span></div>'
body+='<div class="culture-grid">'+''.join(figure(asset,caption) for asset,caption in [
    ('culture-festival-1','国际文化节｜潍坊风筝展位介绍与交流。'),
    ('culture-gala','苏格兰春晚｜舞台与活动参与团队合影。'),
    ('culture-newyear','新春游园会｜2026格拉斯哥新春游园会现场。'),
    ('culture-tea','国际茶会｜5·21国际茶会英国格拉斯哥分会场。')])+'</div>'
body+=f'<div class="closing"><div><span class="eyebrow">Let’s connect</span><strong>下一个好故事，从一次交流开始。</strong></div><a href="mailto:{EMAIL}">{EMAIL} ↗</a></div>'
pages.append(page(12,'Culture & community',body,'culture'))

CSS=r'''
@page{size:A4;margin:0}

*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:"Noto Sans CJK SC",sans-serif;color:#1d1d1f;background:#e7e7ea;font-size:12px;line-height:1.7;-webkit-print-color-adjust:exact;print-color-adjust:exact}

a{color:inherit;text-decoration:none}
h1,h2,h3,p,figure{margin:0}
img{display:block;max-width:100%}
.page{width:210mm;height:297mm;padding:14mm 16mm 12mm;background:#f5f5f7;break-after:page;position:relative;display:flex;flex-direction:column;gap:12px;overflow:hidden}
.page:last-child{break-after:auto}
.page-header{display:flex;justify-content:space-between;align-items:center;min-height:26px;margin-bottom:7px}
.identity{display:flex;align-items:center;gap:8px;font-size:10px;font-weight:700;letter-spacing:.05em}
.mark{display:grid;place-items:center;background:#1d1d1f;color:#c3f53c;width:26px;height:26px;border-radius:50%;font-size:10px;letter-spacing:-.5px}
.muted{color:#76767c}
.eyebrow{font-size:8.8px;letter-spacing:.12em;text-transform:uppercase;font-weight:600}
.heading h1{font-size:30px;font-weight:700;letter-spacing:-1.2px;line-height:1.3;margin-top:9px}
.deck{font-size:12px;color:#6a6a72;margin-top:11px;line-height:1.8}
.meta{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));background:white;border-radius:13px;padding:12px 15px;gap:13px}
.meta>div{display:flex;flex-direction:column;gap:3px}
.meta span{font-size:9px;color:#76767c}
.meta strong{font-size:10.7px;font-weight:600;line-height:1.7}
.metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
.metrics>div{background:#eaf0df;border-radius:13px;padding:12px 14px;display:flex;flex-direction:column}
.metrics strong{font-size:24px;line-height:1.1;letter-spacing:-.7px;font-weight:600}
.metrics span{font-size:10.3px;margin-top:8px;font-weight:600}
.metrics small{font-size:8.7px;color:#6b7161;margin-top:4px;line-height:1.6}
.stories{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.story{padding:14px 15px;background:#fff;border-radius:13px}
.story h3{font-size:11.5px;font-weight:700;margin-bottom:7px}
.story h3 span{font-size:9px;color:#888b7d;margin-right:5px}
.story p{font-size:11.3px;line-height:1.85;text-align:justify}
footer{display:flex;justify-content:space-between;align-items:center;font-size:8px;letter-spacing:.02em;color:#8a8a90;margin-top:auto;min-height:19px;border-top:1px solid #e2e2e7;padding-top:8px;flex-shrink:0}
footer a{color:#65656c}
.case-visual{margin-top:1px;background:#fff;border-radius:13px;padding:10px;overflow:hidden}
.case-visual img{height:83mm;width:100%;object-fit:contain}
.case-visual figcaption{padding:7px 4px 2px;font-size:9.3px;color:#777780;line-height:1.65}
.brand-case .heading h1{font-size:27px}
.brand-case .deck{font-size:11.5px}
.brand-case .story p{font-size:11.2px}
.brand-case .case-visual{margin-top:auto}
.brand-case .case-visual img{height:80mm}
.brand-case .metrics small{font-size:8.5px}
.question-panel{background:#1b1f3b;color:white;border-radius:15px;padding:18px 22px}
.question-panel .eyebrow{color:#c3f53c}
.question-panel p{font-size:20px;font-weight:500;line-height:1.6;margin:6px 0}
.question-panel small{font-size:10px;color:#bbbed1}
.news .stories{gap:11px}
.news .story p{font-size:11.3px;line-height:1.85}
.watch{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;background:#c3f53c;border-radius:15px;margin-top:auto;gap:20px}
.watch>div{display:flex;flex-direction:column;gap:5px}
.watch strong{font-size:20px;font-weight:600}
.watch>div>span:last-child{font-size:10px;opacity:.7}
.watch .eyebrow{color:#4e6020}
.qr{width:78px;height:78px;background:white;border-radius:5px;flex-shrink:0}
.cover{gap:23px}
.cover-top{display:grid;grid-template-columns:1.7fr 1fr;gap:18px;margin-top:20px}
.name{font-size:60px;letter-spacing:-2px;font-weight:700;line-height:1.2;margin:20px 0 22px}
.name span{font-size:20px;font-weight:400;letter-spacing:-.6px;white-space:nowrap}
.cover h1{font-size:33px;line-height:1.48;letter-spacing:-1.1px;white-space:nowrap}
.cover-copy{font-size:12px;line-height:2;color:#6f6f77;margin-top:20px}
.cover-panel{padding:23px;background:#c3f53c;border-radius:20px;display:flex;flex-direction:column;gap:18px}
.star{font-size:66px;line-height:1}
.cover-panel div{display:flex;flex-direction:column;font-size:21px;font-weight:500;line-height:1.7}
.cover-panel small{font-size:10px;opacity:.7;margin-top:auto}
.cover-photos{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:4px}
.cover-photos figure{background:white;border-radius:16px;overflow:hidden}
.cover-photos img{height:60mm;width:100%;object-fit:cover}
.cover-photos figcaption{font-size:9px;color:#73737b;padding:11px 13px}
.contact-strip{display:grid;grid-template-columns:1fr 1fr;background:white;border-radius:15px;padding:20px;gap:15px;margin-top:3px}
.contact-strip>div{display:flex;flex-direction:column;gap:6px}
.contact-strip a{font-size:12px;font-weight:600}
.cover footer{margin-top:auto}
.overview-intro{font-size:12px;line-height:1.9}
.overview-intro .muted{font-size:10px;margin-top:8px}
.contents{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.contents a{display:flex;align-items:flex-start;gap:10px;padding:14px;background:#fff;border-radius:13px;min-height:87px}
.contents-no{font-size:10px;color:#7a852f;white-space:nowrap;padding-top:2px}
.contents a>div{flex:1}
.contents strong{display:block;font-size:12px}
.contents small{display:block;color:#797981;font-size:9.4px;line-height:1.8;margin-top:4px}
.contents a>span:last-child{font-size:17px;color:#787b6d}
.section-label{display:flex;align-items:center;justify-content:space-between;margin-top:7px}
.section-label h2{font-size:15px;font-weight:600}
.brand-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:8px}
.brand-grid>div{background:white;border-radius:11px;display:flex;flex-direction:column;justify-content:center;align-items:center;padding:11px 6px 7px;gap:6px}
.brand-grid img{height:33px;width:100%;object-fit:contain}
.brand-grid span{font-size:8px;color:#797981}
.experience-note{background:#eaf0df;padding:16px 18px;border-radius:13px;margin-top:4px}
.experience-note b{font-size:11px}
.experience-note p{font-size:11px;line-height:1.85;margin-top:5px}
.internship-stories{grid-template-columns:1fr;gap:12px}
.internship-stories .story{padding:17px 18px}
.internship-stories .story p{font-size:12px}
.internship-stories .story h3{font-size:13px}
.projects-box{background:white;border-radius:14px;padding:17px 18px}
.projects-box h3{font-size:13px;margin-bottom:13px}
.project-tags{display:flex;flex-wrap:wrap;gap:8px}
.project-tags span{border:1px solid #e5e5e9;border-radius:20px;padding:5px 8px;font-size:10px;line-height:1.5}
.next-gallery{display:flex;justify-content:space-between;gap:20px;background:#c3f53c;padding:18px;border-radius:14px;margin-top:auto;font-size:11px}
.onsite-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.onsite-grid figure{background:white;padding:8px;border-radius:12px;overflow:hidden}
.onsite-grid img{width:100%;height:38mm;object-fit:contain;background:#f0f0f3;border-radius:5px}
.onsite-grid figcaption{font-size:10px;line-height:1.65;padding:7px 2px 1px}
.pitch .case-visual{margin-top:auto}
.pitch .case-visual img{height:83mm}
.culture-story{background:white;border-radius:13px;padding:14px 16px}
.culture-story h3{font-size:12px;margin-bottom:5px}
.culture-story p{font-size:11px;line-height:1.8;margin-top:4px}
.culture-scale{display:flex;justify-content:space-between;gap:20px;background:#eaf0df;border-radius:13px;padding:11px 16px;font-size:10px;align-items:center}
.culture-scale b{font-size:21px;font-weight:600;margin-right:6px}
.culture-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.culture-grid figure{background:white;border-radius:12px;padding:8px;overflow:hidden}
.culture-grid img{height:37mm;width:100%;object-fit:contain;background:#f0f0f3;border-radius:5px}
.culture-grid figcaption{font-size:9.5px;line-height:1.65;padding:6px 2px 1px}
.closing{display:flex;justify-content:space-between;align-items:center;background:#1b1f3b;border-radius:13px;padding:14px 16px;color:white;gap:16px}
.closing strong{font-size:12px;display:block;margin-top:5px}
.closing .eyebrow{font-size:8px;color:#c3f53c}
.closing a{font-size:10px;white-space:nowrap}
.culture .deck{font-size:11.5px}
.culture .heading h1{font-size:28px}

@media screen{.page{margin:20px auto;box-shadow:0 10px 40px #0001}
}

@media print{body{background:#f5f5f7}
.page{margin:0;box-shadow:none}
}

'''
# Slightly larger body text for comfortable A4 reading.
CSS += '.story h3{font-size:12.3px}.story p{font-size:12.3px}.news .story p{font-size:12.5px}.brand-case .story p{font-size:12.2px}.meta strong{font-size:11.2px}.metrics small,.brand-case .metrics small{font-size:9.2px}.onsite-grid figcaption{font-size:11px}.culture-grid figcaption{font-size:10.5px}'
html='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>李政 Li Zheng｜内容与文化作品集</title><style>'+CSS+'</style></head><body>'+''.join(pages)+'</body></html>'
html_path=BUILD/'portfolio.html';html_path.write_text(html)
class PreviewHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(PreviewHandler,directory=str(BUILD)))
Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium')
    doc=browser.new_page(viewport={'width':1100,'height':1400},device_scale_factor=1)
    doc.goto(f'http://127.0.0.1:{server.server_port}/portfolio.html',wait_until='load')
    doc.evaluate('()=>document.fonts.ready')
    doc.locator('img').evaluate_all('(imgs)=>Promise.all(imgs.map(i=>i.decode()))')
    doc.emulate_media(media='print')
    checks=doc.locator('.page').evaluate_all('''(pages)=>pages.map(p=>({id:p.id,overflow:p.scrollHeight-p.clientHeight,footer:p.querySelector('footer').getBoundingClientRect().bottom-p.getBoundingClientRect().bottom,broken:[...p.querySelectorAll('img')].filter(i=>!i.complete||!i.naturalWidth).length}))''')
    print(json.dumps(checks,ensure_ascii=False,indent=2))
    bad=[c for c in checks if c['overflow']>1 or c['footer']>1 or c['broken']]
    if bad:raise RuntimeError('Layout overflow/broken images: '+str(bad))
    for n in [1,2,3,5,9,10,11,12]:doc.locator(f'#p{n}').screenshot(path=str(BUILD/f'page-{n:02d}.png'))
    doc.pdf(path=str(OUT/'Li-Zheng-Portfolio.pdf'),prefer_css_page_size=True,print_background=True,display_header_footer=False,tagged=True,outline=True)
    browser.close()
server.shutdown();server.server_close()
with fitz.open(OUT/'Li-Zheng-Portfolio.pdf') as pdf:
    metadata=pdf.metadata
    metadata.update(author='李政 Li Zheng',subject='品牌内容执行｜新闻短片制作｜文化活动策划',keywords='李政, Li Zheng, 作品集, 内容策划, 视频制作, 活动执行')
    pdf.set_metadata(metadata)
    pdf.saveIncr()
print('Saved:',OUT/'Li-Zheng-Portfolio.pdf')
