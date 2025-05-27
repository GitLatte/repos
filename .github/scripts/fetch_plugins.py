import requests
import json
from bs4 import BeautifulSoup

# Depo linkleri ve kısa kodlar
repos = {
    "https://raw.githubusercontent.com/GitLatte/Sinetech/builds/plugins.json": "sinetech",
    "https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json": "nikstream",
    "https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/builds/plugins.json": "feroxxcs3",
    "https://raw.githubusercontent.com/MakotoTokioki/Cloudstream-Turkce-Eklentiler/refs/heads/main/plugins.json": "makoto",
    "https://raw.githubusercontent.com/maarrem/cs-Kekik/refs/heads/builds/plugins.json": "kekikdevam",
    "https://raw.githubusercontent.com/Kraptor123/cs-kekikanime/refs/heads/builds/plugins.json": "kekikan",
    "https://raw.githubusercontent.com/sarapcanagii/Pitipitii/refs/heads/builds/plugins.json": "sarapcanagii"
}

# GitHub HTML kaynak kodundan son güncelleme tarihini alma fonksiyonu
def get_last_updated_from_github(cs3_url):
    github_url = cs3_url.replace("raw.githubusercontent.com", "github.com").replace("/builds/", "/blob/builds/")
    
    response = requests.get(github_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        relative_time_tag = soup.find("relative-time")
        
        if relative_time_tag:
            return relative_time_tag["datetime"].split("T")[0] + " " + relative_time_tag["datetime"].split("T")[1][:5]  # DD/MM/YYYY HH:mm formatı
    return "Bilinmiyor"

all_plugins = []

for repo_url, repo_code in repos.items():
    try:
        response = requests.get(repo_url)
        if response.status_code == 200:
            plugins = response.json()
            
            for plugin in plugins:
                plugin["repoCode"] = repo_code  # Depo ekleme kodu ekleme

                # Eğer plugin içinde 'url' alanı varsa, bu dosyanın son güncelleme tarihini al
                if "url" in plugin:
                    last_updated = get_last_updated_from_github(plugin["url"])
                    plugin["lastUpdated"] = last_updated
                else:
                    plugin["lastUpdated"] = "Bilinmiyor"  # Eğer `url` yoksa bilinmiyor olarak işaretle
                
            all_plugins.extend(plugins)
        else:
            print(f"⚠️ {repo_url} için veri alınamadı (Hata: {response.status_code})")
    except Exception as e:
        print(f"⚠️ {repo_url} işlenirken hata oluştu: {e}")

# Sonuçları `data.json` dosyasına kaydet
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(all_plugins, f, ensure_ascii=False, indent=4)

print("✅ Güncelleme tamamlandı! Son güncelleme tarihleri artık doğru şekilde JSON içinde yer alıyor.")
