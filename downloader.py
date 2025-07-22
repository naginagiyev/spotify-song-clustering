import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SpotiDownloader:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)

    def download_song(self, name: str, author: str, uri: str):
        self.driver.get("https://spotidown.app/")
        self.wait.until(EC.visibility_of_element_located((By.ID, "url"))).send_keys(f"https://open.spotify.com/track/{uri}")
        self.wait.until(EC.element_to_be_clickable((By.ID, "send"))).click()
        self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#download-section > div > div > div > div.mb-3.grid-container > div:nth-child(3) > form > div > button"))).click()
        link_elem = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='rapid.spotidown.app/?token=']")))
        download_url = link_elem.get_attribute("href")
        if download_url:
            headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://spotidown.app/"}
            r = requests.get(download_url, headers=headers)
            if r.status_code == 200:
                with open(f"./songs/{name} by {author}.wav", "wb") as f:
                    f.write(r.content)

    def download_cover(self, name:str, author:str, uri:str):
        self.driver.get("https://www.spotifycover.art/")
        input_box = self.wait.until(EC.visibility_of_element_located((By.ID, "linkInput")))
        input_box.send_keys(f"https://open.spotify.com/track/{uri}")
        input_box.send_keys(Keys.ENTER)

        img = self.wait.until(EC.visibility_of_element_located((By.ID, "image")))
        img_url = img.get_attribute("src")

        response = requests.get(img_url)
        response.raise_for_status()

        with open(f"./covers/{name} by {author}.png", "wb") as f:
            f.write(response.content)

    def close(self):
        self.driver.quit()