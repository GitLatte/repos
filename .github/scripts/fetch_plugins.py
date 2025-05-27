import requests
import json

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

plugin_dict = {}

for repo_url, repo_code in repos.items():
    try:
        response = requests.get(repo_url)
        if response.status_code == 200:
            plugins = response.json()
            
            for plugin in plugins:
                plugin_name = plugin["name"]
                
                # Eğer eklenti daha önce eklendiyse, repo kodunu ekleyelim
                if plugin_name in plugin_dict:
                    plugin_dict[plugin_name]["repoCodes"].append(repo_code)
                else:
                    plugin_dict[plugin_name] = plugin
                    plugin_dict[plugin_name]["repoCodes"] = [repo_code]  # Yeni repo kodu listesi oluştur
                
            print(f"✅ {repo_url} başarıyla işlendi!")
        else:
            print(f"⚠️ {repo_url} için veri alınamadı (Hata: {response.status_code})")
    except Exception as e:
        print(f"⚠️ {repo_url} işlenirken hata oluştu: {e}")

# Sonuçları `data.json` dosyasına kaydet
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(list(plugin_dict.values()), f, ensure_ascii=False, indent=4)

print("✅ Güncelleme tamamlandı! Artık aynı eklenti birden fazla depoda varsa repo kodları birleşiyor.")
