### Configuration de la passerelle
La passerelle est [configurée avec les paramètres standards adaptés pour votre YunoHost et l'instance Matrix-Synapse sélectionnée](https://github.com/YunoHost-Apps/@@APP@@_ynh/blob/master/conf/config.yaml).
Une configuration plus fine peut être effectuée en utilisant le panneau de configuration existant dans le panneau d'administration de Yunohost ou en modifiant le fichier de configuration suivant avec SSH:
```/var/www/@@APP@@/config.yaml```
puis en redémarrant le service @@APP@@.

⚠️ `config.yaml` est régénéré depuis le modèle du paquet à chaque mise à jour : les modifications à la main ne sont gardées que dans une copie de sauvegarde. Utilisez le panneau de configuration pour les options ci-dessous, elles sont conservées d'une mise à jour à l'autre.

#### Permissions des utilisateurs
Rôles : `relay` < `user` < `admin`. On peut donner un identifiant Matrix (`@jean:exemple.fr`), un nom de serveur (`exemple.fr`) ou `*`. Chaque entrée ne doit apparaître qu'une fois : ne donnez pas au même compte les rôles `user` et `admin`.


#### Options conservées aux mises à jour (panneau de configuration, `Main -> Puppetting Bridge Settings`)
@@if backfill@@
- **Importer toutes les anciennes conversations @@SHORT@@ ?** Désactivé par défaut : seules les conversations qui reçoivent de nouveaux messages apparaissent. Activé, toutes les conversations sont importées au prochain démarrage de la passerelle, une page toutes les 2 secondes.
@@endif@@
@@if ghost@@
- **Nom affiché des contacts @@SHORT@@ dans Matrix** : modèle Go, par exemple `@@GHOST_EXAMPLE@@` pour reconnaître les contacts @@SHORT@@ d'un coup d'œil.
@@endif@@
- **Nombre d'anciens messages importés dans une nouvelle conversation** : 50 par défaut, pour les conversations pontées à partir de maintenant.

Les secrets de la passerelle (secret de l'API de provisionnement, clés de signature des médias) sont générés une fois puis gardés dans les réglages de l'application.

#### End-to-bridge encryption
Le robot peut éventuellement chiffrer les messages entre les utilisateurs de Matrix et la passarelle pour cacher les messages du serveur domestique. L'utilisation de Postgres est fortement recommandée lors de l'utilisation du chiffrement end-to-bridge.

Si vous voulez l'activer, allez dans la section `Privacy -> Portal Rooms & Encryption Settings` du panneau de configuration. Si vous activez `Allow Encryption between Matrix Client and Bridge Server?`, la passarelle n'activera pas le cryptage d'elle-même, mais fonctionnera dans les salles cryptées.
Sinon, deux autres options apparaissent, `Force-enable Encryption in all Portal Rooms the Bridge creates?` qui activera automatiquement le cryptage dans les nouveaux portails et `Require encryption?` qui imposera le cryptage sur tous les messages que vous envoyez (ce qui fera que le robot abandonnera tous les messages non cryptés à l'avenir).

Il est également possible de le configurer dans le fichier YAML de configuration du robot dans la section `bridge: encryption`.