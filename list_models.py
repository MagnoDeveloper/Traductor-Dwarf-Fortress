import google.generativeai as genai
import os

try:
    # Leer API key del mismo archivo que usa la aplicación
    API_KEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_key.txt")
    
    if not os.path.exists(API_KEY_PATH):
        print("Error: No se encontró el archivo 'api_key.txt'.")
        print("Por favor, configura tu API Key desde la interfaz de la aplicación primero.")
    else:
        with open(API_KEY_PATH, "r") as f:
            api_key = f.read().strip()
        
        if not api_key:
            print("Error: El archivo 'api_key.txt' está vacío.")
            print("Por favor, configura tu API Key desde la interfaz de la aplicación primero.")
        else:
            genai.configure(api_key=api_key)

            print("=" * 60)
            print("MODELOS DISPONIBLES DE GOOGLE GENERATIVE AI")
            print("=" * 60)
            
            modelos_generativos = []
            for model in genai.list_models():
                # Filtrar solo modelos que soporten generateContent
                if 'generateContent' in model.supported_generation_methods:
                    modelos_generativos.append(model)
            
            if modelos_generativos:
                print(f"\nModelos que soportan generación de contenido ({len(modelos_generativos)}):\n")
                for model in modelos_generativos:
                    print(f"  • {model.name}")
                    print(f"    Descripción: {model.display_name}")
                    print()
            else:
                print("\nNo se encontraron modelos disponibles.")
            
            print("=" * 60)
            print("Usa uno de estos nombres en setup_api() del código:")
            print('Ejemplo: genai.GenerativeModel(model_name="models/gemini-...")')
            print("=" * 60)

except FileNotFoundError:
    print("Error: No se pudo leer el archivo api_key.txt")
except Exception as e:
    print(f"Ocurrió un error: {e}")
