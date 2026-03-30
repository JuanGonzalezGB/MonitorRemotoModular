from estilo.dark import DarkColor
from vista.gui_dictionary import CLASESTEMAS


class EstiloFactory:
    @staticmethod
    def definirEstilo(tipo: str):
        clase = CLASESTEMAS.get(tipo, DarkColor)
        return clase()
