# -*- coding: utf-8 -*-
from datetime import datetime

class Point:
    def __init__(self, x, y, data=None):
        self.x = x
        self.y = y
        self.data = data
        self.timestamp = datetime.now()
        
    def __repr__(self):
        return f"({self.x:.1f}, {self.y:.1f})"
        
    def __hash__(self):
        return hash((self.x, self.y))
        
    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y

class Rectangle:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        
    def contains(self, point):
        return (self.x <= point.x < self.x + self.w and
                self.y <= point.y < self.y + self.h)
                
    def intersects(self, range_rect):
        return not (range_rect.x >= self.x + self.w or
                   range_rect.x + range_rect.w <= self.x or
                   range_rect.y >= self.y + self.h or
                   range_rect.y + range_rect.h <= self.y)
    
    def get_pygame_rect(self):
        """Retorna un rectángulo de pygame si está disponible, o una tupla (x,y,w,h) si no."""
        try:
            import pygame
            return pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))
        except ImportError:
            return (int(self.x), int(self.y), int(self.w), int(self.h))
            
    def __repr__(self):
        return f"Rect[({self.x:.0f},{self.y:.0f}) W:{self.w:.0f} H:{self.h:.0f}]"

class QuadTreeNode:
    def __init__(self, boundary, capacity, depth=0):
        self.boundary = boundary
        self.capacity = capacity
        self.points = []
        self.divided = False
        self.northwest = None
        self.northeast = None
        self.southwest = None
        self.southeast = None
        self.depth_level = depth
        
    def subdivide(self):
        """Divide este nodo en cuatro nodos hijos."""
        x = self.boundary.x
        y = self.boundary.y
        w = self.boundary.w / 2
        h = self.boundary.h / 2
        
        # Crear rectángulos para los cuatro cuadrantes
        nw_rect = Rectangle(x, y, w, h)
        ne_rect = Rectangle(x + w, y, w, h)
        sw_rect = Rectangle(x, y + h, w, h)
        se_rect = Rectangle(x + w, y + h, w, h)
        
        # Crear nodos hijos
        self.northwest = QuadTreeNode(nw_rect, self.capacity, self.depth_level + 1)
        self.northeast = QuadTreeNode(ne_rect, self.capacity, self.depth_level + 1)
        self.southwest = QuadTreeNode(sw_rect, self.capacity, self.depth_level + 1)
        self.southeast = QuadTreeNode(se_rect, self.capacity, self.depth_level + 1)
        
        # Marcar como dividido
        self.divided = True
        
        # Mover puntos existentes a los hijos
        for point in self.points:
            self._insert_into_children(point)
            
        # Vaciar lista de puntos del nodo actual
        self.points = []
        
    def _insert_into_children(self, point):
        """Insertar punto en uno de los nodos hijos."""
        if self.northwest.insert(point): return True
        if self.northeast.insert(point): return True
        if self.southwest.insert(point): return True
        if self.southeast.insert(point): return True
        return False  # No debería ocurrir si boundary.contains(point) es True
        
    def insert(self, point):
        """Insertar un punto en el árbol."""
        # Si el punto no está en los límites de este nodo
        if not self.boundary.contains(point):
            return False
            
        # Si hay espacio en este nodo y no está dividido
        if len(self.points) < self.capacity and not self.divided:
            self.points.append(point)
            return True
            
        # Si no hay espacio, subdividir (si aún no está dividido)
        if not self.divided:
            self.subdivide()
            
        # Insertar punto en uno de los hijos
        return self._insert_into_children(point)
    
    def get_all_points(self):
        """Retorna todos los puntos en este nodo y sus hijos."""
        all_points = list(self.points)
        if self.divided:
            all_points.extend(self.northwest.get_all_points())
            all_points.extend(self.northeast.get_all_points())
            all_points.extend(self.southwest.get_all_points())
            all_points.extend(self.southeast.get_all_points())
        return all_points
    
    def get_depth(self):
        """Retorna la profundidad máxima del árbol."""
        if not self.divided:
            return self.depth_level
        return max(
            self.northwest.get_depth(),
            self.northeast.get_depth(),
            self.southwest.get_depth(),
            self.southeast.get_depth()
        )
    
    def count_nodes(self):
        """Cuenta el número total de nodos en el árbol."""
        count = 1  # Este nodo
        if self.divided:
            count += self.northwest.count_nodes()
            count += self.northeast.count_nodes()
            count += self.southwest.count_nodes()
            count += self.southeast.count_nodes()
        return count

class QuadTree:
    """Clase principal para manejar un QuadTree."""
    def __init__(self, x, y, width, height, capacity=4):
        boundary = Rectangle(x, y, width, height)
        self.root = QuadTreeNode(boundary, capacity)
        
    def insert(self, x, y, data=None):
        """Insertar un punto en las coordenadas (x,y)."""
        point = Point(x, y, data)
        return self.root.insert(point)
    
    def insert_point(self, point):
        """Insertar un objeto Point existente."""
        return self.root.insert(point)
    
    def get_all_points(self):
        """Retorna todos los puntos en el árbol."""
        return self.root.get_all_points()
    
    def get_depth(self):
        """Retorna la profundidad máxima del árbol."""
        return self.root.get_depth()
    
    def count_nodes(self):
        """Cuenta el número total de nodos en el árbol."""
        return self.root.count_nodes()