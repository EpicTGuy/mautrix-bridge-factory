#!/bin/bash

#=================================================
# COMMON VARIABLES AND CUSTOM HELPERS
#=================================================

get_synapse_db_name() {
	# Parameters: synapse instance identifier
	# Returns: database name
	ynh_app_setting_get --app="$1" --key=db_name
}

# Value of a key in a top-level section of the current config.yaml, without quotes.
# Empty if there is no config yet or if the bridge still has to generate it.
read_bridge_value() {
    # Parameters: key, top-level section
    [ -f "$install_dir/config.yaml" ] || return 0
    local value
    value=$(sed -n "/^$2:/,/^[a-z_]*:/p" "$install_dir/config.yaml" | grep -m1 -E "^ +$1:" \
        | sed -E "s/^ +$1: *//; s/^'(.*)'\$/\1/; s/^\"(.*)\"\$/\1/")
    [ "$value" = "generate" ] || [ "$value" = "null" ] || echo "$value"
}

# Secrets and admin choices of config.yaml kept as app settings, so that config.yaml
# can be regenerated from the template at each upgrade without losing them.
# Existing values of config.yaml are taken over the first time.
ensure_bridge_settings() {
    provisioning_shared_secret=$(ynh_app_setting_get --key=provisioning_shared_secret)
    [ -n "$provisioning_shared_secret" ] || provisioning_shared_secret=$(read_bridge_value shared_secret provisioning)
    [ -n "$provisioning_shared_secret" ] || provisioning_shared_secret=$(ynh_string_random --length=64)

    public_media_signing_key=$(ynh_app_setting_get --key=public_media_signing_key)
    [ -n "$public_media_signing_key" ] || public_media_signing_key=$(read_bridge_value signing_key public_media)
    [ -n "$public_media_signing_key" ] || public_media_signing_key=$(ynh_string_random --length=64)

    # direct_media.server_key = "ed25519 <key id> <unpadded base64 seed>", kept as two settings without
    # spaces: YunoHost only redacts secrets without spaces from its logs. The former single setting was
    # logged in clear when generated, so it is dropped (unused while direct_media is disabled) for a new key.
    direct_media_key_id=$(ynh_app_setting_get --key=direct_media_key_id)
    [ -n "$direct_media_key_id" ] || direct_media_key_id=$(ynh_string_random --length=6)
    direct_media_seed_key=$(ynh_app_setting_get --key=direct_media_seed_key)
    [ -n "$direct_media_seed_key" ] || direct_media_seed_key=$(head -c 32 /dev/urandom | base64 | tr -d '=')
    ynh_app_setting_delete --key=direct_media_server_key

    ghost_displayname_template=$(ynh_app_setting_get --key=ghost_displayname_template)
    [ -n "$ghost_displayname_template" ] || ghost_displayname_template=$(read_bridge_value displayname_template network)
    [ -n "$ghost_displayname_template" ] || ghost_displayname_template='@@GHOST_DEFAULT@@'

    backfill_max_initial_messages=$(ynh_app_setting_get --key=backfill_max_initial_messages)
    [ -n "$backfill_max_initial_messages" ] || backfill_max_initial_messages=$(read_bridge_value max_initial_messages backfill)
    [ -n "$backfill_max_initial_messages" ] || backfill_max_initial_messages=50

    ynh_app_setting_set --key=provisioning_shared_secret --value="$provisioning_shared_secret"
    ynh_app_setting_set --key=public_media_signing_key --value="$public_media_signing_key"
    ynh_app_setting_set --key=direct_media_key_id --value="$direct_media_key_id"
    ynh_app_setting_set --key=direct_media_seed_key --value="$direct_media_seed_key"
    ynh_app_setting_set --key=ghost_displayname_template --value="$ghost_displayname_template"
    ynh_app_setting_set --key=backfill_max_initial_messages --value="$backfill_max_initial_messages"
    yaml_quote_settings
}

# Free text settings go to config.yaml as single-quoted YAML strings: a quote is doubled there
# (a name like "Robot d'Instagram" would otherwise make config.yaml invalid and stop the bridge).
yaml_quote_settings() {
    ghost_displayname_yaml=${ghost_displayname_template//\'/\'\'}
    displayname_yaml=${displayname//\'/\'\'}
}

# Write a single-quoted YAML string in config.yaml (ynh_write_var_in_file escapes quotes as \',
# which YAML rejects). Parameters: top-level section, key (first one in that section), value
write_yaml_string() {
    YAML_VALUE="$3" python3 - "$install_dir/config.yaml" "$1" "$2" <<'PY'
import os, re, sys
path, section, key = sys.argv[1:4]
value = "'" + os.environ["YAML_VALUE"].replace("\n", " ").replace("'", "''") + "'"
lines = open(path).read().split("\n")
inside = False
for i, line in enumerate(lines):
    if re.match(r"^[a-z_]+:", line):
        inside = line.startswith(section + ":")
        continue
    m = re.match(r"^(\s+" + re.escape(key) + r":)(\s|$)", line)
    if inside and m:
        lines[i] = m.group(1) + " " + value
        break
else:
    sys.exit(f"{section}.{key} not found in {path}")
open(path, "w").write("\n".join(lines))
PY
}

# The bridge runs with -n (it never writes config.yaml) and needs no write access to its
# install dir: the binary and the config belong to root, the app user can only read them.
secure_install_dir() {
    chown root:"$app" "$install_dir" "$install_dir/@@BINARY@@" "$install_dir/config.yaml"
    chmod 750 "$install_dir" "$install_dir/@@BINARY@@"
    chmod 640 "$install_dir/config.yaml"
}

# Enable double puppeting if the admin registered the shared "doublepuppet" appservice in Synapse
# (https://docs.mau.fi/bridges/general/double-puppeting.html). Nothing happens otherwise.
configure_double_puppet() {
    local doublepuppet_file="/etc/matrix-$synapse_instance/app-service/doublepuppet.yaml"
    if [ -f "$doublepuppet_file" ]; then
        local as_token
        as_token=$(grep "^as_token:" "$doublepuppet_file" | cut -d' ' -f2 | tr -d '"')
        if [ -n "$as_token" ]; then
            sed -i "/^double_puppet:/,/^encryption:/{/^        [^ #].*: as_token:/d;}" "$install_dir/config.yaml"
            sed -i "/^double_puppet:/,/^encryption:/{s/^    secrets:.*/    secrets:\n        $server_name: as_token:$as_token/;}" "$install_dir/config.yaml"
            ynh_print_info "Double puppeting enabled using $doublepuppet_file"
        fi
    fi
}

#=================================================
# CONFIG PANEL SETTERS
#=================================================

apply_permissions() {
    set -o noglob # Disable globbing to avoid expansions when passing * as value.
    declare values="list$role"
    newValues="${!values}" # Here we expand the dynamic variable we created in the previous line. ! Does the trick
    newValues="${newValues//\"}"
    # Split on commas only and trim surrounding whitespace, so that a value containing spaces
    # (e.g. a leftover placeholder sentence) is never split into several bogus entries.
    IFS=',' read -r -a rawArray <<< "$newValues"
    usersArray=()
    for user in "${rawArray[@]}"; do
        user="${user#"${user%%[![:space:]]*}"}"
        user="${user%"${user##*[![:space:]]}"}"
        [ -n "$user" ] || continue
        # A Matrix ID (@user:server), a server name or * (anything else would be written as is in config.yaml)
        [[ "$user" == "*" || "$user" =~ ^@[^[:space:]:\"\'\\]+:[A-Za-z0-9.-]+(:[0-9]+)?$ || "$user" =~ ^[A-Za-z0-9.-]+(:[0-9]+)?$ ]] \
            || ynh_die "Invalid entry for role $role: '$user'. Give Matrix IDs (@john:example.com), server names (example.com) or *."
        usersArray+=("$user")
    done

    if [ ${#usersArray[@]} -gt 0 ]
    then
        # Only touch the "permissions:" block of the bridge section (it ends at the top-level "database:" key).
        allDefinedEntries=$(sed -n '/^    permissions:/,/^database:/p' "$install_dir/config.yaml" | sed '1d;$d' | sed '/^ *#/d' | grep -v -E ": \"?$role\"?$" | sed -E 's/^ *"?([^"]*)"?: .*/\1/')
        # Delete everything from the corresponding role to insert the new defined values. This way we also handle deletion of users.
        sed -i -E "/^    permissions:/,/^database:/{/: \"?$role\"?$/d;}" "$install_dir/config.yaml"
        for user in "${usersArray[@]}"
        do
            if grep -q -x -F "${user}" <<< "$allDefinedEntries"
            then
                ynh_print_info "User $user already defined in another role."
            else
                sed -i "/^    permissions:/a \        \\\"$user\\\": $role" "$install_dir/config.yaml" # Whitespaces are needed so that the file can be correctly parsed
            fi
        done
    fi
    set +o noglob

    ynh_print_info "Users with role $role added in $install_dir/config.yaml"
}

set__listuser() {
  role="user"
  ynh_app_setting_set --key=listuser --value="$listuser"
  apply_permissions
  ynh_store_file_checksum "$install_dir/config.yaml"
}

set__listrelay() {
  role="relay"
  ynh_app_setting_set --key=listrelay --value="$listrelay"
  apply_permissions
  ynh_store_file_checksum "$install_dir/config.yaml"
}

set__listadmin() {
  role="admin"
  ynh_app_setting_set --key=listadmin --value="$listadmin"
  apply_permissions
  ynh_store_file_checksum "$install_dir/config.yaml"
}
