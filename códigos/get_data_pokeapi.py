# -*- coding: utf-8 -*-
"""
Created on Sun Oct  8 23:09:02 2023

@author: mauricio.tomida
"""

import pandas as pd
import numpy as np
import requests

class PokemonData:
    url_base = 'https://pokeapi.co/api/v2'

    def __init__(self, id_pkmn):
        self.id_pkmn = id_pkmn
        self.data = self._get_data(f'{self.url_base}/pokemon/{id_pkmn}/')
        self.species_data = self._get_data(f'{self.url_base}/pokemon-species/{id_pkmn}/')

    def _get_data(self, url):
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def _get_effect_from_url(self, url):
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        for entry in data['effect_entries']:
            if entry['language']['name'] == 'en':
                return entry['effect']
        return None

    def basic_info(self):
        return pd.DataFrame([{
            'id': self.id_pkmn,
            'name': self.data['name'],
            'base_experience': self.data['base_experience'],
            'height': self.data['height'],
            'weight': self.data['weight']
        }])

    def abilities_info(self):
        abilities = {}
        for index, ability in enumerate(self.data['abilities'], start=1):
            abilities[f'ability_{index}_name'] = ability['ability']['name']
            abilities[f'ability_{index}_description'] = self._get_effect_from_url(ability['ability']['url'])
            abilities[f'ability_{index}_is_hidden'] = ability['is_hidden']
        return pd.DataFrame([abilities])

    def stats_info(self):
        stats = {stat['stat']['name']: stat['base_stat'] for stat in self.data['stats']}
        stats['total'] = sum(stats.values())
        return pd.DataFrame([stats])

    def types_info(self):
        if self.data['past_types']:
            types = {f'type_{type_pkm["slot"]}': type_pkm['type']['name'] for type_pkm in self.data['past_types'][0]['types']}
        else:
            types = {f'type_{type_pkm["slot"]}': type_pkm['type']['name'] for type_pkm in self.data['types']}

        return pd.DataFrame([types])

    def species_info(self):
        return pd.DataFrame([{
            'base_happiness': self.species_data['base_happiness'],
            'capture_rate': self.species_data['capture_rate'],
            'pre_evolution': self.species_data['evolves_from_species']['name'] if self.species_data.get('evolves_from_species') else np.nan,
            'gender_rate': self.species_data['gender_rate'] / 8 if self.species_data['gender_rate'] > 0 else self.species_data['gender_rate'],
            'generation': self.species_data['generation']['name'],
            'growth_rate': self.species_data['growth_rate']['name']
        }])

    def consolidate(self):
        basic_df = self.basic_info()
        abilities_df = self.abilities_info()
        stats_df = self.stats_info()
        types_df = self.types_info()
        species_df = self.species_info()
        
        return pd.concat([basic_df, abilities_df, stats_df, types_df, species_df], axis=1)