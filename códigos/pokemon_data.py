# -*- coding: utf-8 -*-
"""
Created on Sun Oct  8 20:27:55 2023

@author: mauricio.tomida
"""

import requests
import pandas as pd
import numpy as np
import re

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

df_sprite_3d = pd.DataFrame({'name': filenames, 'url_sprite': raw_urls})

# Remove .gif from filename
df_sprite_3d['name'] = df_sprite_3d['name'].str.replace('.gif', '')

# Remove special sprites, like megaevolution
condition = df_sprite_3d['name'].str.contains('_')
exception1 = df_sprite_3d['name'].str.contains('Mr._Mime')
exception2 = df_sprite_3d['name'].str.contains('Nidoran_Female')
exception3 = df_sprite_3d['name'].str.contains('Nidoran_Male')
df_sprite_3d = df_sprite_3d[~condition | exception1 | exception2 | exception3].reset_index(drop=True)

# Pokemon name to lower
df_sprite_3d['name'] = df_sprite_3d['name'].apply(lambda x: x.lower() if isinstance(x, str) else x)

# Adjusting the name to pokeapi
df_sprite_3d['name'] = df_sprite_3d['name'].replace('mr._mime', 'mr-mime') 
df_sprite_3d['name'] = df_sprite_3d['name'].replace('nidoran_female', 'nidoran-f')
df_sprite_3d['name'] = df_sprite_3d['name'].replace('nidoran_male', 'nidoran-m') 
df_sprite_3d['name'] = df_sprite_3d['name'].replace("farfetch'd", 'farfetchd')    

########################################

########################################
############ Pokemon cries #############
########################################

### The Pokémon cries used in this project are sourced from https://www.smogon.com/forums/threads/pok%C3%A9mon-xy-remastered-cries.3512615/
REPO_OWNER = "mhirokitomida"
REPO_NAME = "pokedash"
BRANCH_NAME = "main"
FOLDER_PATH = "pokemon_cries"
GITHUB_API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/{BRANCH_NAME}?recursive=1"

response = requests.get(GITHUB_API_BASE)
response_data = response.json()

# Filtrando apenas arquivos .wav no diretório desejado
wav_files = [file for file in response_data['tree'] if file['path'].startswith(FOLDER_PATH) and file['path'].endswith('.wav')]

file_names = []
urls = []

for file in wav_files:
    file_name = int(re.search(r'(\d+)', file['path']).group(1))
    raw_url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH_NAME}/{file['path']}"
    file_names.append(file_name)
    urls.append(raw_url)

# Criando o DataFrame
df_cries = pd.DataFrame({
    'id': file_names,
    'url_cry': urls
})

########################################

########################################
############## Types tag ###############
########################################

### The Pokémon types tags used in this project are sourced from https://archives.bulbagarden.net/w/index.php?title=Category:Type_icons&fileuntil=FireIC+XD.png#mw-category-media
REPO_OWNER = "mhirokitomida"
REPO_NAME = "pokedash"
BRANCH_NAME = "main"
FOLDER_PATH = "imagens/types_tag"
GITHUB_API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/{BRANCH_NAME}?recursive=1"

response = requests.get(GITHUB_API_BASE)
response_data = response.json()

png_files = [file for file in response_data['tree'] if file['path'].startswith(FOLDER_PATH) and file['path'].endswith('.png')]

type_names = []
urls = []

for file in png_files:
    type_name = re.search(r'/(\w+).png', file['path']).group(1)  # Adaptação para pegar o nome do arquivo sem a extensão
    raw_url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH_NAME}/{file['path']}"
    type_names.append(type_name)
    urls.append(raw_url)

# Criando o DataFrame
df_types_tag = pd.DataFrame({
    'type': type_names,
    'url_type_tag': urls
})

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

# Merge 3D sprites 
df_result = pd.merge(df_pokemon_info, df_sprite_3d, on='name', how='inner')

# Remove line break
df_result = df_result.replace({r'\n': ' '}, regex=True)
df_result = df_result.replace({r'  +': ' '}, regex=True)

# Merge Pokemon cries
df_result = df_result.merge(df_cries, on='id', how='left')

# Merge Evolutions
df_aux = df_result.copy()
df_aux = df_aux[['pre_evolution', 'name']]
df_aux = df_aux.rename(columns={'pre_evolution': 'name', 'name': 'evolution'})
df_aux = df_aux.dropna(subset=['name'])
df_aux['evolution_count'] = df_aux.groupby('name').cumcount() + 1
df_pivot = df_aux.pivot(index='name', columns='evolution_count', values='evolution')
df_pivot.columns = [f'evolution_{i}' for i in df_pivot.columns]
df_result = df_result.merge(df_pivot, on='name', how='left')

# Remove pre-evolution that is not include in Gen I
mask = ~df_result['pre_evolution'].isin(df_result['name'])
df_result.loc[mask, 'pre_evolution'] = np.nan

# Remove evoltution that is not include in Gen I
evolution_columns = [col for col in df_result.columns if 'evolution' in col]
for col in evolution_columns:
    mask = ~df_result[col].isin(df_result['name'])
    df_result.loc[mask, col] = np.nan

# Reorder columns
cols = df_result.columns.tolist()
index_pre_evolution = cols.index('pre_evolution')
cols = cols[:index_pre_evolution] + evolution_columns + [c for c in cols[index_pre_evolution+1:] if c not in evolution_columns]
df_result = df_result[cols]

# Merge Pokemon Tag Type
df_result = df_result.merge(df_types_tag, left_on='type_1', right_on='type', how='left')
df_result.drop('type', axis=1, inplace=True)
df_result = df_result.merge(df_types_tag, left_on='type_2', right_on='type', how='left')
df_result.drop('type', axis=1, inplace=True)
df_result = df_result.rename(columns={'url_type_tag_x': 'url_type_1_tag', 'url_type_tag_y': 'url_type_2_tag'})


# Conveting None to nan
df_result.replace({None: np.nan}, inplace=True)

# Export to .csv
df_result.to_csv('pokemon_database.csv', index=False)