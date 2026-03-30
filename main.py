#!/usr/bin/env python3
"""
Entry point del monitor.
Lee el tema desde config.json (creado automáticamente en el primer arranque).
Si no existe config.json, usa "dark" por defecto.
El tema también puede forzarse con: python main.py <codigo_tema>
"""
import sys
from modelo import config
from estilo.estiloFactory import EstiloFactory
from vista.app import MonitorApp


def main():
    # sys.argv[1] permite forzar un tema puntualmente sin tocar config.json
    tema = sys.argv[1] if len(sys.argv) > 1 else config.get_tema()
    estilo = EstiloFactory.definirEstilo(tema)
    MonitorApp(estilo).run()


if __name__ == "__main__":
    main()
