from estilo.estilizador import Estilo


class TealColor(Estilo):
    def __init__(self):
        self.nombre = "teal_dark"

        self.bg = "#050b0c"        # negro azulado profundo
        self.bg2 = "#071416"       # fondo secundario más visible
        self.border = "#0f2a2f"    # bordes teal oscuros

        self.green = "#2ee6c5"     # good (turquesa vivo pero controlado)
        self.orange = "#1faf7f"    # mid (teal más suave / aqua warning)
        self.red = "#6063a6"       # bad (teal profundo más “serio”)

        self.cyan = "#7fffd4"      # acento aqua brillante
        self.blue = "#38b6ff"      # azul frío que combina con teal

        self.white = "#d9f7f3"     # texto claro con tinte frío
        self.muted = "#2a4a4f"     # texto apagado verde-azulado

        self.boton = "#06191c"     # botones oscuros con tono marino

    def colorBg(self):     return self.bg
    def colorBg2(self):    return self.bg2
    def colorBorder(self): return self.border
    def colorGreen(self):  return self.green
    def colorOrange(self): return self.orange
    def colorRed(self):    return self.red
    def colorCyan(self):   return self.cyan
    def colorBlue(self):   return self.blue
    def colorWhite(self):  return self.white
    def colorMuted(self):  return self.muted
    def colorBoton(self):  return self.boton
    def getNombre(self):   return self.nombre
