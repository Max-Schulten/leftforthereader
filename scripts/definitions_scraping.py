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
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)

base_url = "https://proofwiki.org/"

# Set home url for definitions namespace
home_url = base_url + "wiki/Special:AllPages?from=&to=&namespace=102"

# Create dataframe for ease of use
definitions = pd.DataFrame(
    columns = ['source', 'term', 'definition', 'examples']
)

def save_results(results, checkpoint_iter, checkpoint_url):
    # Scrape all of the definitions
    definitions = results

    # Convert to dataframe
    definitions_df = pd.DataFrame(definitions)

    # Dir
    out_dir = "E:/leftforthereader/data/proof_wiki_definitions"
    
    # create dir if not already existi
    os.makedirs(out_dir, exist_ok=True)

    # Save as a csv
    definitions_df.to_csv(
        f'{out_dir}/definitions({checkpoint_iter}).csv'
    )
    
    with open(f"{out_dir}/checkpoint_url({checkpoint_iter}).txt", "w") as f:
                f.write(checkpoint_url)

    return True

def scrape_definition(page_url, session = None):
    if not session:
        session = requests.Session()
    # Get page
    def_page = session.get(page_url)
    # Get html
    def_page_html = BeautifulSoup(def_page.text, 'html.parser')
   
    # Find beginning of definition part of page  
    start_span = def_page_html.find("span", id = 'Definition')
    start = start_span.find_parent("h2") if start_span else None
    
    # Stop looking if no definition found
    if not start or not start_span:
        logging.info(f"No definition section found on {page_url}.")
        return None, None
    
    # Find term
    term = def_page_html.find("span", class_ = "mw-page-title-main").text
    
    # Need term, definition on its own not useful for context
    if not term:
        logging.info(f"No term found in title on {page_url}.")
        return None, None
    
    
    # Track content read
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
    
    # Return concatenated
    return term, "\n".join(content).strip()

def scrape_definition_pages(start_url):
    # Initialization
    current_url = start_url
    visited = set()
    results = {'links': [], 'terms': [], 'defs': []}
    page_count = 0
    
    # Begin session with the server
    session = requests.Session()

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

        # Prepare page for parsing
        home_html = BeautifulSoup(response.text, 'html.parser')

        # Link title pattern
        pattern = re.compile("^Definition:.*")

        # Find all definition links
        bullets = home_html.find_all('ul', class_='mw-allpages-chunk')

        for li in bullets:
            for link in li.find_all('a', href=True):
                if pattern.search(link.getText()):
                    def_link = base_url + link['href']
                    
                    # Get definition and term from link
                    term, definition = scrape_definition(def_link, session)
                    # Select random sleep time to limit rate
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    if def_link and term and definition:
                        results['links'].append(def_link)
                        results['terms'].append(term)
                        results['defs'].append(definition)

        # Save progress every 3 pages
        if page_count % 3 == 0:
            logging.info(f"CHECKPOINT: {page_count} pages scraped. Saving progress and clearing dict...")
            save_results(results, page_count, current_url)
            # Clear the dict so it doesn't get too big
            results = {'links': [], 'terms': [], 'defs': []}

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

scrape_definition_pages(home_url)