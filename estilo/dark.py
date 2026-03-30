from estilo.estilizador import Estilo

class DarkColor(Estilo):
    def __init__(self):     
        self.nombre = "dark"
        self.bg ="#0f0f12"
        self.bg2 ="#161620"  
        self.border ="#1e1e2a"
        self.green ="#3ddc84"  
        self.orange = "#f0a030"   
        self.red = "#e05252"   
        self.cyan = "#7fd4c1"   
        self.blue = "#7a9fd4"   
        self.white = "#e0e0e8"   
        self.muted = "#4a4a5a"   
        self.boton = "#0f2520"
        
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