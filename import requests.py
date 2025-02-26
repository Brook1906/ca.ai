import os
import requests
import pdfplumber
import yfinance as yf
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import time
import pandas as pd

# Folders to save extracted text and PDFs
TEXT_FOLDER = "scraped_texts"
PDF_FOLDER = "downloaded_pdfs"
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

# Recursive function to scrape text and find all links
def scrape_text_and_links(url, base_url):
    if url in visited_urls or not url.startswith(base_url):
        return
    visited_urls.add(url)

    print(f"\n🔍 Scraping: {url}")
    page_content = get_page_content(url)
    soup = BeautifulSoup(page_content, "html.parser")

    # Save extracted text
    text = soup.get_text(separator="\n", strip=True)
    file_name = os.path.join(TEXT_FOLDER, urlparse(url).path.replace("/", "_") + ".txt")
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(text)
    print(f"✅ Saved text: {file_name}")

    # Find and scrape all sub-links
    for link in soup.find_all("a", href=True):
        full_url = urljoin(base_url, link["href"])
        if base_url in full_url and full_url not in visited_urls:
            scrape_text_and_links(full_url, base_url)

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
                extract_text_from_pdf(pdf_name)

# Extract text from PDFs
def extract_text_from_pdf(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        text_file = file_path.replace(".pdf", ".txt").replace(PDF_FOLDER, TEXT_FOLDER)
        with open(text_file, "w", encoding="utf-8") as file:
            file.write(text)
        print(f"📜 Extracted text from PDF: {text_file}")
    except Exception as e:
        print(f"❌ Error extracting PDF text: {e}")

# Function to fetch all NSE stock symbols
def get_nse_stock_symbols():
    url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        stock_symbols = [item['symbol'] + ".NS" for item in data["data"]]
        return stock_symbols
    else:
        print("❌ Failed to fetch NSE stock symbols")
        return []

# Function to fetch stock prices for all NSE companies
def get_all_stock_prices():
    stock_symbols = get_nse_stock_symbols()  # Get all NSE stock symbols
    stock_data = []
    
    for stock_symbol in stock_symbols:
        try:
            stock = yf.Ticker(stock_symbol)
            stock_info = stock.history(period="1mo")
            latest_price = stock_info["Close"].iloc[-1] if not stock_info.empty else "No Data"
            
            print(f"✅ {stock_symbol}: ₹{latest_price}")
            stock_data.append({"Symbol": stock_symbol, "Price": latest_price})
        
        except Exception as e:
            print(f"❌ Error fetching {stock_symbol}: {e}")

    # Save to CSV
    df = pd.DataFrame(stock_data)
    df.to_csv("all_stock_prices.csv", index=False)
    print("\n✅ All stock prices saved to all_stock_prices.csv")

# User input for base URL
base_url = input("Enter the starting URL to scrape: ")
scrape_text_and_links(base_url, base_url)
scrape_pdfs(base_url, base_url)
get_all_stock_prices()

print("\n🚀 Scraping completed successfully!")
