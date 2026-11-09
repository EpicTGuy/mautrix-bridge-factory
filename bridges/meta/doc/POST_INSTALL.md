## Log in to Messenger

In your Matrix client, start a direct chat with `@__BOTNAME__:__SERVER_NAME__` (if it isn't found in the user directory, type the full ID). Use an **encrypted** chat if possible, since you will send credentials in it. The bridge deletes the messages containing your password or cookies by itself.

### Method 1: username and password (recommended)

1. Send `login messenger-lite` (or `login messenger-lite-android`).
2. Answer the bot: your Facebook email or phone number, then your password, then the two-factor code if asked.

### Method 2: browser cookies

1. Send `login messenger` (or `login facebook`).
2. In a desktop browser logged in to messenger.com (or facebook.com), open the developer tools (`F12` or `Cmd+Option+I`) → **Network** tab, reload the page, right-click any request to the site → **Copy** → **Copy as cURL**, and paste it as a reply to the bot.
3. **Don't log out** of that browser session (it would invalidate the bridge session).

Once logged in, your conversations appear as Matrix rooms. Useful commands: `help`, `list-logins`, `logout <login ID>`. Logs: `sudo yunohost service log __APP__`.
