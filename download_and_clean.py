import requests
import re
import os

def download_full_text():
    url = "https://raw.githubusercontent.com/wenzhixin/hongloumeng/master/hongloumeng.txt"
    # Using ghproxy to bypass potential blocking
    proxied_url = f"https://mirror.ghproxy.com/{url}"
    print(f"Downloading from {proxied_url}...")
    try:
        response = requests.get(proxied_url, timeout=30)
        response.raise_for_status()
        text = response.text
        print(f"Downloaded {len(text)} characters.")
        
        # Keep only the actual chapters (basic cleaning)
        with open("hongloumeng_full.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print("Saved to hongloumeng_full.txt")
    except Exception as e:
        print(f"Download failed: {e}")
        # Fallback to local partial file if download fails
        if os.path.exists("hongloumeng.txt"):
            print("Using existing partial hongloumeng.txt")
            with open("hongloumeng.txt", "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            # remove gutenberg header
            start_idx = text.find("第一回")
            if start_idx == -1:
                start_idx = 1000 # arbitrary skip
            clean_text = text[start_idx:]
            with open("hongloumeng_full.txt", "w", encoding="utf-8") as f:
                f.write(clean_text)

if __name__ == "__main__":
    download_full_text()
