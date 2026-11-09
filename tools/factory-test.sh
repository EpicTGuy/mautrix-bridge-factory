#!/bin/bash
# Run as root on a test YunoHost server with Synapse: test the factory-rendered meta / instagram / gmessages packages.
# /root/factory-test/<app>_ynh = new package, /root/factory-test/old/<app>_ynh = previous commit.
set -u
T=${T:-/root/factory-test}
DOMAIN=${DOMAIN:?set DOMAIN to the Synapse server name}
ARGS="synapse_instance=synapse&encryption=true&botadmin=@admin:$DOMAIN&botusers=$DOMAIN&enable_relaybot=true"
ok() { echo "  OK  $*"; }
ko() { echo "  KO  $*"; FAIL=1; }
FAIL=0

check() {  # app key expected (setting) ; config grep pattern
    local app=$1 key=$2 want=$3 pat=$4
    got=$(yunohost app setting "$app" "$key")
    [ "$got" = "$want" ] && ok "$app setting $key=$got" || ko "$app setting $key='$got' (want '$want')"
    grep -qF -- "$pat" /var/www/$app/config.yaml && ok "$app config has: $pat" || ko "$app config lacks: $pat"
}

active() {
    sleep 5
    systemctl is-active --quiet "$1" && ok "$1 active" || { ko "$1 not active"; journalctl -u "$1" -n 20 --no-pager; }
    echo "  exposure $(systemd-analyze security "$1" 2>/dev/null | tail -1 | grep -o '[0-9.]* [A-Z]*' | head -1)"
}

echo "### instagram: upgrade in place"
yunohost app config set mautrix_instagram advanced.network.disable_typing -v true >/dev/null
yunohost app config set mautrix_instagram main.bridge.ghost_displayname_template -v '{{.Username}} (IG)' >/dev/null
yunohost app upgrade mautrix_instagram -F -f $T/mautrix_instagram_ynh >/dev/null 2>$T/ig-upgrade.log || ko "ig upgrade failed (see ig-upgrade.log)"
check mautrix_instagram disable_typing true 'disable_typing: true'
check mautrix_instagram ghost_displayname_template '{{.Username}} (IG)' "displayname_template: '{{.Username}} (IG)'"
check mautrix_instagram thread_backfill_batch_count 0 'batch_count: 0'
active mautrix_instagram
yunohost app config set mautrix_instagram advanced.network.disable_typing -v false >/dev/null
yunohost app config set mautrix_instagram main.bridge.ghost_displayname_template -v '{{or .DisplayName .Username "Unknown user"}}' >/dev/null

for app in mautrix_meta mautrix_gmessages; do
    echo "### $app: old install -> settings -> upgrade -> backup/restore"
    bot=${app#mautrix_}; [ $bot = meta ] && bot=facebook
    yunohost app install $T/old/${app}_ynh -a "$ARGS&botname=${bot}bot" --force >/dev/null 2>$T/$app-install.log || { ko "$app old install failed"; continue; }
    if [ $app = mautrix_meta ]; then
        yunohost app config set $app advanced.network.send_presence_on_typing -v true >/dev/null
        yunohost app config set $app main.bridge.thread_backfill_batch_count -v 0 >/dev/null
        yunohost app config set $app main.bridge.ghost_displayname_template -v '{{.DisplayName}} (FB)' >/dev/null
    else
        yunohost app config set $app advanced.network.aggressive_reconnect -v true >/dev/null
        yunohost app config set $app advanced.network.displayname_template -v '{{.FullName}} (SMS)' >/dev/null
    fi
    yunohost app config set $app main.bridge.backfill_max_initial_messages -v 20 >/dev/null 2>&1 || true
    yunohost app upgrade $app -F -f $T/${app}_ynh >/dev/null 2>$T/$app-upgrade.log || ko "$app upgrade failed (see $app-upgrade.log)"
    if [ $app = mautrix_meta ]; then
        check $app send_presence_on_typing true 'send_presence_on_typing: true'
        check $app thread_backfill_batch_count 0 'batch_count: 0'
        check $app ghost_displayname_template '{{.DisplayName}} (FB)' "displayname_template: '{{.DisplayName}} (FB)'"
        check $app backfill_max_initial_messages 20 'max_initial_messages: 20'
    else
        check $app aggressive_reconnect true 'aggressive_reconnect: true'
        check $app ghost_displayname_template '{{.FullName}} (SMS)' "displayname_template: '{{.FullName}} (SMS)'"
        grep -q 'os: Matrix (YunoHost)' /var/www/$app/config.yaml && ok "device name kept" || ko "device name lost"
    fi
    grep -q 'shared_secret: generate\|signing_key: generate' /var/www/$app/config.yaml && ko "$app secrets left to 'generate'" || ok "$app secrets fixed"
    stat -c '%U:%G %a %n' /var/log/$app
    stat -c '%U:%G %a %n' /var/www/$app /var/www/$app/config.yaml
    active $app
    # second upgrade: nothing must move
    cfg1=$(cat /var/www/$app/config.yaml)
    yunohost app upgrade $app -F -f $T/${app}_ynh >/dev/null 2>>$T/$app-upgrade.log || ko "$app 2nd upgrade failed"
    # the registration (-g) gives new appservice tokens at each upgrade: anything else must stay
    other=$(diff <(echo "$cfg1") /var/www/$app/config.yaml | grep '^[<>]' | grep -vc '_token: ')
    [ "$other" = 0 ] && ok "$app config unchanged by 2nd upgrade (except appservice tokens)" || ko "$app config changed by 2nd upgrade ($other lines)"
    # backup / restore
    yunohost backup create --apps $app -n factorytest-$app >/dev/null 2>&1 && ok "$app backup" || ko "$app backup"
    yunohost app remove $app --purge >/dev/null 2>&1
    yunohost backup restore factorytest-$app --apps $app --force >/dev/null 2>$T/$app-restore.log && ok "$app restore" || ko "$app restore"
    stat -c '%U:%G %a %n' /var/log/$app
    active $app
    [ $app = mautrix_meta ] && check $app send_presence_on_typing true 'send_presence_on_typing: true'
    [ $app = mautrix_gmessages ] && check $app aggressive_reconnect true 'aggressive_reconnect: true'
    yunohost app remove $app --purge >/dev/null 2>&1 && ok "$app removed"
    yunohost backup delete factorytest-$app >/dev/null 2>&1
done
echo "### result: $([ $FAIL = 0 ] && echo ALL OK || echo FAILURES)"
