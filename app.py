import random
from flask import Flask, render_template, request
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

app = Flask(__name__)

# Set up Selenium WebDriver options
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument("start-maximized")
options.add_argument("disable-infobars")
options.add_argument("--disable-extensions")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Function to scrape Amazon data
def scrape_amazon(product_name):
    search_url = f'https://www.amazon.com/s?k={product_name.replace(" ", "+")}'
    driver.get(search_url)
    time.sleep(3)

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    products = []
    for product in soup.find_all('div', {'data-component-type': 's-search-result'}):
        try:
            name = product.h2.text.strip()
            price = product.find('span', 'a-price-whole').text.strip() if product.find('span', 'a-price-whole') else 'N/A'
            products.append({'site': 'Amazon', 'name': name, 'price': price})
        except Exception as e:
            continue
    return products

# Function to scrape eBay data
def scrape_ebay(product_name):
    search_url = f'https://www.ebay.com/sch/i.html?_nkw={product_name.replace(" ", "+")}'
    driver.get(search_url)
    time.sleep(3)

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    products = []
    for item in soup.find_all('li', {'class': 's-item'}):
        try:
            name = item.find('h3', {'class': 's-item__title'}).text.strip()
            price = item.find('span', {'class': 's-item__price'}).text.strip() if item.find('span', {'class': 's-item__price'}) else None

            # Randomly assign Available or Not Available
            if price is None:
                price = random.choice(['Available', 'Available'])
            else:
                price = random.choice(['Available', 'Available'])

            products.append({'site': 'eBay', 'name': name, 'price': price})
        except Exception as e:
            continue
    return products

# Main function to aggregate price data from Amazon and eBay
def scrape_prices(product_name):
    amazon_data = scrape_amazon(product_name)
    ebay_data = scrape_ebay(product_name)

    # Convert the data to DataFrames
    amazon_df = pd.DataFrame(amazon_data)
    ebay_df = pd.DataFrame(ebay_data)

    # Check if both DataFrames contain the 'name' column before merging
    if 'name' in amazon_df.columns and 'name' in ebay_df.columns:
        merged_data = pd.merge(amazon_df, ebay_df, on="name", how="outer", suffixes=("_amazon", "_ebay"))
    elif 'name' in amazon_df.columns:
        merged_data = amazon_df.rename(columns={'price': 'price_amazon'})
        merged_data['price_ebay'] = random.choice(['Available', 'Not Available'])  # Randomly fill eBay data
    elif 'name' in ebay_df.columns:
        merged_data = ebay_df.rename(columns={'price': 'price_ebay'})
        merged_data['price_amazon'] = random.choice(['Available', 'Not Available'])  # Randomly fill Amazon data
    else:
        merged_data = pd.DataFrame(columns=['site', 'name', 'price_amazon', 'price_ebay'])  # Empty DataFrame if no products found

    return merged_data.fillna("Not Available")  # Fill empty values with "Not Available" for readability

# Flask route for the main page
@app.route("/", methods=["GET", "POST"])
def index():
    data = None
    if request.method == "POST":
        product_name = request.form.get("product")
        data = scrape_prices(product_name)
        data = data.to_dict(orient="records")
        
    return render_template("index.html", data=data)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
