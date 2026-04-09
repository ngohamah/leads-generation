import re
import json
import requests
import time
from pathlib import Path
from constants import GOOGLE_API_KEY, CX


def create_dorks(name, company, domain):
    """
    Create a google dork string and save to file.
    """
    dorks = f"site:{domain} intext:{name} intext:{company}"

    with open("dorks/custom_dorks.txt", 'w') as f:
        f.write(dorks)
    f.close()
    return dorks


def extract_names_from_linkedin_url(url):
    """
    Extracts the first and last name from a typical LinkedIn profile URL.
    """
    # Remove trailing slash (if any) and split URL on "/"
    parts = url.rstrip("/").split("/")

    # The last segment is the "username"
    username = parts[-1]

    name_parts = username.split("-")

    # linkedin profile URLS:
    # "https://evaboot.com/blog/linkedin-url-example#:~:text=Don't%20know%20how%20to,Full%20Name%20+%20Keyword"

    first_name = name_parts[0]
    middle_name = name_parts[1] if len(name_parts) > 1 else ""
    last_name = name_parts[2] if len(name_parts) > 2 else ""
    # unique_id = name_parts[3] if len(name_parts) > 3 else "" # sometimes
    # linkedin adds unique id at end of URL

    return [first_name, middle_name, last_name]


def match_profile(linkedin_url, name_parts):
    """Check if a URL is a LinkedIn profile."""
    match = re.search(r"linkedin\.com/in/", linkedin_url)

    if match:
        extracted_names = extract_names_from_linkedin_url(linkedin_url)
        # ensure both first and last names are in the URL - standard matching
        # practice for linkedin profiles
        if name_parts[0].lower(
        ) in extracted_names and name_parts[-1].lower() in extracted_names:
            return linkedin_url  # return the matched URL
        # handle cases like "jdoe" for "John Doe":
        elif name_parts[0][0].lower() + name_parts[1].lower() in extracted_names:
            return linkedin_url
        elif name_parts[0] + name_parts[1].lower() in extracted_names:
            return linkedin_url  # handle cases like "johndoe" for "John Doe"
    else:
        return None  # not a linkedin profile URL


def read_json(json_filepath):
    """Read JSON file into a Python object."""
    with open(json_filepath, "r") as jsonfile:
        return json.load(jsonfile)


def get_profile_url(url, name):
    """Return best LinkedIn profile URL from results."""

    if match_profile(url, name.split(' ')):
        print("Profile URL exists")
        return url
    else:
        # print("No profile URL exists")
        return None


def remove_unknown_professional(indices, people):
    count = 0
    for pos in indices:
        if count == 0:
            # remove first occurrence without position update
            people.remove(people[pos])
        else:
            # update position as list reduces after removal
            people.remove(people[pos - count])
        count += 1
    return people


def query_the_web(query):
    try:
        response = requests.get(
            f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={CX}&q={query}")

        # handle rate limiting by Google Custom Search API or any other request
        # errors
        if (response.status_code != 200):
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        else:
            # write response to file
            with open("search_results.json", 'w') as f:
                f.write(json.dumps(response.content.decode('utf-8'), indent=2))
            f.close()
            return response.status_code
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def read_professional_search_results(filepath):
    '''Read complete information of all available professionals from a file and decode JSON.'''
    # add second json.load b/c of double json encoding in Custom Google Search
    # Engine results.
    try:
        with open(filepath, "r") as f:
            content = f.read()
        return json.loads(json.loads(content))
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None


def get_professional_bio(item):
    '''Returns the professional bio of a single professional
       item: JSON data of a single professional
    '''
    pagemap = item.get("pagemap", {})
    metatags = pagemap.get("metatags", [])
    bio = metatags[0].get("og:description", "")
    return bio


def process_query_results(name, search_results_filepath="search_results.json"):
    '''Process the query results to extract linkedin profile URL and bio.'''

    data = read_professional_search_results(search_results_filepath)
    
    try:
        profile_search_results = data["items"]
        bio = ""

        for result in profile_search_results:

            linkedin_profile_url = get_profile_url(
                result["link"], name)  # get matching linkedin profile url

            if linkedin_profile_url is not None:
                # get professional bio if linkedin profile url exists
                bio += get_professional_bio(result)
                break  # exit loop if linkedin profile url is found
    except Exception as e:
        print(f"No search results found for the professional with name: {name}")
        linkedin_profile_url = None
        bio = ""

    return linkedin_profile_url, bio


def get_linkedin_profile_infos(json_input_filepath, json_output_filepath):
    """Main routine to read input, run dorking, and save results."""

    people = list(read_json(json_input_filepath))

    professional_position_in_list = 0
    unknown_professionals = []

    for professional in people:
        name = professional["name"]
        company = professional["company_name"]

        if "None" in name or company == "":
            unknown_professionals.append(professional_position_in_list)
            professional_position_in_list += 1
            continue  # speed up code by skipping professionals with no name

        professional_position_in_list += 1

        # query the web and save results to file
        status = query_the_web(
            create_dorks(
                name=name,
                company=company,
                domain="linkedin.com"))
        
        time.sleep(4)  # sleep for 4 seconds after every request.

        if status is None:
            print("Exiting due to error in querying the web.")
            exit(1)

        linkedin_profile_url, bio = process_query_results(name)

        # update professional info
        professional["linkedin"] = linkedin_profile_url
        professional["bio"] = str(bio)

        with open(json_output_filepath, 'w') as f:
            f.write(json.dumps(people, indent=2))

    # unknwown professionals are those with first and last names = "None" in
    # input file
    people = remove_unknown_professional(unknown_professionals, people)

    # clean file by removing all unknown professionals
    with open(json_output_filepath, 'w') as f:
        f.write(json.dumps(people, indent=2))
    f.close()


def get_directory_structure(root_dir):
    root = Path(root_dir)
    count = 0
    paths = []
    for path in root.rglob("team2*.json"):
        paths.append(str(root_dir) + "/" + str(path.relative_to(root)))
        count += 1
    # print(f"Total files found: {count}")
    with open("all_paths.json", 'w') as f:
        f.write(json.dumps(paths, indent=4))
    f.close()
    return paths


def set_new_path(path_str):
    path = Path(path_str)
    new_name = path.name.replace("team2", "team5")
    new_path = path.parent / new_name
    new_path.write_text("")  # Creates an empty file
    # print(f"Created: {new_path}")
    return str(new_path)


if __name__ == "__main__":
    
    # processing all files in a directory
    path = get_directory_structure("countries")

    start_at = 0
    for p in path:
        print(f"Processing: {p}")
        try:
            get_linkedin_profile_infos(p, set_new_path(p))
        except Exception as e:
            print(f"An error occurred processing {p}: {e}")
            break
   
