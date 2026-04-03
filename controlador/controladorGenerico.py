import socket
class Cositas():

    def __init__(self, app):
        self._app = app
    
# ─── Pausa ───────────────────────────────────────────────────────────────
    def pause(self):
        self._app._paused = True
        if self._app._after_id:
            self._app.root.after_cancel(self._app._after_id)
            self._app._after_id = None

    def resume(self):
        self._app._paused = False
        self._app._schedule()
# ─── IP ───────────────────────────────────────────────────────────────
