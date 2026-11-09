## Connexion à Instagram

Instagram ne propose pas de connexion par QR code. Deux méthodes sont disponibles, toutes deux depuis la discussion avec le robot.

Dans votre client Matrix, ouvrez une discussion privée avec `@__BOTNAME__:__SERVER_NAME__` (si le compte n'apparaît pas dans l'annuaire, tapez l'identifiant complet). Utilisez si possible une discussion **chiffrée**, puisque vous y enverrez vos identifiants.

### Méthode 1 : identifiant et mot de passe (recommandée)

1. Envoyez `login instagram-password`.
2. Répondez au robot : votre identifiant Instagram (ou e-mail), puis votre mot de passe.
3. Si demandé, envoyez le code de double authentification, ou validez la connexion depuis la notification Instagram sur votre téléphone.
4. Supprimez de la discussion vos messages contenant le mot de passe.

Si Instagram demande un CAPTCHA, cette méthode ne peut pas aboutir depuis la discussion : utilisez la méthode 2.

### Méthode 2 : cookies du navigateur

1. Envoyez `login instagram`.
2. Dans un navigateur de bureau connecté à instagram.com, ouvrez les outils de développement (`F12` ou `Cmd+Option+I`) → onglet **Réseau**, rechargez la page, clic droit sur une requête vers `www.instagram.com` → **Copier** → **Copier en tant que cURL**, et collez le résultat en réponse au robot.
3. Supprimez le message contenant les cookies, et **ne vous déconnectez pas** d'instagram.com dans ce navigateur (cela invaliderait la session).

Une fois connecté, vos conversations apparaissent comme des salons Matrix.

Commandes utiles (dans la discussion avec le robot) : `help`, `list-logins`, `logout <ID de connexion>`.

En cas de problème : `sudo yunohost service log __APP__` ou `/var/log/__APP__/__APP__.log`.
