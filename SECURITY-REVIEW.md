# Security and reliability review (November 2026)

Scope: the packages rendered by the factory, the factory itself (`build.py`) and its test scripts.

## Method

1. **Threat model.** Assets: network sessions (cookies, tokens), messages, appservice tokens, the shared
   double-puppeting token. Attackers: a malicious contact on a bridged network, another local system account
   (a compromised app), the supply chain (upstream binaries), leaks through logs or backups, admin mistakes in the
   config panel.
2. **Static analysis.** shellcheck (all levels) on the rendered scripts; line-by-line reading of `_common.sh`,
   install, upgrade, config, backup, restore, remove. Entry points: install questions and config panel values
   written into `config.yaml`.
3. **Secrets.** Full git history of the packages; bridge logs; YunoHost operation logs, compared with the real
   values without printing them.
4. **Supply chain.** sha256 of every binary in the manifests compared with the digest GitHub computed at upload,
   independently of the `sha256sums.txt` published upstream.
5. **Real runs on a test server.** Listening ports, file modes (config, appservice registrations, settings,
   logs, backups, config copies), systemd exposure, crafted panel values (quotes, backslashes, forged permission
   entries, bot name with `/`, non-mxc avatar), install → upgrade ×2 → backup → removal → restore cycles.

## Findings

| # | Severity | Finding | Status |
|---|---|---|---|
| 1 | Medium | An apostrophe in the contact or bot display name (`ynh_write_var_in_file` writes `\'`, invalid YAML) made `config.yaml` invalid; the bridge stopped at the next restart. The bot name at install was not quoted. | **Fixed**: single-quoted YAML strings with doubled quotes (`write_yaml_string`, `yaml_quote_settings`) |
| 2 | Medium | `direct_media.server_key` ("ed25519 id seed", with spaces) was printed in clear in the YunoHost install log: YunoHost only redacts values without spaces, and those logs are readable by local accounts and shareable (`yunohost log share`). No effect while direct media is disabled (default). | **Fixed**: two settings without spaces; the old key is dropped and replaced at upgrade |
| 3 | Medium | Copies of `config.yaml` (secrets included) stay in `/var/cache/yunohost/appconfbackup` after removal; their owner UID is reused by the next app user (seen: a removed bridge's copy readable by another bridge's account). | **Fixed**: `remove` deletes them. YunoHost core issue, to report |
| 4 | Medium | Restore recreated `/var/log/<app>` owned by root: the bridge could not start. Same code in mautrix_whatsapp_ynh. | **Fixed**; upstream PR to propose |
| 5 | Low | Permission entries from the panel written without validation; bot name and avatar unchecked. | **Fixed**: clear refusal (Matrix ID, server name or `*`; `^[a-z0-9._=-]+$`; `mxc://…`) |
| 6 | Low | The factory trusted only the release's `sha256sums.txt`. | **Fixed**: compared with the GitHub digest, build stops on mismatch (27/27 match) |
| 7 | Info | Appservice tokens regenerated at each upgrade (`-g`): harmless, Synapse gets the new ones. | Accepted |
| 8 | Info | YunoHost backups readable by the `admins` group (core behaviour). | Accepted |

Checked without findings: every bridge listens on 127.0.0.1; appservice registrations 600 synapse; settings 400
root; `config.yaml` 640 root:app; logs 600; systemd exposure 1.3; no secret in the git history (the occurrences
found are upstream examples); no secret in bridge logs; no GitHub workflow in the packages.

## Tests

`tools/factory-test.sh` (full cycles) and `tools/security-test.sh` (findings 1, 2, 3, 5): all OK.
