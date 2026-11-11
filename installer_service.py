import os
import sys
import glob
import json
import zipfile
import shutil
import tempfile
import subprocess

def get_desktop_paths():
    """Retorna os possíveis caminhos da Área de Trabalho (padrão e OneDrive)."""
    paths = []
    user_profile = os.environ.get("USERPROFILE", "")
    if user_profile:
        # Padrão
        p1 = os.path.join(user_profile, "Desktop")
        if os.path.exists(p1) and p1 not in paths:
            paths.append(p1)
        # OneDrive
        p2 = os.path.join(user_profile, "OneDrive", "Desktop")
        if os.path.exists(p2) and p2 not in paths:
            paths.append(p2)
        # OneDrive em Português
        p3 = os.path.join(user_profile, "OneDrive", "Área de Trabalho")
        if os.path.exists(p3) and p3 not in paths:
            paths.append(p3)
        # Área de trabalho em Português
        p4 = os.path.join(user_profile, "Área de Trabalho")
        if os.path.exists(p4) and p4 not in paths:
            paths.append(p4)
    public_desktop = os.environ.get("PUBLIC", "")
    if public_desktop:
        p5 = os.path.join(public_desktop, "Desktop")
        if os.path.exists(p5) and p5 not in paths:
            paths.append(p5)
    return paths

def get_apps_root_dir():
    """Diretório central onde os projetos completos ficam instalados."""
    local_app_data = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    root_dir = os.path.join(local_app_data, "EmpresaApps")
    os.makedirs(root_dir, exist_ok=True)
    return root_dir

def get_project_install_dir(project_id):
    """Caminho da pasta de instalação do projeto específico."""
    return os.path.join(get_apps_root_dir(), project_id)

def get_version_file_path(project_id):
    return os.path.join(get_project_install_dir(project_id), "version.json")

def read_installed_version(project_id):
    """Lê a versão registrada na pasta de instalação."""
    v_file = get_version_file_path(project_id)
    if os.path.exists(v_file):
        try:
            with open(v_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("version")
        except Exception:
            pass
    return None

def write_installed_version(project_id, version_str, exe_path=""):
    """Grava a versão instalada e o caminho do executável."""
    install_dir = get_project_install_dir(project_id)
    os.makedirs(install_dir, exist_ok=True)
    v_file = get_version_file_path(project_id)
    try:
        with open(v_file, "w", encoding="utf-8") as f:
            json.dump({"version": version_str, "exe_path": exe_path}, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar versão instalada: {e}")

def find_desktop_shortcut(project_name, keywords=None):
    """
    Verifica se o programa possui atalho ou executável na Área de Trabalho com priorização:
    1. Nome do arquivo idêntico ao nome do projeto (ex: 'CIC Reformulado.lnk' == 'CIC Reformulado')
    2. Nome do projeto completo contido no arquivo
    3. Palavras-chave específicas, descartando versões opostas (ex: ignorar 'antigo'/'original' para 'reformulado')
    """
    if keywords is None:
        keywords = []
    
    clean_target = project_name.lower().strip()
    desktops = get_desktop_paths()

    # 1. Correspondência exata do nome base
    for d_path in desktops:
        try:
            for fname in os.listdir(d_path):
                if fname.lower().endswith((".lnk", ".exe")):
                    base = os.path.splitext(fname)[0].strip().lower()
                    if base == clean_target:
                        return os.path.join(d_path, fname)
        except Exception:
            pass

    # 2. Nome completo do projeto contido no nome do arquivo
    for d_path in desktops:
        try:
            for fname in os.listdir(d_path):
                if fname.lower().endswith((".lnk", ".exe")):
                    base = os.path.splitext(fname)[0].strip().lower()
                    if clean_target in base:
                        return os.path.join(d_path, fname)
        except Exception:
            pass

    # 3. Palavras-chave com exclusão de falsos positivos
    negatives = []
    if "reformulado" in clean_target or "novo" in clean_target:
        negatives = ["antigo", "original", "velho", "legacy"]

    for d_path in desktops:
        try:
            for fname in os.listdir(d_path):
                if fname.lower().endswith((".lnk", ".exe")):
                    fname_lower = fname.lower()
                    if any(neg in fname_lower for neg in negatives):
                        continue
                    for kw in keywords:
                        kw_lower = kw.strip().lower()
                        if kw_lower and kw_lower in fname_lower:
                            return os.path.join(d_path, fname)
        except Exception:
            pass

    return None

def is_project_installed(project_id, project_name, keywords=None, fallback_exe=None):
    r"""
    Determina se o projeto está instalado no computador:
    0. Se o executável de fallback direto existir no disco.
    1. Se existe na pasta central %LOCALAPPDATA%\EmpresaApps\{project_id}
    2. Ou se existe atalho/executável na Área de Trabalho.
    """
    if fallback_exe and os.path.exists(fallback_exe):
        return True

    install_dir = get_project_install_dir(project_id)
    v_file = get_version_file_path(project_id)
    if os.path.exists(install_dir) and os.path.exists(v_file):
        return True

    # Verifica na área de trabalho
    shortcut = find_desktop_shortcut(project_name, keywords)
    if shortcut:
        return True

    return False

def create_desktop_shortcut(target_exe_path, shortcut_name, arguments="", icon_path="", working_dir=""):
    """
    Cria ou atualiza um atalho (.lnk) na Área de Trabalho usando PowerShell nativo.
    """
    desktops = get_desktop_paths()
    if not desktops:
        return None
    desktop = desktops[0]
    shortcut_path = os.path.join(desktop, f"{shortcut_name}.lnk")

    work_dir = working_dir if working_dir else os.path.dirname(target_exe_path)
    icon_line = f"$Shortcut.IconLocation = '{icon_path}'" if icon_path else ""

    ps_script = f"""
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
    $Shortcut.TargetPath = '{target_exe_path}'
    $Shortcut.WorkingDirectory = '{work_dir}'
    $Shortcut.Arguments = '{arguments}'
    {icon_line}
    $Shortcut.Save()
    """
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        return shortcut_path
    except Exception as e:
        print(f"Erro ao criar atalho na área de trabalho: {e}")
        return None

def install_launcher_desktop_shortcut():
    """
    Cria ou atualiza o atalho do Launcher na Área de Trabalho com o nome 'NORDESTINA APP SUITE'
    e o ícone oficial da empresa.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "assets", "app_icon.ico")

    # 1. Se estiver rodando como executável compilado (.exe)
    if getattr(sys, 'frozen', False):
        target = sys.executable
        arguments = ""
    else:
        # 2. Se existe o executável standalone compilado em dist
        standalone_exe = os.path.join(base_dir, "dist", "NordestinaAppSuite.exe")
        if os.path.exists(standalone_exe):
            target = standalone_exe
            arguments = ""
        else:
            # 3. Rodando via interpretador python
            # Evita o caminho restrito C:\Program Files\WindowsApps usando o App Execution Alias público
            alias_pythonw = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps", "pythonw.exe")
            if os.path.exists(alias_pythonw):
                target = alias_pythonw
            elif shutil.which("pyw.exe"):
                target = shutil.which("pyw.exe")
            elif shutil.which("pythonw.exe"):
                target = shutil.which("pythonw.exe")
            else:
                target = sys.executable
            main_file = os.path.join(base_dir, "main.py")
            arguments = f'"{main_file}"'

    return create_desktop_shortcut(
        target_exe_path=target,
        shortcut_name="NORDESTINA APP SUITE",
        arguments=arguments,
        icon_path=icon_path if os.path.exists(icon_path) else "",
        working_dir=base_dir
    )

def install_or_update_package(project_id, project_name, downloaded_file_path, version_tag):
    r"""
    Instala ou atualiza o pacote automaticamente:
    - Descompacta o .zip dentro de %LOCALAPPDATA%\EmpresaApps\{project_id}
    - Encontra o executável principal
    - Cria/atualiza o atalho na Área de Trabalho
    - Salva o arquivo de versão local
    """
    install_dir = get_project_install_dir(project_id)
    os.makedirs(install_dir, exist_ok=True)

    # Encerra processos do projeto caso estejam abertos para liberar arquivos
    for proc_name in [f"{project_id}.exe", f"{project_name}.exe", "dashboard_inventario.exe", "levantamento_diario.exe", "dashboard_financeiro.exe", "dashboard_vendas.exe"]:
        try:
            subprocess.run(f'taskkill /f /im "{proc_name}"', shell=True, capture_output=True)
        except Exception:
            pass

    main_exe = None

    if downloaded_file_path.lower().endswith(".zip"):
        # Descompacta o arquivo zip
        with zipfile.ZipFile(downloaded_file_path, 'r') as zip_ref:
            zip_ref.extractall(install_dir)

        # Procura o executável principal na pasta
        exe_files = []
        for root, _, files in os.walk(install_dir):
            for f in files:
                if f.lower().endswith(".exe") and not f.lower().startswith("uninstall"):
                    exe_files.append(os.path.join(root, f))

        if exe_files:
            # Prefere o executável com nome parecido ao projeto ou o maior
            exe_files.sort(key=lambda x: os.path.getsize(x), reverse=True)
            main_exe = exe_files[0]
    elif downloaded_file_path.lower().endswith(".exe"):
        dest_exe = os.path.join(install_dir, f"{project_name}.exe")
        shutil.copy2(downloaded_file_path, dest_exe)
        main_exe = dest_exe

    # Atualiza o arquivo de versão
    write_installed_version(project_id, version_tag, main_exe or "")

    # Cria atalho na Área de Trabalho se encontrou executável
    if main_exe:
        create_desktop_shortcut(main_exe, project_name)

    return True, main_exe

def launch_project(project_id, project_name, keywords=None, fallback_exe=None):
    r"""
    Executa o programa:
    1. Tenta o atalho da Área de Trabalho
    2. Tenta o executável registrado em %LOCALAPPDATA%\EmpresaApps\{project_id}
    3. Tenta o fallback_exe se configurado.
    """
    # 1. Checa atalho na Área de Trabalho
    shortcut = find_desktop_shortcut(project_name, keywords)
    if shortcut and os.path.exists(shortcut):
        try:
            os.startfile(shortcut)
            return True, f"Iniciando via atalho: {shortcut}"
        except Exception as e:
            print(f"Erro ao abrir atalho: {e}")

    # 2. Checa no version.json da pasta de instalação
    v_file = get_version_file_path(project_id)
    if os.path.exists(v_file):
        try:
            with open(v_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                exe = data.get("exe_path")
                if exe and os.path.exists(exe):
                    subprocess.Popen([exe], cwd=os.path.dirname(exe), shell=False)
                    return True, f"Iniciando: {exe}"
        except Exception as e:
            print(f"Erro ao abrir via version.json: {e}")

    # 3. Fallback configurado
    if fallback_exe and os.path.exists(fallback_exe):
        try:
            subprocess.Popen([fallback_exe], cwd=os.path.dirname(fallback_exe), shell=False)
            return True, f"Iniciando fallback: {fallback_exe}"
        except Exception as e:
            return False, f"Falha ao iniciar: {e}"

    return False, "Executável ou atalho não encontrado. Instale o projeto primeiro."

def apply_launcher_update(downloaded_file_path, version_tag):
    """
    Substitui o executável atual do Launcher pelo novo arquivo baixado da release
    e reinicia a aplicação de forma limpa e transparente.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    is_frozen = getattr(sys, 'frozen', False)

    # 1. Extrai o executável se o arquivo baixado for .zip
    new_exe_path = None
    if downloaded_file_path.lower().endswith(".zip"):
        temp_extract = tempfile.mkdtemp(prefix="nordestina_upd_")
        with zipfile.ZipFile(downloaded_file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract)

        candidates = []
        for root, _, files in os.walk(temp_extract):
            for f in files:
                if f.lower().endswith(".exe"):
                    candidates.append(os.path.join(root, f))
        
        if candidates:
            # Prefere arquivo com nome Nordestina ou o maior .exe
            candidates.sort(key=lambda x: (("nordestina" in os.path.basename(x).lower()), os.path.getsize(x)), reverse=True)
            new_exe_path = candidates[0]
    elif downloaded_file_path.lower().endswith(".exe"):
        new_exe_path = downloaded_file_path

    if not new_exe_path or not os.path.exists(new_exe_path):
        return False, "Nenhum executável válido foi encontrado no pacote baixado."

    # 2. Se estiver rodando como executável compilado (.exe)
    if is_frozen:
        current_exe = sys.executable
        pid = os.getpid()
        updater_bat = os.path.join(tempfile.gettempdir(), f"updater_suite_{pid}.bat")
        
        # Script em lote desacoplado para aguardar encerramento, sobrescrever e relançar
        bat_script = f"""@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

set "TARGET_EXE={current_exe}"
set "NEW_EXE={new_exe_path}"
set "APP_PID={pid}"

timeout /t 1 /nobreak > nul

:WAIT_PID
tasklist /fi "PID eq !APP_PID!" 2>nul | find "!APP_PID!" > nul
if not errorlevel 1 (
    timeout /t 1 /nobreak > nul
    goto WAIT_PID
)

:REPLACE_LOOP
copy /y "!NEW_EXE!" "!TARGET_EXE!" > nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak > nul
    goto REPLACE_LOOP
)

del /f /q "!NEW_EXE!" > nul 2>&1

start "" "!TARGET_EXE!"

(goto) 2>nul & del "%~f0"
"""
        try:
            with open(updater_bat, "w", encoding="utf-8") as f:
                f.write(bat_script)

            DETACHED_PROCESS = 0x00000008
            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(
                ["cmd.exe", "/c", updater_bat],
                creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                close_fds=True
            )
            # Encerramento imediato do processo atual
            os._exit(0)
        except Exception as e:
            return False, f"Falha ao iniciar processo de atualização automática: {e}"

    else:
        # 3. Rodando em modo script/desenvolvimento: atualiza dist/NordestinaAppSuite.exe
        dist_dir = os.path.join(base_dir, "dist")
        os.makedirs(dist_dir, exist_ok=True)
        target_dist_exe = os.path.join(dist_dir, "NordestinaAppSuite.exe")
        try:
            shutil.copy2(new_exe_path, target_dist_exe)
            install_launcher_desktop_shortcut()
            return True, f"Executável compilado em '{target_dist_exe}' atualizado para {version_tag} com sucesso!"
        except Exception as e:
            return False, f"Erro ao copiar executável para a pasta dist: {e}"

