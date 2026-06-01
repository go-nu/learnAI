import requests

# api_key
apiKey = ""

url = f"http://www.omdbapi.com/?s=movie&y=2026&apikey={apiKey}&page=1"
response = requests.get(url)

print(response.text)