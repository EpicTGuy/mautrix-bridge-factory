# mautrix bridge logos (recipe)

Base = the mautrix logo of the YunoHost catalog (`base-mautrix.png`, cat between Matrix brackets), unchanged.
Badge in the bottom-right corner = a disc in the network's colour with a simple white glyph, drawn here (not the
networks' trademarked logos).

Rebuild: `python3 make_logos.py base-mautrix.png <dir>` → one 460×460 SVG per bridge, then render to PNG, e.g.

- `rsvg-convert -w 460 -h 460 mautrix_<x>.svg -o mautrix_<x>.png` then `pngquant --quality 70-95` (≈ 7-9 KB), or
- on macOS: `qlmanage -t -s 460 -o <dir> mautrix_<x>.svg` then
  `magick <dir>/mautrix_<x>.svg.png -strip -colors 96 -define png:compression-level=9 mautrix_<x>.png` (≈ 7 KB).

ImageMagick alone renders the badge badly. Adding a network = one line in `GLYPHS`.

14 bridges: WhatsApp, Telegram, Signal, Discord, iMessage, Instagram, Messenger, Google Messages, Slack, X, LinkedIn,
Bluesky, Google Voice, Zulip (`planche.png`).
