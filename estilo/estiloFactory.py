# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Juan S.G. Castellanos

from estilo.dark import DarkColor
from vista.gui_dictionary import CLASESTEMAS


class EstiloFactory:
    @staticmethod
    def definirEstilo(tipo: str):
        clase = CLASESTEMAS.get(tipo, DarkColor)
        return clase()
