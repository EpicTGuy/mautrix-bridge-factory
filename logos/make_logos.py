#!/usr/bin/env python3
"""Recipe for the mautrix bridge logos of the YunoHost catalog.
Base = the shared mautrix logo (cat between Matrix brackets), unchanged.
Badge = a coloured disc in the bottom-right corner with a simple white glyph of the network
(drawn here, not the networks' trademarked logos). Output: SVG per bridge, 460x460."""
import base64, sys, os
base = base64.b64encode(open(sys.argv[1], 'rb').read()).decode()
out = sys.argv[2]

W = 'fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"'
BUBBLE = 'M50 16c-19 0-34 13.5-34 30.5 0 9.3 4.6 17.6 11.8 23.2L24 84l16.2-8.6c3.1.8 6.4 1.2 9.8 1.2 19 0 34-13.5 34-30.5S69 16 50 16z'
GLYPHS = {
    # name: (background (colour or gradient stops), glyph drawn in a 100x100 box)
    'instagram': (['#feda75', '#fa7e1e', '#d62976', '#962fbf', '#4f5bd5'],
                  f'<rect x="22" y="22" width="56" height="56" rx="16" {W}/><circle cx="50" cy="50" r="13" {W}/><circle cx="66" cy="34" r="4" fill="#fff"/>'),
    'telegram': ('#2AABEE', '<path d="M20 48 78 25 68 77 50 63 40 73 41 59 68 35 36 55z" fill="#fff"/>'),
    'whatsapp': ('#25D366', f'<path d="{BUBBLE}" {W}/><path d="M39 36c-3 3-3 8 1 14 4 6 9 10 15 12 4 1 7-1 8-4l-5-5-5 2c-3-1-6-4-7-7l2-5-5-5z" fill="#fff"/>'),
    'discord': ('#5865F2', '<path d="M28 34c6-5 14-7 22-7s16 2 22 7c5 9 8 18 8 30-5 5-11 8-17 9l-4-6c-6 2-12 2-18 0l-4 6c-6-1-12-4-17-9 0-12 3-21 8-30z" fill="#fff"/><circle cx="40" cy="54" r="6" fill="#5865F2"/><circle cx="60" cy="54" r="6" fill="#5865F2"/>'),
    'signal': ('#3A76F0', f'<path d="{BUBBLE}" {W} stroke-dasharray="11 6"/>'),
    'meta': (['#00B2FF', '#006AFF', '#A033FF', '#FF5280'],
             f'<path d="{BUBBLE}" fill="#fff"/><path d="M30 56 45 40l8 8 15-8-15 16-8-8z" fill="#7a3cff"/>'),
    'imessage': ('#34C759', f'<path d="{BUBBLE}" fill="#fff"/>'),
    'gmessages': ('#1A73E8', f'<path d="{BUBBLE}" fill="#fff"/><path d="M36 40h28M36 52h18" stroke="#1A73E8" stroke-width="7" stroke-linecap="round"/>'),
    # channels: a hash sign
    'slack': ('#4A154B', '<path d="M40 22 34 78M66 22 60 78M22 40h58M20 60h58" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round"/>'),
    # X: a plain cross of two strokes
    'twitter': ('#000000', '<path d="M27 25 73 75M73 25 27 75" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round"/>'),
    # "in" drawn with shapes
    'linkedin': ('#0A66C2', '<circle cx="31" cy="29" r="7" fill="#fff"/><rect x="24" y="42" width="14" height="36" rx="3" fill="#fff"/>'
                 '<path d="M51 78V44M51 58c0-9 6-14 13-14s12 5 12 14v20" fill="none" stroke="#fff" stroke-width="12" stroke-linejoin="round"/>'),
    # sky: a butterfly
    'bluesky': ('#1185FE', '<g transform="translate(50 50) scale(1.3) translate(-50 -52)"><path d="M50 50C40 30 22 20 18 30c-4 12 8 22 22 22-12 4-14 18-4 20 8 2 12-10 14-16 2 6 6 18 14 16 10-2 8-16-4-20 '
                '14 0 26-10 22-22-4-10-22 0-32 20z" fill="#fff"/></g>'),
    # voice calls: a phone handset
    'gvoice': ('#0F9D58', '<path d="M34 22c3-2 7-1 9 2l6 9c2 3 1 6-1 8l-4 4c3 7 9 13 16 16l4-4c2-2 5-3 8-1l9 6c3 2 4 6 2 9l-4 5c-3 3-8 4-12 2'
               '-16-7-29-20-36-36-2-4-1-9 2-12z" fill="#fff"/>'),
    # topics: a bubble with a Z
    'zulip': ('#6492FE', f'<path d="{BUBBLE}" fill="#fff"/><path d="M37 34h26L37 58h26" fill="none" stroke="#6492FE" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'),
}
CX, CY, R = 362, 362, 86
for name, (bg, glyph) in GLYPHS.items():
    if isinstance(bg, list):
        stops = ''.join(f'<stop offset="{i / (len(bg) - 1):.2f}" stop-color="{c}"/>' for i, c in enumerate(bg))
        defs, fill = f'<defs><linearGradient id="g" x1="0" y1="1" x2="1" y2="0">{stops}</linearGradient></defs>', 'url(#g)'
    else:
        defs, fill = '', bg
    s = R * 2 * 0.62 / 100  # glyph box = 62 % of the disc
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="460" height="460" viewBox="0 0 460 460">{defs}
<image width="460" height="460" xlink:href="data:image/png;base64,{base}"/>
<circle cx="{CX}" cy="{CY}" r="{R + 9}" fill="#fff"/><circle cx="{CX}" cy="{CY}" r="{R}" fill="{fill}"/>
<g transform="translate({CX - 50 * s:.1f} {CY - 50 * s:.1f}) scale({s:.4f})">{glyph}</g></svg>'''
    open(os.path.join(out, f'mautrix_{name}.svg'), 'w').write(svg)
    print(name)
