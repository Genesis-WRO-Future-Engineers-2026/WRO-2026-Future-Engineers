# Pista.py

class Pista():
    
    SENTIDO_HORARIO = 0
    SENTIDO_ANTIHORARIO = 1
    SENTIDO_INDETERMINADO = -1
    
    ANCHO = 3000
    LARGO = 3000
    
    def __init__(self):
        self.__resuelto = False
        self.__sentido = Pista.SENTIDO_INDETERMINADO
        
    # --- GRUPO DE MÉTODOS 1 (Compatibilidad con código nuevo) ---
    def get_resuelto(self):
        return self.__resuelto
    
    def set_resuelto(self, res):
        self.__resuelto = res
        
    def get_sentido(self):
        return self.__sentido
    
    def set_sentido(self, sentido):
        self.__sentido = sentido

    # --- GRUPO DE MÉTODOS 2 (Compatibilidad con código viejo en caché) ---
    def esta_resuelta(self):
        """Redirige al nuevo sistema de resolución"""
        return self.__resuelto
    
    def resuelta(self):
        """Marca la pista como resuelta para el código antiguo"""
        self.__resuelto = True