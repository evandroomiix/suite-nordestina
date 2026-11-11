import json
import os
import sys

try:
    from version import __version__, __default_repo__, __author__
except ImportError:
    __version__ = "v1.0.0"
    __default_repo__ = "evandroomiix/suite-nordestina"
    __author__ = "Evandro Magno"

DEFAULT_PROJECTS = [
    {
        "id": "producao",
        "name": "Levantamento Diário de Produção",
        "repo": "evandroomiix/levantamento-diario-producao",
        "description": "Controle e apontamento diário da produção operacional.",
        "category": "Operacional",
        "icon_emoji": "📋",
        "keywords": ["producao", "produção", "levantamento"],
        "installed_version": "v1.0.0",
        "fallback_exe": ""
    },
    {
        "id": "inventario",
        "name": "Dashboard de Inventário",
        "repo": "evandroomiix/dashboard-inventario",
        "description": "Monitoramento em tempo real de estoque, insumos e giros.",
        "category": "Logística",
        "icon_emoji": "📦",
        "keywords": ["inventario", "inventário", "estoque"],
        "installed_version": "v1.0.0",
        "fallback_exe": ""
    },
    {
        "id": "financeiro",
        "name": "Dashboard Financeiro",
        "repo": "evandroomiix/dashboard-financeiro",
        "description": "Fluxo de caixa, DRE, conciliações e indicadores de custos.",
        "category": "Controladoria",
        "icon_emoji": "💰",
        "keywords": ["financeiro", "finanças", "caixa"],
        "installed_version": "v1.0.0",
        "fallback_exe": ""
    },
    {
        "id": "vendas",
        "name": "Dashboard de Vendas",
        "repo": "evandroomiix/dashboard-vendas",
        "description": "Metas, conversões, faturamento e desempenho comercial.",
        "category": "Comercial",
        "icon_emoji": "📈",
        "keywords": ["vendas", "comercial", "faturamento"],
        "installed_version": "v1.0.0",
        "fallback_exe": ""
    },
    {
        "id": "cic",
        "name": "CIC Reformulado",
        "repo": "",
        "description": "Consulta de clientes antigos, títulos a receber/quitados e movimentos de pedidos.",
        "category": "Gestão",
        "icon_emoji": "🏢",
        "keywords": ["cic reformulado", "reformulado"],
        "installed_version": "v2.0.0",
        "fallback_exe": "D:\\Lojas Nordestina\\SISTEMAS E PROGRAMAS\\CIC\\CIC REFORMULADO\\dist\\CIC\\CIC.exe"
    },
    {
        "id": "mysoft",
        "name": "MYSOFT Reformulado",
        "repo": "",
        "description": "Sistema de consulta de cadastros de clientes antigos e histórico MYSOFT.",
        "category": "Legado",
        "icon_emoji": "💾",
        "keywords": ["mysoft", "antigos", "clientes antigos"],
        "installed_version": "v1.1.0",
        "fallback_exe": "D:\\Lojas Nordestina\\SISTEMAS E PROGRAMAS\\MYSOFT\\dist\\Clientes Antigos.exe"
    }
]

DEFAULT_CONFIG = {
    "creator": __author__,
    "launcher_version": __version__,
    "launcher_repo": __default_repo__,
    "view_mode": "cards",  # "cards" ou "table"
    "appearance_mode": "dark",  # "dark" ou "light"
    "admin_password": "admin",  # Senha padrão de administrador para configurações sensíveis
    "github_token": "",
    "check_interval_minutes": 60,
    "minimize_to_tray": True,
    "projects": DEFAULT_PROJECTS
}

def get_config_path():
    """Retorna o caminho seguro do arquivo de configuração do usuário."""
    app_data = os.environ.get("APPDATA") or os.path.expanduser("~")
    config_dir = os.path.join(app_data, "EmpresaHubLauncher")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")

def merge_projects(existing_projects, incoming_projects):
    """
    Mescla novos aplicativos na lista de projetos existente,
    preservando as versões instaladas e customizações locais.
    """
    projects_by_id = {p.get("id"): p for p in existing_projects if p.get("id")}
    
    for inc in incoming_projects:
        p_id = inc.get("id")
        if not p_id:
            continue
        if p_id not in projects_by_id:
            existing_projects.append(inc)
            projects_by_id[p_id] = inc
        else:
            # Atualiza metadados informativos (descrição, nome, repositório) se estiverem vazios
            curr = projects_by_id[p_id]
            for key in ["name", "description", "category", "icon_emoji", "repo"]:
                if not curr.get(key) and inc.get(key):
                    curr[key] = inc[key]
    return existing_projects

def load_config():
    """Carrega as configurações do arquivo JSON ou cria o padrão."""
    path = get_config_path()
    if not os.path.exists(path):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # Atualiza chaves ausentes com valores do default
            for k, v in DEFAULT_CONFIG.items():
                if k not in data:
                    data[k] = v

            # Sincroniza sempre a versão do executável atual com o arquivo de configuração
            data["launcher_version"] = __version__
            
            # Migração de repositório antigo para o oficial se aplicável
            if data.get("launcher_repo") == "evandroomiix/hub-launcher":
                data["launcher_repo"] = __default_repo__

            # Garante que novos projetos do código existam na lista
            data["projects"] = merge_projects(data.get("projects", []), DEFAULT_PROJECTS)
            
            # Salva de volta para persistir sincronizações
            save_config(data)
            return data
    except Exception as e:
        print(f"Erro ao ler configuração: {e}")
        return DEFAULT_CONFIG

def save_config(config_data):
    """Salva as configurações no arquivo JSON."""
    path = get_config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar configuração: {e}")
        return False
