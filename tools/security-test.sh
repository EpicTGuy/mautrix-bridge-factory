#!/bin/bash
# Run as root on the test server after factory-test.sh: checks the fixes of the security review (SECURITY-REVIEW.md).
# /root/factory-test/<app>_ynh = new packages. Uses mautrix_slack (installed) and a fresh mautrix_zulip.
set -u
T=${T:-/root/factory-test}
DOMAIN=${DOMAIN:?set DOMAIN to the Synapse server name}
ok() { echo "  OK  $*"; }
ko() { echo "  KO  $*"; FAIL=1; }
FAIL=0
yaml_ok() { python3 -c "import yaml; yaml.safe_load(open('/var/www/$1/config.yaml'))" 2>/dev/null; }
up() { sleep 6; systemctl is-active --quiet "$1"; }

app=mautrix_slack; c=/var/www/$app/config.yaml
echo "### 1. media signing key: new split settings, never in clear in the logs"
yunohost app upgrade $app -F -f $T/${app}_ynh >/dev/null 2>&1 || ko "upgrade failed"
[ -z "$(yunohost app setting $app direct_media_server_key)" ] && ok "old one-piece setting removed" || ko "old setting still there"
seed=$(yunohost app setting $app direct_media_seed_key); id=$(yunohost app setting $app direct_media_key_id)
[ ${#seed} -ge 40 ] && [ ${#id} = 6 ] && ok "new key id + seed set" || ko "new key missing"
grep -qF "server_key: ed25519 $id $seed" $c && ok "config.yaml has the full key" || ko "config.yaml key wrong"
n=$(grep -lF -- "$seed" /var/log/yunohost/operations/*.log 2>/dev/null | wc -l)
[ "$n" = 0 ] && ok "seed in no operation log" || ko "seed in clear in $n operation logs"
up $app && ok "bridge active" || ko "bridge not active"

echo "### 2. quotes in free text options"
yunohost app config set $app main.bridge.ghost_displayname_template -v "{{.Name}} (l'ami)" >/dev/null 2>&1 || ko "panel refused"
yunohost app config set $app main.bot.displayname -v "Robot d'Slack: #1" >/dev/null 2>&1 || ko "panel refused displayname"
yaml_ok $app && ok "config.yaml valid after panel" || ko "config.yaml invalid after panel"
grep -q "displayname_template: '{{.Name}} (l''ami)'" $c && ok "template written as YAML" || ko "template not written"
grep -q "displayname: 'Robot d''Slack: #1'" $c && ok "bot name written as YAML" || ko "bot name not written"
up $app && ok "bridge active" || ko "bridge not active"
yunohost app upgrade $app -F -f $T/${app}_ynh >/dev/null 2>&1 || ko "upgrade failed"
yaml_ok $app && grep -q "(l''ami)" $c && grep -q "Robot d''Slack: #1" $c && ok "kept and valid after upgrade" || ko "lost or invalid after upgrade"
up $app && ok "bridge active after upgrade" || ko "bridge not active after upgrade"

echo "### 3. inputs rejected"
yunohost app config set $app main.bot.avatar -v "javascript:alert(1)" >/dev/null 2>&1 && ko "bad avatar accepted" || ok "bad avatar refused"
yunohost app config set $app main.permissions.listuser -v "$DOMAIN, @x:y\": admin" >/dev/null 2>&1 && ko "bad permission accepted" || ok "bad permission refused"
yunohost app config set $app main.bot.botname -v 'bad/name' >/dev/null 2>&1 && ko "bad bot name accepted" || ok "bad bot name refused"
grep -q '"@x:y' $c && ko "bad permission written" || ok "config.yaml untouched"
yaml_ok $app && up $app && ok "bridge still fine" || ko "bridge broken"
# back to defaults
yunohost app config set $app main.bridge.ghost_displayname_template -v '{{or .Profile.DisplayName .Profile.RealName .Name}}{{if .IsBot}} (bot){{end}}' >/dev/null 2>&1
yunohost app config set $app main.bot.displayname -v 'Slack bridge bot' >/dev/null 2>&1

echo "### 4. remove deletes the config copies kept by YunoHost"
z=mautrix_zulip
yunohost app upgrade $z -F -f $T/${z}_ynh >/dev/null 2>&1 || ko "zulip upgrade failed"
echo "# manual edit" >> /var/www/$z/config.yaml
yunohost app upgrade $z -F -f $T/${z}_ynh >/dev/null 2>&1
ls /var/cache/yunohost/appconfbackup/var/www/$z/ >/dev/null 2>&1 && ok "a copy exists before removal" || echo "  (no copy was made)"
yunohost app remove $z --purge >/dev/null 2>&1
[ -e /var/cache/yunohost/appconfbackup/var/www/$z ] && ko "copies left after removal" || ok "no copy left after removal"

echo "### result: $([ $FAIL = 0 ] && echo ALL OK || echo FAILURES)"
