from estilo.estilizador import Estilo


class LightColor(Estilo):
    def __init__(self):     
        self.nombre = "light"
        self.bg ="#ecdcd2"
        self.bg2 ="#ebdbd5"  
        self.border ="#41412b"
        self.green ="#19b37f"  
        self.orange = "#e0bd20"   
        self.red = "#c0392b"   
        self.cyan = "#1a7a6a"   
        self.blue = "#2a5fa8"   
        self.white = "#1a1a18"   
        self.muted = "#8a8a7a"   
        self.boton = "#79bbab"

    def colorBg(self):
        return self.bg
    def colorBg2(self):
        return self.bg2
    def colorBorder(self):
        return self.border
    def colorGreen(self):
        return self.green
    def colorOrange(self):
        return self.orange
    def colorRed(self):
        return self.red
    def colorCyan(self):
        return self.cyan
    def colorBlue(self):
        return self.blue
    def colorWhite(self):
        return self.white
    def colorMuted(self):
        return self.muted
    def colorBoton(self):
        return self.boton    
    def getNombre(self):
        return self.nombre