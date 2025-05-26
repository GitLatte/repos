import requests
import json

# İşlenecek repo linkleri
repos = [
    "https://raw.githubusercontent.com/GitLatte/Sinetech/builds/plugins.json",
    "https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json",
    "https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/builds/plugins.json"
]

# JSON verilerini saklamak için boş liste
all_plugins = []

for repo in repos:
    try:
        response = requests.get(repo)
        if response.status_code == 200:
            plugins = response.json()
            all_plugins.extend(plugins)
        else:
            print(f"⚠️ {repo} için veri alınamadı (Hata: {response.status_code})")
    except Exception as e:
        print(f"⚠️ {repo} işlenirken hata oluştu: {e}")

# Sonuçları `data.json` dosyasına kaydet
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(all_plugins, f, ensure_ascii=False, indent=4)

print("✅ Tüm eklenti bilgileri başarıyla `data.json` dosyasına kaydedildi!")
