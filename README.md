# mautrix bridge factory for YunoHost

One template, one settings file, many packages. This repository renders the YunoHost packages of
[mautrix](https://github.com/mautrix) bridgev2 bridges (written in Go) from a single reference package, so a fix
made once lands in every bridge.

| | |
|---|---|
| `template/` | the reference package, with `@@TOKEN@@` markers, `@@if feature@@ … @@endif@@` blocks and `@@NETOPTS_*@@` slots |
| `bridges.toml` | one entry per bridge: name, upstream repo, binary, version, bot, port, network-specific options (documented at the top of the file) |
| `bridges/<id>/` | hand-written texts that replace the generated ones (README, `doc/…`) |
| `build.py [id …]` | renders `../mautrix_<id>_ynh` in place (the package keeps its own git history); `FACTORY_OUT=<dir>` renders elsewhere, to compare |
| `tools/factory-test.sh`, `tools/security-test.sh` | full test cycles, run as root on a test YunoHost server with Synapse |
| `tools/make_template.py` | one-off script that turned `mautrix_meta_ynh` into `template/`, kept for the record |
| `logos/` | logo recipe: the catalog's mautrix logo with a small badge per network |

Packages rendered today: [Messenger](https://github.com/EpicTGuy/mautrix_meta_ynh),
[Instagram](https://github.com/EpicTGuy/mautrix_instagram_ynh),
[Google Messages](https://github.com/EpicTGuy/mautrix_gmessages_ynh),
[Slack](https://github.com/EpicTGuy/mautrix_slack_ynh), [X / Twitter](https://github.com/EpicTGuy/mautrix_twitter_ynh),
[LinkedIn](https://github.com/EpicTGuy/mautrix_linkedin_ynh), [Bluesky](https://github.com/EpicTGuy/mautrix_bluesky_ynh),
[Google Voice](https://github.com/EpicTGuy/mautrix_gvoice_ynh), [Zulip](https://github.com/EpicTGuy/mautrix_zulip_ynh).

The existing YunoHost-Apps packages (WhatsApp, Telegram, Signal, Discord) are not rendered from here. The same
method could keep them aligned too; see
[mautrix_telegram_ynh#90](https://github.com/YunoHost-Apps/mautrix_telegram_ynh/issues/90).

## What the template gives every bridge

- Packaging v2, helpers 2.1.
- `config.yaml` rebuilt from the upstream example configs at the released version: the network part comes from
  the bridge (`pkg/connector/example-config.yaml` or `network_config`), the common part from
  `bridgev2/matrix/mxmain/example-config.yaml` of mautrix-go at the version in the bridge's `go.mod`.
- Settings and secrets kept across upgrades; config panel options (`network_options`) stored as settings, so they
  survive upgrades.
- Bridge run with `-n` (it never rewrites its own config), install dir owned by root, hardened systemd unit
  (`systemd-analyze security` ≈ 1.3).
- Double puppeting enabled automatically when a shared `doublepuppet` appservice is registered in Synapse.
- Release binaries checked against `sha256sums.txt` **and** against the digest GitHub computed at upload; the build
  stops on any mismatch.

## Changing a package

Edit `template/`, `bridges.toml` or `bridges/<id>/`, never a rendered package. Then:

```sh
FACTORY_OUT=/tmp/x python3 build.py      # render elsewhere and diff with the current packages
python3 build.py                         # render in place
```

A published package that changes without a new bridge version: bump `revision` (→ `~ynh2`, …).

Adding a bridge = one entry in `bridges.toml` (plus `bridges/<id>/` if the generated texts are not enough).

## Tests

`tools/factory-test.sh`: install of the previous version, settings changed, upgrade ×2 (settings kept, config
unchanged except appservice tokens), backup / removal / restore, systemd exposure.
`tools/security-test.sh`: the fixes listed in [SECURITY-REVIEW.md](SECURITY-REVIEW.md).

## License

AGPL-3.0, like the packages.
