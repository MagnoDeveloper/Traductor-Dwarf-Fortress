import google.generativeai as genai
import os

try:
    # Get API key from environment variable
    api_key = os.environ.get('API_KEY')

    if not api_key:
        print("Error: La variable de entorno 'API_KEY' no está configurada.")
    else:
        genai.configure(api_key=api_key)

        print("Modelos disponibles:")
        for model in genai.list_models():
            print(model.name)

except Exception as e:
    print(f"Ocurrió un error: {e}")
