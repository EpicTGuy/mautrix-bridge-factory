## Connexion à Messenger

Dans votre client Matrix, ouvrez une discussion privée avec `@__BOTNAME__:__SERVER_NAME__` (si le compte n'apparaît pas dans l'annuaire, tapez l'identifiant complet). Utilisez si possible une discussion **chiffrée**, puisque vous y enverrez vos identifiants. La passerelle supprime d'elle-même les messages contenant votre mot de passe ou vos cookies.

### Méthode 1 : identifiant et mot de passe (recommandée)

1. Envoyez `login messenger-lite` (ou `login messenger-lite-android`).
2. Répondez au robot : votre e-mail ou numéro Facebook, puis votre mot de passe, puis le code de double authentification si demandé.

### Méthode 2 : cookies du navigateur

1. Envoyez `login messenger` (ou `login facebook`).
2. Dans un navigateur de bureau connecté à messenger.com (ou facebook.com), ouvrez les outils de développement (`F12` ou `Cmd+Option+I`) → onglet **Réseau**, rechargez la page, clic droit sur une requête vers le site → **Copier** → **Copier en tant que cURL**, et collez le résultat en réponse au robot.
3. **Ne vous déconnectez pas** de cette session du navigateur (cela invaliderait la session de la passerelle).

Une fois connecté, vos conversations apparaissent comme des salons Matrix. Commandes utiles : `help`, `list-logins`, `logout <ID de connexion>`. Journaux : `sudo yunohost service log __APP__`.
