from abc import ABC, abstractmethod
class Estilo(ABC):
    @abstractmethod    
    def colorBg(self):
        pass
    @abstractmethod   
    def colorBg2(self):
        pass
    @abstractmethod   
    def colorBorder(self):
        pass
    @abstractmethod   
    def colorGreen(self):
        pass
    @abstractmethod   
    def colorOrange(self):
        pass
    @abstractmethod   
    def colorRed(self):
        pass
    @abstractmethod   
    def colorCyan(self):
        pass
    @abstractmethod   
    def colorBlue(self):
        pass
    @abstractmethod   
    def colorWhite(self):
        pass
    @abstractmethod   
    def colorMuted(self):
        pass
    @abstractmethod   
    def colorBoton(self):
        pass