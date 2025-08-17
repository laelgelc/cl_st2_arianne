#%% md
# <center>
# <img src="https://laelgelcpublic.s3.sa-east-1.amazonaws.com/lael_50_years_narrow_white.png.no_years.400px_96dpi.png" width="300" alt="LAEL 50 years logo">
# <h3>APPLIED LINGUISTICS GRADUATE PROGRAMME (LAEL)</h3>
# </center>
# <hr>
#%% md
# # Corpus Linguistics - Study 2 - Phase 1 - Arianne
#%% md
# This phase aims at extracting text from the blog posts of the following websites:
# - [Greenpeace Stories](https://www.greenpeace.org/international/story/)
# - [WWF](https://www.worldwildlife.org/stories?page=1&threat_id=effects-of-climate-change)
# - [WRI](https://www.wri.org/resources/topic/climate-53/type/insights-50?page=0)
#%% md
# ## Required Python packages
#%% md
# - beautifulsoup4
# - pandas
# - tqdm
# - selenium
# - lxml
#%% md
# ## Import the required libraries
#%%
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys
import time
import logging
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.edge.options import Options
#%% md
# ## Define input variables
#%%
input_directory = 'cl_st2_ph1_arianne'
output_directory = 'cl_st2_ph1_arianne'
#%% md
# ## Create output directory
#%%
# Check if the output directory already exists. If it does, do nothing. If it doesn't exist, create it.
if os.path.exists(output_directory):
    print('Output directory already exists.')
else:
    try:
        os.makedirs(output_directory)
        print('Output directory successfully created.')
    except OSError as e:
        print('Failed to create the directory:', e)
        sys.exit(1)
#%% md
# ## Set up logging
#%%
log_filename = f"{output_directory}/{output_directory}.log"
#%%
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=log_filename
)
#%% md
# ## Functions
#%% md
# ### Create output subdirectories
#%%
def create_directory(path):
    """Creates a subdirectory if it doesn't exist."""
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            print(f"Successfully created the directory: {path}")
        except OSError as e:
            print(f"Failed to create the {path} directory: {e}")
            sys.exit(1)
    else:
        print(f"Directory already exists: {path}")
#%% md
# ### Scrape web pages
#%%
def scrape_html(url):
    """Loads a web page and returns its source HTML."""
    # Setting up the WebDriver
    #service = Service(r'C:\Users\eyamr\OneDrive\00-Technology\msedgedriver\edgedriver_win64\msedgedriver.exe')
    service = Service('/Users/eyamrog/msedgedriver/edgedriver_mac64/msedgedriver')
    #service = Service('/home/eyamrog/msedgedriver/edgedriver_linux64/msedgedriver')

    # Configure Edge to run headless
    options = Options()
    # For modern Edge/Chromium; if incompatible with your version, try "--headless"
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Edge(service=service, options=options)
    html = None
    try:
        driver.get(url)

        # Explicit wait for stable page load
        wait = WebDriverWait(driver, 10)
        max_wait_time = 30
        start_time = time.time()
        previous_html = ''

        while True:
            current_html = driver.page_source
            if current_html == previous_html or time.time() - start_time > max_wait_time:
                break
            previous_html = current_html
            time.sleep(2)

        html = driver.page_source  # Capture page source
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
    finally:
        # Always close WebDriver
        driver.quit()

    return html
#%%
def scrape_html_docs(df, path):
    """Iterates over a DataFrame and saves HTML pages within multiple WebDriver sessions."""
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as e:
            logging.error(f"Failed to create the {path} directory: {e}")
            sys.exit(1)

    for _, row in tqdm(df.iterrows(), total=len(df), desc='Scraping HTML documents'):
        url = row['Post URL']
        doc_id = row['Post ID']
        filename = os.path.join(path, f"{doc_id}.html")

        page_source = scrape_html(url)  # Call the scrape_html function

        if page_source:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(page_source)
            logging.info(f"Saved: {filename}")
#%% md
# ## Scraping [Greenpeace Stories](https://www.greenpeace.org/international/story/)
#%% md
# ### Define local variables
#%%
id = 'grp'
path = os.path.join(output_directory, id)
dataset_filename_1 = f"{id}_list"
dataset_filename_2 = f"{id}"
#%% md
# ### Create output subdirectory
#%%
create_directory(path)
##%% md
## ### Capture a few document pages for inspection
##%%
#filename_sample_1 = 'greenpeace_stories_sample1.html'
#url_sample_1 = 'https://www.greenpeace.org/international/story/page/1/'
#filename_sample_11 = 'greenpeace_stories_sample11.html'
#url_sample_11 = 'https://www.greenpeace.org/international/story/77736/from-hiroshima-to-gaza-defending-peace/'
#filename_sample_2 = 'greenpeace_stories_sample2.html'
#url_sample_2 = 'https://www.greenpeace.org/international/story/page/2/'
#filename_sample_21 = 'greenpeace_stories_sample21.html'
#url_sample_21 = 'https://www.greenpeace.org/international/story/77406/boots-to-boost-justice-standing-in-solidarity-with-indonesian-migrant-fishers/'
#filename_sample_3 = 'greenpeace_stories_sample3.html'
#url_sample_3 = 'https://www.greenpeace.org/international/story/page/3/'
#filename_sample_31 = 'greenpeace_stories_sample31.html'
#url_sample_31 = 'https://www.greenpeace.org/international/story/76810/vanishing-millet-fields-endangered-sparrows-the-climate-crisis-and-taiwans-forgotten-guardians/'
##%%
#document_page_sample_1 = scrape_html(url_sample_1)
#
#with open(f'{path}/{filename_sample_1}', 'w', encoding='utf8', newline='\n') as file:
#    file.write(document_page_sample_1)
##%%
#document_page_sample_11 = scrape_html(url_sample_11)
#
#with open(f'{path}/{filename_sample_11}', 'w', encoding='utf8', newline='\n') as file:
#    file.write(document_page_sample_11)
##%%
#document_page_sample_2 = scrape_html(url_sample_2)
#
#with open(f'{path}/{filename_sample_2}', 'w', encoding='utf8', newline='\n') as file:
#    file.write(document_page_sample_2)
##%%
#document_page_sample_21 = scrape_html(url_sample_21)
#
#with open(f'{path}/{filename_sample_21}', 'w', encoding='utf8', newline='\n') as file:
#    file.write(document_page_sample_21)
##%%
#document_page_sample_3 = scrape_html(url_sample_3)
#
#with open(f'{path}/{filename_sample_3}', 'w', encoding='utf8', newline='\n') as file:
#    file.write(document_page_sample_3)
##%%
#document_page_sample_31 = scrape_html(url_sample_31)
#
#with open(f'{path}/{filename_sample_31}', 'w', encoding='utf8', newline='\n') as file:
#    file.write(document_page_sample_31)
##%% md
## ### Scraping the post metadata
##%%
#def scrape_posts(source, index_page_url_1, index_page_url_2, start_page, end_page):
#    """Iterates over a set of index pages and extracts post metadata."""
#    data = []
#
#    for i in tqdm(range(start_page, end_page + 1)):
#        url = f"{index_page_url_1}{i}{index_page_url_2}"
#
#        index_page = scrape_html(url)
#
#        # Parse page source with BeautifulSoup
#        soup = BeautifulSoup(index_page, 'lxml')
#
#        # Capture the listing page content
#        listing_page_content = soup.find('div', id='listing-page-content')
#
#        # Extract the items
#        if listing_page_content:
#            list = listing_page_content.find('ul', class_='wp-block-post-template')
#            if list:
#                items = list.find_all('li')
#
#        for item in items:
#            # Extract the item body
#            body = item.find('div', class_='query-list-item-body')
#
#            # Extract the post term
#            if body:
#                post_term = body.find('div', class_='wp-block-post-terms')
#                if post_term:
#                    post_term_text = ' '.join(post_term.get_text(' ', strip=True).split()) if post_term else ''
#
#            # Extract the post tags
#            if body:
#                post_tags = body.find('div', class_='taxonomy-post_tag wp-block-post-terms')
#                if post_tags:
#                    post_tags_list = [a.get_text(strip=True) for a in post_tags.select('a[rel="tag"]')]
#                    post_tags_text = ", ".join(post_tags_list) if post_tags_list else ''
#
#            # Extract the title
#            if body:
#                headline = body.find('h4', class_='query-list-item-headline wp-block-post-title')
#                title_text = ' '.join(headline.get_text(' ', strip=True).split()) if headline else ''
#
#            # Extract the post URL
#            if headline:
#                anchor_url = headline.find('a')
#                post_url = anchor_url['href'] if anchor_url else ''
#
#            ## Extract the category
#            #post_page = scrape_html(post_url)
#            #soup_article = BeautifulSoup(post_page, 'lxml')
#            #tag_wrap_issues = soup_article.find('div', class_='tag-wrap issues')
#            #if tag_wrap_issues:
#            #    anchor_category = tag_wrap_issues.find('a')
#            #    category_text = anchor_category.get_text(strip=True) if anchor_category else ''
#
#            # Extract the authors
#            if body:
#                authors = body.find('span', class_='article-list-item-author')
#                authors_text = ' '.join(authors.get_text(' ', strip=True).split()) if authors else ''
#
#            # Extract post date
#            if body:
#                post_date = body.find('div', class_='wp-block-post-date')
#                if post_date:
#                    time = post_date.find('time')
#                    post_date_time = time['datetime'] if time else ''
#
#            # Append the extracted data
#            data.append({
#                'Source': source,
#                'Post Term': post_term_text,
#                #'Category': category_text,
#                'Post Tags': post_tags_text,
#                'Title': title_text,
#                'Post URL': post_url,
#                'Authors': authors_text,
#                'Post Date': post_date_time
#            })
#
#    return pd.DataFrame(data)
##%%
#source = 'Greenpeace'
#index_page_url_1 = 'https://www.greenpeace.org/international/story/page/'
#index_page_url_2 = '/'
#start_page = 1
#end_page = 1
##%% md
## Note: On 17/08/2025, when the data was extracted, the end page was 136.
##%%
#df_grp = scrape_posts(source, index_page_url_1, index_page_url_2, start_page, end_page)
##%%
#df_grp['Post Date'] = pd.to_datetime(df_grp['Post Date'], errors='coerce', utc=True)
##%%
#df_grp['Post ID'] = id + df_grp.index.astype(str).str.zfill(6)
##%%
#df_grp.dtypes
##%%
#df_grp
##%% md
## #### Export to a file
##%%
#df_grp.to_json(f"{output_directory}/{dataset_filename_1}.jsonl", orient='records', lines=True)
#%% md
# ### Scrape the posts
#%% md
# #### Import the data into a DataFrame
#%%
df_grp = pd.read_json(f"{input_directory}/{dataset_filename_1}.jsonl", lines=True)
#%%
df_grp['Post Date'] = pd.to_datetime(df_grp['Post Date'], unit='ms')
#%% md
# #### Scrape the posts
#%%
scrape_html_docs(df_grp, path)
##%% md
## ### Extract the text from the posts
##%%
#def extract_text(df, path):
#    """Extracts text from HTML files and saves as text files."""
#
#    for post_id in df['Post ID']:
#        html_file = os.path.join(path, f"{post_id}.html")
#        txt_file = os.path.join(path, f"{post_id}.txt")
#
#        # Check if the HTML file exists
#        if not os.path.exists(html_file):
#            logging.error(f"Skipping {html_file}: File not found")
#            continue
#
#        # Read HTML content
#        with open(html_file, 'r', encoding='utf-8') as file:
#            soup = BeautifulSoup(file, 'lxml')
#
#        # Initialise text variable
#        text = ''
#
#        # Web Scraping - Begin
#
#        # Capture the 'article body'
#        post_body = soup.find('article')
#
#        # Extract the paragraphs
#        if post_body:
#            post_content = post_body.find('div', class_='post-content')
#            if post_content:
#                post_details = post_content.find('div', class_='post-details clearfix')
#                if post_details:
#                    # Iterate top-level content blocks in order: paragraphs and lists
#                    for block in post_details.find_all(['p', 'ul', 'ol'], recursive=False):
#                        if block.name == 'p':
#                            paragraph_text = ' '.join(block.get_text(' ', strip=True).split())
#                            text += f"{paragraph_text}\n"
#                        elif block.name in ('ul', 'ol'):
#                            # Capture top-level list items in order
#                            for li in block.find_all('li', recursive=False):
#                                li_text = ' '.join(li.get_text(' ', strip=True).split())
#                                text += f"{li_text}\n"
#
#        # Web Scraping - End
#
#        # Save text to a text file
#        with open(txt_file, 'w', encoding='utf-8', newline='\n') as file:
#            file.write(text)
#
#        logging.info(f"Saved text for {post_id} to {txt_file}")
##%%
#extract_text(df_grp, path)
##%% md
## ### Break down the texts into paragraphs
##%%
## Prepare to collect rows
#data = []
#
## Loop through each 'Post ID' in the DataFrame
#for _, row in df_grp.iterrows():
#    post_id = row['Post ID']
#
#    paragraph_count = 0
#    file_path = os.path.join(path, f"{post_id}.txt")
#
#    if not os.path.isfile(file_path):
#        print(f"Missing file: {file_path}")
#        continue
#
#    with open(file_path, 'r', encoding='utf-8') as file:
#        for line in file:
#            line = ' '.join(line.split()).strip()
#            if not line:
#                continue
#            paragraph_count += 1
#            data.append({
#                'Post ID': post_id,
#                'Paragraph': f"Paragraph {paragraph_count}",
#                'Text Paragraph': line
#                })
#
## Create final DataFrame
#df_paragraph = pd.DataFrame(data)
##%%
#df_paragraph
##%%
#df_grp_paragraph = df_grp.merge(df_paragraph, on='Post ID', how='left')
##%%
#df_grp_paragraph
##%% md
## #### Export to a file
##%%
#df_grp_paragraph.to_json(f"{output_directory}/{dataset_filename_2}.jsonl", orient='records', lines=True)
##%%
#df_grp_paragraph.to_excel(f"{output_directory}/{dataset_filename_2}.xlsx", index=False)