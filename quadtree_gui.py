# -*- coding: utf-8 -*-

import pygame
import random
import sys

# Importar solo la clase QuadTree desde el módulo quadtree
from quadtree import QuadTree

# --- Funciones de visualización ---
def draw_quadtree(screen, node, color=(255, 255, 255)):
    """Dibuja el Quadtree recursivamente."""
    # Dibujar los límites de este nodo
    pygame.draw.rect(screen, color, node.boundary.get_pygame_rect(), 1)
    
    # Dibujar puntos en este nodo
    for point in node.points:
        pygame.draw.circle(screen, (255, 255, 0), (int(point.x), int(point.y)), 2)
    
    # Recursión para los hijos si está dividido
    if node.divided:
        draw_quadtree(screen, node.northwest, color)
        draw_quadtree(screen, node.northeast, color)
        draw_quadtree(screen, node.southwest, color)
        draw_quadtree(screen, node.southeast, color)

def main():
    # Inicializar pygame
    pygame.init()
    
    # Configuración de la pantalla
    width, height = 800, 600  # Tamaño de pantalla estándar
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("QuadTree Visualización")
    
    # Crear el QuadTree
    quadtree = QuadTree(0, 0, width, height)
    
    # Colores
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    
    # Fuente para texto
    font = pygame.font.Font(None, 24)
    
    running = True
    clock = pygame.time.Clock()
    
    # Variables para mensajes e instrucciones
    instructions = [
        "Click Izquierdo: Insertar punto",
        "R: Insertar 20 puntos aleatorios",
        "C: Limpiar el árbol",
        "ESC: Salir"
    ]
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    
                elif event.key == pygame.K_r:  # Generar puntos aleatorios
                    for _ in range(20):
                        x = random.uniform(0, width)
                        y = random.uniform(0, height)
                        quadtree.insert(x, y)
                        
                elif event.key == pygame.K_c:  # Limpiar
                    quadtree = QuadTree(0, 0, width, height)
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Click izquierdo
                    x, y = event.pos
                    quadtree.insert(x, y)
        
        # Limpiar pantalla
        screen.fill(BLACK)
        
        # Dibujar el quadtree
        draw_quadtree(screen, quadtree.root, WHITE)
        
        # Mostrar estadísticas del árbol
        stats_text = f"Puntos: {len(quadtree.get_all_points())} | Profundidad: {quadtree.get_depth()} | Nodos: {quadtree.count_nodes()}"
        stats_surface = font.render(stats_text, True, GREEN)
        screen.blit(stats_surface, (10, height - 30))
        
        # Mostrar instrucciones
        y_offset = 10
        for line in instructions:
            text = font.render(line, True, GREEN)
            screen.blit(text, (10, y_offset))
            y_offset += 25
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()