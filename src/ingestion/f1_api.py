import requests

season = 2025
url = f"https://api.jolpi.ca/ergast/f1/{season}/driverstandings/"

try:
    reponse = requests.get(url, timeout=10)
except requests.RequestException as erreur:
    print(f"Erreur réseau : {erreur}")
else:
    if reponse.status_code == 200:
        data = reponse.json()
        print(data)
    else:
        print(f"Erreur lors de la requête : {reponse.status_code}")