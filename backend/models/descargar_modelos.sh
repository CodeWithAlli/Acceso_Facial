#!/bin/bash
# backend/models/descargar_modelos.sh
#
# Version Linux/bash de DESCARGAR_MODELOS.txt (ese archivo trae comandos
# de PowerShell, que solo sirven para tu maquina Windows). Este script
# se usa en el buildCommand de Render, que corre en un contenedor Linux.
#
# Uso local (si alguna vez trabajas desde WSL/Linux/Mac):
#   bash backend/models/descargar_modelos.sh

set -e  # corta el build si alguna descarga falla, en vez de arrancar sin modelos

mkdir -p backend/models

if [ ! -f backend/models/face_detection_yunet_2023mar.onnx ]; then
  echo "Descargando face_detection_yunet_2023mar.onnx..."
  curl -L -o backend/models/face_detection_yunet_2023mar.onnx \
    "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
fi

if [ ! -f backend/models/face_recognition_sface_2021dec.onnx ]; then
  echo "Descargando face_recognition_sface_2021dec.onnx..."
  curl -L -o backend/models/face_recognition_sface_2021dec.onnx \
    "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"
fi

echo "Modelos listos:"
ls -la backend/models/*.onnx
