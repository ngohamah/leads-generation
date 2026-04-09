import json
import requests
from pathlib import Path
from constants import GOOGLE_API_KEY, CX

l = [
        {
            "1": "one"
        },
        {
            "2": "two"
        },
        {
            "3": "three"
        },
        {
            "4": "four"
        },
        {
            "5": "five"
        },
        {
            "6": "six"
        }
    ]

def removeItem(list_of_items: list, index:list) -> list:
    
    for i in range(len(list_of_items)):
        if i==index:
            list_of_items.remove(list_of_items[index])
            return list_of_items
        else: 
            continue
    else:
        print("wrong index")

def remove_unknown_list_items(items, listofitems):
    item_count = 0
    for pos in items:

        if item_count!=0:
            listofitems.remove(listofitems[pos-1]) # update position as list strings after removal 
        else:
            listofitems.remove(listofitems[pos])
        item_count+=1

    return listofitems

def query_the_web(query):
    response = requests.get(f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={CX}&q={query}")
    print(response.content.decode('utf-8'))
    with open("search_results.json", 'w') as f:
            f.write(json.dumps(response.content.decode('utf-8'), indent=4))
    f.close()
    
def read_professional_infos(filepath):
    with open(filepath, "r") as f:
        content = f.read()
    
    f.close()
    return content

def get_directory_structure(root_dir):
    root = Path(root_dir)
    count =0
    paths = []
    for path in root.rglob("team2*.json"):
        paths.append(str(root_dir)+"/"+str(path.relative_to(root)))
        count+=1
    print(f"Total files found: {count}") 
    with open("all_paths.json", 'w') as f:
            f.write(json.dumps(paths, indent=4))
    f.close()
    return paths   


if __name__ == "__main__":
    file_paths = get_directory_structure("Countries_karim")
    count=0
    for file in file_paths:
        if file=="Countries_karim/Mena/UAE/team2_UAE_real_estate_companies_test.json":
            print("counter: ", count)
            break
        count+=1
        
    

