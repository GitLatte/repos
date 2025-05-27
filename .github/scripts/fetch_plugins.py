import requests
import json
import os

# GitHub token'ı al
github_token = os.getenv('PAT_TOKEN')
if not github_token:
    print("⚠️ PAT_TOKEN bulunamadı! API rate limit düşük olacak.")

# API headers'ı hazırla
api_headers = {
    "Accept": "application/vnd.github.v3+json"
}
if github_token:
    api_headers["Authorization"] = f"token {github_token}"
    print("✅ GitHub token başarıyla yüklendi.")

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
    # GitHub API URL'ini düzelt
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"
    params = {
        "path": file_path.lstrip("/"),  # Başındaki / karakterini kaldır
        "per_page": 1
    }
    
    try:
        print(f"🔍 Tarih alınıyor: {repo_owner}/{repo_name} - {file_path}")
        response = requests.get(api_url, params=params, headers=api_headers)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                commit_date = data[0]["commit"]["committer"]["date"]
                print(f"✅ Tarih alındı: {commit_date}")
                return commit_date
            else:
                print(f"⚠️ Commit bulunamadı: {repo_owner}/{repo_name}")
        else:
            print(f"⚠️ API Hatası ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Hata oluştu: {str(e)}")
    
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
        print(f"\n📦 {repo_url} deposundan eklentiler alınıyor...")
        response = requests.get(repo_url)
        if response.status_code == 200:
            plugins = response.json()
            
            for plugin in plugins:
                plugin["repoCode"] = repo_code
                
                # URL'yi parse et
                if "url" in plugin:
                    url = plugin["url"]
                    print(f"\n🔍 İşleniyor: {plugin['name']} ({url})")
                    
                    # GitHub raw URL'sini parse et
                    if "raw.githubusercontent.com" in url:
                        parts = url.split("/")
                        if len(parts) >= 4:  # En az 4 parça olmalı: ['https:', '', 'raw.githubusercontent.com', 'owner', 'repo', ...]                            
                            repo_owner = parts[3]
                            repo_name = parts[4]
                            file_path = "/".join(parts[5:])
                            
                            print(f"📄 Dosya bilgileri:\n  Repo: {repo_owner}/{repo_name}\n  Yol: {file_path}")
                            
                            last_updated = get_last_updated(repo_owner, repo_name, file_path)
                            plugin["lastUpdated"] = format_date(last_updated)
                        else:
                            print(f"⚠️ Geçersiz URL formatı: {url}")
                            plugin["lastUpdated"] = "Bilinmiyor"
                    else:
                        print(f"⚠️ GitHub raw URL'si değil: {url}")
                        plugin["lastUpdated"] = "Bilinmiyor"
                else:
                    print(f"⚠️ URL bulunamadı: {plugin['name']}")
                    plugin["lastUpdated"] = "Bilinmiyor"
                
            all_plugins.extend(plugins)
            print(f"✅ {len(plugins)} eklenti başarıyla işlendi.")
        else:
            print(f"⚠️ {repo_url} için veri alınamadı (Hata: {response.status_code})")
    except Exception as e:
        print(f"❌ {repo_url} işlenirken hata oluştu: {e}")

# Sonuçları `data.json` dosyasına kaydet
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(all_plugins, f, ensure_ascii=False, indent=4)

print("✅ Güncelleme tamamlandı! Yeni repos ve doğru tarih formatı eklendi.")
