import tkinter as tk
from tkinter import messagebox
import google.generativeai as genai
from PIL import ImageGrab, Image, ImageTk
import easyocr
import numpy as np
import sys
import os
import threading
import ctypes
import json

# import tkinter.tix as tix  # Eliminado

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert") if self.widget.winfo_ismapped() else (0, 0, 0, 0)
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#333", foreground="white",
                         relief=tk.SOLID, borderwidth=1,
                         font=("Arial", 9))
        label.pack(ipadx=5, ipady=2)

    def hide_tip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class TraductorDFApp:
    def __init__(self, root):
        self.root = root
        self.last_bbox = None
        self.is_selecting = False
        self.reader = None
        self.api_key_configurada = False
        self.status_text = ""
        self.model = None
        self.history = []

        self.USER_DIR = os.path.dirname(os.path.abspath(__file__))
        self.ICON_PATH = os.path.join(self.USER_DIR, "icon.ico")
        self.API_KEY_PATH = os.path.join(self.USER_DIR, "api_key.txt")
        self.CONFIG_PATH = os.path.join(self.USER_DIR, "config.json")

        self.setup_app_id()
        self.load_config()
        self.setup_api()
        self.setup_gui()

        if not self.api_key_configurada:
            self.mostrar_mensaje_api()

        threading.Thread(target=self.cargar_modelo_ocr, daemon=True).start()

    def setup_app_id(self):
        myappid = 'dftraductor.v1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    def setup_api(self):
        if not os.path.exists(self.API_KEY_PATH):
            try:
                with open(self.API_KEY_PATH, "w") as f:
                    f.write("")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear el archivo api_key.txt: {e}")
                self.root.quit()

        if self.cargar_api_key():
            self.api_key_configurada = True
            try:
                self.model = genai.GenerativeModel(model_name="gemini-1.5-flash")
            except Exception as e:
                self.actualizar_overlay(f"Error al configurar el modelo de IA: {e}")

    def cargar_api_key(self):
        try:
            with open(self.API_KEY_PATH, "r") as f:
                api_key = f.read().strip()
            if api_key:
                genai.configure(api_key=api_key)
                return True
        except Exception:
            pass
        return False

    def setup_gui(self):
        self.root.title("Traductor DF")
        try:
            self.root.iconbitmap(default=self.ICON_PATH)
        except tk.TclError:
            print(f"No se pudo cargar el icono: {self.ICON_PATH}")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.85)
        self.root.geometry(self.config.get("geometry", "800x200"))
        self.root.minsize(400, 150)

        self.main_frame = tk.Frame(self.root, bg="black")
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.setup_title_bar()
        self.setup_buttons()
        self.setup_content_area()
        self.setup_bindings()

    def setup_title_bar(self):
        title_bar = tk.Frame(self.main_frame, bg="gray20", height=25)
        title_bar.pack(fill="x", pady=(0, 5))
        title_bar.bind("<Button-1>", self.on_drag_start)
        title_bar.bind("<B1-Motion>", self.on_drag_motion)

    def setup_buttons(self):
        button_frame = tk.Frame(self.main_frame, bg="black")
        button_frame.pack(fill="x", pady=(0, 10))

        self.select_button = tk.Button(button_frame, text="Seleccionar Área (Ctrl+Q)", command=self.iniciar_seleccion_y_traduccion, bg="dark grey", fg="white")
        self.select_button.pack(side="left", padx=5)

        self.retry_button = tk.Button(button_frame, text="Reintentar (Ctrl+R)", command=self.procesar_captura, bg="dark grey", fg="white", state="disabled")
        self.retry_button.pack(side="left", padx=5)

        self.clear_button = tk.Button(button_frame, text="Limpiar (Ctrl+W)", command=self.limpiar_overlay, bg="dark grey", fg="white")
        self.clear_button.pack(side="left", padx=5)

        self.history_button = tk.Button(button_frame, text="📜 Historial", command=self.mostrar_historial, bg="dark grey", fg="white")
        self.history_button.pack(side="left", padx=5)

        self.config_button = tk.Button(button_frame, text="⚙️ Configuración", command=self.abrir_configuracion, bg="dark grey", fg="white")
        self.config_button.pack(side="right", padx=5)

        self.setup_tooltips()

    def setup_tooltips(self):
        Tooltip(self.select_button, "Seleccionar un área de la pantalla para traducir (Ctrl+Q)")
        Tooltip(self.retry_button, "Reintentar la traducción del último área seleccionada (Ctrl+R)")
        Tooltip(self.clear_button, "Limpiar el texto de la traducción (Ctrl+W)")
        Tooltip(self.history_button, "Mostrar el historial de traducciones")
        Tooltip(self.config_button, "Abrir la ventana de configuración para establecer la API Key")

    def setup_content_area(self):
        content_frame = tk.Frame(self.main_frame, bg="black")
        content_frame.pack(fill="both", expand=True, padx=5)

        self.spinner = LoadingSpinner(content_frame, self)

        self.label_traduccion = tk.Label(content_frame, font=("Arial", 12), bg="black", fg="white", wraplength=780, justify="left")
        self.label_traduccion.pack(fill="both", expand=True)

    def setup_bindings(self):
        self.root.bind('<Configure>', self.on_resize)
        self.root.bind('<Control-q>', lambda e: self.iniciar_seleccion_y_traduccion())
        self.root.bind('<Control-r>', lambda e: self.procesar_captura() if self.retry_button['state'] == 'normal' else None)
        self.root.bind('<Control-w>', lambda e: self.limpiar_overlay())
        self.root.bind('<Control-Alt-q>', lambda e: self.root.destroy())
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_config(self):
        try:
            with open(self.CONFIG_PATH, "r") as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {"geometry": "800x200"}

    def save_config(self):
        self.config['geometry'] = self.root.geometry()
        with open(self.CONFIG_PATH, "w") as f:
            json.dump(self.config, f)

    def on_closing(self):
        self.save_config()
        self.root.destroy()

    def mostrar_historial(self):
        history_window = tk.Toplevel(self.root)
        history_window.title("Historial de Traducciones")
        history_window.geometry("600x400")
        history_window.transient(self.root)
        history_window.grab_set()

        x = self.root.winfo_x() + (self.root.winfo_width() - 600) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 400) // 2
        history_window.geometry(f"600x400+{x}+{y}")

        text_widget = tk.Text(history_window, bg="black", fg="white", wrap="word", font=("Arial", 10))
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        for i, item in enumerate(reversed(self.history)):
            text_widget.insert(tk.END, f"--- Traducción {len(self.history) - i} ---\n", "title")
            text_widget.insert(tk.END, item + "\n\n")

        text_widget.tag_config("title", foreground="cyan", font=("Arial", 12, "bold"))
        text_widget.config(state="disabled")


    def on_drag_start(self, event):
        self.root._drag_start_x = event.x
        self.root._drag_start_y = event.y

    def on_drag_motion(self, event):
        x = self.root.winfo_x() - self.root._drag_start_x + event.x
        y = self.root.winfo_y() - self.root._drag_start_y + event.y
        self.root.geometry(f"+{x}+{y}")

    def iniciar_seleccion_y_traduccion(self, event=None):
        if self.is_selecting:
            return
        self.is_selecting = True
        self.actualizar_overlay("")

        selector_window = tk.Toplevel(self.root)
        selector_window.attributes("-fullscreen", True)
        selector_window.attributes("-alpha", 0.2)
        selector_window.attributes("-topmost", True)
        selector_window.overrideredirect(True)

        canvas = tk.Canvas(selector_window, cursor="cross", bg="grey")
        canvas.pack(fill="both", expand=True)

        start_x, start_y, rect = None, None, None

        def on_press(event):
            nonlocal start_x, start_y, rect
            start_x, start_y = event.x, event.y
            rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline='red', width=2)

        def on_move(event):
            canvas.coords(rect, start_x, start_y, event.x, event.y)

        def on_release(event):
            self.is_selecting = False
            end_x, end_y = event.x, event.y
            selector_window.destroy()

            x1, y1 = min(start_x, end_x), min(start_y, end_y)
            x2, y2 = max(start_x, end_x), max(start_y, end_y)

            if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
                self.last_bbox = (x1, y1, x2, y2)
                self.retry_button.config(state="normal")
                self.root.after(50, self.procesar_captura)

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_move)
        canvas.bind("<ButtonRelease-1>", on_release)

    def cargar_modelo_ocr(self):
        if not self.reader:
            try:
                self.status_text = "Cargando OCR"
                self.actualizar_overlay("Cargando modelo de OCR...", loading=True)
                self.reader = easyocr.Reader(['en'])
                self.actualizar_overlay("Modelo de OCR cargado. Listo para traducir.")
            except Exception as e:
                self.actualizar_overlay(f"Error al cargar el modelo de OCR: {e}")

    def procesar_captura(self):
        if not self.last_bbox:
            return

        if not self.reader:
            self.actualizar_overlay("El modelo de OCR aún se está cargando. Inténtalo de nuevo en un momento.")
            return

        if not self.api_key_configurada or not self.model:
            self.mostrar_mensaje_api()
            return

        self.actualizar_overlay("", loading=True)
        self.retry_button.config(state="disabled")

        threading.Thread(target=self._procesar_captura_thread, daemon=True).start()

    def _procesar_captura_thread(self):
        try:
            self.status_text = "Traduciendo"
            screenshot = ImageGrab.grab(bbox=self.last_bbox)
            texto_extraido = "\n".join(self.reader.readtext(np.array(screenshot), detail=0, paragraph=True))

            if not texto_extraido.strip():
                self.root.after(0, lambda: self.actualizar_overlay("No se detectó texto."))
                self.root.after(0, lambda: self.retry_button.config(state="normal"))
                return

            prompt = self.crear_prompt(texto_extraido)
            response = self.model.generate_content(prompt)

            traduccion = response.text
            self.history.append(traduccion)
            if len(self.history) > 10:
                self.history.pop(0)

            self.root.after(0, lambda: self.actualizar_overlay(traduccion))
            self.last_bbox = None
            self.root.after(0, lambda: self.retry_button.config(state="disabled"))

        except genai.types.generation_types.StopCandidateException as e:
            self.root.after(0, lambda: self.actualizar_overlay(f"Error de contenido: {e}\nIntenta seleccionar un área diferente."))
            self.root.after(0, lambda: self.retry_button.config(state="normal"))
        except Exception as e:
            self.root.after(0, lambda: self.actualizar_overlay(f"Error en la traducción: {e}\nPuedes reintentarlo."))
            self.root.after(0, lambda: self.retry_button.config(state="normal"))

    def crear_prompt(self, texto):
        return (
            "Eres un sistema de traducción automática. Tu única función es traducir el siguiente texto de inglés a español, con un conocimiento experto del videojuego Dwarf Fortress. "
            "Sigue estas reglas de forma estricta:\n"
            "1. NO incluyas preámbulos, explicaciones, saludos o cualquier texto que no sea la traducción directa.\n"
            "2. Mantén la estructura de saltos de línea y párrafos idéntica a la del texto original.\n"
            "3. Conserva intactos todos los símbolos, números, puntuación y nombres propios (personajes, lugares, etc.).\n"
            "4. Utiliza la terminología establecida de Dwarf Fortress en español (ej. 'dwarves' -> 'enanos').\n"
            "5. El formato, mayúsculas, y cualquier elemento de la interfaz de usuario debe permanecer igual.\n\n"
            "**Texto a traducir:**\n\n"
            f"```\n{texto}\n```"
        )

    def actualizar_overlay(self, texto, loading=False):
        def actualizar():
            if loading:
                self.label_traduccion.pack_forget()
                self.spinner.start()
            else:
                self.spinner.stop()
                self.label_traduccion.config(text=texto)
                self.label_traduccion.configure(wraplength=self.main_frame.winfo_width() - 20)
                self.label_traduccion.pack(fill="both", expand=True, padx=5)
            self.root.update_idletasks()

        if self.root.winfo_exists():
            self.root.after(0, actualizar)

    def limpiar_overlay(self):
        self.actualizar_overlay("")

    def on_resize(self, event):
        if event.widget == self.root:
            self.label_traduccion.configure(wraplength=self.main_frame.winfo_width() - 20)

    def abrir_configuracion(self):
        config_window = tk.Toplevel(self.root)
        config_window.title("Configuración")
        config_window.geometry("400x150")
        config_window.resizable(False, False)
        config_window.transient(self.root)
        config_window.grab_set()

        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 150) // 2
        config_window.geometry(f"400x150+{x}+{y}")

        frame = tk.Frame(config_window, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="API Key de Google AI:").pack(anchor="w")
        api_entry = tk.Entry(frame, width=50)
        api_entry.pack(fill="x", pady=(5, 15))

        try:
            with open(self.API_KEY_PATH, "r") as f:
                api_entry.insert(0, f.read().strip())
        except FileNotFoundError:
            pass

        def guardar_config():
            api_key = api_entry.get().strip()
            if api_key:
                try:
                    with open(self.API_KEY_PATH, "w") as f:
                        f.write(api_key)
                    self.setup_api()
                    self.actualizar_overlay("Configuración guardada. ¡Listo para traducir!")
                    config_window.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Error al guardar la configuración: {e}", parent=config_window)
            else:
                messagebox.showwarning("Advertencia", "Por favor, ingresa una API Key válida", parent=config_window)

        button_frame = tk.Frame(frame)
        button_frame.pack(fill="x", pady=(10, 0))
        tk.Button(button_frame, text="Guardar", command=guardar_config, width=10).pack(side="right", padx=5)
        tk.Button(button_frame, text="Cancelar", command=config_window.destroy, width=10).pack(side="right", padx=5)

    def mostrar_mensaje_api(self):
        mensaje = ("Por favor, configura tu API Key de Google AI para comenzar.\n\n"
                   "1. Obtén una API Key en: https://aistudio.google.com/apikey\n"
                   "2. Haz clic en el botón de configuración (⚙️)\n"
                   "3. Pega tu API Key y guarda.")
        self.actualizar_overlay(mensaje)

class LoadingSpinner:
    def __init__(self, parent, app_ref):
        self.parent = parent
        self.app = app_ref
        self.spinner_frame = tk.Frame(parent, bg="black")
        self.loading_label = tk.Label(self.spinner_frame, text="", font=("Arial", 12), fg="white", bg="black")
        self.loading_label.pack(expand=True)
        self.spinner_chars = ["|", "/", "-", "\\"]
        self.spinner_index = 0
        self.is_spinning = False

    def start(self):
        self.is_spinning = True
        self.spinner_frame.pack(fill="both", expand=True)
        self.animate()

    def stop(self):
        self.is_spinning = False
        self.spinner_frame.pack_forget()

    def animate(self):
        if self.is_spinning:
            char = self.spinner_chars[self.spinner_index]
            status_text = self.app.status_text
            self.loading_label.config(text=f"{status_text}... {char}")
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
            self.parent.after(100, self.animate)

if __name__ == "__main__":
    root = tk.Tk()
    app = TraductorDFApp(root)
    root.mainloop()

