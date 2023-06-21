import geopy.distance
import random

class Driver:
    def __init__(self, id, origen):
        self.id = id
        self.peso_max = 450
        self.peso = 0
        self.volumen_max = 2
        self.volumen = 0
        self.origen = origen
        self.ruta = []
        self.ecommerce = []
        self.deliveries = []
        self.tiempo = 0
        # self.ubicaion_actual = []
    
    def reset(self):
        self.peso = 0
        self.volumen = 0
        self.ruta = []
        self.ecommerce = []
        self.deliveries = []
        self.tiempo = 0

    def agregar_ecommerce(self, ecommerce):
        self.peso += ecommerce.peso
        self.volumen += ecommerce.volumen
        self.ruta.append(ecommerce.ubicacion)
        self.ecommerce.append(ecommerce)
        self.tiempo += random.randint(8, 15)
        
        # self.ubicacion_actual = ecommerce.ubicacion
    
    def eliminar_ecommerce(self, ecommerce):
        self.peso -= ecommerce.peso
        self.volumen -= ecommerce.volumen
        self.ruta.remove(ecommerce.ubicacion)
        self.ecommerce.remove(ecommerce)
        self.tiempo -= random.randint(8, 15)
        # self.ubicacion_actual = ecommerce.ubicacion
    
    def agregar_delivery(self, paquete):
        self.peso += paquete.peso
        self.volumen += paquete.volumen
        self.ruta.append(paquete.ubicacion)
        self.deliveries.append(paquete)
        self.tiempo += random.randint(4, 8)


class Ecommerce:
    def __init__(self, id, ubicacion):
        self.id = id
        self.peso = 0
        self.volumen = 0
        self.ubicacion = ubicacion
        self.paquetes = []
        self.vecindad = []
        self.recogido = False

    def agregar_paquete(self, paquete):
        self.paquetes.append(paquete)
        self.peso += paquete.peso
        self.volumen += paquete.volumen
    
    def eliminar_paquete(self, paquete):
        self.paquetes.remove(paquete)
        self.peso -= paquete.peso
        self.volumen -= paquete.volumen
    
    def recoger(self):
        self.recogido = True


class Paquete:
    def __init__(self, id, peso, ubicacion, x1,x2,x3, delivery_day, ecommerce):
        self.id = id
        self.peso = peso
        self.x1 = x1 / 100
        self.x2 = x2 / 100
        self.x3 = x3 / 100
        self.volumen = self.x1*self.x2*self.x3
        self.ubicacion = ubicacion
        self.dia = delivery_day
        self.ecommerce = ecommerce


class Centro:
    def __init__(self, id, ubicacion):
        self.id = id
        self.ubicacion = ubicacion