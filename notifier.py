import sys

def show_update_notification(app_name, new_version, on_click_action=None):
    """
    Exibe uma notificação flutuante nativa (Toast) no Windows 10/11.
    """
    try:
        from winotify import Notification, audio
        
        toast = Notification(
            app_id="Hub de Dashboards",
            title=f"🔔 Atualização Disponível: {app_name}",
            msg=f"Uma nova versão ({new_version}) está disponível no repositório. Clique para abrir o Launcher e atualizar.",
            duration="short"
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
        return True
    except Exception as e:
        print(f"[Notifier] Erro ao disparar notificação: {e}")
        return False
