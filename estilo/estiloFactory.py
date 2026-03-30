from estilo import dark
from vista.gui_dictionary import CLASESTEMAS

class EstiloFactory:
    @staticmethod
    def definirEstilo(tipo: str):    
        estilo = CLASESTEMAS.get(tipo, dark.DarkColor)
        return estilo()