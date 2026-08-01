📁 ¿Qué carpetas y archivos DEBES ELIMINAR antes de comprimir?
Elimina sin miedo las siguientes carpetas. Al quitarlas, tu proyecto pasará de pesar cientos de megabytes a solo unos pocos kilobytes:

# backend/venv/ 
(Entorno virtual de Python): Es la carpeta más pesada del backend. No se debe compartir porque contiene los archivos binarios de Python específicos de tu computadora. Cuando descomprimas el proyecto, la volverás a crear con el comando python -m venv venv.

# backend/models/*.onnx (Modelos de Inteligencia Artificial): 
Los dos archivos .onnx que descargaste con PowerShell (face_detection_yunet... y face_recognition_sface...) pesan mucho. Como ya tienes las instrucciones de descarga en el archivo DESCARGAR_MODELOS.txt (o en tu Readme), el usuario que lo reciba los puede volver a bajar con los comandos de PowerShell.

# backend/__pycache__/ (y todas las carpetas __pycache__ internas):
Son archivos temporales que Python genera automáticamente para acelerar la ejecución del código. Si los borras, Python los volverá a crear la próxima vez que arranques el servidor.

# backend/uploads/fotos/ (Contenido de imágenes cargadas):
Borra las fotos de prueba que se hayan guardado ahí para no arrastrar archivos innecesarios. Ojo: Deja la estructura de carpetas vacía si tu código la necesita, o asegúrate de recrearla al volver a iniciar.

Archivos ocultos del sistema: Si ves archivos como .DS_Store (en Mac) o carpetas ocultas de editores como .vscode/, también puedes borrarlas.