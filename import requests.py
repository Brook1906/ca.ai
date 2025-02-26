import os
import requests
import pdfplumber
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import time

# Folders to save extracted text and PDFs
TEXT_FOLDER = "scraped_texts"
PDF_FOLDER = "downloaded_pdfs"
JSON_OUTPUT = "scraped_data.json"
os.makedirs(TEXT_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

# Set up Edge WebDriver
def get_edge_driver():
    options = Options()
    options.add_argument("--headless")  # Run in background
    options.add_argument("--disable-gpu")  
    options.add_argument("--log-level=3")  
    options.add_argument("--disable-usb-keyboard-detect")  
    service = Service("C:/Users/bodas/AppData/Local/Programs/Python/Python313/Lib/site-packages/selenium/webdriver/edgedriver_win32/msedgedriver.exe")
    return webdriver.Edge(service=service, options=options)

# Fetch page content using Selenium for JavaScript-heavy pages
def get_page_content(url):
    driver = get_edge_driver()
    driver.get(url)
    time.sleep(3)  # Allow JavaScript to load
    page_source = driver.page_source
    driver.quit()
    return page_source

# Keep track of visited pages to prevent loops
visited_urls = set()
MAX_DEPTH = 10  # Adjust this to limit how deep the scraper goes
scraped_data = []

# Function to sanitize filenames
def sanitize_filename(url):
    filename = urlparse(url).path.replace("/", "_").replace("-", "_")
    return filename[:150]  # Limit filename length to avoid OS errors

# Recursive function to scrape text and find all links
def scrape_text_and_links(url, base_url, depth=0):
    if depth > MAX_DEPTH:
        print(f"⚠️ Reached max depth ({MAX_DEPTH}), stopping recursion.")
        return

    if url in visited_urls or not url.startswith(base_url):
        return
    visited_urls.add(url)

    print(f"\n🔍 Scraping (Depth {depth}): {url}")
    page_content = get_page_content(url)
    soup = BeautifulSoup(page_content, "html.parser")

    # Extract and save text
    text = soup.get_text(separator="\n", strip=True)
    scraped_data.append({"url": url, "text": text})
    
    file_name = os.path.join(TEXT_FOLDER, sanitize_filename(url) + ".txt")
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(text)
    print(f"✅ Saved text: {file_name}")

    # Find and scrape all sub-links (limited depth)
    for link in soup.find_all("a", href=True):
        full_url = urljoin(base_url, link["href"])
        if base_url in full_url and full_url not in visited_urls:
            scrape_text_and_links(full_url, base_url, depth + 1)

# Function to scrape and download PDFs
def scrape_pdfs(url, base_url):
    page_content = get_page_content(url)
    soup = BeautifulSoup(page_content, "html.parser")

    for link in soup.find_all("a", href=True):
        if link["href"].endswith(".pdf"):
            pdf_url = urljoin(base_url, link["href"])
            pdf_name = os.path.join(PDF_FOLDER, pdf_url.split("/")[-1])

            if not os.path.exists(pdf_name):
                response = requests.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"})
                if response.status_code == 200:
                    with open(pdf_name, "wb") as file:
                        file.write(response.content)
                    print(f"📥 Downloaded PDF: {pdf_name}")
                extract_text_from_pdf(pdf_name, pdf_url)

# Extract text from PDFs and save in JSON
def extract_text_from_pdf(file_path, pdf_url):
    try:
        with pdfplumber.open(file_path) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        text_file = file_path.replace(".pdf", ".txt").replace(PDF_FOLDER, TEXT_FOLDER)
        with open(text_file, "w", encoding="utf-8") as file:
            file.write(text)
        print(f"📜 Extracted text from PDF: {text_file}")
        
        # Add to JSON output
        scraped_data.append({"url": pdf_url, "text": text})
    except Exception as e:
        print(f"❌ Error extracting PDF text: {e}")

# Save extracted data to JSON
def save_to_json():
    with open(JSON_OUTPUT, "w", encoding="utf-8") as json_file:
        json.dump(scraped_data, json_file, indent=4, ensure_ascii=False)
    print(f"📄 Data saved to {JSON_OUTPUT}")

# User input for base URL
base_url = input("Enter the starting URL to scrape: ")
scrape_text_and_links(base_url, base_url)
scrape_pdfs(base_url, base_url)
save_to_json()

print("\n🚀 Scraping completed successfully!")
