import requests
import os

# Proxy settings (if required)
proxies = {
    "http": "http://proxy.abs.com:port",
    "https": "http://proxy.abs.com:port"
}

# API URL and headers
url = "https://example.com/api"
headers = {
    "Authorization": f"Bearer {os.getenv('API_KEY')}",
    "Content-Type": "application/json"
}

# Make the request
response = requests.get(url, headers=headers, proxies=proxies)

# Print the response
print(response.status_code)
print(response.text)