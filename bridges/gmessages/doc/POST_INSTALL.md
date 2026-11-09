## Pair your phone

In your Matrix client, start a direct chat with `@__BOTNAME__:__SERVER_NAME__` (if it isn't found in the user directory, type the full ID).

1. Send `login qr`. The bot sends a QR code.
2. On your phone, open Google Messages → your profile picture → **Device pairing** → **QR code scanner**, and scan it.

Your SMS/RCS conversations then appear as Matrix rooms. Keep the phone connected to the internet.

If you also use messages.google.com in a browser, the bridge may lose the active session: send `set-active` to the bot to take it back.

Useful commands: `help`, `list-logins`, `logout <login ID>`. Logs: `sudo yunohost service log __APP__`.
