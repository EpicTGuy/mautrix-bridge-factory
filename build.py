#!/usr/bin/env python3
"""Build YunoHost packages for mautrix bridgev2 bridges from one reference package.

template/ = one package with @@TOKENS@@ (packaging v2, helpers 2.1, settings and secrets kept across
upgrades, bridge run with -n, root-owned install dir, hardened unit). Everything network-specific
comes from bridges.toml, from bridges/<id>/ (hand-written docs) and from the bridge's own example
config at its release tag.

  build.py [bridge ...]     build out/mautrix_<bridge>_ynh (all bridges when none is given)
"""
import json, os, re, shutil, sys, tomllib, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / 'template'  # made from mautrix_meta_ynh by tools/make_template.py
OUT = Path(os.environ.get('FACTORY_OUT', HERE.parent))  # packages live next to the others, each with its own git history
CACHE = HERE / 'cache'
BRIDGES = tomllib.loads((HERE / 'bridges.toml').read_text())


def fetch(url):
    CACHE.mkdir(exist_ok=True)
    f = CACHE / re.sub(r'[^A-Za-z0-9._-]', '_', url.split('://', 1)[1])
    if not f.exists():
        with urllib.request.urlopen(url, timeout=60) as r:
            f.write_bytes(r.read())
    return f.read_text()


# ----------------------------------------------------------------------------- config.yaml
# (path of the key in the example config) -> value written in the template
COMMON = {
    ('bridge', 'command_prefix'): '"{command_prefix}"',
    ('bridge', 'personal_filtering_spaces'): '__PERSONAL_FILTERING_SPACES__',
    ('bridge', 'relay', 'enabled'): '__ENABLE_RELAYBOT__',
    ('bridge', 'relay', 'admin_only'): '__ADMIN_ONLY__',
    ('database', 'uri'): 'postgres://__APP__:__DB_PWD__@localhost:5432/__DB_NAME__?sslmode=disable',
    ('homeserver', 'address'): 'https://__DOMAIN__',
    ('homeserver', 'domain'): '__SERVER_NAME__',
    ('homeserver', 'async_media'): '__ASYNC_MEDIA__',
    ('appservice', 'address'): 'http://localhost:__PORT__',
    ('appservice', 'port'): '__PORT__',
    ('appservice', 'id'): '__APP__',
    ('appservice', 'bot', 'username'): '__BOTNAME__',
    ('appservice', 'bot', 'displayname'): "'__DISPLAYNAME_YAML__'",
    ('appservice', 'bot', 'avatar'): '__AVATAR__',
    ('appservice', 'ephemeral_events'): '__EPHEMERAL_EVENTS__',
    ('appservice', 'username_template'): '__USERNAME_TEMPLATE__',
    ('matrix', 'delivery_receipts'): '__DELIVERY_RECEIPTS__',
    ('provisioning', 'shared_secret'): '__PROVISIONING_SHARED_SECRET__',
    ('public_media', 'signing_key'): '__PUBLIC_MEDIA_SIGNING_KEY__',
    ('direct_media', 'server_key'): 'ed25519 __DIRECT_MEDIA_KEY_ID__ __DIRECT_MEDIA_SEED_KEY__',
    ('backfill', 'enabled'): 'true',
    ('backfill', 'max_initial_messages'): '__BACKFILL_MAX_INITIAL_MESSAGES__',
    ('encryption', 'allow'): '__ENCRYPTION__',
    ('encryption', 'default'): '__ENCRYPTION_DEFAULT__',
    ('encryption', 'require'): '__ENCRYPTION_REQUIRE__',
    ('encryption', 'pickle_key'): '__PICKLE_KEY__',
    ('logging', 'min_level'): '__PRINT_LEVEL__',
}
# keys that must exist in every supported mautrix-go version (the scripts rely on them)
REQUIRED = {k for k in COMMON if k[0] not in ('public_media', 'direct_media')}
PERMISSIONS = ['        "__LISTRELAY__": "relay"', '        "__LISTUSER__": "user"', '        "__LISTADMIN__": "admin"']
# example entries the bridges put back by themselves anyway, removed for readability
DROP = [re.compile(r'^\s+anotherserver\.example\.org: '), re.compile(r'^\s+example\.com: as_token:foobar')]


def templatize_common(text, b):
    out, stack, seen, in_perms = [], [], set(), False
    for line in text.splitlines():
        m = re.match(r'^( *)([A-Za-z_][A-Za-z0-9_]*):(.*)$', line)
        if in_perms:
            if re.match(r'^        \S', line):
                continue  # example permissions replaced below
            in_perms = False
        if any(d.match(line) for d in DROP):
            continue
        if m:
            depth = len(m.group(1)) // 4
            stack = stack[:depth] + [m.group(2)]
            path = tuple(stack)
            if path == ('bridge', 'permissions'):
                out.append(line)
                out.extend(PERMISSIONS)
                in_perms = True
                continue
            if path in COMMON:
                value = COMMON[path].format(**b)
                comment = re.search(r'\s+#.*$', m.group(3))
                line = f'{m.group(1)}{m.group(2)}: {value}' + (comment.group(0) if comment else '')
                seen.add(path)
            elif path == ('logging', 'writers'):
                pass
        if re.match(r'^ +filename: \./logs/', line):
            line = re.sub(r'filename: .*', 'filename: /var/log/__APP__/__APP__.log', line)
        out.append(line)
    missing = REQUIRED - seen
    assert not missing, f'{b["id"]}: keys not found in example config: {sorted(missing)}'
    assert '/var/log/__APP__/__APP__.log' in '\n'.join(out)
    return '\n'.join(out) + '\n'


def templatize_network(text):
    lines = []
    for line in text.splitlines():
        if re.match(r'^displayname_template:', line):
            line = "displayname_template: '__GHOST_DISPLAYNAME_YAML__'"
        lines.append(('    ' + line) if line.strip() else '')
    return '# Network-specific config options\nnetwork:' + ('\n' + '\n'.join(lines) if any(lines) else ' {}') + '\n\n'


def default_displayname(text):
    m = re.search(r'^displayname_template:\s*(.+?)\s*$', text, re.M)
    if not m:
        return None
    v = m.group(1)
    if v[0] in '\'"' and v[-1] == v[0]:
        v = v[1:-1]
    return v


# ----------------------------------------------------------------------------- package
TEXT_SUFFIXES = ('', '.md', '.toml', '.sh', '.service', '.yaml', '.j2', '.yml')


def conditionals(text, features):
    """Keep @@if f@@ ... @@endif@@ blocks when feature f is on, drop them otherwise (no nesting)."""
    out, keep = [], True
    for line in text.splitlines(keepends=True):
        m = re.match(r'^@@if (\w+)@@\n?$', line)
        if m:
            keep = m.group(1) in features
            continue
        if re.match(r'^@@endif@@\n?$', line):
            keep = True
            continue
        if keep:
            out.append(line)
    return ''.join(out)


def netopts(b):
    opts = b.get('network_options', [])
    if not opts:
        return {'@@NETOPTS_INSTALL@@\n': '', '@@NETOPTS_UPGRADE@@\n': '', '@@NETOPTS_PANEL@@\n': ''}
    comment = '# Network options of the config panel (bound to config.yaml, kept as settings)\n'
    install, upgrade = comment, comment
    panel = f'    [advanced.network]\n    name = "{b["display"]} specific config options"\n\n'
    for o in opts:
        k, d = o['key'], o.get('default', 'false')
        install += f'{k}="{d}"\nynh_app_setting_set --key={k} --value="${k}"\n'
        upgrade += (f'{k}=$(ynh_app_setting_get --key={k})\n'
                    f'[ -n "${k}" ] || {k}=$(read_bridge_value {k} network)\n'
                    f'[ -n "${k}" ] || {k}="{d}"\n'
                    f'ynh_app_setting_set --key={k} --value="${k}"\n')
        panel += (f'        [advanced.network.{k}]\n        ask = "{o["ask"]}"\n        type = "boolean"\n'
                  f'        yes = "true"\n        no = "false"\n'
                  + (f'        help = "{o["help"]}"\n' if 'help' in o else '')
                  + '        bind = ":__INSTALL_DIR__/config.yaml"\n\n')
    return {'@@NETOPTS_INSTALL@@\n': install, '@@NETOPTS_UPGRADE@@\n': upgrade, '@@NETOPTS_PANEL@@\n': panel}


def build(name):
    b = {'id': name, **BRIDGES[name]}
    app, binary, display = f'mautrix_{name}', b['binary'], b['display']
    short = b.get('short', display)
    tag = b['version']
    gomod = fetch(f'https://raw.githubusercontent.com/mautrix/{b["repo"]}/{tag}/go.mod')
    gover = re.search(r'^\s*maunium\.net/go/mautrix (v\S+)', gomod, re.M).group(1)
    common = fetch(f'https://raw.githubusercontent.com/mautrix/go/{gover}/bridgev2/matrix/mxmain/example-config.yaml')
    network = fetch(f'https://raw.githubusercontent.com/mautrix/{b["repo"]}/{tag}/{b.get("network_config", "pkg/connector/example-config.yaml")}')
    sums = dict(l.split()[::-1] for l in fetch(
        f'https://github.com/mautrix/{b["repo"]}/releases/download/{tag}/sha256sums.txt').splitlines() if l.strip())
    # second opinion on the checksums: the sha256 GitHub computed itself when the assets were uploaded
    release = json.loads(fetch(f'https://api.github.com/repos/mautrix/{b["repo"]}/releases/tags/{tag}'))
    digests = {a['name']: (a.get('digest') or '').removeprefix('sha256:') for a in release['assets']}
    for asset in (f'{binary}-amd64', f'{binary}-arm64', f'{binary}-arm'):
        assert digests.get(asset) == sums[asset], f'{name}: {asset} checksum differs between sha256sums.txt and GitHub'
    ghost_default = default_displayname(network)
    features = {f for f, on in (('backfill', 'backfill' in b), ('ghost', ghost_default is not None)) if on}

    dest = OUT / f'{app}_ynh'
    if dest.exists():  # rebuild in place, keeping the package's git history
        for item in dest.iterdir():
            if item.name != '.git':
                shutil.rmtree(item) if item.is_dir() else item.unlink()
    shutil.copytree(TEMPLATE, dest, dirs_exist_ok=True)
    overlay = HERE / 'bridges' / name
    if overlay.is_dir():
        shutil.copytree(overlay, dest, dirs_exist_ok=True)

    tokens = {
        '@@NAME@@': b.get('name', f'Mautrix {display}'),
        '@@DISPLAY@@': display,
        '@@SHORT@@': short,
        '@@APP@@': app,
        '@@BINARY@@': binary,
        '@@REPO@@': b['repo'],
        '@@BOT@@': b['bot'],
        '@@PREFIX@@': b['prefix'],
        '@@CMD@@': b['command_prefix'],
        '@@AVATAR@@': b['avatar'],
        '@@BACKFILL_DEFAULT@@': str(b.get('backfill', 0)),
        '@@GHOST_DEFAULT@@': ghost_default or '{{.ID}}',
        '@@GHOST_HELP@@': b.get('ghost_help', f'Go template, see the upstream example config. Default: {json.dumps(ghost_default or "")[1:-1]}'),
        '@@GHOST_EXAMPLE@@': b.get('ghost_example', f'{ghost_default} ({display})'),
    }
    slots = netopts(b)
    for p in dest.rglob('*'):
        if '.git' in p.relative_to(dest).parts or not p.is_file() or p.name == 'LICENSE' or p.suffix not in TEXT_SUFFIXES:
            continue
        t = conditionals(p.read_text(), features)
        for a, c in slots.items():
            t = t.replace(a, c)
        for a, c in tokens.items():
            t = t.replace(a, c)
        if p.relative_to(dest).as_posix() in ('scripts/install', 'scripts/upgrade'):
            t = re.sub(r'\n{3,}', '\n\n', t)
        p.write_text(t)

    # config template: network part with the options of the panel as settings
    net = templatize_network(network)
    if 'backfill' in features:
        net, n = re.subn(r'^(    thread_backfill:\n(?:      #.*\n)*      batch_count:) .*$', r'\1 __THREAD_BACKFILL_BATCH_COUNT__', net, flags=re.M)
        assert n == 1, f'{name}: thread_backfill.batch_count not found in the example config'
    for o in b.get('network_options', []):
        net, n = re.subn(rf'^(    {o["key"]}:) .*$', rf'\1 __{o["key"].upper()}__', net, flags=re.M)
        assert n == 1, f'{name}: network option {o["key"]} not found in the example config'
    for path, value in b.get('network_set', {}).items():
        *parents, key = path.split('.')
        indent = '    ' * (len(parents) + 1)
        net, n = re.subn(rf'^({indent}{key}:) .*$', rf'\1 {value}', net, flags=re.M)
        assert n == 1, f'{name}: network key {path} not found (or not unique) in the example config'
    (dest / 'conf/config.yaml').write_text(net + templatize_common(common, b))

    # manifest: sources, port, upstream
    p = dest / 'manifest.toml'
    t = p.read_text()
    version = tag.lstrip('v') + f'~ynh{b.get("revision", 1)}'
    t = re.sub(r'^version = ".*"', f'version = "{version}"', t, flags=re.M)
    for arch, asset in (('amd64', f'{binary}-amd64'), ('arm64', f'{binary}-arm64'), ('armhf', f'{binary}-arm')):
        t = re.sub(rf'{arch}\.url = ".*"', f'{arch}.url = "https://github.com/mautrix/{b["repo"]}/releases/download/{tag}/{asset}"', t)
        t = re.sub(rf'{arch}\.sha256 = ".*"', f'{arch}.sha256 = "{sums[asset]}"', t)
    t = re.sub(r'main\.default = \d+', f'main.default = {b["port"]}', t)
    for lang in ('en', 'fr'):
        if f'description_{lang}' in b:
            t = re.sub(rf'^description\.{lang} = ".*"', f'description.{lang} = "{b[f"description_{lang}"]}"', t, flags=re.M)
    p.write_text(t)

    # docs specific to the network, unless given in bridges/<id>/
    def doc(rel, text):
        if not (dest / rel).exists():
            (dest / rel).write_text(text)
    doc('doc/DESCRIPTION.md',
        f'Matrix puppeting bridge for {display}, based on the official [{binary}](https://github.com/mautrix/{b["repo"]}) bridge (Go, bridgev2).\n\n'
        f'The bridge is a Synapse application service and relies on a PostgreSQL database. Your {display} conversations show up as Matrix rooms.\n')
    doc('doc/DESCRIPTION_fr.md',
        f'Passerelle Matrix pour {display}, basée sur la passerelle officielle [{binary}](https://github.com/mautrix/{b["repo"]}) (Go, bridgev2).\n\n'
        f'La passerelle est un service d\'application Synapse et repose sur une base PostgreSQL. Vos conversations {display} apparaissent comme des salons Matrix.\n')
    for lang, intro, docs in (
            ('', '* A Synapse instance must be installed on the server.\n* The **bridge administrator** must be a single Matrix account (e.g. `@john:example.com`). Do not put the same account in the **authorized users** field: use your server name there (e.g. `example.com`) to authorize all local accounts.\n',
             f'* Upstream documentation: <https://docs.mau.fi/bridges/go/{b["repo"]}/index.html> — support room: `#{b["repo"]}:maunium.net`\n'),
            ('_fr', '* Une instance Synapse doit être installée sur le serveur.\n* L\'**administrateur de la passerelle** doit être un seul compte Matrix (ex. `@john:example.com`). Ne mettez pas ce même compte dans le champ des **utilisateurs autorisés** : indiquez-y votre nom de serveur (ex. `example.com`) pour autoriser tous les comptes locaux.\n',
             f'* Documentation upstream : <https://docs.mau.fi/bridges/go/{b["repo"]}/index.html> — salon d\'aide : `#{b["repo"]}:maunium.net`\n')):
        doc(f'doc/PRE_INSTALL{lang}.md', intro + docs)
    if not (dest / 'doc/POST_INSTALL.md').exists():
        doc('doc/POST_INSTALL.md',
            f'## Log in to {display}\n\nIn your Matrix client, start a direct chat with `@__BOTNAME__:__SERVER_NAME__` (if it isn\'t found in the user directory, type the full ID). '
            f'Use an **encrypted** chat if possible, since you will send credentials in it.\n\n{b["login_en"]}\n\n'
            'Once logged in, your conversations appear as Matrix rooms. Useful commands: `help`, `list-logins`, `logout <login ID>`. Logs: `sudo yunohost service log __APP__`.\n')
        doc('doc/POST_INSTALL_fr.md',
            f'## Connexion à {display}\n\nDans votre client Matrix, ouvrez une discussion privée avec `@__BOTNAME__:__SERVER_NAME__` (s\'il n\'apparaît pas dans l\'annuaire, tapez l\'identifiant complet). '
            f'Utilisez si possible une discussion **chiffrée**, car vous allez y envoyer des identifiants.\n\n{b["login_fr"]}\n\n'
            'Une fois connecté, vos conversations apparaissent comme des salons Matrix. Commandes utiles : `help`, `list-logins`, `logout <ID de connexion>`. Journaux : `sudo yunohost service log __APP__`.\n')
    doc('README.md', README.format(display=display, binary=binary, repo=b['repo'], app=app, ver=tag))

    leftovers = [str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file() and '.git' not in p.relative_to(dest).parts
                 and p.suffix in TEXT_SUFFIXES and '@@' in p.read_text(errors='ignore')]
    assert not leftovers, f'{app}: unrendered markers in {leftovers}'
    print(f'{app}: {version}, mautrix-go {gover}')


README = '''# Mautrix {display} for YunoHost

Matrix / Synapse puppeting bridge for {display}, packaged for [YunoHost](https://yunohost.org).
Upstream bridge: <https://github.com/mautrix/{repo}> ({binary} {ver}, Go / bridgev2).

## ⚠️ Status: looking for testers

The YunoHost side of this package is tested on YunoHost 12 / Debian 12: install, upgrades with settings kept, backup / restore, registration with Synapse, config panel.

**Feedback on real use is welcome**: please install it and report how it went in the issues (login, sending/receiving messages, media). Packages confirmed by testers will be proposed to the YunoHost catalog.

## Install

```bash
sudo yunohost app install https://github.com/EpicTGuy/{app}_ynh
```

Then, in your Matrix client, open a chat with the bot, send `login` and follow the [official authentication guide](https://docs.mau.fi/bridges/go/{repo}/authentication.html).

## Features of this package

- Config generated from the upstream example config, with a config panel for the main settings: permissions, encryption, display name of contacts, number of past messages imported in new chats.
- Settings and bridge secrets are kept across upgrades (`config.yaml` is regenerated from the template, the bridge runs with `-n` and never rewrites it, so upgrades don't print its diff).
- Hardened: the binary and `config.yaml` belong to root and are only readable by the bridge user; strict systemd sandbox (`systemd-analyze security` ≈ 1.3); listens on 127.0.0.1 only.
- Double puppeting enabled automatically when a shared `doublepuppet` appservice is registered in Synapse (`/etc/matrix-<synapse instance>/app-service/doublepuppet.yaml`, see <https://docs.mau.fi/bridges/general/double-puppeting.html>).

Based on the [mautrix_whatsapp_ynh](https://github.com/YunoHost-Apps/mautrix_whatsapp_ynh) package. License: AGPL-3.0-or-later.
'''

if __name__ == '__main__':
    for n in sys.argv[1:] or BRIDGES:
        build(n)
