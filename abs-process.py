#!/usr/bin/env python3
import argparse
import requests
import re
import math


# Define the base URL of your AudiobookShelf instance and the API key

collection_id_cache = {}
mismatched_asins = []

# todo create collections via API if not present

def read_config(config_file):
    global g_base_url, g_api_key, g_library_name, headers
    abs_config = {}
    with open(config_file, 'r') as f:
        for line in f:
            key_value = line.strip().split('=')
            if len(key_value) > 1:
                abs_config[key_value[0].strip()] = key_value[1].strip()

    g_base_url = abs_config.get('BASE_URL', '')
    g_api_key = abs_config.get('API_KEY', '')
    g_library_name = abs_config.get('LIBRARY', '')

    headers = {
        'Authorization': f'Bearer {g_api_key}'
    }

def get_library_id(g_library_name):
    print(f'Get library id for {g_library_name}... ', end='')
    response = requests.get(f'{g_base_url}/libraries', headers=headers)
    response.raise_for_status()
    for library in response.json()["libraries"]:
        if library["name"] == g_library_name:
            print(f'{library["id"]}')
            return library["id"]
    return None  # not found

def get_all_items(library_id, limit):
    # Fetch all items from the library
    print(f'Get all items... ',end='')
    response = requests.get(f'{g_base_url}/libraries/{library_id}/items?sort=addedAt&desc=1&limit={limit}', headers=headers)
    response.raise_for_status()
    print(f'[DONE]')
    return response.json()['results']

def get_all_batch(all_items_json):
    print(f'Get all BATCH items... ', end='')
    all_ids = [item.get('id') for item in all_items_json]
    data = {'libraryItemIds': all_ids}
    try:
        response = requests.post(f'{g_base_url}/items/batch/get', headers=headers, json=data)
        response.raise_for_status()
        print(f'[DONE]')
        return response.json()['libraryItems']
    except:
        print(f'Error getting bulk object')

def get_collections():
    print(f'Get all collections... ', end='')
    response = requests.get(f'{g_base_url}/collections/', headers=headers)
    response.raise_for_status()
    json_data =  response.json()
    # trim for performance - not sure it helps
    for collection in json_data['collections']:
        for book in collection['books']:
            if 'media' in book:
                del book['media']
            if 'libraryFiles' in book:
                del book['libraryFiles']
    print(f'[DONE]')
    return json_data

def add_to_collection(item_id, collection_id, collection_name):
    data = {'id': item_id}
    try:
        response = requests.post(f'{g_base_url}/collections/{collection_id}/book', headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except:
        print(f'(Error adding {item_id} to {collection_name} collection')

def update_tags(id, tags):
    data = {'tags': tags}
    try:
        response = requests.patch(f'{g_base_url}/items/{id}/media', headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except:
        print(f'Error adding {tags} to {id} item')

def get_item(id):
    response = requests.get(f'{g_base_url}/items/{id}', headers=headers)
    response.raise_for_status()
    return response.json()

def get_item_files(id):
    response = requests.get(f'{g_base_url}/items/{id}', headers=headers)
    response.raise_for_status()
    return response.json()['media']['audioFiles']

def book_id_in_collection(book_id, collection_name, collections_json):
    for collection in collections_json["collections"]:
        if collection["name"] == collection_name:
            return any(book["id"] == book_id for book in collection["books"])
    return False

def getset_collection_id_by_name(library_id, collection_name, collections_json):
    for collection in collections_json['collections']:
        if collection['name'] == collection_name:
            return collection['id']
    # if we didn't return here it means the collection doesn't exist
    data = {
        'libraryId': LIB_ID,
        'name': collection_name
        }
    try:
        response = requests.post(f'{g_base_url}/collections', headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except:
        print(f'(Failed to create new collection {collection_name}')
    return None

def main():

    read_config("abs.ini")
    
    library_id=get_library_id(g_library_name)

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Fetch items from a library.')
    parser.add_argument('--limit', type=int, help='Limit the number of items returned')

    args = parser.parse_args()
    if args.limit:
        item_limit = args.limit
    else:
        item_limit = 0

    collections = get_collections()

    batch_items = get_all_batch(get_all_items(library_id, item_limit))

    #with open('get_all_batch.json', 'w') as f:
    #    json.dump(batch_items, f)

    total = len(batch_items)
    total_digits = int(math.log10(total)) + 1

    i = 1
    for item in batch_items:
        item_id = item['id']
        item_title = item['media']['metadata']['title']
        item_tags = item['media']['tags']
        item_files = item['media']['audioFiles']
        item_asin = item['media']['metadata']['asin']

        print(f'\033[36m{i:0{total_digits}} of {total}\033[40m', end=' ')

        for item_file in item_files:
            filename = item_file['metadata']['filename']
            filepath = item_file['metadata']['path']
            if filename.endswith(".m4b"):
                if '.com.' in filename:
                    collection_name = 'audible.com'
                elif '.co_uk.' in filename:
                    collection_name = 'audible.co.uk'
                elif 'LATW/' in filepath:
                    collection_name = 'LATW'
                elif 'The Great Courses/' in filepath:
                    collection_name = 'The Great Courses'
                elif re.search(r'\[\w+\]', filename) and '.com.' not in filename and '.co_uk.' not in filename:
                    collection_name = 'audible_legacy'
                else:
                    continue

                if not book_id_in_collection(item_id, collection_name, collections):
                    print(f'\033[92m[adding to {collection_name}]\033[00m - {item_id} ({item_title})',end="")

                    if collection_name in collection_id_cache:
                        collection_id = collection_id_cache[collection_name]  # Use cached result
                    else:
                        # Call the API and store the result in the cache
                        collection_id = getset_collection_id_by_name(library_id, collection_name, collections)
                        collection_id_cache[collection_name] = collection_id  # Cache the result
                    add_to_collection(item_id, collection_id, collection_name)
                else:
                    print(f'\033[93m[exists in {collection_name}]\033[00m - {item_id} ({item_title})',end="")

                if collection_name not in item_tags:
                        print(f' - \033[96m tagging {collection_name}\033[00m',end="")
                        item_tags.append(collection_name)
                        update_tags(item_id, item_tags)

                file_asin_matches = [m for m in re.findall(r"\[(.*?)\]", filename) if len(m) >= 4]
                if file_asin_matches:
                    file_asin = file_asin_matches[-1]
                    if file_asin!= item_asin:
                        mismatched_asins.append(item_title)

        print(f'')
        i += 1

    print(f'\n\033[31m{len(mismatched_asins)} ASIN mismatches!\033[00m\n')
    print(*mismatched_asins,sep="\n")

if __name__ == '__main__':
    main()
