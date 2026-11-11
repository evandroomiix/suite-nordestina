import subprocess
import sys
import os

def build():
    print("==================================================")
    print("Gerando o executável standalone do Nordestina App Suite...")
    print("==================================================")
    
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name=NordestinaAppSuite",
        "--icon=assets/app_icon.ico",
        "--add-data=assets;assets",
        "--collect-all=customtkinter",
        "--collect-all=winotify",
        "--collect-all=pystray",
        "main.py"
    ]
    
    print("Executando:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    if res.returncode == 0:
        print("\n✔ SUCESSO! Executável gerado na pasta: dist/NordestinaAppSuite.exe")
    else:
        print("\n❌ Erro durante a geração do executável.")

if __name__ == "__main__":
    build()
