# -*- coding: utf-8 -*-
"""
Created on Sun Oct  8 20:27:55 2023

@author: mauricio.tomida
"""

import requests
import pandas as pd

########################################
############## Sprites 3D ##############
########################################

### The Pokémon sprites used in this project are sourced from Nackha1's Hd-sprites GitHub Repository, authored by TilableToast.
REPO_OWNER = "Nackha1"
REPO_NAME = "Hd-sprites"
BRANCH = "master"

def list_gif_files_in_repository(owner, repo, branch):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    response = requests.get(url)
    response.raise_for_status()

    files = [file['path'] for file in response.json()['tree'] if file['path'].endswith('.gif')]

    return files

def generate_raw_url(owner, repo, branch, filepath):
    return f"https://github.com/{owner}/{repo}/blob/{branch}/{filepath}?raw=true"

gif_files = list_gif_files_in_repository(REPO_OWNER, REPO_NAME, BRANCH)

filenames = [filepath.split('/')[-1] for filepath in gif_files]
raw_urls = [generate_raw_url(REPO_OWNER, REPO_NAME, BRANCH, filepath) for filepath in gif_files]

df_sprite_3d = pd.DataFrame({'name': filenames, 'url': raw_urls})

# Remove .gif from filename
df_sprite_3d['name'] = df_sprite_3d['name'].str.replace('.gif', '')

# Remove special sprites, like megaevolution
condition = df_sprite_3d['name'].str.contains('_')
exception1 = df_sprite_3d['name'].str.contains('Mr._Mime')
exception2 = df_sprite_3d['name'].str.contains('Nidoran_Female')
exception3 = df_sprite_3d['name'].str.contains('Nidoran_Male')
df_sprite_3d = df_sprite_3d[~condition | exception1 | exception2 | exception3].reset_index(drop=True)

# Pokemon name to lower
df_sprite_3d = df_sprite_3d.applymap(lambda x: x.lower() if isinstance(x, str) else x)

# Adjusting the name to pokeapi
df_sprite_3d['name'] = df_sprite_3d['name'].replace('mr._mime', 'mr-mime') 
df_sprite_3d['name'] = df_sprite_3d['name'].replace('nidoran_female', 'nidoran-f')
df_sprite_3d['name'] = df_sprite_3d['name'].replace('nidoran_male', 'nidoran-m') 
df_sprite_3d['name'] = df_sprite_3d['name'].replace("farfetch'd", 'farfetchd')    

########################################

########################################
############# Pokeapi data #############
########################################

from get_data_pokeapi import PokemonData

df_pokemon_info = pd.DataFrame()

for i in range(1, 152):
    print(f'Buscando pokemon de id = {i}...')
    pokemon = PokemonData(i)
    result_df = pokemon.consolidate()
    df_pokemon_info = pd.concat([df_pokemon_info, result_df], ignore_index=True)

########################################

########################################
############ Export to .csv ############
########################################

# Merge
df_result = pd.merge(df_pokemon_info, df_sprite_3d, on='name', how='inner')

df_result = df_result.replace({r'\n': ' '}, regex=True)
df_result = df_result.replace({r'  +': ' '}, regex=True)

# Export to .csv
df_result.to_csv('pokemon_database.csv', index=False)
