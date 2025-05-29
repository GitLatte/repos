import requests
import json
from datetime import datetime, timedelta
import time
import re
import os
import subprocess

YENI_BEKLEME_SAATI = 72  # 3 gün

def run_command(command):
    try:
        print(f"Çalıştırılıyor: {command}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✓ Başarılı.")
        print(result.stdout)
        if result.stderr:
            print("Stderr:")
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Hata oluştu: {e}")
        print("Stderr:")
        print(e.stderr)
        print("Stdout:")
        print(e.stdout)
        return False
    except FileNotFoundError:
        print(f"❌ Komut bulunamadı: {command.split()[0]}")
        return False

def get_api_headers():
    github_token = os.getenv('ACTIONHELPER')
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if github_token:
        headers['Authorization'] = f'token {github_token}'
        print(f"✓ GitHub token bulundu: {github_token[:4]}...")
    else:
        print("⚠️ GitHub token bulunamadı! API istekleri sınırlı olacak.")
    return headers

def get_last_updated_by_api(api_commit_url_base, file_path, headers):
     try:
        params = {'path': file_path, 'per_page': 1}
        response = requests.get(api_commit_url_base, headers=headers, params=params)

        if response.status_code in [403, 429]:
            print(f"⚠️ GitHub API rate limit aşıldı, commit zamanı atlanıyor. (Hata: {response.status_code})")
            return None

        if response.status_code == 200:
            commits = response.json()
            if commits and len(commits) > 0:
                return commits[0]['commit']['committer']['date']
        else:
             print(f"⚠️ {api_commit_url_base} adresinden commit bilgisi alınamadı (Hata: {response.status_code})")

     except Exception as e:
         print(f"⚠️ Commit zamanı alınırken hata oluştu: {e}")
     return None

repos = {
    "https://raw.githubusercontent.com/GitLatte/Sinetech/builds/plugins.json": "Latte",
    "https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json": "nikstream",
    "https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/builds/plugins.json": "feroxxcs3",
    "https://raw.githubusercontent.com/MakotoTokioki/Cloudstream-Turkce-Eklentiler/refs/heads/main/plugins.json": "makoto",
    "https://raw.githubusercontent.com/maarrem/cs-Kekik/refs/heads/builds/plugins.json": "kekikdevam",
    "https://raw.githubusercontent.com/Kraptor123/cs-kekikanime/refs/heads/builds/plugins.json": "kekikan",
    "https://raw.githubusercontent.com/sarapcanagii/Pitipitii/refs/heads/builds/plugins.json": "sarapcanagii",
    "https://raw.githubusercontent.com/Sertel392/Makotogecici/refs/heads/main/plugins.json": "MakotoGecici"
}

api_headers = get_api_headers()

all_plugins_raw = []

print("Eklentiler repolardan çekiliyor...")
for repo_url, repo_code in repos.items():
    try:
        response = requests.get(repo_url)
        if response.status_code == 200:
            plugins = response.json()
            if isinstance(plugins, dict) and 'plugins' in plugins:
                plugins = plugins['plugins']
            elif not isinstance(plugins, list):
                 print(f"⚠️ {repo_url} beklenmeyen JSON formatı algılandı (liste değil). Atlanıyor.")
                 continue

            print(f"✅ {repo_url} ({repo_code}) başarıyla çekildi, {len(plugins)} eklenti bulundu.")

            temp_plugins_from_repo = []
            for plugin in plugins:
                if plugin.get("status") == 0:
                    print(f"⚠️ Eklenti '{plugin.get('name', 'Bilinmeyen Eklenti')}' ({repo_code}) devre dışı (status: 0), atlanıyor.")
                    continue

                plugin["repoCodes"] = [repo_code]

                plugin_file_url = plugin.get("url")
                file_path = None
                if plugin_file_url:
                    try:
                         path_match = re.search(r'raw.githubusercontent.com/[^/]+/[^/]+/[^/]+/(.+)', plugin_file_url)
                         if path_match:
                             file_path = path_match.group(1)
                    except Exception as e:
                         print(f"⚠️ Eklenti URL işlenirken hata oluştu: {e}")

                timestamp = None
                if file_path:
                     try:
                          url_parts = plugin_file_url.split('raw.githubusercontent.com/')[-1].split('/')
                          if len(url_parts) >= 3:
                              repo_owner = url_parts[0]
                              repo_name = url_parts[1]
                              branch = url_parts[2]
                              api_commit_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits'
                              timestamp = get_last_updated_by_api(api_commit_url, file_path, api_headers)
                          else:
                                print(f"⚠️ Eklenti URL'sinden repo bilgisi alınamadı: {plugin_file_url}")
                     except Exception as e:
                          print(f"⚠️ Eklentinin commit zamanı alınırken hata oluştu: {e}")
                else:
                     print(f"⚠️ Eklenti '{plugin.get('name', 'Bilinmeyen Eklenti')}' ({repo_code}) için dosya yolu yok, commit zamanı atlanıyor.")

                if "repoTimestamps" not in plugin:
                     plugin["repoTimestamps"] = {}
                plugin["repoTimestamps"][repo_code] = timestamp if timestamp else datetime.utcnow().isoformat() + "Z"

                temp_plugins_from_repo.append(plugin)

            all_plugins_raw.extend(temp_plugins_from_repo)
            print(f"✅ {repo_url} ({repo_code}) işlendi, {len(temp_plugins_from_repo)} eklenti all_plugins_raw'a eklendi.")
            print(f"Toplam all_plugins_raw boyutu: {len(all_plugins_raw)}")

        else:
            print(f"⚠️ {repo_url} ({repo_code}) için veri alınamadı (Hata: {response.status_code})")
    except Exception as e:
        print(f"⚠️ {repo_url} ({repo_code}) işlenirken hata oluştu: {e}")

print("\n--- Tüm repolar gezildi ---")
print(f"Tüm repolardan çekilen toplam ham eklenti sayısı (all_plugins_raw): {len(all_plugins_raw)}")

datas_dir = "datas"
os.makedirs(datas_dir, exist_ok=True)

plugin_status_temp = {}

print("\nDepo özelindeki dosyalar (mevcut/yeni) oluşturuluyor...")
all_unique_repo_codes = list(repos.values())

for repo_code in all_unique_repo_codes:
    repo_data_dir = os.path.join(datas_dir, repo_code.replace('/', '_'))
    os.makedirs(repo_data_dir, exist_ok=True)

    existing_file_path = os.path.join(repo_data_dir, f"{repo_code.replace('/', '_')}_mevcut.json")
    new_file_path = os.path.join(repo_data_dir, f"{repo_code.replace('/', '_')}_yeni.json")

    existing_repo_plugins = {}
    if os.path.exists(existing_file_path):
        with open(existing_file_path, "r", encoding="utf-8") as f:
            try:
                existing_plugins_list = json.load(f).get("plugins", [])
                existing_repo_plugins = {
                    ((p.get("pluginId") or p.get("name")), p.get("repoCodes")[0] if p.get("repoCodes") else None): p
                    for p in existing_plugins_list
                    if (p.get("pluginId") or p.get("name")) and (p.get("repoCodes") and p.get("repoCodes")[0])
                }
            except json.JSONDecodeError:
                print(f"⚠️ {existing_file_path} dosyası bozuk, yeniden oluşturuluyor.")
                existing_repo_plugins = {}

    current_repo_plugins_for_status = []
    for plugin in all_plugins_raw:
        if plugin.get("repoCodes") and plugin.get("repoCodes")[0] == repo_code:
             current_repo_plugins_for_status.append(plugin)

    for plugin_data in current_repo_plugins_for_status:
        plugin_id_or_name = plugin_data.get("pluginId") or plugin_data.get("name")
        current_plugin_repo_code = plugin_data.get("repoCodes")[0] if plugin_data.get("repoCodes") else None

        if not plugin_id_or_name or not current_plugin_repo_code:
             continue

        status_key = (plugin_id_or_name, current_plugin_repo_code)

        # --- ADDEDAT EKLEME ve KORUMA ---
        added_at = None
        if status_key in existing_repo_plugins:
            added_at = existing_repo_plugins[status_key].get("addedAt")
        if not added_at:
            # Eğer eklenti eski dosyada yoksa veya addedAt yoksa, şu anki zamanı ata
            added_at = datetime.utcnow().isoformat() + "Z"
        plugin_data["addedAt"] = added_at
        # --- ADDEDAT BİTTİ ---

        # --- isNew Hesaplama ---
        now = datetime.utcnow()
        try:
            added_at_dt = datetime.fromisoformat(added_at.replace("Z", ""))
        except Exception:
            added_at_dt = now
        is_new = (now - added_at_dt) < timedelta(hours=YENI_BEKLEME_SAATI)
        # --- isNew Bitti ---

        is_updated = False
        if status_key not in existing_repo_plugins:
            is_updated = False
        else:
            existing_plugin_data = existing_repo_plugins[status_key]
            if plugin_data.get("version") != existing_plugin_data.get("version") or \
               plugin_data.get("fileSize") != existing_plugin_data.get("fileSize") or \
               plugin_data.get("url") != existing_plugin_data.get("url"):
                is_updated = True

        plugin_status_temp[status_key] = {'isNew': is_new, 'isUpdated': is_updated, 'addedAt': added_at}

    plugins_for_this_repo = [p for p in all_plugins_raw if p.get("repoCodes") and p.get("repoCodes")[0] == repo_code]

    # --- addedAt bilgisini json'a mutlaka ekle ---
    for p in plugins_for_this_repo:
        key = ((p.get("pluginId") or p.get("name")), p.get("repoCodes")[0] if p.get("repoCodes") else None)
        if key in plugin_status_temp:
            p["addedAt"] = plugin_status_temp[key]['addedAt']

    if not os.path.exists(existing_file_path):
        with open(existing_file_path, "w", encoding="utf-8") as dest_f:
            json.dump({"plugins": plugins_for_this_repo}, dest_f, ensure_ascii=False, indent=4)

    with open(new_file_path, "w", encoding="utf-8") as f:
        json.dump({"plugins": plugins_for_this_repo}, f, ensure_ascii=False, indent=4)

    with open(new_file_path, "r", encoding="utf-8") as src_f:
        new_content = src_f.read()
    with open(existing_file_path, "w", encoding="utf-8") as dest_f:
        dest_f.write(new_content)

print("Depo özelindeki dosyalar tamamlandı.")

print("\nFinal data.json listesi oluşturuluyor...")
final_plugins_list = []
for plugin in all_plugins_raw:
    plugin_id_or_name = plugin.get("pluginId") or plugin.get("name")
    plugin_repo_code = plugin.get("repoCodes")[0] if plugin.get("repoCodes") else None

    overall_is_new = False
    overall_is_updated = False
    added_at = None

    if plugin_id_or_name and plugin_repo_code:
         status_key = (plugin_id_or_name, plugin_repo_code)
         if status_key in plugin_status_temp:
              overall_is_new = plugin_status_temp[status_key]['isNew']
              overall_is_updated = plugin_status_temp[status_key]['isUpdated']
              added_at = plugin_status_temp[status_key]['addedAt']
              if overall_is_new:
                  overall_is_updated = False

    plugin["isNew"] = overall_is_new
    plugin["isUpdated"] = overall_is_updated
    plugin["addedAt"] = added_at

    plugin["repoUpdated"] = {}
    if plugin_id_or_name and plugin_repo_code:
         status_key = (plugin_id_or_name, plugin_repo_code)
         if status_key in plugin_status_temp:
              plugin["repoUpdated"][plugin_repo_code] = plugin_status_temp[status_key]['isUpdated']

    final_plugins_list.append(plugin)

current_time_iso = datetime.utcnow().isoformat() + "Z"
data_output = {
    "timestamp": current_time_iso,
    "plugins": final_plugins_list
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data_output, f, ensure_ascii=False, indent=4)

print(f"\n✅ Ana data.json dosyası oluşturuldu! Son güncelleme zamanı: {current_time_iso}")

print("\nGit değişiklikleri ekliyor ve commit ediyor...")
if run_command("git add data.json datas/"):
    commit_message = f"Otomatik güncelleme: data.json ve datas/ ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
    run_command("git config user.name 'ActionHelper[bot]'")
    run_command("git config user.email '212895703+ActionHelper@users.noreply.github.com'")

    if run_command(f'git commit -m "{commit_message}"'):
        print("Değişiklikler commit edildi.")
    else:
        print("ℹ️ Commit edilecek değişiklik yok veya commit işlemi başarısız.")

else:
    print("❌ Git add işlemi başarısız.")
