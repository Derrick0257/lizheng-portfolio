# 李政｜PDF作品集

下载地址：https://derrick0257.github.io/lizheng-portfolio/portfolio/Li-Zheng-Portfolio.pdf

A4纵向，共12页。沿用个人网站的灰白底、荧光绿、深靛蓝和圆角卡片风格。

内容包括个人介绍与项目索引、两部新闻片、三个综艺品牌合作项目、《说唱听我的》现场制作、湖南卫视制片实习与8张现场记录、芒果青年说提案、学联文化活动。游戏与电竞板块不纳入PDF。

两部新闻片通过PDF中的可点击链接和二维码访问。目录支持内部跳转，页脚链接返回个人网站。

## 更新PDF

生成器读取仓库根目录的`index.html`，提取当前项目资料和图片，按固定的12页结构排版。

```bash
python portfolio/build_portfolio.py
```

需要Python、Pillow、reportlab、PyMuPDF、Playwright、Chromium（`/usr/bin/chromium`）以及Noto Sans CJK SC字体。中间HTML和页面预览输出到`/tmp/lizheng-portfolio-pdf/`，最终PDF输出到当前目录。
