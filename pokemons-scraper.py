#!/usr/bin/env python3
import os
import re
import time
import logging
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import boto3
from botocore.exceptions import ClientError

# Configuration
BUCKET_NAME = "pokemon-images-khalil"
S3_PREFIX = 'images/pokemon/'
DELAY = 2
MAX_POKEMON = 10  # Test avec 10 d'abord
MAX_RETRIES = 2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class PokemonScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Educational Pokemon Project)'
        })

        self.s3 = boto3.client('s3')

        try:
            self.s3.head_bucket(Bucket=BUCKET_NAME)
            logger.info(f"✅ Bucket S3 accessible: {BUCKET_NAME}")
        except Exception as e:
            logger.error(f"❌ Erreur S3: {e}")
            raise

    def get_pokemon_data(self):
        url = "https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_National_Pok%C3%A9dex_number"

        logger.info(f"📡 Récupération de {url}")

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            pokemon_list = []
            tables = soup.find_all('table', class_='roundy')

            logger.info(f"Tables trouvées: {len(tables)}")

            for table_idx, table in enumerate(tables[:2]):  # Les 2 premières tables
                logger.info(f"Traitement table {table_idx + 1}")
                rows = table.find_all('tr')[1:]  # Skip header

                for i, row in enumerate(rows):
                    if len(pokemon_list) >= MAX_POKEMON:
                        break

                    cells = row.find_all('td')

                    if len(cells) >= 3:
                        # Extraire le numéro (gérer #0001, 0001, 1, etc.)
                        number_text = cells[0].get_text().strip()
                        number_clean = re.sub(r'[^\d]', '', number_text)

                        if not number_clean:
                            continue

                        try:
                            number = int(number_clean)
                        except ValueError:
                            continue

                        # Image
                        img = cells[1].find('img')
                        if not img:
                            continue

                        img_src = img.get('src', '')
                        if img_src.startswith('//'):
                            img_src = 'https:' + img_src
                        elif img_src.startswith('/'):
                            img_src = 'https://bulbapedia.bulbagarden.net' + img_src

                        # Nom
                        name = cells[2].get_text().strip().split('\n')[0]  # Prendre seulement la première ligne
                        name = re.sub(r'[^\w\s-]', '', name)[:20]

                        if number and name and img_src:
                            pokemon_data = {
                                'number': f"{number:03d}",
                                'name': name,
                                'image_url': img_src,
                                'filename': f"{number:03d}_{name.replace(' ', '_')}.png"
                            }
                            pokemon_list.append(pokemon_data)
                            logger.info(f"Pokémon ajouté: #{number:03d} {name}")

            logger.info(f"✅ {len(pokemon_list)} Pokémon trouvés")
            return pokemon_list

        except Exception as e:
            logger.error(f"❌ Erreur scraping: {e}")
            import traceback
            traceback.print_exc()
            return []

    def download_image(self, pokemon):
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"📥 Téléchargement: {pokemon['name']}")

                response = self.session.get(pokemon['image_url'], timeout=10)
                response.raise_for_status()

                if 'image' in response.headers.get('content-type', ''):
                    logger.info(f"✅ Image téléchargée: {len(response.content)} bytes")
                    return response.content
                else:
                    logger.warning(f"⚠️ Pas une image: {pokemon['name']}")
                    return None

            except Exception as e:
                logger.warning(f"⚠️ Tentative {attempt + 1} échouée: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)

        return None

    def upload_to_s3(self, image_data, pokemon):
        s3_key = f"{S3_PREFIX}{pokemon['filename']}"

        try:
            self.s3.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=image_data,
                ContentType='image/png',
            )

            public_url = f"https://{BUCKET_NAME}.s3.eu-west-3.amazonaws.com/{s3_key}"
            logger.info(f"✅ Uploadé: {pokemon['name']} -> S3")
            return public_url

        except ClientError as e:
            logger.error(f"❌ Erreur upload {pokemon['name']}: {e}")
            return None

    def run(self):
        logger.info("🚀 Début du scraping Pokémon")

        pokemon_list = self.get_pokemon_data()

        if not pokemon_list:
            logger.error("❌ Aucun Pokémon trouvé!")
            return

        success_count = 0

        for i, pokemon in enumerate(pokemon_list):
            try:
                logger.info(f"[{i+1}/{len(pokemon_list)}] Traitement: {pokemon['name']}")

                image_data = self.download_image(pokemon)
                if not image_data:
                    continue

                url = self.upload_to_s3(image_data, pokemon)
                if url:
                    success_count += 1
                    logger.info(f"🔗 URL publique: {url}")

                time.sleep(DELAY)

            except KeyboardInterrupt:
                logger.info("🛑 Arrêt demandé")
                break
            except Exception as e:
                logger.error(f"❌ Erreur {pokemon['name']}: {e}")

        logger.info(f"🎉 Terminé! {success_count}/{len(pokemon_list)} images uploadées")

def main():
    try:
        scraper = PokemonScraper()
        scraper.run()
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()