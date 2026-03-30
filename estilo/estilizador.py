# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Juan S.G. Castellanos

from abc import ABC, abstractmethod


class Estilo(ABC):
    @abstractmethod
    def colorBg(self) -> str: pass
    @abstractmethod
    def colorBg2(self) -> str: pass
    @abstractmethod
    def colorBorder(self) -> str: pass
    @abstractmethod
    def colorGreen(self) -> str: pass
    @abstractmethod
    def colorOrange(self) -> str: pass
    @abstractmethod
    def colorRed(self) -> str: pass
    @abstractmethod
    def colorCyan(self) -> str: pass
    @abstractmethod
    def colorBlue(self) -> str: pass
    @abstractmethod
    def colorWhite(self) -> str: pass
    @abstractmethod
    def colorMuted(self) -> str: pass
    @abstractmethod
    def colorBoton(self) -> str: pass
    @abstractmethod
    def getNombre(self) -> str: pass
