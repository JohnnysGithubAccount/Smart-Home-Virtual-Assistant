import os
import json
import subprocess

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool

@tool
def search_information() -> str:
    """Search for all the information in the world"""
    return "He is a person."

@tool
def open_chrome() -> str:
    """Open Google Chrome browser."""
    return "Chrome opened."

# @tool
def navigate_to_hackernews() -> str:
    """Navigate to Hacker News website."""
    return "Navigated to Hacker News."

# @tool
def get_https_links(url: str) -> list[str]:
    """Get all HTTPS links from a given web page URL."""
    return ["https://example.com", "https://news.ycombinator.com"]


# def open_chrome(self):
#     try:
#         subprocess.run(["open", "-a", "Google Chrome"], check=True)
#         print("Google Chrome opened successfully.")
#     except subprocess.CalledProcessError as e:
#         print(f"Failed to open Google Chrome: {e}")
#
#
# def navigate_to_hackernews(self, query):
#     self.url = "https://news.ycombinator.com/"
#     try:
#         subprocess.run(["open", "-a", "Google Chrome", self.url], check=True)
#         print(f"Opened '{query}' opened in Google Chrome.")
#     except subprocess.CalledProcessError as e:
#         print(f"Failed to open search in Google Chrome: {e}")
#
#
# def get_https_links(self, url):
#     try:
#         response = requests.get(url)
#         response.raise_for_status()
#
#         soup = BeautifulSoup(response.text, 'html.parser')
#         links = soup.find_all('a')
#
#         for link in links:
#             link_text = link.get_text(strip=True)
#             link_url = link.get('href')
#             if link_url and link_url.startswith('https'):
#                 print(f"Link Name: {link_text if link_text else 'No text'}")
#                 print(f"Link URL: {link_url}")
#                 print('---')
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching the URL: {e}")

TOOLS = {
    "open_chrome": open_chrome,
    "search_information": search_information,
}