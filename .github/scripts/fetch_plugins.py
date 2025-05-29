import requests
import json
from datetime import datetime
import time
import re
import os
import subprocess # Git komutlarını çalıştırmak için eklendi

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


# Depo linkleri ve kısa kodlar
repos = {
    "https://raw.githubusercontent.com/GitLatte/Sinetech/builds/plugins.json": "Latte/sinetech",
    "https://raw.githubusercontent.com/nikyokki/nik-cloudstream/builds/plugins.json": "nikstream",
    "https://raw.githubusercontent.com/feroxx/Kekik-cloudstream/builds/plugins.json": "feroxxcs3",
    "https://raw.githubusercontent.com/MakotoTokioki/Cloudstream-Turkce-Eklentiler/refs/heads/main/plugins.json": "makoto",
    "https://raw.githubusercontent.com/maarrem/cs-Kekik/refs/heads/builds/plugins.json": "kekikdevam",
    "https://raw.githubusercontent.com/Kraptor123/cs-kekikanime/refs/heads/builds/plugins.json": "kekikan",
    "https://raw.githubusercontent.com/sarapcanagii/Pitipitii/refs/heads/builds/plugins.json": "sarapcanagii"
}

plugin_dict = {}
api_headers = get_api_headers()

all_plugins_raw = []
plugins_by_id = {}

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
                         else:
                             print(f"⚠️ Eklenti URL formatı tanınmadı: {plugin_file_url}")

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


                plugin["repoTimestamps"] = {repo_code: timestamp if timestamp else datetime.utcnow().isoformat() + "Z"}

                plugin_id = plugin.get("pluginId")
                if plugin_id:
                    if plugin_id not in plugins_by_id:
                        plugins_by_id[plugin_id] = []
                    plugins_by_id[plugin_id].append(plugin)

                all_plugins_raw.append(plugin)

            print(f"✅ {repo_url} başarıyla işlendi!")
        else:
            print(f"⚠️ {repo_url} için veri alınamadı (Hata: {response.status_code})")
    except Exception as e:
        print(f"⚠️ {repo_url} işlenirken hata oluştu: {e}")

for plugin in all_plugins_raw:
    plugin_id = plugin.get("pluginId")
    if plugin_id and plugin_id in plugins_by_id:
        common_repos = []
        for common_plugin_copy in plugins_by_id[plugin_id]:
             if common_plugin_copy.get("repoCodes"):
                 common_repos.extend(common_plugin_copy["repoCodes"])

        common_repos = [repo for repo in common_repos if repo not in plugin.get("repoCodes", [])]
        plugin["commonRepoCodes"] = list(set(common_repos))
    else:
        plugin["commonRepoCodes"] = []

datas_dir = "datas"
os.makedirs(datas_dir, exist_ok=True)

plugin_status_temp = {}

for repo_url, repo_code in repos.items():
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
                    (p.get("pluginId", p.get("name")), tuple(p.get("repoCodes", []))): p
                    for p in existing_plugins_list
                    if p.get("pluginId") or p.get("name")
                }

            except json.JSONDecodeError:
                print(f"⚠️ {existing_file_path} dosyası bozuk, yeniden oluşturuluyor.")
                existing_repo_plugins = {}


    current_repo_plugins_indexed = {
         (p.get("pluginId", p.get("name")), tuple(p.get("repoCodes", []))): p
         for p in all_plugins_raw
         if p.get("repoCodes") and p.get("repoCodes")[0] == repo_code
         and (p.get("pluginId") or p.get("name"))
    }

    for plugin_identifier_tuple, plugin_data in current_repo_plugins_indexed.items():
        plugin_id_or_name = plugin_identifier_tuple[0]
        repo_code_tuple = plugin_identifier_tuple[1]

        is_new = False
        is_updated = False

        if plugin_identifier_tuple not in existing_repo_plugins:
            is_new = True
        else:
            existing_plugin_data = existing_repo_plugins[plugin_identifier_tuple]
            if plugin_data.get("version") != existing_plugin_data.get("version") or \
               plugin_data.get("fileSize") != existing_plugin_data.get("fileSize") or \
               plugin_data.get("url") != existing_plugin_data.get("url"):
                is_updated = True

        plugin_status_temp[(plugin_id_or_name, repo_code)] = {'isNew': is_new, 'isUpdated': is_updated}

    plugins_for_this_repo = [p for p in all_plugins_raw if p.get("repoCodes") and p.get("repoCodes")[0] == repo_code]
    if not os.path.exists(existing_file_path):
        with open(existing_file_path, "w", encoding="utf-8") as dest_f:
            json.dump({"plugins": plugins_for_this_repo}, dest_f, ensure_ascii=False, indent=4)

    with open(new_file_path, "w", encoding="utf-8") as f:
        json.dump({"plugins": plugins_for_this_repo}, f, ensure_ascii=False, indent=4)

    with open(new_file_path, "r", encoding="utf-8") as src_f:
        new_content = src_f.read()
    with open(existing_file_path, "w", encoding="utf-8") as dest_f:
        dest_f.write(new_content)

final_plugins_list = []
for plugin in all_plugins_raw:
    plugin_id_or_name = plugin.get("pluginId", plugin.get("name"))
    repo_code = plugin.get("repoCodes")[0] if plugin.get("repoCodes") else None

    if plugin_id_or_name and repo_code:
        status_key = (plugin_id_or_name, repo_code)
        if status_key in plugin_status_temp:
            plugin["isNew"] = plugin_status_temp[status_key]['isNew']
            plugin["isUpdated"] = plugin_status_temp[status_key]['isUpdated']
        else:
             plugin["isNew"] = False
             plugin["isUpdated"] = False

    else:
         plugin["isNew"] = False
         plugin["isUpdated"] = False

    final_plugins_list.append(plugin)

current_time_iso = datetime.utcnow().isoformat() + "Z"
data_output = {
    "timestamp": current_time_iso,
    "plugins": final_plugins_list
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data_output, f, ensure_ascii=False, indent=4)

print(f"✅ Güncelleme tamamlandı! Son güncelleme zamanı: {current_time_iso}")

print("Git değişiklikleri ekliyor ve commit ediyor...")
if run_command("git add data.json datas/"):
    commit_message = f"Otomatik güncelleme: data.json ve datas/ ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
    run_command("git config user.name 'ActionHelper[bot]'")
    run_command("git config user.email '212895703+ActionHelper@users.noreply.github.com'")

    if run_command(f'git commit -m "{commit_message}"'):
        print("Değişiklikler commit edildi.")
    else:
        print("❌ Commit işlemi başarısız. Değişiklik yok olabilir.") # Commit atılacak değişiklik yoksa hata verebilir
else:
    print("❌ Git add işlemi başarısız.")
