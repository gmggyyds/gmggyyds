#!/usr/bin/env python3
"""生成首屏那条渐变打字动画（typing.svg）。

    python3 scripts/make_typing_svg.py

为什么不用 readme-typing-svg：它的 color 参数只吃单色，
出来的 SVG 里全是纯色 fill，做不出和 banner 一致的渐变。
自己生成还有两个好处：不依赖第三方服务（对方挂了首屏就空一块），
配色能跟 banner 的波浪精确对齐。

配色取自 banner 的 capsule-render 参数 color=0:1a365d,100:e8543f
—— 同一组渐变，首屏上下两块才是一套。

🔴 三条踩过的：
  1. **纯 CSS 动画，不用 SMIL**。GitHub 的 camo 代理会剥掉一些东西，
     实测 <style> 里的 @keyframes 能过（贡献图那张火箭就是这么动的）。
  2. **打字效果用 transform 移动 clipPath，不要动画 width**。
     SVG geometry properties 当 CSS 属性来动画，旧浏览器不认；
     transform 是所有浏览器都稳的。
  3. **中文字体写字体栈不写具体字体**。SVG 在客户端渲染，
     字体得是对方机器上有的。
"""
import io
import os

W, H = 640, 64
LINES = [
    "99% 的事情都有答案，不要自己瞎折腾",
    "先定生意，再定 Agent",
    "吸进来，得化得掉",
]
FONT = "'PingFang SC','Hiragino Sans GB','Microsoft YaHei','Helvetica Neue',Arial,sans-serif"
C_FROM, C_TO = "#1a365d", "#e8543f"     # 与 banner 波浪同一组渐变

TYPE_S, HOLD_S, FADE_S = 1.6, 2.2, 0.5  # 打字 / 停留 / 淡出
PER = TYPE_S + HOLD_S + FADE_S
TOTAL = PER * len(LINES)


def pct(sec):
    return round(sec / TOTAL * 100, 3)


def build():
    L = []
    A = L.append
    A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
      f'fill="none" role="img" aria-label="{LINES[0]}">')
    A('  <defs>')
    # 🔴 objectBoundingBox 而不是 userSpaceOnUse：渐变按每行文字自己的包围盒铺，
    #    短句才能跟长句一样走完整条 navy→橙。用 userSpaceOnUse 铺满 640px 的话，
    #    居中的短句只落在渐变中段，渲出来是一片发闷的酱红 —— 和 banner 根本不是一个颜色。
    A('    <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">')
    A(f'      <stop offset="0%" stop-color="{C_FROM}"/>')
    A(f'      <stop offset="100%" stop-color="{C_TO}"/>')
    A('    </linearGradient>')
    # 每句一个 clip：一块和画布等宽的矩形从左边滑入，滑到哪露到哪
    for i in range(len(LINES)):
        A(f'    <clipPath id="c{i}"><rect class="t t{i}" x="{-W}" y="0" width="{W}" height="{H}"/></clipPath>')
    A('  </defs>')
    A('  <style>')
    A(f'    .l {{ font-family:{FONT}; font-size:21px; font-weight:600; fill:url(#g); '
      f'opacity:0; animation:none {TOTAL}s linear infinite; }}')
    A(f'    .t {{ animation:none {TOTAL}s linear infinite; }}')
    for i in range(len(LINES)):
        s = i * PER
        # 🔴 关键帧百分比必须严格递增且不重复。第一句 s=0 时 pct(s)==0，
        #    如果照写会生成「0%,0%」——无效 CSS，整条动画被浏览器直接丢弃。
        #    所以逐句构造停靠点，去重后再排序输出。
        def frames(pairs):
            seen, out = set(), []
            for k, v in sorted(pairs, key=lambda x: x[0]):
                k = round(k, 3)
                if k in seen:
                    continue
                seen.add(k)
                out.append(f'{k}% {{{v}}}')
            return " ".join(out)

        # 文字可见窗口：本句开始才亮，打字+停留期间保持，然后灭
        A(f'    @keyframes o{i} {{ ' + frames([
            (0.0, "opacity:1" if i == 0 else "opacity:0"),
            (pct(s), "opacity:1"),
            (pct(s + TYPE_S + HOLD_S), "opacity:1"),
            (pct(s + PER), "opacity:0"),
            (100.0, "opacity:0"),
        ]) + ' }')

        # 打字：clip 矩形从 -W 推到 0（translateX 0 → W），推到哪露到哪
        A(f'    @keyframes k{i} {{ ' + frames([
            (0.0, "transform:translateX(0)"),
            (pct(s), "transform:translateX(0)"),
            (pct(s + TYPE_S), f"transform:translateX({W}px)"),
            (100.0, f"transform:translateX({W}px)"),
        ]) + ' }')
        A(f'    .l{i} {{ animation-name:o{i}; }}')
        A(f'    .t{i} {{ animation-name:k{i}; }}')
    A('  </style>')
    for i, text in enumerate(LINES):
        esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        A(f'  <g clip-path="url(#c{i})">')
        A(f'    <text class="l l{i}" x="{W//2}" y="{H//2+8}" text-anchor="middle">{esc}</text>')
        A('  </g>')
    A('</svg>')
    return "\n".join(L)


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "typing.svg")
    io.open(out, "w", encoding="utf-8").write(build())
    print(f"typing.svg  {os.path.getsize(out)} bytes  {len(LINES)} 句 / {TOTAL:.1f}s 一轮")


if __name__ == "__main__":
    main()
