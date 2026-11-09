## Log in to Instagram

Instagram has no QR code login. Two methods are available, both from the chat with the bot.

In your Matrix client, start a direct chat with `@__BOTNAME__:__SERVER_NAME__` (if it isn't found in the user directory, type the full ID). Use an **encrypted** chat if possible, since you will send credentials in it.

### Method 1: username and password (recommended)

1. Send `login instagram-password`.
2. Answer the bot: your Instagram username (or email), then your password.
3. If asked, send the two-factor code, or approve the sign-in from the Instagram notification on your phone.
4. Delete your messages containing the password from the chat.

If Instagram asks for a CAPTCHA, this method can't complete from the chat: use method 2.

### Method 2: browser cookies

1. Send `login instagram`.
2. In a desktop browser logged in to instagram.com, open the developer tools (`F12` or `Cmd+Option+I`) → **Network** tab, reload the page, right-click any request to `www.instagram.com` → **Copy** → **Copy as cURL**, and paste it as a reply to the bot.
3. Delete the message containing the cookies, and **don't log out** of instagram.com in that browser (it would invalidate the session).

Once logged in, your conversations appear as Matrix rooms.

Useful commands (in the bot chat): `help`, `list-logins`, `logout <login ID>`.

If something doesn't work: `sudo yunohost service log __APP__` or `/var/log/__APP__/__APP__.log`.
