#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict
import re

class PSPHomebrewScraper:
    def __init__(self):
        self.base_url = "https://archive.org"
        self.collection_url = "https://archive.org/details/psp-homebrew-library"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_collection_items(self) -> List[str]:
        print("Obteniendo lista de items de la colección...")
        
        api_url = "https://archive.org/advancedsearch.php"
        params = {
            'q': 'collection:psp-homebrew-library',
            'fl[]': ['identifier', 'title'],
            'rows': 10000,
            'page': 1,
            'output': 'json'
        }
        
        try:
            response = self.session.get(api_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            items = data.get('response', {}).get('docs', [])
            identifiers = [item['identifier'] for item in items]
            print(f"Encontrados {len(identifiers)} items en la colección")
            return identifiers
            
        except Exception as e:
            print(f"Error obteniendo items de la colección: {e}")
            return []
    
    def get_item_details(self, identifier: str) -> Dict:
        """Obtiene los detalles de un item específico"""
        item_url = f"{self.base_url}/details/{identifier}"
        metadata_url = f"{self.base_url}/metadata/{identifier}"
        
        try:
            metadata_response = self.session.get(metadata_url, timeout=30)
            metadata_response.raise_for_status()
            metadata = metadata_response.json()
            
            item_data = {
                'identifier': identifier,
                'title': metadata.get('metadata', {}).get('title', ''),
                'category': self.extract_category(metadata),
                'tags': self.extract_tags(metadata),
                'download_url': None,
                'url': item_url
            }
            
            # Buscar archivo .zip en los archivos del item
            files = metadata.get('files', [])
            for file in files:
                filename = file.get('name', '')
                if filename.lower().endswith('.zip'):
                    item_data['download_url'] = f"{self.base_url}/download/{identifier}/{filename}"
                    break
            
            if not item_data['download_url']:
                for file in files:
                    filename = file.get('name', '')
                    if filename.lower().endswith(('.rar', '.7z', '.pbp')):
                        item_data['download_url'] = f"{self.base_url}/download/{identifier}/{filename}"
                        break
            
            return item_data
            
        except Exception as e:
            print(f"Error obteniendo detalles de {identifier}: {e}")
            return None
    
    def extract_category(self, metadata: Dict) -> str:
        """Extrae la categoría del metadata"""
        meta = metadata.get('metadata', {})
        
        subject = meta.get('subject', [])
        if isinstance(subject, str):
            subject = [subject]
        
        categories = ['Games', 'Emulators', 'Applications', 'Utilities', 
                     'Media', 'Demos', 'Plugins', 'Themes']
        
        for cat in categories:
            for subj in subject:
                if cat.lower() in str(subj).lower():
                    return cat
        
        if subject:
            return str(subject[0])
        
        return 'Unknown'
    
    def extract_tags(self, metadata: Dict) -> List[str]:
        meta = metadata.get('metadata', {})
        tags = []
        
        subject = meta.get('subject', [])
        if isinstance(subject, str):
            subject = [subject]
        tags.extend([str(s) for s in subject])
        
        keywords = meta.get('keywords', [])
        if isinstance(keywords, str):
            keywords = [keywords]
        tags.extend([str(k) for k in keywords])
        
        tags = list(set([tag.strip() for tag in tags if tag]))
        
        return tags
    
    def scrape_all(self) -> List[Dict]:
        identifiers = self.get_collection_items()
        results = []
        
        total = len(identifiers)
        for idx, identifier in enumerate(identifiers, 1):
            print(f"Procesando {idx}/{total}: {identifier}")
            
            item_data = self.get_item_details(identifier)
            if item_data and item_data['download_url']:
                results.append(item_data)
            
            time.sleep(0.5)
        
        return results
    
    def save_to_json(self, data: List[Dict], filename: str = 'psp_homebrew_library.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'total_items': len(data),
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
                'items': data
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\nDatos guardados en {filename}")
        print(f"Total de items con enlace de descarga: {len(data)}")


def main():
    scraper = PSPHomebrewScraper()
    
    print("Iniciando scraping de PSP Homebrew Library...")
    print("=" * 60)
    
    results = scraper.scrape_all()
    scraper.save_to_json(results)
    
    print("=" * 60)
    print("Scraping completado!")
    
    categories = {}
    for item in results:
        cat = item['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nEstadísticas por categoría:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")


if __name__ == '__main__':
    main()
