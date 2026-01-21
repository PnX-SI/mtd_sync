# Plugin comportant les fonctionnalités pour l'instance depobio

Pour l'instance depobio, il y a besoin de faire une gestion particulière dans le cas de la clôture d'un cadre d'aquisition.
Ce plugin permet de configurer l'envoi d'email dans le cadre de cette clôture.

## Get Started

### Requis

- GeoNature >= 2.16.0

### Installation

```sh
cd <cheminVersVotreGeoNature>
source backend/venv/bin/activate
pip install git+https://github.com/PnX-SI/gn_plugin_depobio
```

### Configuration

Pour configurer le plugin, ajouter un fichier de configuration `gn_plugin_depobio.toml` dans le dossier `config` de votre GeoNature. Un exemple est accessible dans le fichier `gn_plugin_depobio.toml.example`.

Il faut aussi dans la configuration de GeoNature, mettre la variable `EXTENDED_AF_PUBLISH_ROUTE_NAME` égal à `plugin_depobio.extended_af_publish`, pour que lors de la clôture du cadre d'acquisition la route du plugin soit appelé, et la variable `ENABLE_CLOSE_AF` à true pour activer la clôture des cadres d'acquisition.

Les variables de configurations sont définies dans le tableau suivant :

| Variable                           | Type   | Description                                                                                                   |
| ---------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------- |
| `MAIL_SUBJECT_AF_CLOSED_BASE`      | string | Sujet de l'email envoyé lors de la clôture d'un cadre d'acquisition                                           |
| `MAIL_CONTENT_AF_CLOSED_ADDITION`  | string | Contenue additionel ajouté à l'email lors de la clôture d'un cadre d'acquisition                              |
| `MAIL_CONTENT_AF_CLOSED_PDF`       | string | Phrase ajouté à l'email lors de la clôture d'un cadre d'acquisition pour présenter le liens du pdf de clôture |
| `MAIL_CONTENT_AF_CLOSED_GREETINGS` | string | Salutations ajoutée à la fin de l'email envoyé lors de la clôture d'un cadre d'acquisition                    |
