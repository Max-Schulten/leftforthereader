from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
import logging
import time
import random
import os

# Setup logging for sanity
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("scraper_theorems.log"),
        logging.StreamHandler()
    ]
)

base_url = "https://proofwiki.org/"

# Set home url for definitions namespace
home_url = base_url + "wiki/Special:AllPages?from=&to=&namespace=0"

# Create dataframe for ease of use
definitions = pd.DataFrame(
    columns = ['source', 'theorem', 'proof']
)

def save_results(results, checkpoint_iter, checkpoint_url):
    # Scrape all of the definitions
    definitions = results

    # Convert to dataframe
    definitions_df = pd.DataFrame(definitions)

    # Dir
    out_dir = "./data/proof_wiki_theorems"
    
    # create dir if not already existi
    os.makedirs(out_dir, exist_ok=True)

    # Save as a csv
    definitions_df.to_csv(
        f'{out_dir}/theorems({checkpoint_iter}).csv'
    )
    
    with open(f"{out_dir}/checkpoint_url({checkpoint_iter}).txt", "w") as f:
                f.write(checkpoint_url)

    return True

def scrape_text(start):
    content = []
    current = start.find_next_sibling()
    while current and current.name != "h2":
        # Track all of the parts we've seen
        parts = []
        # Iterate over all descendants looking for latex
        for descendant in current.descendants:
            if descendant.name == "script" and descendant.get("type") == "math/tex":
                if descendant.string:
                    parts.append(f"${descendant.string.strip()}$")
            elif descendant.name is None:  # It's a NavigableString (text node)
                parts.append(descendant.strip())
        # concatenate everything
        text = " ".join(parts).strip()
        # Only add if not empty
        
        if text:
            content.append(text)
        current = current.find_next_sibling()
    
    return "\n".join(content).strip()

def scrape_theorem(page_url, session = None):
    if not session:
        session = requests.Session()
    # Get page
    def_page = session.get(page_url)
    # Get html
    def_page_html = BeautifulSoup(def_page.text, 'html.parser')
   
    # Find beginning of definition part of page
    thm_regex = re.compile('.*Theorem.*')
    start_span = def_page_html.find("span", {"id": thm_regex})
    start = start_span.find_parent("h2") if start_span else None
    
    # Stop looking if no definition found
    if not start or not start_span:
        logging.info(f"No theorem section found on {page_url}.")
        return None, None
    
    # Need term, definition on its own not useful for context
    
    thm = scrape_text(start)

    if not thm:
        logging.info(f"No theorem found in theorem section on {page_url}.")
        return None, None

    proof_regex = re.compile('.*Proof.*')
    start_span = def_page_html.find('span', {"id": proof_regex})
    start = start_span.find_parent('h2') if start_span else None

    if not start or not start_span:
        logging.info(f"No proof section found on {page_url}.")
        return None, None

    proof = scrape_text(start)

    if not proof:
        logging.info(f"No proof found in proof section on {page_url}.")
        return None, None
    
    return thm, proof

def check_link_name(name: str):
    name = name.strip()
    
    if re.search(r'(historical note|mistake)', name, re.IGNORECASE):
        return False
    if re.fullmatch(r'^-?(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?$', name):
        return False

    return True

def scrape_theorem_pages(start_url, page_count = 0):
    # Initialization
    current_url = start_url
    visited = set()
    results = {'links': [], 'thms': [], 'proofs': []}
    # Begin session with the server
    session = requests.session()

    while current_url and current_url not in visited:
        visited.add(current_url)
        page_count += 1

        logging.info(f"Starting page: {current_url}")
        
        # Get the home page so we can get all of the links 
        try:
            response = session.get(current_url)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.warning(f"Failed to fetch {current_url}: {e}")
            break
        except requests.exceptions.ConnectionError as e:
            logging.warning(f'Ran into an exception: {e} on url: {current_url}')
            session.close()
            time.sleep(1)
            session = requests.session()
            response = session.get(current_url)
            response.raise_for_status()

        # Prepare page for parsing
        home_html = BeautifulSoup(response.text, 'html.parser')

        # Find all definition links
        bullets = home_html.find_all('ul', class_='mw-allpages-chunk')

        for li in bullets:
            for link in li.find_all('a', href=True):
                if check_link_name(link.getText()):
                    def_link = base_url + link['href']
                    
                    # Get definition and term from link
                    try:
                        thm, proof = scrape_theorem(def_link, session)
                    except requests.exceptions.ConnectionError as e:
                        logging.warning(f'Ran into an exception: {e} on url: f{def_link}')
                        session.close()
                        time.sleep(1)
                        session = requests.session()
                        thm, proof = scrape_theorem(def_link, session)
                         
                    # Select random sleep time to limit rate
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    if def_link and thm and proof:
                        results['links'].append(def_link)
                        results['thms'].append(thm)
                        results['proofs'].append(proof)
                else:
                    logging.info(f"Link skipped due to name: {link.getText()}")

        # Save progress every 3 pages
        if page_count % 3 == 0:
            logging.info(f"CHECKPOINT: {page_count} pages scraped. Saving progress and clearing dict...")
            save_results(results, page_count, current_url)
            # Clear the dict so it doesn't get too big
            results = {'links': [], 'thms': [], 'proofs': []}

        # Get next page URL from the nav section
        nav = home_html.find('div', class_='mw-allpages-nav')
        next_link = None
        if nav:
            for link in nav.find_all('a', href=True):
                if re.match("^Next page.*", link.get_text()):
                    next_link = link['href']
                    break

        if next_link:
            current_url = base_url + next_link
        else:
            print("No more pages found.")
            break

    # Save final
    return save_results(results, checkpoint_iter=page_count, checkpoint_url=current_url)

scrape_theorem_pages('https://proofwiki.org//w/index.php?title=Special:AllPages&from=Lower+and+Upper+Bounds+for+Sequences', page_count = 78)