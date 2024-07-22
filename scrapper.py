from firecrawl import FirecrawlApp
from dotenv import load_dotenv
import os 
from datetime import datetime
load_dotenv()

CRAWLER_API_KEY = os.getenv("CRAWLER_API_KEY")

def scrape_data(url):
    app = FirecrawlApp(api_key=CRAWLER_API_KEY)
    scraped_data = app.scrape_url(
        url,
        {'pageOptions':
            { 'onlyMainContent': True,
              'removeTags': ["pre",'footer','nav']
            },
        }
    )
    
    if 'markdown' in scraped_data:
        return scraped_data['markdown']
    else:
        raise KeyError("The key 'markdown' does not exist in the scraped data.")
    
def save_data(data, timestamp, filename,output_folder='output'):
    os.makedirs(output_folder, exist_ok=True)
    
    raw_output_path = os.path.join(output_folder, f'{filename}_{timestamp}.md')
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        f.write(data)
    print(f"Raw data saved to {raw_output_path}")