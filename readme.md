# Pokemon Scraper - AWS EC2 + S3

Scraper automatisé qui récupère les images de Pokemon depuis Bulbapedia et les stocke dans Amazon S3 via une instance EC2.

## Architecture

**Composants :**
- **EC2** (t2.micro) : Environnement d'exécution Python
- **S3** : Stockage des images avec accès public  
- **IAM** : Gestion des permissions sécurisée

## Prérequis

- Compte AWS avec accès Free Tier
- Instance EC2 Ubuntu 22.04
- Python 3.10+

## Configuration AWS

### 1. Créer l'utilisateur IAM

1. Console AWS → IAM → Utilisateurs → Créer un utilisateur
2. Nom : `pokemon-scraper`
3. Accès par programmation : Activé
4. Créer une politique avec ces permissions :

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:ListBucket"],
            "Resource": "arn:aws:s3:::pokemon-images-*"
        },
        {
            "Effect": "Allow",
            "Action": ["s3:PutObject", "s3:GetObject"],
            "Resource": "arn:aws:s3:::pokemon-images-*/images/*"
        }
    ]
}
```

### 2. Créer le bucket S3

1. Console AWS → S3 → Créer un compartiment
2. Nom : `pokemon-images-[votre-nom]` (remplacer [votre-nom])
3. Région : `eu-west-3` (Paris)
4. Bloquer l'accès public : Décocher toutes les cases
5. Ajouter cette politique de compartiment :

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::pokemon-images-VOTRE-NOM/images/*"
        }
    ]
}
```

### 3. Créer l'instance EC2

1. Console AWS → EC2 → Lancer une instance
2. Configuration :
   - AMI : Ubuntu Server 22.04 LTS
   - Type : **t2.micro** (Free Tier obligatoire)
   - Paire de clés : Créer une nouvelle
   - Security Group : SSH (22), HTTP (80), HTTPS (443)

## Installation

### 1. Connexion à l'instance EC2

```bash
ssh -i votre-cle.pem ubuntu@IP-EC2
```

### 2. Setup de l'environnement Python

```bash
# Mise à jour du système
sudo apt update && sudo apt install python3-pip python3-venv awscli -y

# Création de l'environnement virtuel
python3 -m venv pokemon_env
source pokemon_env/bin/activate

# Installation des dépendances
pip install requests beautifulsoup4 boto3 lxml
```

### 3. Configuration AWS CLI

```bash
aws configure
```

Saisir :
- Access Key ID : [votre clé IAM]
- Secret Access Key : [votre clé secrète IAM]
- Default region : `eu-west-3`
- Default output format : `json`

### 4. Téléchargement et exécution du script

```bash
# Cloner le projet
git clone https://github.com/Kdnuebe/pokemon-scraper.git
cd pokemon-scraper

# Modifier le nom du bucket dans le script
nano pokemons_scraper.py
# Ligne 11 : BUCKET_NAME = "pokemon-images-votre-nom"

# Lancer le scraper
python3 pokemon_sscraper.py
```

## Résultats

Le script télécharge et stocke 10 images de Pokemon avec des URLs publiques :
- `https://pokemon-images-khalil.s3.eu-west-3.amazonaws.com/images/pokemon/001_Bulbasaur.png`
- `https://pokemon-images-khalil.s3.eu-west-3.amazonaws.com/images/pokemon/002_Ivysaur.png`
- Etc.

## Configuration du script

### Paramètres principaux
- `MAX_POKEMON` : Nombre de Pokemon à traiter (défaut : 10)
- `DELAY` : Délai entre requêtes (défaut : 2 secondes)
- `MAX_RETRIES` : Tentatives maximum par téléchargement (défaut : 2)

## Bonnes pratiques implémentées

- **Sécurité** : Clés AWS via profil IAM, jamais en dur dans le code
- **Permissions** : Principe du moindre privilège (accès S3 limité)
- **Respect serveur** : Délai entre requêtes, User-Agent identifiant
- **Gestion d'erreurs** : Retry automatique, logging complet
- **Free Tier** : Configuration optimisée pour rester gratuit

## Métriques

- **Performance** : 25 secondes pour 10 Pokemon
- **Taux de succès** : 100%
- **Coût AWS** : 0 euros (Free Tier)
- **Taille moyenne** : 9KB par image

## Arrêt des ressources

Une fois le projet terminé :

1. **Arrêter l'instance EC2** (pas supprimer) pour éviter la consommation d'heures
2. **Garder le bucket S3** avec les images pour la démonstration
3. Les URLs publiques restent fonctionnelles même instance arrêtée

## Documentation technique

Voir le rapport technique complet dans `docs/rapport_technique.md`
