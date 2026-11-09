# Mautrix Google Messages for YunoHost

Matrix / Synapse puppeting bridge for Google Messages (SMS, MMS and RCS of an Android phone), packaged for [YunoHost](https://yunohost.org).
Upstream bridge: <https://github.com/mautrix/gmessages> (mautrix-gmessages v26.10, Go / bridgev2).

## ⚠️ Status: looking for testers

The YunoHost side of this package is tested on YunoHost 12 / Debian 12: install, upgrades with settings kept, backup / restore, registration with Synapse, config panel.

**Feedback on real use is welcome**: if you have Google Messages as the default SMS app of an Android phone, please install it and report how it went in the issues (pairing, sending/receiving SMS, MMS, RCS). Packages confirmed by testers will be proposed to the YunoHost catalog.

Notes:
- iPhone is not supported (Google Messages is Android only).
- On Android without Google services (e.g. /e/OS with microG), the Google Messages app can be installed and SMS/MMS usually work, but RCS depends on Google services. Messages still go through Google's servers between the phone and the bridge.

## Install

```bash
sudo yunohost app install https://github.com/EpicTGuy/mautrix_gmessages_ynh
```

Then, in your Matrix client, open a chat with the bot, send `login qr` and scan the QR code from Google Messages → profile picture → **Device pairing**.

## Features of this package

- Config generated from the upstream example config (v26.10), with a config panel for the main settings: permissions, encryption, display name of contacts, number of past messages imported in new chats, taking back the active session automatically.
- Settings and bridge secrets are kept across upgrades (`config.yaml` is regenerated from the template, the bridge runs with `-n` and never rewrites it, so upgrades don't print its diff).
- Hardened: the binary and `config.yaml` belong to root and are only readable by the bridge user; strict systemd sandbox (`systemd-analyze security` ≈ 1.3); listens on 127.0.0.1 only.
- The bridge shows up as "Matrix (YunoHost)" in the paired devices of the phone.
- Bridge permissions handled from the install questions and the config panel (no duplicate entries when the same account is admin and user).
- Double puppeting enabled automatically when a shared `doublepuppet` appservice is registered in Synapse (`/etc/matrix-<synapse instance>/app-service/doublepuppet.yaml`, see <https://docs.mau.fi/bridges/general/double-puppeting.html>).

Based on the [mautrix_whatsapp_ynh](https://github.com/YunoHost-Apps/mautrix_whatsapp_ynh) package. License: AGPL-3.0-or-later.
