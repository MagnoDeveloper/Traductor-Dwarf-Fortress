# Traductor DF

Traductor OCR para Dwarf Fortress

Esta aplicación permite seleccionar un área de la pantalla, extraer texto en inglés usando OCR y traducirlo automáticamente al español, manteniendo la terminología y formato del juego Dwarf Fortress. Utiliza Google Gemini AI para traducción y easyocr para reconocimiento óptico de caracteres.

## Características
- Selección de área de pantalla para OCR
- Traducción automática inglés → español especializada en Dwarf Fortress
- Interfaz gráfica simple (Tkinter)
- Configuración de API Key de Google AI
- Compatible con Windows

## Requisitos
- Python 3.8+
- Dependencias Python:
  - tkinter
  - easyocr
  - pillow
  - numpy
  - google-generativeai
  - keyboard

## Instalación
1. Clona o descarga este repositorio.
2. Instala las dependencias:
   ```sh
   pip install -r requirements.txt
   ```
3. Descarga tu API Key de Google AI en https://aistudio.google.com/apikey y pégala en el archivo `api_key.txt` (se puede hacer desde la app).
4. Ejecuta la app:
   ```sh
   python traductor_df.py
   ```

### Empaquetado para Windows
Para crear un ejecutable:
```sh
pip install pyinstaller
pyinstaller traductor_df.py --onedir --noconsole --icon=icon.ico
```

El empaquedo va a la carpeta `dist/Traductor DF/`.

## Créditos
- [easyocr](https://github.com/JaidedAI/EasyOCR)
- [Google Gemini AI](https://ai.google.dev/)
- [Tkinter](https://docs.python.org/3/library/tkinter.html)

---
¡Disfruta traduciendo Dwarf Fortress!

