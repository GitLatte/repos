import requests
import json

# İşlenecek repo linkleri
repos = [
    "https://raw.githubusercontent.com/GitLatte/Sinetech/builds/plugins.json",
    "https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json",
    "https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/builds/plugins.json"
]

# GitHub API üzerinden commit tarihini almak için fonksiyon
def get_last_updated(repo_owner, repo_name, file_path):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits?path={file_path}&per_page=1"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]["commit"]["committer"]["date"]  # Son commit tarihi
    return "Bilinmiyor"

all_plugins = []

for repo in repos:
    try:
        response = requests.get(repo)
        if response.status_code == 200:
            plugins = response.json()
            
            for plugin in plugins:
                url_parts = plugin["url"].split("/")
                repo_owner = url_parts[3]  # GitHub Kullanıcı adı
                repo_name = url_parts[4]   # Repo adı
                file_path = "/".join(url_parts[6:])  # Dosya yolu (builds/EKLENTI_ADI.cs3 gibi)

                # API isteğini güvenli yapmak için
                if file_path.endswith(".cs3"):
                    last_updated = get_last_updated(repo_owner, repo_name, file_path)
                else:
                    last_updated = "Bilinmiyor"

                plugin["lastUpdated"] = last_updated

            all_plugins.extend(plugins)
        else:
            print(f"⚠️ {repo} için veri alınamadı (Hata: {response.status_code})")
    except Exception as e:
        print(f"⚠️ {repo} işlenirken hata oluştu: {e}")

# Sonuçları `data.json` dosyasına kaydet
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(all_plugins, f, ensure_ascii=False, indent=4)

print("✅ Güncelleme tarihleri başarıyla eklendi!")
