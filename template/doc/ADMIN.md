## Configuration of the bridge
The bridge is [roughly configured at installation](https://github.com/YunoHost-Apps/@@APP@@_ynh/blob/master/conf/config.yaml), e.g. allowed admin and user of the bot.
Finer configuration can be done by using the existing config panel in the Yunohost admin panel or by modifying the
following configuration file with SSH:
```/var/www/@@APP@@/config.yaml```
and then restarting the @@APP@@ service.

⚠️ `config.yaml` is regenerated from the package template at each upgrade: manual changes are kept in a backup copy only. Use the config panel for the options below, they are kept across upgrades.

#### User permissions
Roles are `relay` < `user` < `admin`. A Matrix ID (`@john:example.com`), a server name (`example.com`) or `*` can be given. Each entry may only appear once: do not give the same account both `user` and `admin` roles.


#### Options kept across upgrades (config panel, `Main -> Puppetting Bridge Settings`)
@@if backfill@@
- **Import all older @@SHORT@@ chats?** Off by default: only the chats that receive new messages appear. When enabled, every chat is imported at the next bridge start, one page every 2 seconds.
@@endif@@
@@if ghost@@
- **Display name of @@SHORT@@ contacts in Matrix**: Go template, e.g. `@@GHOST_EXAMPLE@@` to recognise @@SHORT@@ contacts at a glance.
@@endif@@
- **How many past messages to import in a new chat?** 50 by default, for chats bridged from now on.

The bridge secrets (provisioning shared secret, media signing keys) are generated once and kept in the app settings.

#### End-to-bridge encryption
The bridge can optionally encrypt messages between Matrix users and the bridge to hide messages from the homeserver. Using Postgres is strongly recommended when using end-to-bridge encryption.

If you want to enable it, go to the config panel section `Privacy -> Portal Rooms & Encryption Settings`. If you enable `Allow Encryption between Matrix Client and Bridge Server?`, the bridge won't enable encryption on its own, but will work in encrypted rooms.
Alternatively two more options will appear, `Force-enable Encryption in all Portal Rooms the Bridge creates?` which will automatically enable encryption in new portals and `Require encryption?` which will enforce encryption on any of the messages that you send (this will make the bridge drop any future unencrypted messages).

There is also the possibity to configure it in the bridge configuration YAML file in the section `bridge: encryption`.