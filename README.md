# MonitorRemoto: Configurar ip del pc del cual quiere leer las temperaturas
el pc del cual quiere leer las temperaturas debe tener netdata!

algunos valores se verán inflados, esto se debe a la forma en que netdata lee los datos, incluirá la info de consumo de recursos mas lo que está cacheado por el kernel.

.sh para extraer de netdata
--------------------------------------------------------------------------
.py = gui
--------------------------------------------------------------------------
puede usar solo el .sh con:

	watch -n 2 "./monitor_pc.sh"

o directamente con gui(pensado para pantalla 3.5" en raspberry pi)

	python3 main.py

puede instalar con pyinstaller:

    python3 -m PyInstaller --onedir --add-data "monitor_pc.sh:." --name="Resources Monitor"  main.py

This project includes code generated with assistance of AI tools and manually reviewed and modified by the author.

Este proyecto incluye código generado con asistencia de herramientas de IA, manualmente revisado y modificado por el autor.
