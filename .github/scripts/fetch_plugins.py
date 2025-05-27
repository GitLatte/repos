import requests
import json

# Yeni eklenen repo linkleri ve kısa kodları
repos = {
    "https://raw.githubusercontent.com/GitLatte/Sinetech/builds/plugins.json": "sinetech",
    "https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json": "nikstream",
    "https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/builds/plugins.json": "feroxxcs3",
    "https://raw.githubusercontent.com/MakotoTokioki/Cloudstream-Turkce-Eklentiler/refs/heads/main/plugins.json": "makoto",
    "https://raw.githubusercontent.com/maarrem/cs-Kekik/refs/heads/builds/plugins.json": "kekikdevam",
    "https://raw.githubusercontent.com/Kraptor123/cs-kekikanime/refs/heads/builds/plugins.json": "kekikan",
    "https://raw.githubusercontent.com/sarapcanagii/Pitipitii/refs/heads/builds/plugins.json": "sarapcanagii"
}

# GitHub API üzerinden commit tarihini almak için fonksiyon
def get_last_updated(repo_owner, repo_name, file_path):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits?path={file_path}&per_page=1"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]["commit"]["committer"]["date"]  # ISO formatında tarih
    return "Bilinmiyor"

# ISO tarih formatını Türkçe formatta dönüştürme fonksiyonu
def format_date(iso_string):
    if not iso_string or iso_string == "Bilinmiyor":
        return "Bilinmiyor"
    date = iso_string.replace("Z", "").replace("T", " ")
    return date.split(".")[0]  # Milisaniyeleri kaldır

all_plugins = []

for repo_url, repo_code in repos.items():
    try:
        response = requests.get(repo_url)
        if response.status_code == 200:
            plugins = response.json()
            
            for plugin in plugins:
                plugin["repoCode"] = repo_code  # Depo ekleme kodu ekleme

                url_parts = plugin["url"].split("/")
                if len(url_parts) < 7:
                    plugin["lastUpdated"] = "Bilinmiyor"
                    continue
                
                repo_owner = url_parts[3]  
                repo_name = url_parts[4]   
                file_path = "/".join(url_parts[6:])  

                last_updated = get_last_updated(repo_owner, repo_name, file_path)
                plugin["lastUpdated"] = format_date(last_updated) 

            all_plugins.extend(plugins)
        else:
            print(f"⚠️ {repo_url} için veri alınamadı (Hata: {response.status_code})")
    except Exception as e:
        print(f"⚠️ {repo_url} işlenirken hata oluştu: {e}")

# Sonuçları `data.json` dosyasına kaydet
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(all_plugins, f, ensure_ascii=False, indent=4)

print("✅ Güncelleme tamamlandı! Yeni repos ve doğru tarih formatı eklendi.")
