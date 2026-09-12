class Pista:

    SENTIDO_HORARIO = 0
    SENTIDO_ANTIHORARIO = 1
    SENTIDO_INDETERMINADO = -1

    ANCHO = 3000
    LARGO = 3000
    
    ESQUINAS_TOTAL = 12
    # Instancia única
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)

        return cls.__instance

    def __init__(self):
        # __init__ se ejecuta cada vez que alguien hace Pista()
        # por eso necesitamos evitar reinicializar el estado.
        if getattr(self, "_inicializada", False):
            return

        self.__resuelto = False
        self.__sentido = Pista.SENTIDO_INDETERMINADO

        self._inicializada = True
        
        self.conteo_esquinas = 0

    # =========================================================
    # GRUPO DE MÉTODOS 1
    # Compatibilidad con código nuevo
    # =========================================================

    def get_resuelto(self):
        return self.__resuelto

    def set_resuelto(self, res):
        self.__resuelto = res

    def get_sentido(self):
        return self.__sentido

    def set_sentido(self, sentido):
        self.__sentido = sentido
        
    def get_esquinas_recorridas(self):
        return self.conteo_esquinas
    
    def marcar_esquina(self):
        self.conteo_esquinas = self.conteo_esquinas + 1
    # =========================================================
    # GRUPO DE MÉTODOS 2
    # Compatibilidad con código viejo
    # =========================================================

    def esta_resuelta(self):
        """Retorna si la pista ya fue resuelta."""
        return self.__resuelto

    def resuelta(self):
        """Marca la pista como resuelta."""
        self.__resuelto = True