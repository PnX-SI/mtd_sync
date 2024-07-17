# Module de synchronisation avec SINP-Métadonnées

L'INPN met à disposition un [catalogue](https://inpn.mnhn.fr/mtd) des fiches de métadonnées pour décrire le contexte ou cadre d’acquisition de données d’occurrences de taxons (collecte opportuniste, inventaire, suivi…) et les jeux de données associés.
Ce module python permet de synchroniser les méta-données provenant de ce catalogue avec celle d'une instance de [GeoNature](https://github.com/PnX-SI/GeoNature).


## Get Started

### Requis

 - GeoNature >= 2.15.0

### Installation

```sh
cd <cheminVersVotreGeoNature>
source backend/venv/bin/activate
pip install git+https://github.com/PnX-SI/mtd_sync
```

### Configuration

Pour configurer la synchronisation, ajouter un fichier de configuration `mtd_sync.toml` dans le dossier `config` de votre GeoNature. Un exemple est accessible dans le fichier `mtd_sync.toml.example`.

Les variables de configurations sont définies dans le tableau suivant :


| Variable                      | Type                                                                    | Description                                                                                                                                    |
|-------------------------------|-------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| `BASE_URL`                    | string                                                                  | URL de l'API pour récupérer les informations d'un utilisateur dans l'INPN                                                                      |
| `XML_NAMESPACE`               | string                                                                  | Utiliser lors de la lecture des fichiers XML retourner par l'API MTD                                                                           |
| `USER`                        | string                                                                  | Identifiant pour se connecter à l'API permettant de récupérer les informations des utilisateurs de l'INPN                                      |
| `PASSWORD`                    | string                                                                  | Mot de passe pour se connecter à l'API permettant de récupérer les informations des utilisateurs de l'INPN                                     |
| `ID_INSTANCE_FILTER`          | integer                                                                 | Identifiant de l'instance                                                                                                                      |
| `MTD_API_ENDPOINT`            | string                                                                  | URL de l'API du service Métadonnées                                                                                                            |
| `SYNC_LOG_LEVEL`              | string (https://docs.python.org/3/howto/logging.html#logging-to-a-file) | Niveau de verbosité des logs produits par le processus de synchronisation                                                                      |
| `USERS_CAN_SEE_ORGANISM_DATA` | bool                                                                    | Les utilisateurs ajoutés peuvent-ils voir les données des utilisateurs de leur organismes (défini par le groupe indiqué dans `ID_USER_SOCLE_2`)  |
| `JDD_MODULE_CODE_ASSOCIATION` | list[string]                                                            | Liste des modules associées aux nouveaux jeux de données synchronisés                                                                          |
| `ID_PROVIDER_INPN`            | string                                                                  | Identifiant du fournisseur d'identités permettant de se connecter au CAS INPN dans votre GeoNature                                             |
| `ID_USER_SOCLE_1`             | integer                                                                 | Identifiant d'un groupe dans votre instance GeoNature                                                                                          |
| `ID_USER_SOCLE_2`             | integer                                                                 | Identifiant d'un groupe dans votre instance GeoNature                                                                                          |

## Commandes disponibles

Pour lancer une synchronisation globale :

```sh
geonature mtd_sync sync
``` 

Pour lance la synchronisation sur un utilisateur : 

```sh
geonature mtd_sync sync --id-role <ID_UTILISATEUR_MTD>
``` 

Pour lance la synchronisation sur un cadre d'acquisition : 

```sh
geonature mtd_sync sync --id-af <ID_CADRE_ACQUISTION_MTD>
``` 

