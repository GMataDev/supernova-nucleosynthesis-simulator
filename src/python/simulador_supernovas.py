import sys
import os
import math
import numpy as np
import matplotlib
# ¡IMPORTANTE! Usar el backend de Qt5
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle, Rectangle, Arc # Arc para campo magnético
# Backend para incrustar Matplotlib en PyQt5
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# --- NUEVO: Toolbar para la gráfica interactiva ---
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

# --- IMPORTACIONES DE PYQT5 ---
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QStackedWidget, QMessageBox,
    QFrame, QSizePolicy, QSpacerItem, QProgressBar, QDialog # --- NUEVO: QDialog para la ventana emergente
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, pyqtProperty, QEasingCurve

# --- IMPORTACIONES CIENTÍFICAS ---
try:
    import astropy.units as u
    from astropy.constants import M_sun, L_sun
except ImportError:
    app = QApplication(sys.argv)
    QMessageBox.critical(None, "Error de Dependencia",
                         "Este programa requiere la biblioteca 'astropy'.\n\nInstálela con: pip install astropy")
    sys.exit()

# --- Constantes Globales de Animación ---
COUNTDOWN_SECONDS = 3
FRAMES_PER_SECOND = 25
COUNTDOWN_FRAMES = COUNTDOWN_SECONDS * FRAMES_PER_SECOND
POST_COUNTDOWN_PAUSE_FRAMES = 40
INITIAL_WAIT_FRAMES = COUNTDOWN_FRAMES + POST_COUNTDOWN_PAUSE_FRAMES
NUM_EXPANSION_FRAMES = 120
NUM_FADE_FRAMES = 100
ANIMATION_INTERVAL = 40
VIEW_LIMIT = 70.0
MAX_RADIUS = VIEW_LIMIT + 10.0
INITIAL_WAVE_FRAMES = 25
FLASH_DURATION_FRAMES = 8
FINAL_FADE_FRAMES = 20

# --- Constantes Físicas ---
FOE = (1e51 * u.erg)
L_SOLAR_ERG_S = L_sun.to(u.erg / u.s).value
M_SOLAR_KG = M_sun.to(u.kg)
M_SOLAR_VAL_KG = M_sun.to(u.kg).value # Valor flotante para cálculos rápidos

# --- NUEVO: Constantes para comparaciones ---
EARTH_ANNUAL_ENERGY_JOULES = 5.8e20  # Consumo aprox anual de la humanidad (~160,000 TWh)
REF_DISTANCE_PC = 197.0 # Distancia de Betelgeuse en parsecs (~642 años luz)

# Radios representativos (escalados para visibilidad)
NEUTRON_STAR_RADIUS_KM = 15 # Radio típico en km
SCHWARZSCHILD_RADIUS_KM_PER_MSUN = 3 # Radio Schwarzschild por masa solar en km

# --- Parámetros de Simulación (Colores) ---
AGUJERO_NEGRO_COLOR = '#0a0a0a'
FONDO_MENU_COLOR = '#000018'
FONDO_SIM_COLOR = 'black'
COLOR_TEXTO_PRIN = '#FFFFFF'
COLOR_TEXTO_SEC = '#DDDDDD'
COLOR_ACENTO_PRI = '#00FFFF' # Cyan
COLOR_ACENTO_SEC = '#FFA500' # Orange
COLOR_AMARILLO = '#FFFF00'

# (Optimización Anti-Lag)
NUM_PARTICULAS_GRUESAS = 450
NUM_PARTICULAS_FINAS = 550
NUM_PARTICULAS_NEBULOSA = 200
NUM_ESTRELLAS_FONDO = 500
NUM_ESTRELLAS_FONDO_MENU = 150 # Menos estrellas para el fondo del menú

# --- Información de Créditos ---
NOMBRE_USUARIO = "Gustavo Mata Batalla"
CREDITO_PROGRAMA_L1 = f"Programa hecho por {NOMBRE_USUARIO}"
CREDITO_PROGRAMA_L2 = "con la ayuda de Gemini AI."
ESCUELA_UNAM = "UNAM"
ESCUELA_CCH = "CCH NAUCALPAN"
CREDITO_ESCUELA = f"{ESCUELA_UNAM} | {ESCUELA_CCH}"

# --- Elementos Base ---
# --- MODIFICACIÓN: Se agregó 'mass_fraction' para calcular los KG expulsados ---
ELEMENTOS_TIPO_IA = [
    {'nombre': 'Silicio (Si)', 'color': '#33ff33', 'tamaño': 50, 'zona': 'exterior', 'cantidad': NUM_PARTICULAS_GRUESAS, 'mass_fraction': 0.3},
    {'nombre': 'Níquel (Ni-56)', 'color': '#FFFFE0', 'tamaño': 25, 'zona': 'nucleo', 'cantidad': NUM_PARTICULAS_FINAS, 'mass_fraction': 0.6},
]
ELEMENTOS_TIPO_II = [
    {'nombre': 'Hidrógeno (H)', 'color': '#FF3333', 'tamaño': 70, 'zona': 'exterior', 'cantidad': NUM_PARTICULAS_GRUESAS, 'mass_fraction': 0.5},
    {'nombre': 'Helio (He)', 'color': '#FF9933', 'tamaño': 50, 'zona': 'media', 'cantidad': NUM_PARTICULAS_GRUESAS, 'mass_fraction': 0.3},
    {'nombre': 'Oxígeno (O) / Núcleo', 'color': '#3399FF', 'tamaño': 20, 'zona': 'nucleo', 'cantidad': NUM_PARTICULAS_FINAS, 'mass_fraction': 0.15},
]
ELEMENTOS_TIPO_IB = [
    {'nombre': 'Helio (He)', 'color': '#FF9933', 'tamaño': 60, 'zona': 'exterior', 'cantidad': NUM_PARTICULAS_GRUESAS, 'mass_fraction': 0.4},
    {'nombre': 'Oxígeno (O) / Carbono (C)', 'color': '#3399FF', 'tamaño': 30, 'zona': 'media', 'cantidad': NUM_PARTICULAS_FINAS, 'mass_fraction': 0.4},
    {'nombre': 'Silicio (Si) / Núcleo', 'color': '#33ff33', 'tamaño': 20, 'zona': 'nucleo', 'cantidad': NUM_PARTICULAS_FINAS, 'mass_fraction': 0.2},
]
ELEMENTOS_TIPO_IC = [
    {'nombre': 'Oxígeno (O) / Carbono (C)', 'color': '#3399FF', 'tamaño': 60, 'zona': 'exterior', 'cantidad': NUM_PARTICULAS_GRUESAS, 'mass_fraction': 0.5},
    {'nombre': 'Silicio (Si)', 'color': '#33ff33', 'tamaño': 30, 'zona': 'media', 'cantidad': NUM_PARTICULAS_FINAS, 'mass_fraction': 0.3},
    {'nombre': 'Hierro (Fe) / Núcleo', 'color': '#FFFFE0', 'tamaño': 20, 'zona': 'nucleo', 'cantidad': NUM_PARTICULAS_FINAS, 'mass_fraction': 0.2},
]

# --- Colores Miku ---
COLOR_MIKU_PELO = '#39C5BB' # Cyan Miku
COLOR_MIKU_CARA = '#FFC0CB' # Pink
COLOR_MIKU_MOÑO = '#888888' # Gris/Negro

ELEMENTOS_TIPO_MIKU = [
    {'nombre': 'Pelo (Hatsune)', 'color': COLOR_MIKU_PELO, 'tamaño': 70, 'zona': 'exterior', 'cantidad': NUM_PARTICULAS_GRUESAS, 'mass_fraction': 0.5},
    {'nombre': 'Cara (Kagamine... wait)', 'color': COLOR_MIKU_CARA, 'tamaño': 40, 'zona': 'media', 'cantidad': NUM_PARTICULAS_GRUESAS, 'mass_fraction': 0.3},
    {'nombre': 'Moño (Ribbon)', 'color': COLOR_MIKU_MOÑO, 'tamaño': 20, 'zona': 'nucleo', 'cantidad': NUM_PARTICULAS_FINAS, 'mass_fraction': 0.2},
]

ELEMENTOS_NEBULOSA_FONDO = [
    {'nombre': 'Nebulosa (H)', 'color': '#FF3333', 'tamaño': 150, 'zona': 'fondo', 'cantidad': NUM_PARTICULAS_NEBULOSA // 2, 'mass_fraction': 0},
    {'nombre': 'Nebulosa (O)', 'color': '#3399FF', 'tamaño': 120, 'zona': 'fondo', 'cantidad': NUM_PARTICULAS_NEBULOSA // 2, 'mass_fraction': 0},
]

star_exploded = False

# --- Lógica de Curva de Luz Visual ---
def calculate_visual_brightness(i, start_frame, peak_frame, end_frame):
    base_alpha = 0.9
    if i < start_frame: return 0.0
    elif i <= peak_frame:
        progress = (i - start_frame) / (peak_frame - start_frame); return base_alpha * progress**3
    elif i <= end_frame:
        progress = (i - peak_frame) / (end_frame - peak_frame); return base_alpha * (1.0 - progress)**1.8
    else: return 0.0

# --- CLASE MEJORADA: Gráfica Interactiva con Zoom y Pan ---
class LightCurveDialog(QDialog):
    def __init__(self, sim_data, parent=None):
        super().__init__(parent)
        self.sim_data = sim_data
        self.setWindowTitle("Análisis Científico: Curva de Luz (Interactivo)")
        self.resize(1000, 700) # Un poco más grande para apreciar detalles
        self.setStyleSheet(f"background-color: {FONDO_MENU_COLOR}; color: white;")
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # --- CONFIGURACIÓN MATPLOTLIB ---
        self.figure = Figure(figsize=(8, 6), dpi=100, facecolor='#111111')
        self.canvas = FigureCanvas(self.figure)
        
        # Barra de herramientas nativa (necesaria para la interactividad base)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("background-color: white; color: black;")
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # --- CONECTAR EVENTOS DEL MOUSE PARA ZOOM ---
        # Esto permite detectar el movimiento de la rueda
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        
        # Dibujar la gráfica inicial
        self.plot_curve()
        
        # Activar modo "Pan" (Moverse) por defecto en la toolbar para no tener que hacer clic en el botón
        # Esto permite arrastrar con el clic izquierdo inmediatamente
        self.toolbar.pan() 

    def on_scroll(self, event):
        """ Función para hacer Zoom con la rueda del mouse centrado en el cursor """
        ax = self.figure.axes[0]
        if event.inaxes != ax: return

        # Factor de zoom (base_scale > 1 hace zoom in, < 1 hace zoom out)
        base_scale = 1.2
        if event.button == 'up': # Rueda hacia arriba (Zoom In)
            scale_factor = 1/base_scale
        elif event.button == 'down': # Rueda hacia abajo (Zoom Out)
            scale_factor = base_scale
        else:
            return

        # Obtener límites actuales
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()

        # Calcular nuevo ancho y alto
        xdata = event.xdata # Posición del mouse en X
        ydata = event.ydata # Posición del mouse en Y
        
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

        # Calcular nuevas posiciones relativas para mantener el mouse en el mismo punto visual
        relx = (cur_xlim[1] - xdata)/(cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata)/(cur_ylim[1] - cur_ylim[0])

        # Aplicar nuevos límites
        ax.set_xlim([xdata - new_width * (1-relx), xdata + new_width * (relx)])
        ax.set_ylim([ydata - new_height * (1-rely), ydata + new_height * (rely)])
        
        self.canvas.draw()

    def plot_curve(self):
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('black')
        
        # Días extendidos
        days = np.linspace(0, 250, 600)
        luminosity = np.zeros_like(days)
        
        explosion_type = self.sim_data.get('explosion_type', 'None')
        tipo_str = self.sim_data.get('tipo_str', '')
        
        # Factor de escala (1000x)
        SCALE_FACTOR = 1000.0 

        if explosion_type == 'None':
            ax.text(0.5, 0.5, "SIN EXPLOSIÓN - ESTRELLA ESTABLE", color='white', ha='center', fontsize=16)
            ax.set_ylim(0, 10)
        
        elif explosion_type == 'Ia' or "Ia" in tipo_str:
            # Modelo Ia
            peak_val = 100 * SCALE_FACTOR
            tail_val = 30 * SCALE_FACTOR
            luminosity = peak_val * np.exp(-((days - 18)**2) / (2 * 8**2)) + tail_val * np.exp(-(days)/40) * (days > 20)
            
            ax.plot(days, luminosity, color='cyan', linewidth=2.5, label='Luminosidad Bolométrica')
            ax.set_title("Curva de Luz Tipo Ia (Termonuclear)", color='white', fontsize=16, fontweight='bold')
            
            ax.annotate('Pico Máximo (Ni-56)', xy=(18, peak_val), xytext=(50, peak_val * 1.1),
                        arrowprops=dict(facecolor='yellow', shrink=0.05, width=2), color='yellow', fontsize=12)

        elif 'II' in tipo_str:
            # Modelo II-P
            plateau_height = 80 * SCALE_FACTOR
            tail_height = 40 * SCALE_FACTOR
            
            rise = 1 / (1 + np.exp(-(days - 10))) 
            plateau = np.where((days > 15) & (days < 90), plateau_height, 0)
            tail = np.exp(-(days - 90)/20) * tail_height * (days >= 90)
            
            luminosity = rise * np.where(days<=15, days * (plateau_height/15), 0) + plateau + tail
            luminosity = np.convolve(luminosity, np.ones(10)/10, mode='same')
            
            ax.plot(days, luminosity, color='orange', linewidth=2.5, label='Luminosidad Bolométrica')
            ax.set_title("Curva de Luz Tipo II-P (Colapso de Núcleo)", color='white', fontsize=16, fontweight='bold')
            
            ax.annotate('Meseta (Recombinación H)', xy=(50, plateau_height), xytext=(50, plateau_height * 1.3),
                        arrowprops=dict(facecolor='yellow', shrink=0.05, width=2), color='yellow', fontsize=12)

        else: # Ib/Ic
            peak_val = 90 * SCALE_FACTOR
            tail_val = 20 * SCALE_FACTOR
            luminosity = peak_val * np.exp(-((days - 15)**2) / (2 * 6**2)) + tail_val * np.exp(-(days)/30) * (days > 20)
            
            ax.plot(days, luminosity, color='magenta', linewidth=2.5, label='Luminosidad')
            ax.set_title(f"Curva de Luz {tipo_str} (Colapso sin H)", color='white', fontsize=16, fontweight='bold')

        # Etiquetas y Estilo
        ax.set_xlabel("Días desde la explosión", color='#DDDDDD', fontsize=12)
        ax.set_ylabel("Luminosidad Relativa (x1000)", color='#DDDDDD', fontsize=12)
        ax.tick_params(axis='x', colors='white', labelsize=10)
        ax.tick_params(axis='y', colors='white', labelsize=10)
        ax.grid(True, linestyle='-', alpha=0.2, color='#444444')
        
        # Ajuste de límites iniciales
        ylim = ax.get_ylim()
        ax.set_ylim(bottom=0, top=ylim[1] * 1.1) 
        
        self.canvas.draw()


# --- CLASE DE CANVAS DE MATPLOTLIB ---
class MplCanvas(FigureCanvas):
    # (Clase sin cambios)
    def __init__(self, parent=None, width=10, height=10, dpi=100, face_color=FONDO_SIM_COLOR): 
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=face_color) 
        self.ax = self.fig.add_subplot(111); self.ax.set_facecolor(face_color) 
        self.ax.set_xlim(-VIEW_LIMIT, VIEW_LIMIT); self.ax.set_ylim(-VIEW_LIMIT, VIEW_LIMIT)
        self.ax.set_xticks([]); self.ax.set_yticks([]); self.ax.set_aspect('equal', adjustable='box')
        self.fig.tight_layout(pad=2.0)
        super(MplCanvas, self).__init__(self.fig); self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

# --- INICIO DE MODIFICACIÓN (Transiciones) ---
# Clase QStackedWidget personalizada para manejar el fade
class FadingStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super(FadingStackedWidget, self).__init__(parent)
        self.m_now = 0
        self.m_next = 0
        self.m_wrap = False
        self.m_pnow = QWidget()
        self.m_anim = QPropertyAnimation()
        self.m_speed = 500 # Duración del fade en ms

    def setSpeed(self, speed):
        self.m_speed = speed

    def animation(self, old_widget, new_widget):
        new_widget.hide()
        pnext = new_widget.grab()
        self.m_pnow = old_widget.grab()

        self.m_anim = QPropertyAnimation(new_widget, b"opacity", duration=self.m_speed, finished=self.animDone)
        self.m_anim.setStartValue(0.0)
        self.m_anim.setEndValue(1.0)
        self.m_anim.setEasingCurve(QEasingCurve.InOutQuad) # Curva suave

        old_widget.hide()
        new_widget.setWindowOpacity(0.0)
        new_widget.show()
        self.m_anim.start()

    def setCurrentIndex(self, index):
        if self.currentIndex() == index: return
        old_widget = self.currentWidget()
        new_widget = self.widget(index)
        super(FadingStackedWidget, self).setCurrentIndex(index) # Importante cambiar el índice *antes* de animar
        self.animation(old_widget, new_widget)

    def animDone(self):
        self.widget(self.currentIndex()).setWindowOpacity(1.0) # Asegurar opacidad final

    # Propiedad 'opacity' necesaria para QPropertyAnimation
    def _get_opacity(self):
        return self.windowOpacity()
    def _set_opacity(self, opacity):
        self.setWindowOpacity(opacity)
    opacity = pyqtProperty(float, _get_opacity, _set_opacity)
# --- FIN DE MODIFICACIÓN ---

# --- CLASE PRINCIPAL DE LA APLICACIÓN (PYQT5) ---
class SupernovaSimulatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sim_ani = None # Renombrado para claridad
        self.menu_bg_ani = None # Animación separada para el fondo del menú
        self.element_layers = []; self.nebula_layers = []
        self.mag_field_lines = [] # Artista para las líneas de campo
        self.sim_data = {}; self.remnant_current_pos = [0.0, 0.0]
        self.setWindowTitle("Simulador de Supernovas (UNAM - CCH Naucalpan) - v3.12") 
        self.setStyleSheet(f"""
            /* (QSS sin cambios) */
            QMainWindow, QWidget {{ background-color: {FONDO_MENU_COLOR}; color: {COLOR_TEXTO_SEC}; font-family: 'Segoe UI', Arial, sans-serif; }}
            QLabel#TitleLabel {{ font-size: 44px; font-weight: bold; color: {COLOR_TEXTO_PRIN}; padding-top: 15px; background-color: transparent; }}
            QLabel#SubTitleLabel {{ font-size: 24px; font-style: italic; color: {COLOR_TEXTO_SEC}; padding-bottom: 20px; background-color: transparent; }}
            QLabel#InputLabel {{ font-size: 26px; color: {COLOR_TEXTO_PRIN}; padding-top: 15px; background-color: transparent; }}
            QLabel#SuggestLabel {{ font-size: 18px; color: {COLOR_TEXTO_SEC}; background-color: transparent; }}
            QLabel#SuggestHeader {{ font-size: 18px; color: {COLOR_AMARILLO}; padding-top: 15px; background-color: transparent; }}
            QLabel#CreditsLabel {{ font-size: 16px; font-style: italic; color: {COLOR_AMARILLO}; background-color: transparent; }}
            QLabel#CreditsSubLabel {{ font-size: 16px; font-style: italic; color: {COLOR_TEXTO_PRIN}; background-color: transparent; }}
            QLineEdit {{ font-size: 24px; background-color: #222222; color: {COLOR_TEXTO_PRIN}; border: 1px solid #555; border-radius: 5px; padding: 10px; max-width: 180px; alignment: center; }}
            QPushButton#MenuButton {{ font-size: 22px; font-weight: bold; color: {COLOR_ACENTO_PRI}; background-color: #001144; border: none; border-radius: 8px; padding: 12px 20px; margin-top: 30px; }}
            QPushButton#MenuButton:hover {{ background-color: #003388; color: {COLOR_TEXTO_PRIN}; }}
            QPushButton#ReturnButton {{ font-size: 18px; font-weight: bold; color: #AAAAAA; background-color: #111111; border: 1px solid #333333; border-radius: 8px; padding: 10px 18px; }}
            QPushButton#ReturnButton:hover {{ background-color: #222222; color: #FFFFFF; }}
            /* NUEVO ESTILO PARA BOTON DE GRAFICA */
            QPushButton#GraphButton {{ font-size: 18px; font-weight: bold; color: {COLOR_AMARILLO}; background-color: #333300; border: 1px solid {COLOR_AMARILLO}; border-radius: 8px; padding: 8px 15px; margin-top: 10px; }}
            QPushButton#GraphButton:hover {{ background-color: {COLOR_AMARILLO}; color: black; }}
            
            QWidget#SimWidget {{ background-color: {FONDO_SIM_COLOR}; }}
            QWidget#InfoPanel {{ background-color: {FONDO_SIM_COLOR}; border-right: 1px solid #333; }}
            QLabel#InfoTitle {{ font-size: 30px; font-weight: bold; color: {COLOR_ACENTO_PRI}; padding-bottom: 15px; background-color: transparent; }}
            QLabel#InfoText {{ font-size: 22px; color: {COLOR_TEXTO_PRIN}; background-color: transparent; }}
            QLabel#DataLabel {{ font-size: 22px; font-weight: bold; color: {COLOR_ACENTO_SEC}; background-color: transparent; }}
            QLabel#DataSubLabel {{ font-size: 16px; color: {COLOR_TEXTO_SEC}; padding-bottom: 10px; background-color: transparent; }}
            QFrame[frameShape="4"] {{ color: #444; }}
            QLabel#LightCurveDesc {{ font-size: 18px; color: {COLOR_TEXTO_SEC}; font-style: italic; padding-top: 10px; padding-bottom: 5px; background-color: transparent; }}
            QProgressBar {{
                border: 1px solid #555;
                border-radius: 5px;
                text-align: center; 
                font-size: 12px;
                color: {COLOR_TEXTO_SEC};
                height: 10px; 
                margin-top: 10px;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_ACENTO_SEC}; 
                border-radius: 4px;
            }}
        """)
        
        self.stacked_widget = FadingStackedWidget(self)
        self.stacked_widget.setSpeed(400) 
        
        self.setCentralWidget(self.stacked_widget)
        self.main_menu_page = self.create_main_menu_page()
        self.simulation_page = QWidget() # Placeholder
        self.stacked_widget.addWidget(self.main_menu_page)
        
        # Iniciar la animación del fondo del menú solo si estamos en esa página
        if self.stacked_widget.currentWidget() == self.main_menu_page:
            self.start_menu_background_animation()
        self.stacked_widget.currentChanged.connect(self.handle_page_change) # Conectar señal
            
        self.showMaximized()

    def handle_page_change(self, index):
        """ Controla el inicio/parada de las animaciones al cambiar de página """
        if self.stacked_widget.widget(index) == self.main_menu_page:
            self.stop_simulation_animation() # Detener sim si volvemos al menú
            self.start_menu_background_animation()
        else:
            self.stop_menu_background_animation()
            # La animación de simulación se inicia en handle_input_and_build

    def create_main_menu_page(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        # Añadir Canvas para el fondo animado
        self.menu_bg_canvas = MplCanvas(widget, width=5, height=4, dpi=100, face_color=FONDO_MENU_COLOR)
        self.menu_bg_canvas.ax.set_xticks([]) # Ocultar ejes
        self.menu_bg_canvas.ax.set_yticks([])
        self.menu_bg_canvas.ax.set_xlim(0, 1); self.menu_bg_canvas.ax.set_ylim(0, 1) # Usar coordenadas normalizadas
        self.menu_bg_canvas.setStyleSheet("background-color: transparent;") # Hacer el fondo del widget transparente
        self.menu_bg_canvas.setAttribute(Qt.WA_TransparentForMouseEvents) # Ignorar eventos de mouse
        self.menu_bg_canvas.lower() # Ponerlo detrás de otros widgets
        # Usaremos un layout diferente para superponer los widgets
        main_menu_content_widget = QWidget(widget) # Contenedor para el contenido real
        main_menu_layout = QVBoxLayout(main_menu_content_widget)
        main_menu_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        layout.addWidget(self.menu_bg_canvas) # El canvas ocupa todo el fondo
        layout.addWidget(main_menu_content_widget) # El contenido va encima
        # Preparar datos para las estrellas del menú
        self.menu_stars_x = np.random.rand(NUM_ESTRELLAS_FONDO_MENU)
        self.menu_stars_y = np.random.rand(NUM_ESTRELLAS_FONDO_MENU)
        self.menu_stars_sizes = np.random.rand(NUM_ESTRELLAS_FONDO_MENU) * 1.5 + 0.5
        self.menu_stars_alpha = np.random.uniform(0.1, 0.4, NUM_ESTRELLAS_FONDO_MENU)
        self.menu_stars_vx = np.random.uniform(-0.0005, 0.0005, NUM_ESTRELLAS_FONDO_MENU) # Velocidad muy lenta
        self.menu_stars_vy = np.random.uniform(-0.0005, 0.0005, NUM_ESTRELLAS_FONDO_MENU)
        self.menu_bg_scatter = self.menu_bg_canvas.ax.scatter(self.menu_stars_x, self.menu_stars_y, s=self.menu_stars_sizes, color='white', alpha=self.menu_stars_alpha, zorder=-10)

        # Añadir el resto de widgets al main_menu_layout
        title = QLabel("🌌 Simulador Físico de Supernovas 💥"); title.setObjectName("TitleLabel"); title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("Visualiza el destino final de las estrellas"); subtitle.setObjectName("SubTitleLabel"); subtitle.setAlignment(Qt.AlignCenter)
        main_menu_layout.addWidget(title); main_menu_layout.addWidget(subtitle)

        sep1 = QFrame(); sep1.setFrameShape(QFrame.HLine); sep1.setFrameShadow(QFrame.Sunken)
        main_menu_layout.addWidget(sep1, 0, Qt.AlignHCenter)

        input_label = QLabel("Ingrese la Masa Solar (M☉) de la estrella:"); input_label.setObjectName("InputLabel"); input_label.setAlignment(Qt.AlignCenter)
        self.mass_entry = QLineEdit(); self.mass_entry.setAlignment(Qt.AlignCenter)
        self.mass_entry.returnPressed.connect(self.handle_input_and_build)
        main_menu_layout.addWidget(input_label, 0, Qt.AlignCenter); main_menu_layout.addWidget(self.mass_entry, 0, Qt.AlignCenter)

        sug_header = QLabel("--- Clasificación Espectral (Sugerencias) ---"); sug_header.setObjectName("SuggestHeader"); sug_header.setAlignment(Qt.AlignCenter)
        main_menu_layout.addWidget(sug_header, 0, Qt.AlignHCenter)
        sug_list = ["✨ 1.4 M☉  ➜  Tipo Ia", "🌟 15.0 M☉ ➜  Tipo II", "🌟 22.0 M☉ ➜  Tipo Ib", "🌟 30.0 M☉ ➜  Tipo Ic", "⭐ ≤ 8 M☉    ➜  No Supernova"]
        for sug in sug_list:
            label = QLabel(sug); label.setObjectName("SuggestLabel"); label.setAlignment(Qt.AlignCenter)
            main_menu_layout.addWidget(label, 0, Qt.AlignCenter)
        sim_button = QPushButton("Simular Destino Estelar"); sim_button.setObjectName("MenuButton")
        sim_button.clicked.connect(self.handle_input_and_build)
        main_menu_layout.addWidget(sim_button, 0, Qt.AlignCenter)
        main_menu_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine); sep2.setFrameShadow(QFrame.Sunken)
        main_menu_layout.addWidget(sep2, 0, Qt.AlignHCenter)
        cred_escuela = QLabel(CREDITO_ESCUELA); cred_escuela.setObjectName("CreditsLabel"); cred_escuela.setAlignment(Qt.AlignCenter)
        cred_prog = QLabel(f"{CREDITO_PROGRAMA_L1} {CREDITO_PROGRAMA_L2}"); cred_prog.setObjectName("CreditsSubLabel"); cred_prog.setAlignment(Qt.AlignCenter)
        main_menu_layout.addWidget(cred_escuela, 0, Qt.AlignCenter); main_menu_layout.addWidget(cred_prog, 0, Qt.AlignCenter)
        btn_salir = QPushButton("Salir del Programa"); btn_salir.setObjectName("ReturnButton")
        btn_salir.clicked.connect(self.close)
        main_menu_layout.addWidget(btn_salir, 0, Qt.AlignCenter); main_menu_layout.addSpacing(20)

        return widget

    def animate_menu_background(self, i):
        """ Anima las estrellas del fondo del menú """
        try:
            # Mover estrellas
            self.menu_stars_x = (self.menu_stars_x + self.menu_stars_vx) % 1.0 # Usar módulo para que reaparezcan
            self.menu_stars_y = (self.menu_stars_y + self.menu_stars_vy) % 1.0
            
            # Parpadeo sutil
            self.menu_stars_alpha = np.clip(self.menu_stars_alpha + np.random.uniform(-0.02, 0.02, NUM_ESTRELLAS_FONDO_MENU), 0.1, 0.4)
            
            self.menu_bg_scatter.set_offsets(np.c_[self.menu_stars_x, self.menu_stars_y])
            self.menu_bg_scatter.set_alpha(self.menu_stars_alpha)
            return [self.menu_bg_scatter]
        except Exception as e:
            print(f"Error en animación de fondo de menú: {e}")
            self.stop_menu_background_animation() # Detener si hay error
            return []

    def start_menu_background_animation(self):
        if self.menu_bg_ani is None and hasattr(self, 'menu_bg_canvas'):
            try:
                self.menu_bg_ani = FuncAnimation(
                    self.menu_bg_canvas.fig,
                    self.animate_menu_background,
                    interval=50, # Intervalo un poco más largo para suavidad
                    blit=True,
                    repeat=True
                )
                self.menu_bg_canvas.draw()
                print("DEBUG: Iniciando animación de fondo de menú.")
            except Exception as e:
                print(f"Error al iniciar animación de fondo de menú: {e}")
                self.menu_bg_ani = None

    def stop_menu_background_animation(self):
        if self.menu_bg_ani and hasattr(self.menu_bg_ani, 'event_source') and self.menu_bg_ani.event_source is not None:
            try:
                self.menu_bg_ani.event_source.stop()
                print("DEBUG: Deteniendo animación de fondo de menú.")
            except Exception as e:
                print(f"Error al detener animación de fondo de menú: {e}")
            self.menu_bg_ani = None

    def handle_input_and_build(self):
        user_input = self.mass_entry.text()
        if user_input.upper() == 'MIKU':
            try:
                self.remnant_current_pos = [0.0, 0.0]
                self.stop_simulation_animation()
                self.sim_data = self.build_simulation_data("MIKU") # Pasa el string "MIKU"
                
                if hasattr(self, 'simulation_page') and self.simulation_page is not None:
                    self.stacked_widget.removeWidget(self.simulation_page)
                    self.simulation_page.deleteLater()
                
                self.simulation_page = self.create_simulation_page(self.sim_data)
                self.stacked_widget.addWidget(self.simulation_page)
                self.stacked_widget.setCurrentWidget(self.simulation_page)
                self.start_simulation_animation()
                return # Salir de la función aquí
            except Exception as e:
                QMessageBox.critical(self, "Error de Easter Egg", f"Ocurrió un error: {e}")
                print(f"Error detallado: {e}"); import traceback; traceback.print_exc()
                return

        try:
            masa_solar_float = float(user_input) # Usar user_input
            if masa_solar_float <= 0: QMessageBox.warning(self, "Masa Inválida", "La masa debe ser un número positivo."); return
            self.remnant_current_pos = [0.0, 0.0]
            self.stop_simulation_animation() # Usar nombre específico
            self.sim_data = self.build_simulation_data(masa_solar_float)
            # Recrear la página de simulación cada vez
            if hasattr(self, 'simulation_page') and self.simulation_page is not None:
                self.stacked_widget.removeWidget(self.simulation_page)
                self.simulation_page.deleteLater()
            self.simulation_page = self.create_simulation_page(self.sim_data)
            self.stacked_widget.addWidget(self.simulation_page)
            self.stacked_widget.setCurrentWidget(self.simulation_page) # Esto activará handle_page_change -> stop_menu_background_animation
            self.start_simulation_animation() # Usar nombre específico
        except ValueError: QMessageBox.warning(self, "Entrada Inválida", "Por favor, ingrese un número válido.")
        except Exception as e:
            QMessageBox.critical(self, "Error Inesperado", f"Ocurrió un error: {e}")
            print(f"Error detallado: {e}"); import traceback; traceback.print_exc()

    def build_simulation_data(self, masa_solar_float):
        sim_data = {'is_pulsar': False, 'rem_vx': 0.0, 'rem_vy': 0.0}
        sim_data['light_curve_desc'] = "No aplica"
        sim_data['descripcion'] = "" # Descripción por defecto
        L_PEAK_FACTOR = 2.6e9

        if isinstance(masa_solar_float, str) and masa_solar_float == "MIKU":
            sim_data['masa_Msun'] = 39.0 # 39 = Miku
            sim_data['tipo_str'] = 'Tipo SN-39 (MIKU)'; sim_data['elementos'] = ELEMENTOS_TIPO_MIKU; sim_data['explosion_type'] = 'Ia' # Tipo Ia para destrucción total
            M_progenitor = 1.4 * M_sun # Simular como una Ia
            M_remanente = 0.0 * M_sun; M_ej = M_progenitor - M_remanente; v_ej = np.sqrt(2 * (FOE * 2.0) / M_ej.to(u.kg)) # Más energía
            sim_data['M_ni56_Msun'] = 0.6; sim_data['asymmetry_factor'] = 0.5; # Más asimétrica
            sim_data['rem_size_base'] = 0.0
            sim_data['final_text'] = "How did we get here?, btw Gus says hello"; sim_data['star_color'] = COLOR_MIKU_PELO; sim_data['star_radius'] = 16.0
            sim_data['E_K_erg'] = FOE.value * 2.0; sim_data['light_curve_desc'] = "Curva Luz: ¡Máximo Brillo! (Project DIVA)"
            sim_data['descripcion'] = ("Vocaloid Anomaly SN-39:\n"
                                     "Una fluctuación cuántica en el código ha materializado una singularidad. "
                                     "La estrella progenitora colapsó bajo el peso de 100,000+ canciones.")
            sim_data['abs_magnitude'] = -20.0
            
            sim_data['velocidad_kms'] = v_ej.to(u.km / u.s).value; sim_data['M_rem_Msun'] = M_remanente.to(u.M_sun).value; sim_data['M_ej_Msun'] = M_ej.to(u.M_sun).value
            sim_data['L_peak_Lsun'] = L_PEAK_FACTOR * sim_data['M_ni56_Msun'] * 39.0 # Mucha más luz
            if 'star_radius' in sim_data: sim_data['star_radius'] = min(sim_data['star_radius'], VIEW_LIMIT * 0.5)
            sim_data['elementos'].extend(ELEMENTOS_NEBULOSA_FONDO)
            return sim_data
        
        sim_data['masa_Msun'] = masa_solar_float
        M_progenitor = masa_solar_float * M_sun
        sim_data['light_curve_desc'] = "No aplica (sin supernova)"
        sim_data['abs_magnitude'] = -17.0 # Default

        if masa_solar_float == 1.4:
            sim_data['tipo_str'] = 'Tipo Ia'; sim_data['elementos'] = ELEMENTOS_TIPO_IA; sim_data['explosion_type'] = 'Ia'
            M_remanente = 0.0 * M_sun; M_ej = M_progenitor - M_remanente; v_ej = np.sqrt(2 * (FOE * 1.3) / M_ej.to(u.kg))
            sim_data['M_ni56_Msun'] = 0.6; sim_data['asymmetry_factor'] = 0.1;
            sim_data['rem_size_base'] = 0.0
            sim_data['final_text'] = "Remanente: NINGUNO (Destrucción Total)"; sim_data['star_color'] = 'white'; sim_data['star_radius'] = 12.0
            sim_data['E_K_erg'] = FOE.value * 1.3; sim_data['light_curve_desc'] = "Curva Luz: Pico rápido (~20d), caída exp (Ni-56)"
            sim_data['abs_magnitude'] = -19.3
        elif masa_solar_float <= 8.0:
            sim_data['tipo_str'] = f'Baja Masa ({masa_solar_float:.1f} M☉)'; sim_data['elementos'] = []; sim_data['explosion_type'] = 'None'
            v_ej = 0.0 * u.km / u.s; M_remanente = 0.0 * M_sun; M_ej = 0.0 * M_sun
            sim_data['M_ni56_Msun'] = 0.0; sim_data['asymmetry_factor'] = 0.0; sim_data['rem_size_base'] = 0.0
            sim_data['final_text'] = "Evoluciona a Neb. Planetaria y Enana Blanca"; sim_data['star_color'] = 'red'; sim_data['star_radius'] = 15.0 + masa_solar_float * 1.0
            sim_data['E_K_erg'] = 0.0
            sim_data['abs_magnitude'] = 5.0
        else:
            sim_data['explosion_type'] = 'CoreCollapse'; sim_data['star_color'] = 'blue'; sim_data['E_K_erg'] = FOE.value
            sim_data['abs_magnitude'] = -17.5
            kick_speed = 0.1; kick_angle = np.random.rand() * 2 * np.pi; sim_data['rem_vx'] = np.cos(kick_angle) * kick_speed; sim_data['rem_vy'] = np.sin(kick_angle) * kick_speed
            if masa_solar_float > 25.0:
                sim_data['tipo_str'] = f'Tipo Ic ({masa_solar_float:.1f} M☉)'; sim_data['elementos'] = ELEMENTOS_TIPO_IC
                M_remanente = 3.0 * M_sun;
                rs_km = SCHWARZSCHILD_RADIUS_KM_PER_MSUN * M_remanente.to(u.M_sun).value
                sim_data['rem_size_base'] = 0.3 * (rs_km / 9.0) # Escala relativa a 3 Msun BH
                sim_data['remnant_info'] = f"Agujero Negro ({M_remanente.to(u.M_sun).value:.1f} M☉)\nRadio Schw: ~{rs_km:.0f} km"
                sim_data['rem_color'] = AGUJERO_NEGRO_COLOR
                sim_data['final_text'] = "Remanente: AGUJERO NEGRO"; sim_data['rem_linewidth'] = 2.0; sim_data['rem_edgecolor'] = 'white'
                sim_data['M_ni56_Msun'] = 0.15; sim_data['asymmetry_factor'] = 0.35; sim_data['light_curve_desc'] = "Curva Luz: Rápida (~15d), sin H/He, caída Ni-56"
            else:
                M_remanente = 1.4 * M_sun;
                sim_data['rem_size_base'] = 0.6 * (NEUTRON_STAR_RADIUS_KM / 15.0) # Escala relativa a 15km NS
                sim_data['remnant_info'] = f"Estrella Neutrones ({M_remanente.to(u.M_sun).value:.1f} M☉)\nRadio: ~{NEUTRON_STAR_RADIUS_KM:.0f} km (Púlsar)"
                sim_data['rem_color'] = 'blue'
                sim_data['final_text'] = "Remanente: ESTRELLA DE NEUTRONES"; sim_data['rem_linewidth'] = 0.0; sim_data['rem_edgecolor'] = 'none'; sim_data['is_pulsar'] = True
                if 8.0 < masa_solar_float <= 20.0:
                    sim_data['tipo_str'] = f'Tipo II-P ({masa_solar_float:.1f} M☉)'; sim_data['elementos'] = ELEMENTOS_TIPO_II; sim_data['M_ni56_Msun'] = 0.07; sim_data['asymmetry_factor'] = 0.2
                    sim_data['light_curve_desc'] = "Curva Luz: Meseta (~100d, recomb H), caída Ni-56"
                else:
                    sim_data['tipo_str'] = f'Tipo Ib ({masa_solar_float:.1f} M☉)'; sim_data['elementos'] = ELEMENTOS_TIPO_IB; sim_data['M_ni56_Msun'] = 0.1; sim_data['asymmetry_factor'] = 0.3
                    sim_data['light_curve_desc'] = "Curva Luz: Rápida (~20d), sin H, caída Ni-56"
            M_ej = M_progenitor - M_remanente; v_ej = np.sqrt(2 * FOE / M_ej.to(u.kg)); sim_data['star_radius'] = 18.0 + (min(masa_solar_float, 50.0) - 8.0) * 0.5
        sim_data['velocidad_kms'] = v_ej.to(u.km / u.s).value; sim_data['M_rem_Msun'] = M_remanente.to(u.M_sun).value; sim_data['M_ej_Msun'] = M_ej.to(u.M_sun).value
        sim_data['L_peak_Lsun'] = L_PEAK_FACTOR * sim_data['M_ni56_Msun'] if sim_data['M_ni56_Msun'] > 0 else 0.0
        if 'star_radius' in sim_data: sim_data['star_radius'] = min(sim_data['star_radius'], VIEW_LIMIT * 0.5)
        if sim_data['explosion_type'] != 'None': sim_data['elementos'].extend(ELEMENTOS_NEBULOSA_FONDO)
        return sim_data

    def _add_info_row(self, layout, label, value_str, sub_text=None):
        row_layout = QHBoxLayout(); label_widget = QLabel(label); label_widget.setObjectName("InfoText")
        value_widget = QLabel(value_str); value_widget.setObjectName("DataLabel"); value_widget.setAlignment(Qt.AlignRight)
        row_layout.addWidget(label_widget); row_layout.addWidget(value_widget); layout.addLayout(row_layout)
        if sub_text:
            sub_label = QLabel(sub_text); sub_label.setObjectName("DataSubLabel"); sub_label.setAlignment(Qt.AlignRight); layout.addWidget(sub_label)

    def generate_color_variations(self, base_color_hex, num_variations, min_brightness=0.7, max_brightness=1.3, hue_offset_range=0.0): # Quitado offset por defecto
        try:
            base_rgb = mcolors.to_rgb(base_color_hex); base_hsv = mcolors.rgb_to_hsv(np.array([base_rgb]))[0]
            h, s, v = base_hsv
            brightness_factors = np.random.normal(loc=1.0, scale=0.15, size=num_variations)
            brightness_factors = np.clip(brightness_factors, min_brightness, max_brightness); new_vs = np.clip(v * brightness_factors, 0, 1)
            # Aplicar offset de hue solo si se especifica
            if hue_offset_range > 0:
                hue_offsets = np.random.uniform(-hue_offset_range, hue_offset_range, num_variations)
                new_hs = (h + hue_offsets) % 1.0 # Usar módulo para envolver hue
            else:
                new_hs = np.full(num_variations, h)

            new_hsvs = np.array([new_hs, np.full(num_variations, s), new_vs]).T # Construcción corregida
            new_rgbs = mcolors.hsv_to_rgb(new_hsvs)
            return np.clip(new_rgbs, 0, 1) # Asegurar que los colores RGB estén en [0, 1]
        except Exception as e: print(f"Error generando variaciones de color para {base_color_hex}: {e}"); return [base_color_hex] * num_variations

    # --- NUEVO: Método para abrir la ventana de gráfica ---
    def show_light_curve_dialog(self):
        if not hasattr(self, 'sim_data') or not self.sim_data:
            return
        dialog = LightCurveDialog(self.sim_data, self)
        dialog.exec_() # Ejecutar modalmente

    def create_simulation_page(self, data):
        global star_exploded; star_exploded = False; self.element_layers = []; self.nebula_layers = []
        widget = QWidget(); widget.setObjectName("SimWidget"); main_layout = QHBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0); info_panel = QWidget()
        info_panel.setObjectName("InfoPanel"); info_panel.setFixedWidth(650); info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(30, 30, 30, 30); info_layout.setAlignment(Qt.AlignTop); title = QLabel("Parámetros Físicos:")
        title.setObjectName("InfoTitle"); info_layout.addWidget(title); explosion_type = data.get('explosion_type', 'CoreCollapse')
        
        if explosion_type != 'None':
            # --- CÁLCULOS CIENTÍFICOS EXTRA ---
            # 1. Energía comparada con la Tierra
            energia_total = data['E_K_erg'] * 1e-7 # Joules
            anios_tierra = energia_total / EARTH_ANNUAL_ENERGY_JOULES
            
            # 2. Magnitud Aparente (Módulo de distancia a Betelgeuse)
            # m - M = 5 * log10(d) - 5
            mag_abs = data.get('abs_magnitude', -17)
            mag_aparente = mag_abs + 5 * np.log10(REF_DISTANCE_PC) - 5
            
            self._add_info_row(info_layout, "Energía Cinética (E_K):", f"{data['E_K_erg']:.1e} erg")
            self._add_info_row(info_layout, "Equiv. Energía Humana:", f"~{anios_tierra:.1e} años", "Consumo actual anual Tierra")
            self._add_info_row(info_layout, "Mag. Aparente (Betelgeuse):", f"m = {mag_aparente:.1f}", f"Visible de día si m < -4")

            if data['L_peak_Lsun'] > 0: self._add_info_row(info_layout, "Luminosidad Pico (L_pico):", f"{data['L_peak_Lsun']:.2e} L☉")
            self._add_info_row(info_layout, "Velocidad Eyección (v_ej):", f"~{data['velocidad_kms']:,.0f} km/s")
            self._add_info_row(info_layout, "Masa Remanente (M_rem):", f"{data['M_rem_Msun']:.1f} M☉")
            self._add_info_row(info_layout, "Masa Eyectada (M_ej):", f"{data['M_ej_Msun']:.1f} M☉")
            
            if 'remnant_info' in data and data['rem_size_base'] > 0:
                rem_info_label = QLabel(data['remnant_info'])
                rem_info_label.setObjectName("DataSubLabel") 
                rem_info_label.setAlignment(Qt.AlignRight)
                rem_info_label.setStyleSheet("padding-top: 5px;")
                info_layout.addWidget(rem_info_label)
                
            sep_lc = QFrame(); sep_lc.setFrameShape(QFrame.HLine); sep_lc.setFrameShadow(QFrame.Sunken); sep_lc.setStyleSheet("margin-top: 15px; margin-bottom: 5px;"); info_layout.addWidget(sep_lc)
            
            # --- NUEVO: Botón para Gráfica ---
            btn_graph = QPushButton("📈 Ver Gráfica de Curva de Luz")
            btn_graph.setObjectName("GraphButton")
            btn_graph.clicked.connect(self.show_light_curve_dialog)
            info_layout.addWidget(btn_graph)
            
            lc_label = QLabel(data.get('light_curve_desc', '')); lc_label.setObjectName("LightCurveDesc"); lc_label.setWordWrap(True); info_layout.addWidget(lc_label)
        else: no_sn_label = QLabel("La estrella no evoluciona como supernova."); no_sn_label.setObjectName("InfoText"); info_layout.addWidget(no_sn_label)
        comp_title = QLabel("Composición de Eyección:"); comp_title.setObjectName("InfoTitle"); comp_title.setStyleSheet("padding-top: 30px;"); info_layout.addWidget(comp_title)
        
        if data.get('descripcion'):
            desc_label = QLabel(data['descripcion'])
            desc_label.setObjectName("DataSubLabel") 
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("padding-bottom: 15px; font-style: italic;") 
            info_layout.addWidget(desc_label)

        if data['elementos']:
            elementos_leyenda = [e for e in data['elementos'] if e['zona'] != 'fondo']
            if not elementos_leyenda: elem_label = QLabel("Ninguno"); elem_label.setObjectName("InfoText"); info_layout.addWidget(elem_label)
            
            masa_total_ej_msun = data.get('M_ej_Msun', 0.0)
            
            for elemento in elementos_leyenda:
                # --- CALCULO DE MASA EN KG ---
                fraccion = elemento.get('mass_fraction', 0.0)
                masa_elem_msun = masa_total_ej_msun * fraccion
                masa_elem_kg = masa_elem_msun * M_SOLAR_VAL_KG
                
                elem_layout = QHBoxLayout(); color_box = QFrame(); color_box.setFixedSize(35, 35); color_box.setStyleSheet(f"background-color: {elemento['color']}; border: 1px solid #555;")
                
                # Texto extendido con kg
                txt_nombre = f"{elemento['nombre']}"
                if masa_elem_kg > 0:
                    txt_masa = f"({masa_elem_kg:.2e} kg)"
                else:
                    txt_masa = ""
                
                txt_completo = f"{txt_nombre}\n{txt_masa}"
                
                elem_label = QLabel(txt_completo); elem_label.setObjectName("InfoText"); elem_label.setStyleSheet("font-size: 16px;")
                elem_layout.addWidget(color_box); elem_layout.addWidget(elem_label); elem_layout.addStretch(); info_layout.addLayout(elem_layout)
        
        info_layout.addStretch() 
        
        cred_escuela = QLabel(CREDITO_ESCUELA); cred_escuela.setObjectName("CreditsLabel"); info_layout.addWidget(cred_escuela)
        cred_prog1 = QLabel(CREDITO_PROGRAMA_L1); cred_prog1.setObjectName("DataSubLabel"); info_layout.addWidget(cred_prog1)
        cred_prog2 = QLabel(CREDITO_PROGRAMA_L2); cred_prog2.setObjectName("DataSubLabel"); info_layout.addWidget(cred_prog2)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False) 
        info_layout.addWidget(self.progress_bar)

        main_layout.addWidget(info_panel)
        sim_area_widget = QWidget(); sim_layout = QVBoxLayout(sim_area_widget); sim_layout.setContentsMargins(10, 10, 10, 10); sim_layout.setSpacing(10)
        self.canvas = MplCanvas(self, width=10, height=10, dpi=100); sim_layout.addWidget(self.canvas); button_layout = QHBoxLayout()
        back_button = QPushButton("Volver al Menú Principal"); back_button.setObjectName("ReturnButton"); back_button.clicked.connect(self.return_to_menu)
        button_layout.addWidget(back_button); button_layout.addStretch(); sim_layout.addLayout(button_layout); main_layout.addWidget(sim_area_widget)
        self.prepare_animation_elements(data); return widget

    def prepare_animation_elements(self, data):
        ax = self.canvas.ax; ax.cla(); ax.set_facecolor(FONDO_SIM_COLOR)
        ax.set_xlim(-VIEW_LIMIT, VIEW_LIMIT); ax.set_ylim(-VIEW_LIMIT, VIEW_LIMIT); ax.set_xticks([]); ax.set_yticks([])

        self.star_x = (np.random.rand(NUM_ESTRELLAS_FONDO) - 0.5) * VIEW_LIMIT * 2; self.star_y = (np.random.rand(NUM_ESTRELLAS_FONDO) - 0.5) * VIEW_LIMIT * 2
        self.star_sizes = np.random.rand(NUM_ESTRELLAS_FONDO) * 2 + 0.5
        base_star_colors = ['#FFFFFF', '#ADD8E6', '#FFD700', '#FFB6C1']
        self.star_colors_rgb = np.array([mcolors.to_rgb(c) for c in np.random.choice(base_star_colors, NUM_ESTRELLAS_FONDO)])
        self.background_stars = ax.scatter(self.star_x, self.star_y, s=self.star_sizes, color=self.star_colors_rgb, alpha=0.3, zorder=-10)

        star_radius = data['star_radius']; star_color = data.get('star_color', 'yellow'); masa_solar = data['masa_Msun']
        rem_color = data.get('rem_color', 'none'); rem_size_base = data.get('rem_size_base', 0.0)
        rem_linewidth = data.get('rem_linewidth', 0.0); rem_edgecolor = data.get('rem_edgecolor', 'none')
        title_text = f"Simulación: {data.get('tipo_str', f'{masa_solar:.1f} M☉')}"
        self.title_text_artist = ax.text(0, VIEW_LIMIT - 6, title_text, color='white', ha='center', fontsize=28, fontweight='bold', zorder=110)
        self.status_label = ax.text(0, VIEW_LIMIT - 12.0, "", color=COLOR_AMARILLO, ha='center', fontsize=26, fontweight='bold', zorder=110)
        self.countdown_text = ax.text(0, 0, "", color='white', ha='center', va='center', fontsize=50, fontweight='bold', visible=False, zorder=110)
        self.scale_time_text = ax.text(-VIEW_LIMIT + 2, -VIEW_LIMIT + 4, "", color=COLOR_TEXTO_SEC, ha='left', va='bottom', fontsize=14, zorder=110)
        self.circ_star = Circle((0, 0), star_radius, color=star_color, fill=True, alpha=0.9, visible=False, zorder=20); ax.add_patch(self.circ_star)
        mass_fontsize = 22 if star_radius > 12 else 18
        
        # Texto especial para la estrella Miku
        if data.get('tipo_str', '').startswith('Tipo SN-39'):
            star_label_text = f"{masa_solar:.0f} MIKU" # Mostrar 39 MIKU
            mass_fontsize = 20
        else:
            star_label_text = rf"{masa_solar:.1f} M☉"
        self.star_label = ax.text(0, 0, star_label_text, color='black', ha='center', va='center', fontsize=mass_fontsize, visible=False, zorder=21)

        self.remnant_circ = Circle((0, 0), 0, facecolor=rem_color, fill=True, visible=False, linewidth=rem_linewidth, edgecolor=rem_edgecolor, alpha=1.0, zorder=10); ax.add_patch(self.remnant_circ)
        self.shockwave_front = Circle((0, 0), 0, edgecolor='white', facecolor='none', linewidth=4, alpha=0.0, visible=False, zorder=15); ax.add_patch(self.shockwave_front)
        self.flash_overlay = Rectangle((-VIEW_LIMIT, -VIEW_LIMIT), VIEW_LIMIT*2, VIEW_LIMIT*2, facecolor='white', alpha=0.0, visible=False, zorder=100); ax.add_patch(self.flash_overlay)

        # Campo Magnético
        self.mag_field_lines = []
        if data.get('is_pulsar', False):
            # Dos arcos simples para representar las líneas de campo
            line1 = Arc((0,0), 1, 1, angle=0, theta1=0, theta2=180, color=COLOR_ACENTO_PRI, linewidth=1.5, alpha=0.0, zorder=9)
            line2 = Arc((0,0), 1, 1, angle=0, theta1=180, theta2=360, color=COLOR_ACENTO_PRI, linewidth=1.5, alpha=0.0, zorder=9)
            ax.add_patch(line1)
            ax.add_patch(line2)
            self.mag_field_lines.extend([line1, line2])

        self.particle_angles = {}; self.particle_base_radii = {}
        self.element_layers = []; self.nebula_layers = []
        # Almacenar colores originales para el efecto Doppler
        self.original_particle_colors = {}
        for elemento in data['elementos']:
            nombre = elemento['nombre']; cantidad = elemento['cantidad']; zona = elemento['zona']
            base_color = elemento['color']
            color_array = self.generate_color_variations(base_color, cantidad)
            self.original_particle_colors[nombre] = color_array.copy() # Guardar copia

            self.particle_angles[nombre] = np.random.rand(cantidad) * 2 * np.pi; self.particle_base_radii[nombre] = np.random.rand(cantidad)**0.5
            x_placeholder = np.zeros(cantidad); y_placeholder = np.zeros(cantidad)
            if zona == 'fondo':
                layer = ax.scatter(x_placeholder, y_placeholder, s=elemento['tamaño'], color=color_array, alpha=0.0, visible=False, zorder=5)
                self.nebula_layers.append({'scatter_obj': layer, 'zona': zona, 'nombre': nombre, 'original_tamaño': elemento['tamaño']})
            else:
                layer = ax.scatter(x_placeholder, y_placeholder, s=elemento['tamaño'], color=color_array, alpha=0.0, visible=False, zorder=25)
                self.element_layers.append({'scatter_obj': layer, 'zona': zona, 'nombre': nombre, 'original_tamaño': elemento['tamaño']})
        self.visual_peak_frame = INITIAL_WAIT_FRAMES + (NUM_EXPANSION_FRAMES * 0.25)
        self.visual_end_frame = INITIAL_WAIT_FRAMES + NUM_EXPANSION_FRAMES + NUM_FADE_FRAMES
        self.total_sim_frames = INITIAL_WAIT_FRAMES + NUM_EXPANSION_FRAMES + NUM_FADE_FRAMES + FINAL_FADE_FRAMES # Para barra de progreso

    def start_simulation_animation(self):
        data = self.sim_data; explosion_type = data.get('explosion_type', 'CoreCollapse')
        total_frames = self.total_sim_frames
        if explosion_type == 'None': total_frames = INITIAL_WAIT_FRAMES + 20
        try:
            self.sim_ani = FuncAnimation(self.canvas.fig, self.animate_frame, frames=total_frames, interval=ANIMATION_INTERVAL, blit=True, repeat=False)
            self.canvas.draw()
            print("DEBUG: Iniciando animación de simulación.")
        except Exception as e:
            QMessageBox.critical(self, "Error de Animación", f"No se pudo iniciar la animación: {e}")
            print(f"Error al crear FuncAnimation: {e}"); import traceback; traceback.print_exc()

    def stop_simulation_animation(self):
        if self.sim_ani and hasattr(self.sim_ani, 'event_source') and self.sim_ani.event_source is not None:
            try: self.sim_ani.event_source.stop(); print("DEBUG: Deteniendo animación de simulación.")
            except Exception as e: print(f"Error al detener animación de simulación: {e}")
            self.sim_ani = None
        plt.close(self.canvas.fig) 

    def animate_frame(self, i):
        data = self.sim_data
        artists = ([layer['scatter_obj'] for layer in self.element_layers] +
                   [layer['scatter_obj'] for layer in self.nebula_layers] +
                   self.mag_field_lines) # Añadir líneas de campo
        artists.extend([self.status_label, self.circ_star, self.star_label, self.remnant_circ, self.countdown_text,
                        self.shockwave_front, self.title_text_artist, self.flash_overlay, self.scale_time_text,
                        self.background_stars])

        try:
            global star_exploded
            explosion_type = data.get('explosion_type', 'CoreCollapse'); final_text = data.get('final_text', 'Simulación Finalizada')
            rem_size_base = data.get('rem_size_base', 0.0); rem_size_scale_factor = 2.8 * 2.0 # Factor visual
            rem_size = rem_size_base * rem_size_scale_factor
            velocidad_kms = data.get('velocidad_kms', 0.0); asymmetry_factor = data.get('asymmetry_factor', 0.0)
            star_radius = data.get('star_radius', 10.0)

            # --- Barra de Progreso ---
            progress_percent = int(100 * i / float(self.total_sim_frames if explosion_type != 'None' else INITIAL_WAIT_FRAMES + 20))
            if hasattr(self, 'progress_bar'): self.progress_bar.setValue(progress_percent)

            # --- Parpadeo estrellas de fondo ---
            current_star_alphas = np.clip(np.random.normal(0.3, 0.1, NUM_ESTRELLAS_FONDO), 0.1, 0.6)
            self.background_stars.set_alpha(current_star_alphas)

            # --- Texto Escala/Tiempo ---
            current_radius_for_scale = 0.0; time_str = ""; scale_str = ""
            if i >= INITIAL_WAIT_FRAMES and explosion_type != 'None':
                frames_since_explosion = i - INITIAL_WAIT_FRAMES; total_main_phase_frames = NUM_EXPANSION_FRAMES + NUM_FADE_FRAMES
                if frames_since_explosion <= total_main_phase_frames:
                    time_progress = frames_since_explosion / float(total_main_phase_frames); days_elapsed = int(time_progress * 365)
                    if days_elapsed < 30: time_str = f"Tiempo: ~{days_elapsed} Días"
                    elif days_elapsed < 365: time_str = f"Tiempo: ~{days_elapsed // 30} Meses"
                    else: time_str = f"Tiempo: ~1 Año"
                    if frames_since_explosion < NUM_EXPANSION_FRAMES:
                        expansion_factor = (frames_since_explosion / NUM_EXPANSION_FRAMES) ** 0.8
                        current_radius_for_scale = expansion_factor * MAX_RADIUS
                    else:
                        frame_in_fade = frames_since_explosion - NUM_EXPANSION_FRAMES; fade_progress = frame_in_fade / float(NUM_FADE_FRAMES)
                        current_radius_for_scale = MAX_RADIUS + (fade_progress * (MAX_RADIUS * 0.4))
                    scale_ly = (current_radius_for_scale / MAX_RADIUS) * 1.0; scale_str = f"Radio: ~{scale_ly:.2f} Años Luz"
                else: time_str = "Tiempo: >1 Año"; scale_str = "Radio: >1 Año Luz"
                self.scale_time_text.set_text(f"{time_str}\n{scale_str}"); self.scale_time_text.set_visible(True)
            else: self.scale_time_text.set_visible(False)

            # --- FASE 0: ESPERA ---
            if i < INITIAL_WAIT_FRAMES:
                frames_into_wait = i
                if frames_into_wait < COUNTDOWN_FRAMES:
                    seconds_left = math.ceil((COUNTDOWN_FRAMES - frames_into_wait) / FRAMES_PER_SECOND)
                    if seconds_left > 0: self.countdown_text.set_text(f"Iniciando en {seconds_left}..."); self.countdown_text.set_visible(True); self.circ_star.set_visible(False); self.star_label.set_visible(False)
                    else: self.countdown_text.set_visible(False); self.circ_star.set_visible(True); self.star_label.set_visible(True); self.status_label.set_text("FASE DE COLAPSO INMINENTE..." if explosion_type != 'None' else "Observando estrella...")
                else: self.countdown_text.set_visible(False); self.circ_star.set_visible(True); self.star_label.set_visible(True); self.status_label.set_text("FASE DE COLAPSO INMINENTE..." if explosion_type != 'None' else "Observando estrella...")
                return artists

            # --- Lógica para estrellas que NO explotan ---
            if explosion_type == 'None':
                if i == INITIAL_WAIT_FRAMES:
                    self.status_label.set_text(final_text)
                    self.status_label.set_y(-VIEW_LIMIT + 8.0) # Posición más baja
                self.circ_star.set_visible(True); self.star_label.set_visible(True); self.countdown_text.set_visible(False); self.shockwave_front.set_visible(False)
                for layer_info in self.element_layers: layer_info['scatter_obj'].set_visible(False)
                for layer_info in self.nebula_layers: layer_info['scatter_obj'].set_visible(False)
                self.remnant_circ.set_visible(False); return artists
            elif i == INITIAL_WAIT_FRAMES:
                 self.status_label.set_y(VIEW_LIMIT - 12.0) # Posición más alta

            # --- CÁLCULO DE BRLLO VISUAL ---
            current_visual_alpha = calculate_visual_brightness(i, INITIAL_WAIT_FRAMES, self.visual_peak_frame, self.visual_end_frame)

            # --- Inicio de Explosión ---
            if i == INITIAL_WAIT_FRAMES:
                self.countdown_text.set_visible(False); self.circ_star.set_visible(True); self.star_label.set_visible(True)
                self.shockwave_front.set_visible(True); self.shockwave_front.set_radius(0.1); self.shockwave_front.set_edgecolor('white'); self.shockwave_front.set_linewidth(15); self.shockwave_front.set_alpha(0.9)
                self.flash_overlay.set_visible(True); self.flash_overlay.set_alpha(1.0)
                for layer_info in self.element_layers: layer_info['scatter_obj'].set_visible(True)
                for layer_info in self.nebula_layers: layer_info['scatter_obj'].set_visible(True)
                if rem_size > 0:
                    self.remnant_circ.set_visible(True)
                    pulsar_factor = 1.0 + 0.2 * math.sin(i * 0.8) if data.get('is_pulsar', False) else 1.0
                    self.remnant_circ.set_radius(rem_size * pulsar_factor)
                    self.remnant_circ.set_center(self.remnant_current_pos)
                self.status_label.set_text("¡EXPLOSIÓN! (Onda de Choque en Expansión)"); star_exploded = False

            # --- FASE 1: EXPANSIÓN PRINCIPAL ---
            if INITIAL_WAIT_FRAMES <= i < (INITIAL_WAIT_FRAMES + NUM_EXPANSION_FRAMES):
                frames_since_explosion_start = i - INITIAL_WAIT_FRAMES
                expansion_progress_raw = frames_since_explosion_start / NUM_EXPANSION_FRAMES
                expansion_progress = expansion_progress_raw ** 0.8 # Desaceleración
                current_radius_expansion = expansion_progress * MAX_RADIUS
                if frames_since_explosion_start < FLASH_DURATION_FRAMES: flash_progress = frames_since_explosion_start / FLASH_DURATION_FRAMES; self.flash_overlay.set_alpha(1.0 - flash_progress**2)
                else: self.flash_overlay.set_visible(False)
                self.shockwave_front.set_radius(current_radius_expansion)
                if frames_since_explosion_start < 10:
                    flash_progress = frames_since_explosion_start / 10.0; alpha_val = np.clip(current_visual_alpha * 1.5, 0, 1.0)
                    r_col_flash, g_col_flash, b_col_flash = 1.0, 1.0, 1.0; color_progress_wave = min(1.0, expansion_progress * 2.0)
                    r_col_wave = 1.0; g_col_wave = 1.0 - (0.8 * color_progress_wave); b_col_wave = 1.0 - (1.0 * color_progress_wave)
                    r_col = r_col_flash * (1.0 - flash_progress) + r_col_wave * flash_progress; g_col = g_col_flash * (1.0 - flash_progress) + g_col_wave * flash_progress; b_col = b_col_flash * (1.0 - flash_progress) + b_col_wave * flash_progress
                    final_linewidth = 4.0 * (1.0 - expansion_progress) + 1.0; linewidth = 15 * (1.0 - flash_progress) + final_linewidth * flash_progress
                    self.shockwave_front.set_edgecolor((r_col, g_col, b_col)); self.shockwave_front.set_linewidth(linewidth); self.shockwave_front.set_alpha(0.9 * (1.0 - flash_progress) + alpha_val * flash_progress)
                else:
                    alpha_val = np.clip(current_visual_alpha * 1.5, 0, 1.0); self.shockwave_front.set_alpha(alpha_val)
                    color_progress = min(1.0, expansion_progress * 2.0); r_col = 1.0; g_col = 1.0 - (0.8 * color_progress); b_col = 1.0 - (1.0 * color_progress)
                    self.shockwave_front.set_edgecolor((r_col, g_col, b_col)); self.shockwave_front.set_linewidth(4.0 * (1.0 - expansion_progress) + 1.0)

                # Procesar capas (Elementos y Nebulosa)
                all_layers = self.element_layers + self.nebula_layers
                for layer_info in all_layers:
                    nombre = layer_info['nombre']; zona = layer_info['zona']; theta = self.particle_angles[nombre]; base_r = self.particle_base_radii[nombre]
                    is_nebula = (zona == 'fondo')
                    
                    velocity_scale = 0.2 if is_nebula else max(0.6, velocidad_kms / 15000.0)
                    effective_radius = current_radius_expansion * velocity_scale
                    
                    jet_factor = 1.0
                    if not is_nebula and explosion_type == 'CoreCollapse':
                        if np.any(np.abs(np.cos(theta)) > 0.8): jet_factor = 1.5
                        
                    if zona == 'exterior': r = (base_r * effective_radius * 0.8 + effective_radius * 0.2) * jet_factor
                    elif zona == 'media': r = (base_r * effective_radius * 0.6) * jet_factor
                    elif zona == 'nucleo': r = (base_r * effective_radius * 0.4) * jet_factor
                    elif zona == 'fondo': r = (base_r * effective_radius * 0.8 + effective_radius * 0.2) # Nebulosa sin jets
                    
                    r = np.maximum(r, base_r * current_radius_expansion * (0.05 if is_nebula else 0.1) )
                    
                    if not is_nebula and frames_since_explosion_start < INITIAL_WAVE_FRAMES:
                        asymmetry_x = 1.0 + asymmetry_factor * np.sin(theta * 2 + np.random.rand() * np.pi) * (1 - frames_since_explosion_start / INITIAL_WAVE_FRAMES)
                        asymmetry_y = 1.0 + asymmetry_factor * np.cos(theta * 3 + np.random.rand() * np.pi) * (1 - frames_since_explosion_start / INITIAL_WAVE_FRAMES)
                    elif not is_nebula:
                        asymmetry_x = 1.0 + asymmetry_factor * np.sin(theta * 2) * 0.5; asymmetry_y = 1.0 + asymmetry_factor * np.cos(theta * 3) * 0.5
                    else: # Nebulosa es simétrica
                        asymmetry_x = 1.0; asymmetry_y = 1.0
                        
                    x = r * np.cos(theta) * asymmetry_x; y = r * np.sin(theta) * asymmetry_y
                    layer_info['scatter_obj'].set_offsets(np.c_[x, y])
                    layer_alpha = 0.4 * current_visual_alpha if is_nebula else current_visual_alpha
                    layer_info['scatter_obj'].set_alpha(layer_alpha)

                    if not is_nebula and layer_alpha > 0.1 and jet_factor > 1.0: # Aplicar solo a jets visibles
                        radial_velocity_factor = np.cos(theta) * asymmetry_x
                        hue_shift = np.clip(radial_velocity_factor * -0.05, -0.05, 0.05) # Azul si se acerca (-x), Rojo si se aleja (+x)
                        original_colors_rgb = self.original_particle_colors[nombre]
                        original_colors_hsv = mcolors.rgb_to_hsv(original_colors_rgb)
                        shifted_hues = (original_colors_hsv[:, 0] + hue_shift) % 1.0
                        shifted_colors_hsv = original_colors_hsv.copy()
                        shifted_colors_hsv[:, 0] = shifted_hues
                        shifted_colors_rgb = mcolors.hsv_to_rgb(shifted_colors_hsv)
                        layer_info['scatter_obj'].set_color(np.clip(shifted_colors_rgb, 0, 1))
                    elif not is_nebula: # Resetear color si no aplica Doppler
                        layer_info['scatter_obj'].set_color(self.original_particle_colors[nombre])

                if not star_exploded:
                    star_alpha_progress = expansion_progress * 5.0
                    if star_alpha_progress >= 1.0: self.circ_star.set_visible(False); self.star_label.set_visible(False); star_exploded = True
                    else: self.circ_star.set_alpha(0.9 * (1.0 - star_alpha_progress))

            # --- FASE 2: DESVANECIMIENTO ---
            elif i < (INITIAL_WAIT_FRAMES + NUM_EXPANSION_FRAMES + NUM_FADE_FRAMES):
                self.status_label.set_text("Remanente de Supernova enfriándose...")
                frame_in_fade = i - (INITIAL_WAIT_FRAMES + NUM_EXPANSION_FRAMES); fade_progress = frame_in_fade / NUM_FADE_FRAMES
                # La expansión continúa desacelerándose ligeramente
                continued_radius = MAX_RADIUS + (fade_progress * (MAX_RADIUS * 0.4)) * (1.0 - fade_progress * 0.2)
                self.shockwave_front.set_visible(False); self.flash_overlay.set_visible(False)
                
                all_layers = self.element_layers + self.nebula_layers
                for layer_info in all_layers:
                    nombre = layer_info['nombre']; zona = layer_info['zona']; theta = self.particle_angles[nombre]; base_r = self.particle_base_radii[nombre]
                    is_nebula = (zona == 'fondo')

                    velocity_scale = 0.2 if is_nebula else max(0.6, velocidad_kms / 15000.0)
                    effective_radius_fade = continued_radius * velocity_scale
                    jet_factor = 1.0
                    if not is_nebula and explosion_type == 'CoreCollapse':
                        if np.any(np.abs(np.cos(theta)) > 0.8): jet_factor = 1.5
                    
                    if zona == 'exterior': r = (base_r * effective_radius_fade * 0.8 + effective_radius_fade * 0.2) * jet_factor
                    elif zona == 'media': r = (base_r * effective_radius_fade * 0.6) * jet_factor
                    elif zona == 'nucleo': r = (base_r * effective_radius_fade * 0.4) * jet_factor
                    elif zona == 'fondo': r = (base_r * effective_radius_fade * 0.8 + effective_radius_fade * 0.2)

                    asymmetry_x = 1.0 if is_nebula else 1.0 + asymmetry_factor * np.sin(theta * 2) * 0.5
                    asymmetry_y = 1.0 if is_nebula else 1.0 + asymmetry_factor * np.cos(theta * 3) * 0.5
                    x = r * np.cos(theta) * asymmetry_x; y = r * np.sin(theta) * asymmetry_y
                    layer_info['scatter_obj'].set_offsets(np.c_[x, y])
                    
                    original_size = layer_info['original_tamaño']
                    diffuse_size = original_size * (1.0 + fade_progress * (0.8 if is_nebula else 1.5)) # Nebulosa se expande menos
                    diffuse_alpha = (0.4 if is_nebula else 0.4) * current_visual_alpha # Ambas se desvanecen similarmente
                    
                    layer_info['scatter_obj'].set_sizes([diffuse_size])
                    layer_info['scatter_obj'].set_alpha(diffuse_alpha)
                    # Resetear color Doppler
                    if not is_nebula: layer_info['scatter_obj'].set_color(self.original_particle_colors[nombre])

            # --- FASE 3: ESTADO FINAL ---
            else:
                for layer_info in self.element_layers: layer_info['scatter_obj'].set_visible(False)
                self.shockwave_front.set_visible(False); self.flash_overlay.set_visible(False)
                for layer_info in self.nebula_layers: layer_info['scatter_obj'].set_visible(False)
                self.status_label.set_text(final_text)

            # --- LÓGICA DE REMANENTE (Pulsar, Kick, Campo Magnético) ---
            if rem_size_base > 0 and i >= INITIAL_WAIT_FRAMES:
                self.remnant_circ.set_visible(True)
                self.remnant_current_pos[0] += data.get('rem_vx', 0.0)
                self.remnant_current_pos[1] += data.get('rem_vy', 0.0)
                self.remnant_circ.set_center(self.remnant_current_pos)
                
                pulsar_brightness_factor = 1.0
                if data.get('is_pulsar', False):
                    # Factor de tamaño y brillo
                    pulse_angle = i * 0.8 # Velocidad del pulso
                    pulsar_size_factor = 1.0 + 0.2 * math.sin(pulse_angle)
                    pulsar_brightness_factor = 1.0 + 0.4 * math.sin(pulse_angle + np.pi/2) # Desfasado para que brille cuando es grande
                    self.remnant_circ.set_radius(rem_size * pulsar_size_factor)
                    # Ajustar brillo (alpha)
                    self.remnant_circ.set_alpha(min(1.0, 0.8 * pulsar_brightness_factor))
                    
                    # --- Lógica Campo Magnético ---
                    if self.mag_field_lines:
                        # Rotar campo lentamente
                        rotation_angle = (i * 0.5) % 360 # Grados
                        # Escalar campo con tamaño del púlsar y posición
                        field_scale = rem_size * pulsar_size_factor * 1.5 # Un poco más grande que el púlsar
                        center_x, center_y = self.remnant_current_pos
                        for idx, line in enumerate(self.mag_field_lines):
                            line.set_center((center_x, center_y))
                            line.set_width(field_scale * 2) # width es diámetro
                            line.set_height(field_scale * 2 * 0.6) # Elipsoidal
                            line.angle = rotation_angle # Rotar
                            line.set_alpha(0.5 * pulsar_brightness_factor if pulsar_brightness_factor > 0.8 else 0.0) # Visible solo en el pico del pulso
                            line.set_visible(True)

                elif i == INITIAL_WAIT_FRAMES: # Fijar tamaño si no es pulsar
                    self.remnant_circ.set_radius(rem_size)
                    self.remnant_circ.set_alpha(1.0)
            
            elif i >= INITIAL_WAIT_FRAMES: # Si no hay remanente
                self.remnant_circ.set_visible(False)
                for line in self.mag_field_lines: line.set_visible(False) # Ocultar campo magnético

            return artists

        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"); print(f"ERROR DURANTE LA ANIMACIÓN (frame {i}): {e}"); print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            import traceback; traceback.print_exc()
            if self.sim_ani: self.sim_ani.event_source.stop() # Usar sim_ani
            # También detener fondo de menú si está activo (por si acaso)
            self.stop_menu_background_animation()
            return artists

    def stop_simulation_animation(self):
        if self.sim_ani and hasattr(self.sim_ani, 'event_source') and self.sim_ani.event_source is not None:
            try: self.sim_ani.event_source.stop(); print("DEBUG: Deteniendo animación de simulación.")
            except Exception as e: print(f"Error al detener animación de simulación: {e}")
            self.sim_ani = None
        # Cerrar figura específica de la simulación para liberar memoria
        if hasattr(self, 'canvas') and self.canvas and self.canvas.fig:
             plt.close(self.canvas.fig)

    def return_to_menu(self):
        self.stacked_widget.setCurrentIndex(0) # Esto activará handle_page_change

    def closeEvent(self, event):
        self.stop_simulation_animation()
        self.stop_menu_background_animation()
        event.accept()

# --- Iniciar el Programa ---
if __name__ == "__main__":
    app = QApplication(sys.argv); main_window = SupernovaSimulatorApp(); sys.exit(app.exec_())
