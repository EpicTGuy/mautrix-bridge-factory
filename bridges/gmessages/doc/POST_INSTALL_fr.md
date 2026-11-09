## Appairer votre téléphone

Dans votre client Matrix, ouvrez une discussion privée avec `@__BOTNAME__:__SERVER_NAME__` (si le compte n'apparaît pas dans l'annuaire, tapez l'identifiant complet).

1. Envoyez `login qr`. Le robot envoie un QR code.
2. Sur le téléphone, ouvrez Google Messages → votre photo de profil → **Association d'appareils** → **Lecteur de code QR**, et scannez-le.

Vos conversations SMS/RCS apparaissent ensuite comme des salons Matrix. Gardez le téléphone connecté à Internet.

Si vous utilisez aussi messages.google.com dans un navigateur, la passerelle peut perdre la session active : envoyez `set-active` au robot pour la reprendre.

Commandes utiles : `help`, `list-logins`, `logout <ID de connexion>`. Journaux : `sudo yunohost service log __APP__`.
