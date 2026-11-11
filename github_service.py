import re
import requests
import json

def parse_version(v_str):
    """
    Extrai números de versão em tuplas (ex: 'v1.2.3' -> (1, 2, 3)).
    Permite comparação correta de versões semânticas.
    """
    if not v_str:
        return (0, 0, 0)
    cleaned = re.sub(r'^[^\d]*', '', str(v_str).strip())
    parts = re.split(r'[-+.]', cleaned)
    nums = []
    for p in parts:
        if p.isdigit():
            nums.append(int(p))
        else:
            break
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)

def is_newer_version(latest_str, current_str):
    """Retorna True se latest_str for estritamente mais recente que current_str."""
    return parse_version(latest_str) > parse_version(current_str)

def get_latest_release(repo, token=None):
    """
    Consulta a API do GitHub para obter a última release do repositório.
    Funciona tanto para repos públicos quanto PRIVADOS se o token for fornecido.
    """
    if not repo:
        return {"success": False, "error": "Repositório não informado."}

    url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Nordestina-App-Suite"
    }
    if token and str(token).strip():
        headers["Authorization"] = f"Bearer {str(token).strip()}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            body_text = data.get("body", "")
            if not body_text or not body_text.strip():
                body_text = "Melhorias gerais de desempenho, estabilidade e novas funcionalidades."

            return {
                "success": True,
                "tag_name": data.get("tag_name", "v0.0.0"),
                "name": data.get("name") or data.get("tag_name", ""),
                "body": body_text.strip(),
                "html_url": data.get("html_url", ""),
                "published_at": data.get("published_at", ""),
                "assets": data.get("assets", []),
                "error": None
            }
        elif response.status_code == 404:
            return {
                "success": False,
                "error": "Nenhuma release encontrada ou repositório privado requer Token.",
                "status_code": 404
            }
        elif response.status_code == 401:
            return {
                "success": False,
                "error": "Token do GitHub inválido ou sem permissão para repositório privado.",
                "status_code": 401
            }
        else:
            return {
                "success": False,
                "error": f"Erro na API do GitHub (HTTP {response.status_code}).",
                "status_code": response.status_code
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Falha de conexão: {str(e)}",
            "status_code": None
        }

def find_asset_for_download(assets, preferred_name=None):
    """
    Identifica o melhor asset para download (.exe ou .zip).
    Prioriza correspondência de nome ou extensões executáveis.
    """
    if not assets:
        return None

    # 1. Procura por nome preferido
    if preferred_name:
        pref = preferred_name.lower().replace(" ", "").replace("-", "").replace("_", "")
        for a in assets:
            a_name = a.get("name", "").lower().replace(" ", "").replace("-", "").replace("_", "")
            if pref in a_name and a_name.endswith((".exe", ".zip")):
                return a

    # 2. Prioriza .exe
    for a in assets:
        if a.get("name", "").lower().endswith(".exe"):
            return a

    # 3. Prioriza .zip
    for a in assets:
        if a.get("name", "").lower().endswith(".zip"):
            return a

    # 4. Retorna o primeiro asset disponível
    return assets[0] if assets else None

def download_release_asset(asset_url, destination_path, token=None, progress_callback=None):
    """
    Baixa um asset (arquivo .exe ou .zip) de uma Release do GitHub.
    Suporta repositórios públicos e privados (com tratamento de redirect seguro).
    """
    headers = {
        "Accept": "application/octet-stream",
        "User-Agent": "Nordestina-App-Suite"
    }
    if token and str(token).strip():
        headers["Authorization"] = f"Bearer {str(token).strip()}"

    try:
        session = requests.Session()
        response = session.get(asset_url, headers=headers, stream=True, timeout=90, allow_redirects=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(destination_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        fraction = downloaded / total_size
                        try:
                            progress_callback(fraction, downloaded, total_size)
                        except TypeError:
                            progress_callback(fraction)
                    elif progress_callback:
                        progress_callback(0.5, downloaded, total_size)

        return True, "Download concluído com sucesso."
    except Exception as e:
        return False, f"Erro ao baixar arquivo: {e}"

def fetch_remote_catalog(repo, token=None):
    """
    Consulta o arquivo 'apps_catalog.json' diretamente do repositório da Suite no GitHub.
    Permite adicionar novos aplicativos dinamicamente a todos os usuários da empresa.
    """
    if not repo:
        return None

    url = f"https://api.github.com/repos/{repo}/contents/apps_catalog.json"
    headers = {
        "Accept": "application/vnd.github.raw+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Nordestina-App-Suite"
    }
    if token and str(token).strip():
        headers["Authorization"] = f"Bearer {str(token).strip()}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            catalog_data = response.json()
            if isinstance(catalog_data, list):
                return catalog_data
    except Exception:
        pass
    return None
