# 🚀 NORDESTINA APP SUITE

Central unificada e inteligente de aplicativos internos e dashboards das **Lojas Nordestina**. O aplicativo funciona como um ecossistema estilo Launcher corporativo que monitora atualizações, instala ferramentas com 1 clique e se auto-atualiza automaticamente via GitHub.

---

## 📌 Principais Recursos

* **Auto-Update da Suite:** A própria Suite verifica se há novas versões no repositório GitHub (`evandroomiix/suite-nordestina`), baixa a atualização em segundo plano e reinicia automaticamente atualizada.
* **Catálogo Dinâmico de Apps:** Permite adicionar novos aplicativos a qualquer momento via repositório (`apps_catalog.json`), disponibilizando novos sistemas para toda a empresa sem precisar reinstalar.
* **Instalação e Atualização com 1 Clique:** Baixa executáveis (.exe) e pacotes (.zip) de releases privadas no GitHub, descompacta, cria atalhos com ícone oficial na Área de Trabalho e registra a versão instalada.
* **Notificações Nativas do Windows:** Alerta os colaboradores na área de trabalho quando uma nova versão de qualquer app ou da própria Suite estiver disponível.
* **Modo Claro / Escuro & System Tray:** Interface responsiva que se adapta ao tema do usuário e roda perto do relógio do Windows com consumo mínimo de recursos.
* **Segurança e Área Administrativa:** Configurações sensíveis (Token do GitHub, repositórios e catálogo) são protegidas por senha de administrador.

---

## 📋 Aplicativos Integrados

| Aplicativo | Repositório / Caminho | Categoria |
| :--- | :--- | :--- |
| **📋 Levantamento Diário de Produção** | `evandroomiix/levantamento-diario-producao` | Operacional |
| **📦 Dashboard de Inventário** | `evandroomiix/dashboard-inventario` | Logística |
| **💰 Dashboard Financeiro** | `evandroomiix/dashboard-financeiro` | Controladoria |
| **📈 Dashboard de Vendas** | `evandroomiix/dashboard-vendas` | Comercial |
| **🏢 CIC Reformulado** | Executável de Rede / Local | Gestão |
| **💾 MYSOFT Reformulado** | Executável de Rede / Local | Legado |

---

## 🔄 Como Adicionar Novos Aplicativos

Como a Suite foi projetada para receber novos apps continuamente, você pode adicionar novos sistemas de duas formas simples:

### Opção 1: Via Arquivo `apps_catalog.json` no GitHub (Recomendado)
Basta editar o arquivo `apps_catalog.json` no repositório da Suite no GitHub e adicionar o novo aplicativo:
```json
{
  "id": "novo_app",
  "name": "Nome do Novo App",
  "repo": "evandroomiix/novo-app",
  "description": "Descrição detalhada do novo aplicativo.",
  "category": "Operacional",
  "icon_emoji": "⚡",
  "keywords": ["novo", "app"],
  "installed_version": "v1.0.0",
  "fallback_exe": ""
}
```
Assim que o commit for publicado no GitHub, na próxima checagem automática o novo app já aparecerá disponível na tela de todos os colaboradores!

### Opção 2: Pela Área Administrativa do App
1. Clique no botão **⚙️ Configurações** no topo direito.
2. Digite a senha administrativa (`admin`).
3. Adicione ou edite os dados do novo aplicativo na lista.

---

## 🏷️ Como Publicar Nova Versão da Suite no GitHub

1. Altere a versão em `version.py`:
   ```python
   __version__ = "v1.1.0"
   ```
2. Gere o novo executável:
   ```bash
   py build_exe.py
   ```
3. No GitHub (`evandroomiix/suite-nordestina`):
   - Vá em **Releases** -> **Draft a new release**.
   - Crie a tag correspondente (ex: `v1.1.0`).
   - Anexe o executável gerado em `dist/NordestinaAppSuite.exe` aos Assets da release.
   - Clique em **Publish release**.
4. Pronto! Todas as instâncias da Suite em execução na empresa exibirão o banner de atualização e farão o auto-update com 1 clique!

---

## 🛠️ Desenvolvimento e Build

### Executar em modo desenvolvimento:
```bash
py main.py
```

### Compilar executável (.exe) oficial:
```bash
py build_exe.py
```
O arquivo final será compilado em `dist/NordestinaAppSuite.exe` com o ícone oficial da empresa embutido.
