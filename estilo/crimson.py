from estilo.estilizador import Estilo

class CrimsonColor(Estilo):
    def __init__(self):     
        self.nombre = "crimson_dark"

        self.bg = "#0a0505"        # negro rojizo profundo
        self.bg2 = "#120707"       # fondo secundario más visible
        self.border = "#920c0c"    # bordes rojo oscuro apagado

        self.green = "#ff0000"     # good (verde clásico para contraste funcional)
        self.orange = "#ff807b"    # mid (ámbar/naranja suave tipo warning)
        self.red = "#ffbebe"       # bad (rojo principal del tema)

        self.cyan = "#ff6b6b"      # acento rojo-rosado tipo highlight
        self.blue = "#b22222"      # rojo oscuro azulado (crimson frío)

        self.white = "#f2e9e9"     # texto claro con tinte cálido
        self.muted = "#805353"     # texto apagado rojizo

        self.boton = "#1a0a0a"     # botones oscuros con leve rojo
        
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