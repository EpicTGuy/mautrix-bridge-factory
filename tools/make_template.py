#!/usr/bin/env python3
"""One-off: turn the mautrix_meta_ynh package into the factory template (template/).

Names become @@TOKENS@@, Meta-only parts become @@if feature@@ ... @@endif@@ blocks or
@@NETOPTS_*@@ slots filled from bridges.toml. Kept for the record: from now on template/ is
the source (edited directly since) and mautrix_meta_ynh is one of its outputs.
"""
import re, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / 'mautrix_meta_ynh'
DST = HERE / 'template'

GHOST = '{{or .DisplayName .Username "Unknown user"}}'
SUBS = [  # order matters
    ('https://github.com/mautrix/meta', 'https://github.com/mautrix/@@REPO@@'),
    ('https://docs.mau.fi/bridges/go/meta/', 'https://docs.mau.fi/bridges/go/@@REPO@@/'),
    ('#meta:maunium.net', '#@@REPO@@:maunium.net'),
    ('Mautrix Meta (Messenger)', '@@NAME@@'),
    ('mautrix_meta', '@@APP@@'),
    ('mautrix-meta', '@@BINARY@@'),
    ('mxc://maunium.net/ygtkteZsXnGJLJHRchUwYWak', '@@AVATAR@@'),
    ('facebook_{{.}}', '@@PREFIX@@_{{.}}'),
    ('facebookbot', '@@BOT@@'),
    ('!fb', '@@CMD@@'),
    ('`' + GHOST + ' (IG)`', '`@@GHOST_EXAMPLE@@`'),
    ('help = "Go template. .DisplayName is the Instagram name and .Username the Instagram username. '
     'For example, add \' (IG)\' at the end to recognise Messenger contacts at a glance."', 'help = "@@GHOST_HELP@@"'),
    ("'" + GHOST + "'", "'@@GHOST_DEFAULT@@'"),
    ('Facebook Messenger', '@@DISPLAY@@'),
    ('Messenger', '@@SHORT@@'),
]


def block(text, start, end, open_, close, include_end=False):
    """Wrap lines from the one matching start up to (excluding, or including) the one matching end."""
    lines, out, inside, done = text.splitlines(keepends=True), [], False, False
    for line in lines:
        if not inside and not done and re.search(start, line):
            out.append(open_ + '\n')
            inside = True
        elif inside and re.search(end, line):
            if include_end:
                out.append(line)
            out.append(close + '\n')
            inside, done = False, True
            if include_end:
                continue
        out.append(line)
    assert done, (start, end)
    return ''.join(out)


def edit(p, fn):
    t = p.read_text()
    n = fn(t)
    assert n != t, p
    p.write_text(n)


if DST.exists():
    shutil.rmtree(DST)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns('.git', '.DS_Store', 'README.md'))
(DST / 'conf/config.yaml').unlink()  # rebuilt from the upstream examples at each build
for f in ('DESCRIPTION', 'PRE_INSTALL', 'POST_INSTALL'):  # per network: generated or from bridges/<id>/
    for lang in ('', '_fr'):
        (DST / f'doc/{f}{lang}.md').unlink()

for p in DST.rglob('*'):
    if p.is_file() and p.name != 'LICENSE':
        t = p.read_text()
        for a, b in SUBS:
            t = t.replace(a, b)
        p.write_text(t)

IF_B, END = '@@if backfill@@', '@@endif@@'

# install: older chats default + network options
edit(DST / 'scripts/install', lambda t: t
     .replace('\n# Older chats to import at login (pages, -1 = all, 0 = none)\nthread_backfill_batch_count=-1\n',
              f'\n{IF_B}\n# Older chats to import at login (pages, -1 = all, 0 = none)\nthread_backfill_batch_count=@@BACKFILL_DEFAULT@@\n{END}\n')
     .replace(re.search(r'# Network options of the config panel.*?\n(?=ynh_app_setting_set --key=thread_backfill)', t, re.S).group(0),
              '@@NETOPTS_INSTALL@@\n')
     .replace('ynh_app_setting_set --key=thread_backfill_batch_count --value="$thread_backfill_batch_count"\n',
              f'{IF_B}\nynh_app_setting_set --key=thread_backfill_batch_count --value="$thread_backfill_batch_count"\n{END}\n'))

# upgrade
edit(DST / 'scripts/upgrade', lambda t: t
     .replace('thread_backfill_batch_count=$(ynh_app_setting_get --key=thread_backfill_batch_count)\n',
              f'{IF_B}\nthread_backfill_batch_count=$(ynh_app_setting_get --key=thread_backfill_batch_count)\n{END}\n')
     .replace('if [ -z "$thread_backfill_batch_count" ]\nthen\n  thread_backfill_batch_count=-1\n',
              f'{IF_B}\nif [ -z "$thread_backfill_batch_count" ]\nthen\n  thread_backfill_batch_count=@@BACKFILL_DEFAULT@@\n')
     .replace('  ynh_app_setting_set --key=thread_backfill_batch_count --value="$thread_backfill_batch_count"\nfi\n',
              f'  ynh_app_setting_set --key=thread_backfill_batch_count --value="$thread_backfill_batch_count"\nfi\n{END}\n')
     .replace(re.search(r'# Network options of the config panel.*?\n(?=ensure_bridge_settings)', t, re.S).group(0),
              '@@NETOPTS_UPGRADE@@\n'))

# config script
edit(DST / 'scripts/config', lambda t: block(t, r'^set__thread_backfill_batch_count\(\)', r'^set__ghost_displayname_template\(\)', IF_B, END))
edit(DST / 'scripts/config', lambda t: block(t, r'^set__ghost_displayname_template\(\)', r'^set__backfill_max_initial_messages\(\)', '@@if ghost@@', END))

# config panel
def panel(t):
    t = block(t, r'^\s+\[main\.bridge\.thread_backfill_batch_count\]', r'^\s+\[main\.bridge\.ghost_displayname_template\]', IF_B, END)
    t = block(t, r'^\s+\[main\.bridge\.ghost_displayname_template\]', r'^\s+\[main\.bridge\.backfill_max_initial_messages\]', '@@if ghost@@', END)
    section = re.search(r'    \[advanced\.network\]\n.*?\n(?=    \[advanced\.appservice\])', t, re.S).group(0)
    return t.replace(section, '@@NETOPTS_PANEL@@\n')
edit(DST / 'config_panel.toml', panel)

# admin docs
for f in ('doc/ADMIN.md', 'doc/ADMIN_fr.md'):
    edit(DST / f, lambda t: re.sub(r'^(- \*\*(?:Import all older|Importer toutes les anciennes).*\n)', IF_B + r'\n\1' + END + '\n', t, flags=re.M))
    edit(DST / f, lambda t: re.sub(r'^(- \*\*(?:Display name of|Nom affiché des).*\n)', r'@@if ghost@@\n\1' + END + '\n', t, flags=re.M))

left = [(str(p.relative_to(DST)), m) for p in DST.rglob('*') if p.is_file() and p.name != 'LICENSE'
        for m in re.findall(r'.{0,30}(?:messenger|facebook|instagram|\(IG\)|thread_backfill_batch_count=-1).{0,30}', p.read_text(), re.I)
        if not m.lstrip().startswith(('ynh_', '[main.bridge.thread', 'set__thread', 'thread_backfill', 'if [ -z "$thread'))]
print('\n'.join(f'{f}: {m}' for f, m in left) or 'template clean')
