import requests
import json
from datetime import datetime
import time
import re
import os

# GitHub API için başlıklar
def get_api_headers():
    github_token = os.getenv('ACTIONHELPER')
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if github_token:
        headers['Authorization'] = f'token {github_token}'
        print(f"✓ GitHub token bulundu: {github_token[:4]}...")
    else:
        print("⚠️ GitHub token bulunamadı! API istekleri sınırlı olacak.")
    return headers

def get_last_updated(repo_url, file_path, headers):
    try:
        # GitHub API URL'sini oluştur
        api_url = repo_url.replace('raw.githubusercontent.com', 'api.github.com/repos')
        if '/builds/' in api_url:
            api_url = re.sub(r'/builds/.*', '', api_url) + '/commits'
        elif '/refs/heads/builds/' in api_url:
            api_url = re.sub(r'/refs/heads/builds/.*', '', api_url) + '/commits'

        params = {'path': file_path, 'per_page': 1}
        response = requests.get(api_url, headers=headers, params=params)

        if response.status_code in [403, 429]:
            print(f"⚠️ GitHub API rate limit aşıldı, bu eklenti için zaman atlanıyor. (Hata: {response.status_code})")
            return None  # Bekleme yok, direkt atla

        if response.status_code == 200:
            commits = response.json()
            if commits and len(commits) > 0:
                return commits[0]['commit']['committer']['date']
    except Exception as e:
        print(f"⚠️ Son güncelleme tarihi alınamadı: {e}")
    return None

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
api_headers = get_api_headers()

for repo_url, repo_code in repos.items():
    try:
        response = requests.get(repo_url)
        if response.status_code == 200:
            plugins = response.json()

            for plugin in plugins:
                plugin_name = plugin["name"]

                # Eklentinin dosya yolunu ve commit zamanını al
                if '/builds/' in plugin["url"]:
                    file_path = plugin["url"].split('/builds/')[-1]
                elif '/refs/heads/builds/' in plugin["url"]:
                    file_path = plugin["url"].split('/refs/heads/builds/')[-1]
                else:
                    file_path = plugin["url"]

                timestamp = get_last_updated(repo_url, file_path, api_headers)

                if plugin_name in plugin_dict:
                    # Aynı isim varsa repo kodunu ekle (tekrarsız)
                    if repo_code not in plugin_dict[plugin_name]["repoCodes"]:
                        plugin_dict[plugin_name]["repoCodes"].append(repo_code)
                else:
                    # Yeni eklenti kaydı
                    plugin_dict[plugin_name] = plugin
                    plugin_dict[plugin_name]["repoCodes"] = [repo_code]

                # Her eklentiye repoTimestamps alanını ekle/güncelle
                if "repoTimestamps" not in plugin_dict[plugin_name]:
                    plugin_dict[plugin_name]["repoTimestamps"] = {}
                if timestamp:
                    plugin_dict[plugin_name]["repoTimestamps"][repo_code] = timestamp

            print(f"✅ {repo_url} başarıyla işlendi!")
        else:
            print(f"⚠️ {repo_url} için veri alınamadı (Hata: {response.status_code})")
    except Exception as e:
        print(f"⚠️ {repo_url} işlenirken hata oluştu: {e}")

# Yeni dizin yapısını oluştur
datas_dir = "datas"
os.makedirs(datas_dir, exist_ok=True)

all_plugins_for_main_data_json = []

for repo_url, repo_code in repos.items():
    repo_data_dir = os.path.join(datas_dir, repo_code)
    os.makedirs(repo_data_dir, exist_ok=True)

    current_repo_plugins = {}
    try:
        response = requests.get(repo_url)
        if response.status_code == 200:
            plugins = response.json()
            for plugin in plugins:
                if plugin.get("status") == 0:
                    print(f"⚠️ Eklenti '{plugin.get('name', 'Bilinmeyen Eklenti')}' devre dışı (status: 0), atlanıyor.")
                    continue
                current_repo_plugins[plugin["name"]] = plugin
        else:
            print(f"⚠️ {repo_url} için veri alınamadı (Hata: {response.status_code})")
    except Exception as e:
        print(f"⚠️ {repo_url} işlenirken hata oluştu: {e}")

    # Mevcut ve yeni dosyaların yolları
    existing_file_path = os.path.join(repo_data_dir, f"{repo_code}_mevcut.json")
    new_file_path = os.path.join(repo_data_dir, f"{repo_code}_yeni.json")

    existing_repo_plugins = {}
    if os.path.exists(existing_file_path):
        with open(existing_file_path, "r", encoding="utf-8") as f:
            try:
                existing_repo_plugins = {p["name"]: p for p in json.load(f).get("plugins", [])}
            except json.JSONDecodeError:
                print(f"⚠️ {existing_file_path} dosyası bozuk, yeniden oluşturuluyor.")

    # isNew ve isUpdated durumlarını belirle
    processed_plugins = []
    for plugin_name, plugin_data in current_repo_plugins.items():
        is_new = False
        is_updated = False

        if plugin_name not in existing_repo_plugins:
            is_new = True
        else:
            # Eklenti daha önce varsa, güncellenip güncellenmediğini kontrol et
            # Basit bir karşılaştırma: versiyon veya dosya boyutu değişti mi?
            existing_plugin_data = existing_repo_plugins[plugin_name]
            if plugin_data.get("version") != existing_plugin_data.get("version") or \
               plugin_data.get("fileSize") != existing_plugin_data.get("fileSize") or \
               plugin_data.get("url") != existing_plugin_data.get("url"):
                is_updated = True

        plugin_data["isNew"] = is_new
        plugin_data["isUpdated"] = is_updated
        # plugin_dict'teki repoTimestamps bilgisini plugin_data'ya ekle
        if plugin_name in plugin_dict and "repoTimestamps" in plugin_dict[plugin_name]:
            plugin_data["repoTimestamps"] = plugin_dict[plugin_name]["repoTimestamps"]
        processed_plugins.append(plugin_data)

    # Eğer _mevcut.json dosyası yoksa, _yeni.json içeriğini _mevcut.json'a kopyala
    # Bu, ilk çalıştırmada _mevcut.json'ın oluşmasını sağlar
    if not os.path.exists(existing_file_path):
        with open(existing_file_path, "w", encoding="utf-8") as dest_f:
            json.dump({"plugins": processed_plugins}, dest_f, ensure_ascii=False, indent=4)

    # Yeni verileri _yeni.json dosyasına yaz
    with open(new_file_path, "w", encoding="utf-8") as f:
        json.dump({"plugins": processed_plugins}, f, ensure_ascii=False, indent=4)

    # Bir sonraki çalıştırma için _yeni.json içeriğini _mevcut.json'a kopyala
    # Bu, mevcut dosyanın güncel olmasını sağlar
    with open(new_file_path, "r", encoding="utf-8") as src_f:
        new_content = src_f.read()
    with open(existing_file_path, "w", encoding="utf-8") as dest_f:
        dest_f.write(new_content)

    # Ana data.json için eklentileri topla
    all_plugins_for_main_data_json.extend(processed_plugins)

# Ana data.json dosyasını oluştur
current_time_iso = datetime.utcnow().isoformat() + "Z"
data_output = {
    "timestamp": current_time_iso,
    "plugins": all_plugins_for_main_data_json
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data_output, f, ensure_ascii=False, indent=4)

print(f"✅ Güncelleme tamamlandı! Son güncelleme zamanı: {current_time_iso}")