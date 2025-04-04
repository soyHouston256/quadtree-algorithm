# -*- coding: utf-8 -*-

import pygame
import random
import sys
import math
from datetime import datetime

# --- Clases Point, Rectangle (sin cambios, pero Point necesita hash/eq) ---
class Point:
    def __init__(self, x, y, data=None): self.x=x; self.y=y; self.data=data; self.timestamp=datetime.now()
    def __repr__(self): return f"({self.x:.1f}, {self.y:.1f})"
    def __hash__(self): return hash((self.x, self.y)) # Necesario para keys/sets
    def __eq__(self, other):
        if not isinstance(other, Point): return NotImplemented
        return self.x == other.x and self.y == other.y

class Rectangle:
    def __init__(self, x, y, w, h): self.x=x; self.y=y; self.w=w; self.h=h; self.cx=x+w/2; self.cy=y+h/2
    def contains(self, point): return (self.x <= point.x < self.x + self.w and self.y <= point.y < self.y + self.h)
    def intersects(self, range_rect): return not (range_rect.x >= self.x + self.w or range_rect.x + range_rect.w <= self.x or range_rect.y >= self.y + self.h or range_rect.y + range_rect.h <= self.y)
    def get_pygame_rect(self): return pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))
    def __repr__(self): return f"Rect[({self.x:.0f},{self.y:.0f}) W:{self.w:.0f} H:{self.h:.0f}]"

# --- Clase QuadTreeNode ---
class QuadTreeNode:
    def __init__(self, boundary, capacity, depth=0): # Añadir profundidad inicial
        self.boundary = boundary; self.capacity = capacity
        self.points = []; self.divided = False
        self.northwest = None; self.northeast = None
        self.southwest = None; self.southeast = None
        self._id = id(self)
        self.depth_level = depth # <<< Almacenar profundidad

    def __hash__(self): return self._id
    def __eq__(self, other):
        if not isinstance(other, QuadTreeNode): return NotImplemented
        return self._id == other._id

    def subdivide(self):
        next_depth = self.depth_level + 1 # Profundidad para hijos
        x, y, w, h = self.boundary.x, self.boundary.y, self.boundary.w / 2, self.boundary.h / 2
        nw_rect = Rectangle(x, y, w, h); ne_rect = Rectangle(x + w, y, w, h)
        sw_rect = Rectangle(x, y + h, w, h); se_rect = Rectangle(x + w, y + h, w, h)
        # Pasar la profundidad correcta a los hijos
        self.northwest = QuadTreeNode(nw_rect, self.capacity, next_depth); self.northeast = QuadTreeNode(ne_rect, self.capacity, next_depth)
        self.southwest = QuadTreeNode(sw_rect, self.capacity, next_depth); self.southeast = QuadTreeNode(se_rect, self.capacity, next_depth)
        self.divided = True
        for point in self.points: self._insert_into_children(point)
        self.points = []

    def _insert_into_children(self, point):
        # (Sin cambios)
        if self.northwest.insert(point): return True
        if self.northeast.insert(point): return True
        if self.southwest.insert(point): return True
        if self.southeast.insert(point): return True
        return False

    def insert(self, point):
        # (Sin cambios)
        if not self.boundary.contains(point): return False
        if len(self.points) < self.capacity and not self.divided:
            self.points.append(point); return True
        else:
            if not self.divided: self.subdivide()
            return self._insert_into_children(point)

    # --- MODIFICADO: query ---
    def query(self, range_rect, found_info=None, visited_nodes=None): # Añadir visited_nodes
        """Busca puntos y nodos hoja, y registra nodos visitados."""
        if found_info is None: found_info = {}
        if visited_nodes is None: visited_nodes = set() # Usar set para evitar duplicados

        # 1. Optimización y Registro de Visita
        if not self.boundary.intersects(range_rect):
            return found_info # No intersecta, no visitar

        visited_nodes.add(self) # <<< REGISTRAR NODO VISITADO

        # 2. Si es hoja, comprobar puntos
        if not self.divided:
            for point in self.points:
                if range_rect.contains(point):
                    if point not in found_info: found_info[point] = self
        # 3. Si está dividido, recurrir
        else:
            self.northwest.query(range_rect, found_info, visited_nodes)
            self.northeast.query(range_rect, found_info, visited_nodes)
            self.southwest.query(range_rect, found_info, visited_nodes)
            self.southeast.query(range_rect, found_info, visited_nodes)

        return found_info # El set visited_nodes se modifica por referencia

    # --- MODIFICADO: find_point ---
    def find_point(self, target_point, path_nodes=None): # Añadir path_nodes
        """
        Busca punto exacto y registra el camino.
        Retorna (Point, Node) o (None, None). Modifica path_nodes.
        """
        if path_nodes is None: path_nodes = [] # Debe ser creado por el llamador inicial

        # Añadir nodo actual al camino
        path_nodes.append(self) # <<< REGISTRAR NODO EN CAMINO

        if not self.boundary.contains(target_point):
            # Aunque no lo contenga, lo añadimos al path para ver la ruta de búsqueda fallida
            return None, None

        if not self.divided:
            for p in self.points:
                if p.x == target_point.x and p.y == target_point.y:
                    return p, self # Encontrado
            return None, None # No encontrado en esta hoja

        # Descender recursivamente
        if self.northwest.boundary.contains(target_point): return self.northwest.find_point(target_point, path_nodes)
        elif self.northeast.boundary.contains(target_point): return self.northeast.find_point(target_point, path_nodes)
        elif self.southwest.boundary.contains(target_point): return self.southwest.find_point(target_point, path_nodes)
        elif self.southeast.boundary.contains(target_point): return self.southeast.find_point(target_point, path_nodes)
        else: return None, None

    # --- NUEVO: get_node_at ---
    def get_node_at(self, target_coords_tuple):
        """Encuentra el nodo más profundo que contiene las coordenadas."""
        target_pt = Point(target_coords_tuple[0], target_coords_tuple[1]) # Crear punto temporal

        if not self.boundary.contains(target_pt):
             return None # Fuera de este nodo/árbol

        # Si no está dividido, este es el nodo más profundo que lo contiene
        if not self.divided:
            return self

        # Si está dividido, descender al cuadrante apropiado
        if self.northwest.boundary.contains(target_pt): return self.northwest.get_node_at(target_coords_tuple)
        elif self.northeast.boundary.contains(target_pt): return self.northeast.get_node_at(target_coords_tuple)
        elif self.southwest.boundary.contains(target_pt): return self.southwest.get_node_at(target_coords_tuple)
        elif self.southeast.boundary.contains(target_pt): return self.southeast.get_node_at(target_coords_tuple)
        else:
             return self # Si cae en borde interno, devolver el padre

    # --- Métodos draw_spatial, get_all_points, get_depth, count_nodes (sin cambios) ---
    def draw_spatial(self, screen, color=(255, 255, 255), line_width=1, # Añadir más args para estilos
                     depth_colors=None, show_depth_colors=False,
                     hovered_node=None, visited_nodes=None, show_query_path=False):

        draw_color = color
        fill_color = None # Por defecto no rellenamos

        # --- Aplicar color por profundidad (Alt A) ---
        if show_depth_colors and depth_colors:
             max_depth_for_color = len(depth_colors) - 1
             color_index = min(self.depth_level, max_depth_for_color)
             fill_color = depth_colors[color_index] # Rellenar con color de profundidad

        # Dibujar relleno si aplica
        if fill_color:
             pygame.draw.rect(screen, fill_color, self.boundary.get_pygame_rect(), 0) # 0 para relleno

        # --- Resaltar borde si es el nodo bajo el cursor (Alt A) ---
        if self == hovered_node:
            draw_color = YELLOW # Borde amarillo para hover
            line_width = 2

        # --- Dibujar Borde Principal ---
        pygame.draw.rect(screen, draw_color, self.boundary.get_pygame_rect(), line_width)

        # --- Superponer resaltado de nodos visitados en query (Alt C) ---
        if show_query_path and visited_nodes and self in visited_nodes:
             # Dibujar un borde adicional o overlay
             overlay_color = (*RED, 100) # Rojo semi-transparente
             # Crear superficie para transparencia
             s = pygame.Surface((self.boundary.w, self.boundary.h), pygame.SRCALPHA)
             pygame.draw.rect(s, overlay_color, s.get_rect(), 0) # Relleno semi-transparente
             screen.blit(s, (self.boundary.x, self.boundary.y))
             # O dibujar un borde grueso rojo:
             # pygame.draw.rect(screen, RED, self.boundary.get_pygame_rect(), 2)


        # Llamadas recursivas pasando los parámetros de estilo/estado
        if self.divided:
            self.northwest.draw_spatial(screen, color, 1, depth_colors, show_depth_colors, hovered_node, visited_nodes, show_query_path)
            self.northeast.draw_spatial(screen, color, 1, depth_colors, show_depth_colors, hovered_node, visited_nodes, show_query_path)
            self.southwest.draw_spatial(screen, color, 1, depth_colors, show_depth_colors, hovered_node, visited_nodes, show_query_path)
            self.southeast.draw_spatial(screen, color, 1, depth_colors, show_depth_colors, hovered_node, visited_nodes, show_query_path)

    def get_all_points(self): # Sin cambios
        all_points = list(self.points);
        if self.divided: all_points.extend(self.northwest.get_all_points()); all_points.extend(self.northeast.get_all_points()); all_points.extend(self.southwest.get_all_points()); all_points.extend(self.southeast.get_all_points())
        return all_points
    def get_depth(self): # Sin cambios (ahora usamos self.depth_level precalculado)
        if not self.divided: return self.depth_level
        else: return max(self.northwest.get_depth(), self.northeast.get_depth(), self.southwest.get_depth(), self.southeast.get_depth())
    def count_nodes(self): # Sin cambios
        count = 1
        if self.divided: count += self.northwest.count_nodes() + self.northeast.count_nodes() + self.southwest.count_nodes() + self.southeast.count_nodes()
        return count

# --- Funciones Visualización Árbol ---
NODE_SIZE_TREE = (45, 22); TREE_VERT_SPACE = 60; TREE_HORIZ_SPACE = 5 # Ajustar tamaño/espacio

# Helper para resaltado (sin cambios)
def is_or_has_highlighted_descendant(node, highlighted_leaf_nodes):
    if node is None: return False
    if node in highlighted_leaf_nodes: return True
    if node.divided: return (is_or_has_highlighted_descendant(node.northwest, highlighted_leaf_nodes) or is_or_has_highlighted_descendant(node.northeast, highlighted_leaf_nodes) or is_or_has_highlighted_descendant(node.southwest, highlighted_leaf_nodes) or is_or_has_highlighted_descendant(node.southeast, highlighted_leaf_nodes))
    return False

# calculate_tree_layout (sin cambios)
def calculate_tree_layout(node, x_start, y, level_height, layout_info):
    # (Código sin cambios)
    if node is None: return x_start, 0
    node_center_y = y + NODE_SIZE_TREE[1] / 2
    if not node.divided:
        node_width = NODE_SIZE_TREE[0]; node_center_x = x_start + node_width / 2
        layout_info[node] = {'x': x_start, 'y': y, 'w': node_width, 'h': NODE_SIZE_TREE[1], 'center_x': node_center_x, 'center_y': node_center_y}
        return node_center_x, node_width
    children = [node.northwest, node.northeast, node.southwest, node.southeast]
    child_centers_x = []; child_total_widths = []; current_x = x_start
    last_valid_child_index = -1
    for i, child in enumerate(children):
        if child is None: continue
        if i > 0 and last_valid_child_index != -1 : current_x += TREE_HORIZ_SPACE
        child_center_x, child_width = calculate_tree_layout(child, current_x, y + level_height, level_height, layout_info)
        child_centers_x.append(child_center_x); child_total_widths.append(child_width)
        current_x += child_width
        last_valid_child_index = i
    first_valid_child = next((c for c in children if c in layout_info), None)
    last_valid_child = next((c for c in reversed(children) if c in layout_info), None)
    if not first_valid_child or not last_valid_child:
        parent_center_x = x_start + NODE_SIZE_TREE[0] / 2; total_children_span = NODE_SIZE_TREE[0]
    else:
        first_child_x = layout_info[first_valid_child]['x']
        last_child_x_end = layout_info[last_valid_child]['x'] + layout_info[last_valid_child]['w']
        parent_center_x = (first_child_x + last_child_x_end) / 2
        total_children_span = last_child_x_end - first_child_x
    layout_info[node] = {'x': parent_center_x - NODE_SIZE_TREE[0] / 2, 'y': y, 'w': NODE_SIZE_TREE[0], 'h': NODE_SIZE_TREE[1], 'center_x': parent_center_x, 'center_y': node_center_y}
    return parent_center_x, total_children_span


# --- MODIFICADO: draw_tree_structure ---
def draw_tree_structure(screen, node, layout_info, font_small, # Nuevos args
                        highlighted_leaf_nodes, specific_search_path,
                        depth_colors, show_depth_colors):
    if node is None or node not in layout_info: return

    node_info = layout_info[node]
    node_rect = pygame.Rect(int(node_info['x']), int(node_info['y']), int(node_info['w']), int(node_info['h']))

    # --- Determinar Estilo del Nodo ---
    is_in_found_branch = is_or_has_highlighted_descendant(node, highlighted_leaf_nodes)
    is_in_search_path = node in specific_search_path

    # Colores base
    fill_color = YELLOW if node.divided else WHITE
    outline_color = GRAY
    outline_width = 1
    depth_text_color = BLACK

    # Aplicar color por profundidad (si está activo y no hay otro resaltado) (Alt A)
    if show_depth_colors and depth_colors and not is_in_found_branch and not is_in_search_path:
         max_depth_for_color = len(depth_colors) - 1
         color_index = min(node.depth_level, max_depth_for_color)
         fill_color = depth_colors[color_index]
         # Cambiar color de texto si el fondo es oscuro
         if sum(fill_color[:3]) < 300: depth_text_color = WHITE


    # Prioridad de resaltado: Camino de búsqueda > Rama encontrada
    # Resaltado de camino de búsqueda específica (Alt C)
    if is_in_search_path:
        fill_color = MAGENTA # Relleno Magenta para nodos en el camino exacto
        outline_color = WHITE
        outline_width = 2
        depth_text_color = BLACK # Asegurar contraste

    # Resaltado de rama con resultados encontrados (Alt B/C - query/find)
    elif is_in_found_branch:
        # Relleno Cyan si está en una rama con resultados pero no en el camino de búsqueda específico
        fill_color = CYAN
        outline_color = WHITE
        outline_width = 2
        depth_text_color = BLACK # Asegurar contraste


    # Dibujar Nodo
    pygame.draw.rect(screen, fill_color, node_rect, border_radius=3)
    pygame.draw.rect(screen, outline_color, node_rect, outline_width, border_radius=3)

    # Dibujar Info Interna (Puntos y Profundidad - Alt A)
    info_text = ""
    if not node.divided and len(node.points) > 0:
        info_text += f"P:{len(node.points)}" # Puntos en hojas
    info_text += f" D:{node.depth_level}" # Profundidad

    if info_text:
        text_surface = font_small.render(info_text.strip(), True, depth_text_color) # Usar color de texto ajustado
        text_rect = text_surface.get_rect(center=node_rect.center)
        # Ajustar para que no se salga del nodo pequeño
        text_rect.clamp_ip(node_rect)
        screen.blit(text_surface, text_rect)

    # Dibujar Conexiones y Recursión (Pasar todos los args de estado)
    if node.divided:
        parent_center_x = node_info['center_x']; parent_bottom_y = node_info['y'] + node_info['h']
        children = [node.northwest, node.northeast, node.southwest, node.southeast]
        for child in children:
            if child is not None and child in layout_info:
                child_info = layout_info[child]; child_center_x = child_info['center_x']; child_top_y = child_info['y']
                # Resaltar línea si ambos nodos (padre e hijo) están en el camino de búsqueda
                line_color = GRAY
                line_width = 1
                if node in specific_search_path and child in specific_search_path:
                     line_color = MAGENTA
                     line_width = 2

                pygame.draw.line(screen, line_color, (int(parent_center_x), int(parent_bottom_y)), (int(child_center_x), int(child_top_y)), line_width)
                draw_tree_structure(screen, child, layout_info, font_small,
                                    highlighted_leaf_nodes, specific_search_path,
                                    depth_colors, show_depth_colors)


# --- Configuración Pygame y Visualización ---
pygame.init()

# Colores (+Magenta, +Colores Profundidad)
WHITE=(255,255,255); BLACK=(0,0,0); GRAY=(100,100,100); DARK_GRAY=(50,50,50)
BLUE=(0,0,255); GREEN=(0,255,0); RED=(255,0,0); YELLOW=(255,255,0); CYAN=(0,255,255)
MAGENTA=(255, 0, 255) # Para camino de búsqueda específica
INFO_PANEL_BG=(30,30,60); INFO_TEXT_COLOR=(200,200,255); INPUT_TEXT_COLOR=(255,255,150)
# Paleta de colores para profundidad (ejemplo simple)
DEPTH_PALETTE = [
    (100, 100, 255), (100, 150, 255), (100, 200, 255), (100, 255, 255), # Azules
    (100, 255, 200), (100, 255, 150), (100, 255, 100), # Verdes azulados
    (150, 255, 100), (200, 255, 100), (255, 255, 100), # Verdes amarillentos
    (255, 200, 100), (255, 150, 100), (255, 100, 100)  # Naranjas/Rojos
]

# Dimensiones
SCREEN_WIDTH=800; SCREEN_HEIGHT=750 # Un poco más de altura para info extra
INFO_PANEL_HEIGHT=150; VISUALIZATION_HEIGHT=SCREEN_HEIGHT-INFO_PANEL_HEIGHT
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Visualización Quadtree - Info Extendida")

# Quadtree
boundary = Rectangle(0, 0, SCREEN_WIDTH, VISUALIZATION_HEIGHT)
NODE_CAPACITY = 4
quadtree = QuadTreeNode(boundary, NODE_CAPACITY, depth=0) # Inicia en profundidad 0

# Variables estado
query_rect_start=None; query_rect_end=None; current_query_rect=None; found_in_query=[]
last_inserted_point = None; last_query_info = {"rect":None, "points_found":[], "count":0}
status_info = {"total_points":0, "depth":0, "node_count":0}
search_target_coords = None; found_specific_point = None; search_status_message = ""
input_mode = False; input_string = ""; input_prompt = "Presiona 'F' para buscar por coords"

# --- NUEVAS VARIABLES DE ESTADO ---
highlighted_tree_nodes = set() # Nodos hoja con resultados
visited_query_nodes = set()    # Nodos visitados en query rango (Alt C)
specific_search_path = []      # Lista de nodos en camino búsqueda específica (Alt C)
show_depth_colors = False      # Flag para colorear por profundidad (Alt A)
show_query_path = False        # Flag para mostrar nodos visitados query (Alt C)
hovered_node_spatial = None    # Nodo bajo el cursor en vista espacial (Alt A)
selected_node_spatial = None   # Nodo seleccionado con Shift+Click (Alt B)

# Fuentes
font=pygame.font.Font(None, 24); font_small=pygame.font.Font(None, 14) # Reducir small para caber info
font_info=pygame.font.Font(None, 24); font_input=pygame.font.Font(None, 20)

# Control visualización
view_mode = 'spatial'; show_help = True
tree_layout_info = {}; needs_layout_recalculation = True

# --- Bucle Principal ---
running = True; clock = pygame.time.Clock()

while running:
    # --- Actualizar estado Hover ---
    mouse_pos = pygame.mouse.get_pos()
    mouse_in_viz_area = (0 <= mouse_pos[0] < SCREEN_WIDTH and 0 <= mouse_pos[1] < VISUALIZATION_HEIGHT)

    # Resetear hover/selected si el ratón sale o cambiamos de modo
    if not mouse_in_viz_area or view_mode != 'spatial':
        hovered_node_spatial = None
        # No reseteamos selected_node_spatial aquí, se resetea con otras acciones

    # Actualizar nodo bajo cursor (solo en modo espacial)
    if view_mode == 'spatial' and mouse_in_viz_area:
         hovered_node_spatial = quadtree.get_node_at(mouse_pos)
    else:
         hovered_node_spatial = None # Limpiar si no está en modo/área correcta


    # --- Manejo de Eventos ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

        # --- Teclado ---
        if event.type == pygame.KEYDOWN:
            if input_mode: # Modo Input Coords
                # ... (Manejo Input: Enter, Backspace, Esc, Chars - como antes) ...
                if event.key == pygame.K_RETURN:
                    highlighted_tree_nodes.clear(); specific_search_path.clear() # Limpiar resaltados
                    try:
                        parts = input_string.split(','); search_x = float(parts[0].strip()); search_y = float(parts[1].strip())
                        search_target_coords = (search_x, search_y); target_point_obj = Point(search_x, search_y)
                        # --- Llamar find_point MODIFICADO ---
                        current_path = [] # Crear lista para el camino
                        found_specific_point, leaf_node = quadtree.find_point(target_point_obj, current_path) # Pasa la lista
                        specific_search_path = list(current_path) # Guardar el camino llenado

                        if found_specific_point:
                            search_status_message = f"Punto encontrado en {found_specific_point!r}!"
                            if leaf_node: highlighted_tree_nodes.add(leaf_node) # Resaltar hoja encontrada
                        else: search_status_message = f"Punto ({search_x:.1f}, {search_y:.1f}) no encontrado."
                        last_inserted_point=None; last_query_info={"rect":None,"points_found":[],"count":0}; current_query_rect=None; found_in_query=[]
                        selected_node_spatial = None # Limpiar selección
                    except: # Manejo genérico de errores de parseo
                        search_status_message = "Entrada inválida (formato: x, y)"; search_target_coords = None; found_specific_point = None
                        specific_search_path.clear() # Limpiar camino si hubo error
                    input_mode = False; input_string = ""; input_prompt = "Presiona 'F' para buscar"
                elif event.key == pygame.K_BACKSPACE: input_string = input_string[:-1]
                elif event.key == pygame.K_ESCAPE:
                    input_mode = False; input_string = ""; input_prompt = "Presiona 'F' para buscar"
                    search_target_coords = None; found_specific_point = None; search_status_message = ""; specific_search_path.clear(); highlighted_tree_nodes.clear()
                else:
                    if event.unicode.isdigit() or event.unicode in ['.', ',', '-']: input_string += event.unicode
            else: # Modo Normal
                if event.key == pygame.K_h: show_help = not show_help
                if event.key == pygame.K_c: # Limpiar
                    quadtree = QuadTreeNode(boundary, NODE_CAPACITY); current_query_rect = None; found_in_query = []
                    last_inserted_point = None; last_query_info = {"rect":None,"points_found":[],"count":0}
                    search_target_coords = None; found_specific_point = None; search_status_message = ""
                    highlighted_tree_nodes.clear(); visited_query_nodes.clear(); specific_search_path.clear()
                    hovered_node_spatial = None; selected_node_spatial = None
                    tree_layout_info.clear(); needs_layout_recalculation = True
                if event.key == pygame.K_r: # Random
                    # (Añadir random...)
                    for _ in range(20): px=random.uniform(0,SCREEN_WIDTH); py=random.uniform(0,VISUALIZATION_HEIGHT); py=min(py,VISUALIZATION_HEIGHT-0.01); p=Point(px,py); quadtree.insert(p)
                    # Limpiar estados relevantes
                    last_inserted_point = None; last_query_info = {"rect":None,"points_found":[],"count":0}
                    search_target_coords = None; found_specific_point = None; search_status_message = ""
                    highlighted_tree_nodes.clear(); visited_query_nodes.clear(); specific_search_path.clear()
                    selected_node_spatial = None
                    needs_layout_recalculation = True
                if event.key == pygame.K_t: # Toggle View
                    view_mode = 'tree' if view_mode == 'spatial' else 'spatial'
                    query_rect_start = None; query_rect_end = None; current_query_rect = None; found_in_query = []
                    # Mantener resaltados/estado al cambiar vista
                if event.key == pygame.K_f: # Entrar modo búsqueda
                     if view_mode == 'spatial':
                        input_mode = True; input_string = ""; input_prompt = "Buscar Coords (x,y): "
                        search_target_coords = None; found_specific_point = None; search_status_message = ""
                        last_inserted_point = None; last_query_info = {"rect":None,"points_found":[],"count":0}
                        current_query_rect = None; found_in_query = []
                        highlighted_tree_nodes.clear(); visited_query_nodes.clear(); specific_search_path.clear()
                        selected_node_spatial = None
                # --- NUEVAS TECLAS TOGGLE ---
                if event.key == pygame.K_d: # Toggle Depth Colors
                     show_depth_colors = not show_depth_colors
                if event.key == pygame.K_p: # Toggle Query Path Vis
                     show_query_path = not show_query_path
                     if not show_query_path: visited_query_nodes.clear() # Limpiar al desactivar


        # --- Interacciones Ratón (si NO está en modo input) ---
        if not input_mode and view_mode == 'spatial' and mouse_in_viz_area:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # --- SHIFT + CLICK IZQUIERDO: Seleccionar Nodo Hoja (Alt B) ---
                keys = pygame.key.get_pressed()
                if event.button == 1 and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
                    clicked_node = quadtree.get_node_at(mouse_pos)
                    if clicked_node and not clicked_node.divided: # Solo seleccionar hojas
                         selected_node_spatial = clicked_node
                         # Limpiar otros estados para enfocar en la selección
                         last_inserted_point = None; last_query_info = {"rect":None,"points_found":[],"count":0}
                         search_target_coords = None; found_specific_point = None; search_status_message = ""
                         highlighted_tree_nodes.clear(); visited_query_nodes.clear(); specific_search_path.clear()
                         current_query_rect = None; found_in_query = []
                    else:
                         selected_node_spatial = None # Click fuera o en nodo interno
                # --- CLICK IZQUIERDO NORMAL: Insertar ---
                elif event.button == 1:
                    mx, my = mouse_pos; point = Point(mx, my)
                    if quadtree.insert(point):
                        last_inserted_point = point
                        last_query_info = {"rect":None,"points_found":[],"count":0}
                        search_target_coords = None; found_specific_point = None; search_status_message = ""
                        highlighted_tree_nodes.clear(); visited_query_nodes.clear(); specific_search_path.clear()
                        selected_node_spatial = None # Limpiar selección
                    current_query_rect = None; found_in_query = []
                    needs_layout_recalculation = True
                # --- CLICK DERECHO: Iniciar Query Rango ---
                elif event.button == 3:
                    query_rect_start = mouse_pos; query_rect_end = mouse_pos
                    found_in_query = []
                    search_target_coords = None; found_specific_point = None; search_status_message = ""
                    highlighted_tree_nodes.clear(); visited_query_nodes.clear(); specific_search_path.clear()
                    selected_node_spatial = None

            # --- Mover Ratón (Query Rango) ---
            if event.type == pygame.MOUSEMOTION:
                if query_rect_start: query_rect_end = mouse_pos

            # --- Soltar Ratón (Finalizar Query Rango) ---
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:
                     highlighted_tree_nodes.clear(); visited_query_nodes.clear() # Limpiar resaltados query
                     if query_rect_start and query_rect_end:
                        x1,y1=query_rect_start; x2,y2=query_rect_end
                        qx,qy=min(x1,x2),min(y1,y2); qw,qh=abs(x1-x2),abs(y1-y2)
                        if qw>0 and qh>0:
                            current_query_rect = Rectangle(qx,qy,qw,qh)
                            # --- Llamar query MODIFICADO ---
                            temp_visited = set() # Set local para nodos visitados
                            result_map = quadtree.query(current_query_rect, visited_nodes=temp_visited)
                            visited_query_nodes = temp_visited # Guardar nodos visitados globalmente
                            found_in_query = list(result_map.keys())
                            highlighted_tree_nodes.update(result_map.values()) # Guardar nodos hoja encontrados

                            last_query_info["rect"]=current_query_rect; last_query_info["points_found"]=found_in_query; last_query_info["count"]=len(found_in_query)
                            last_inserted_point = None; search_target_coords = None; found_specific_point = None; search_status_message = ""; specific_search_path.clear()
                            selected_node_spatial = None
                        else: current_query_rect=None; found_in_query=[]; last_query_info={"rect":None,"points_found":[],"count":0}
                     query_rect_start = None; query_rect_end = None

    # --- Actualizar Estado General (Sin cambios) ---
    status_info["total_points"] = len(quadtree.get_all_points())
    status_info["depth"] = quadtree.get_depth() # Podríamos usar max depth calculada si la tuviéramos
    status_info["node_count"] = quadtree.count_nodes()

    # --- Lógica de Dibujo ---
    # 1. Limpiar área visualización
    visualization_area = pygame.Surface((SCREEN_WIDTH, VISUALIZATION_HEIGHT))
    visualization_area.fill(DARK_GRAY if view_mode == 'tree' else BLACK)

    # 2. Dibujar en área visualización
    if view_mode == 'spatial':
        # --- Dibujo Espacial ---
        # Pasar estado de resaltado/color a draw_spatial
        quadtree.draw_spatial(visualization_area, GRAY, 1,
                              DEPTH_PALETTE, show_depth_colors,
                              hovered_node_spatial,
                              visited_query_nodes, show_query_path)

        # Dibujar Puntos (Normal, Query, Específico, Selección Nodo)
        points_to_draw = quadtree.get_all_points()
        highlight_color = None
        points_to_highlight = []

        if selected_node_spatial: # Prioridad: Resaltar puntos del nodo seleccionado (Alt B)
             points_to_highlight = selected_node_spatial.points # Solo los puntos directos del nodo
             highlight_color = MAGENTA # Usar Magenta para selección
        elif found_in_query: # Resaltado Query Rango
             points_to_highlight = found_in_query
             highlight_color = YELLOW
        elif found_specific_point: # Resaltado Búsqueda Específica
             points_to_highlight = [found_specific_point]
             highlight_color = CYAN

        # Dibujar todos los puntos normales (blanco)
        for point in points_to_draw:
             # No dibujar si va a ser resaltado
             if point not in points_to_highlight:
                 pygame.draw.circle(visualization_area, WHITE, (int(point.x), int(point.y)), 3)

        # Dibujar puntos resaltados (si los hay)
        if highlight_color:
             for point in points_to_highlight:
                 pygame.draw.circle(visualization_area, highlight_color, (int(point.x), int(point.y)), 5) # Más grandes


        # Dibujar Query Rect en progreso
        if query_rect_start and query_rect_end:
            x1, y1 = query_rect_start; x2, y2 = query_rect_end
            temp_rect = pygame.Rect(min(x1, x2), min(y1, y2), abs(x1 - x2), abs(y1 - y2))
            pygame.draw.rect(visualization_area, BLUE, temp_rect, 2)


    elif view_mode == 'tree':
        # --- Dibujo Árbol ---
        if needs_layout_recalculation or not tree_layout_info:
            tree_layout_info.clear(); tree_start_y = 30
            calculate_tree_layout(quadtree, 10, tree_start_y, TREE_VERT_SPACE, tree_layout_info)
            needs_layout_recalculation = False
        # Pasar todos los sets/flags de estado para resaltado
        draw_tree_structure(visualization_area, quadtree, tree_layout_info, font_small,
                            highlighted_tree_nodes, specific_search_path,
                            DEPTH_PALETTE, show_depth_colors)

    # Blit área visualización
    screen.blit(visualization_area, (0, 0))

    # 3. Dibujar Panel Info (Ampliado)
    info_panel_rect = pygame.Rect(0, VISUALIZATION_HEIGHT, SCREEN_WIDTH, INFO_PANEL_HEIGHT)
    pygame.draw.rect(screen, INFO_PANEL_BG, info_panel_rect)
    pygame.draw.line(screen, GRAY, (0, VISUALIZATION_HEIGHT), (SCREEN_WIDTH, VISUALIZATION_HEIGHT), 1)

    info_lines = []
    # Línea 1: Estado General + Toggles Activos
    toggles = []
    if show_depth_colors: toggles.append("Profundidad(D)")
    if show_query_path: toggles.append("CaminoQuery(P)")
    toggle_str = f" | Toggles: {', '.join(toggles) if toggles else 'Ninguno'}"
    info_lines.append(f"Estado: Pts={status_info['total_points']} | Prof={status_info['depth']} | Nodos={status_info['node_count']}{toggle_str}")

    # Línea 2: Info de Hover/Selección (Alt A/B)
    display_node = selected_node_spatial if selected_node_spatial else hovered_node_spatial
    if display_node:
         node_type = "Hoja" if not display_node.divided else "Interno"
         points_str = f" Pts:{len(display_node.points)}" if not display_node.divided else ""
         prefix = "Seleccionado" if display_node == selected_node_spatial else "Hover"
         info_lines.append(f"{prefix}: {node_type} (Prof {display_node.depth_level}){points_str} @ {display_node.boundary!r}")
    else:
         info_lines.append("Hover/Seleccionado: Ninguno")


    # Líneas 3+: Prompt Input o Última Acción (Insert/Query/Search)
    if input_mode:
        input_display_text = input_prompt + input_string + ("_" if int(pygame.time.get_ticks()/500)%2==0 else "")
        info_lines.append(input_display_text)
        # Dibujar esta línea con su propia fuente/posición más tarde
    else:
        action_displayed = False
        if search_target_coords:
            info_lines.append(f"Búsqueda en: ({search_target_coords[0]:.1f}, {search_target_coords[1]:.1f}) -> {search_status_message}")
            action_displayed = True
        elif last_inserted_point:
            info_lines.append(f"Insertado: {last_inserted_point!r}"); action_displayed = True
        elif last_query_info["rect"]:
            info_lines.append(f"Consulta Rango: {last_query_info['rect']!r}")
            info_lines.append(f"  -> {last_query_info['count']} puntos encontrados")
            # (Mostrar lista puntos - sin cambios)
            max_pts=8; pts_str=", ".join([repr(p) for p in last_query_info["points_found"][:max_pts]])
            if last_query_info["count"]>max_pts: pts_str+=", ..."
            if last_query_info["count"]>0: info_lines.append(f"     [{pts_str}]")
            action_displayed = True
        elif selected_node_spatial: # Mostrar puntos del nodo seleccionado si no hay otra acción
             points_in_selected = selected_node_spatial.points
             info_lines.append(f" Puntos en Nodo Seleccionado ({len(points_in_selected)}):")
             max_pts=8; pts_str=", ".join([repr(p) for p in points_in_selected[:max_pts]])
             if len(points_in_selected)>max_pts: pts_str+=", ..."
             if len(points_in_selected)>0: info_lines.append(f"     [{pts_str}]")
             action_displayed = True

        #if not action_displayed: info_lines.append("Última Acción: N/A") # Omitir si no hubo acción reciente

    # Dibujar líneas de info
    line_y = VISUALIZATION_HEIGHT + 5
    for i, line in enumerate(info_lines):
        is_input_line = input_mode and i == 2 # La línea de input ahora es la tercera (índice 2)
        current_font = font_input if is_input_line else font_info
        color = INPUT_TEXT_COLOR if is_input_line else INFO_TEXT_COLOR

        try:
            text_surface = current_font.render(line, True, color)
            screen.blit(text_surface, (10, line_y))
            line_y += current_font.get_linesize() + 2 # Espacio extra
        except Exception as e: print(f"Error renderizando: {line} - {e}")


    # 4. Mostrar ayuda
    if show_help:
        help_start_y = 10
        help_text_lines = [
            f"Modo: {view_mode.upper()} ('T')", "'H': Ayuda", "'C': Limpiar", "'R': Pts Aleat.",
            "'D': Colores Profundidad", "'P': Camino Query Rango",
            "--- Espacial ---", "ClickIzq: Insertar", "'F': Buscar Coords",
             "Shift+ClickIzq: Sel. Nodo", "ArrastrarDer: Query Rango",
        ]
        # (Dibujar ayuda...)
        help_bg_surface = pygame.Surface((210, len(help_text_lines) * 20 + 10), pygame.SRCALPHA); help_bg_surface.fill((0, 0, 0, 150)); screen.blit(help_bg_surface, (5, help_start_y - 5))
        for i, line in enumerate(help_text_lines): text_surface = font.render(line, True, GREEN); screen.blit(text_surface, (10, help_start_y + i * 20))

    # --- Actualizar Pantalla ---
    pygame.display.flip()
    clock.tick(60)

# --- Salir ---
pygame.quit()
sys.exit()