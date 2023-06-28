import geopy.distance
import random
import numpy as np
from copy import deepcopy
import folium
from folium.features import DivIcon
import matplotlib.cm as cm
import matplotlib.colors as cl
import time
import matplotlib.pyplot as plt


def calculate_distance(drivers):
    distance = 0
    for i in range(len(drivers)):
        for j in range(len(drivers[i].ruta)):
            if j != len(drivers[i].ruta) - 1:
                distance += geopy.distance.geodesic(drivers[i].ruta[j], drivers[i].ruta[j+1]).km
    return distance


def distance_driver(driver):
    distance = 0
    for j in range(len(driver.ruta)):
        if j != len(driver.ruta) - 1:
            distance += geopy.distance.geodesic(driver.ruta[j], driver.ruta[j+1]).km
    return distance


def generate_colors(n):
    # Generate color palette for coordinates
    colors = cm.rainbow(np.linspace(0, 1, n))
    colors_new = []
    for el in colors:
        hex = cl.to_hex(el)
        colors_new += [hex]
    return colors_new


def min_route(ecommerces, driver):
    list_route = ecommerces
    route = []
    distance = 10000000
    for i in range(len(list_route)):
        if list_route[i] not in route:
            if driver.peso < 450 and driver.volumen < 2:
                if distance >= geopy.distance.geodesic(driver.origen, list_route[i]).km:
                    distance = geopy.distance.geodesic(driver.origen, list_route[i]).km
                    ecommerce = list_route[i]
    route.append(ecommerce)

    while len(route) < len(list_route):
        distance = 1000000
        
        for i in range(len(list_route)):
            if list_route[i] not in route:
                if driver.peso < 450 and driver.volumen < 2:
                    if distance >= geopy.distance.geodesic(route[-1], list_route[i]).km:
                        distance = geopy.distance.geodesic(route[-1], list_route[i]).km
                        ecommerce = list_route[i]
        route.append(ecommerce)

    return route


def improve_route_aleatory(drivers, paqutes, best_distance):

    i = 0
    best_list = []
    iteration_list = []
    iteration_list.append(i)
    best_list.append(best_distance)
    

    drivers_copy = deepcopy(drivers)

    t_end = time.time() + 60 * 8

    while time.time() < t_end:
        try:
            driver_take = random.randint(0, len(drivers) - 1)
            driver_give = random.randint(0, len(drivers) - 1)
            

            # Asegurarse que son distinto drivers
            while driver_take == driver_give:
                driver_take = random.randint(0, len(drivers) - 1)
                driver_give = random.randint(0, len(drivers) - 1)

            if len(drivers[driver_take].ruta) >= 10 and len(drivers[driver_give].ruta) <= 70:
                
                # Posicion que se cambia
                pos_change = random.randint(1, len(drivers[driver_take].ruta) - 2)
                
                # Guardo el punto a cambiar, lo elimino de un driver y lo inserto en otro
                value_change = drivers[driver_take].ruta[pos_change]
                drivers[driver_give].ruta.insert(-1, value_change)
                drivers[driver_take].ruta.pop(pos_change)
                

                # Entrega nuevas listas con la minima distancia
                bodega = drivers[driver_take].ruta[0]
                driver_take_coor = drivers[driver_take].ruta[-1]
                driver_give_coor = drivers[driver_give].ruta[-1]


                # Actualizo peso y dimension de cada driver
                for e in paqutes:
                    if e.destino == value_change:
                        peso_change = e.peso
                        volumen_change = e.volumen
                drivers[driver_take].peso -= peso_change
                drivers[driver_take].volumen -= volumen_change
                drivers[driver_take].tiempo -= random.randint(4, 6)
                drivers[driver_give].peso += peso_change
                drivers[driver_give].volumen += volumen_change
                drivers[driver_give].tiempo += random.randint(4, 6)
                
                if drivers[driver_give].peso < 450 and drivers[driver_give].volumen < 2 and drivers[driver_take].peso < 450 and drivers[driver_take].volumen < 2:
                    
                    # Revisar nueva ruta para el driver que se le quita un ecommerce
                    if len(drivers[driver_take].ruta) > 10:
                        route_take = min_route(drivers[driver_take].ruta[1:-1], drivers[driver_take])
                        # Agregamos la direccion del driver y bodega
                        drivers[driver_take].ruta = route_take
                        drivers[driver_take].ruta.insert(0, bodega)
                        drivers[driver_take].ruta.append(driver_take_coor)
                        
                    else:
                        route_take = drivers[driver_take].ruta
                    
                    # Revisar nueva ruta para el driver que se le da un ecommerce
                    if len(drivers[driver_give].ruta) > 10: 
                        route_give = min_route(drivers[driver_give].ruta[1:-1], drivers[driver_give])
                        drivers[driver_give].ruta = route_give
                        drivers[driver_give].ruta.insert(0, bodega)
                        drivers[driver_give].ruta.append(driver_give_coor)
                    else:
                        route_give = drivers[driver_give].ruta

                    # Cambio las lista por las nuevas y elimino las viejas
                    drivers[driver_take].ruta = route_take
                    drivers[driver_give].ruta = route_give

                    new_distance = calculate_distance(drivers)

                    if new_distance < best_distance:
                        print('--------------------------')
                        print(f'Mejor distancia ahora {new_distance} antes {best_distance}')
                        print('--------------------------')
                        best_distance = new_distance
                        drivers_copy = deepcopy(drivers)
                    else:
                        drivers = deepcopy(drivers_copy)
                # else:
                #     print('No cumple condicion de Peso o Dimension')

            i+=1
            iteration_list.append(i)
            best_list.append(best_distance)

        except:
            # print("El driver ya no tiene ruta")
            pass
    
    return [drivers, iteration_list, best_list, i]


def distance(value1, value2):
    return geopy.distance.geodesic(value1, value2).km

def time_drivers_delivery(drivers):
    for d in drivers:
        dis = distance_driver(d)
        d.tiempo = 0
        for k in range(len(d.ruta) - 2):
            d.tiempo += np.random.uniform(4, 8)
        tiempo_recoleccion = (dis/40)*60
        d.tiempo += tiempo_recoleccion
    drivers.sort(key=lambda x: x.tiempo)
    return drivers

def order_drivers_time(drivers):
    drivers.sort(key=lambda x: x.tiempo)
    return drivers


def opt2(tour):
    n = len(tour) - 1
    tour_edges = [(tour[i], tour[i+1]) for i in range(n)]
    improved = True

    while improved:
        
        improved = False
        # range(1, n)
        for i in range(1, n):
            for j in range(i+1, n - 1):
            # for j in range(i+1, n):

                # current node
                cur1 = (tour[i], tour[i+1])
                cur2 = (tour[j], tour[(j+1)%n])
                cur_length = distance(tour[i], tour[i+1]) + distance(tour[j], tour[(j+1)%n])

                # Two new edges for tour
                new1 = (tour[i], tour[j])
                new2 = (tour[i+1], tour[(j+1)%n])
                new_length = distance(tour[i], tour[j]) + distance(tour[i+1], tour[(j+1)%n])

                # Reviso si al cambiar los nodos la distancia es menor
                if new_length < cur_length:
                    # print(f'sawp {cur1} {cur2} with {new1} {new2}')
                    # Los nodos que estan entre los nodos escogicos se invierten
                    tour[i+1:j+1] = tour[i+1:j+1][::-1]
                    tour_edges = [(tour[i], tour[i + 1]) for i in range(n)]
                    improved = True
    return tour


def swap_ecommerce(drivers, ecommerces, best_distance, i, iteration_list, best_list):

    drivers_copy = deepcopy(drivers)
    t_end = time.time() + 60 * 5

    while time.time() < t_end:
        try:
            driver1 = random.randint(0, len(drivers) - 1)
            driver2 = random.randint(0, len(drivers) - 1)

            while driver1 == driver2:
                driver1 = random.randint(0, len(drivers) - 1)
                driver2 = random.randint(0, len(drivers) - 1)
            
            pos_change1 = random.randint(1, len(drivers[driver1].ruta) - 2)
            pos_change2 = random.randint(1, len(drivers[driver2].ruta) - 2)

            value_change1 = drivers[driver1].ruta[pos_change1]
            value_change2 = drivers[driver2].ruta[pos_change2]

            drivers[driver1].ruta.remove(value_change1)
            drivers[driver2].ruta.remove(value_change2)

            drivers[driver1].ruta.insert(-1, value_change2)
            drivers[driver2].ruta.insert(-1, value_change1)


            for e in ecommerces:
                if e.ubicacion == value_change1:
                    peso_change1 = e.peso
                    volumen_change1 = e.volumen
                elif e.destino == value_change2:
                    peso_change2 = e.peso
                    volumen_change2 = e.volumen
            drivers[driver1].peso -= peso_change1
            drivers[driver1].volumen -= volumen_change1
            drivers[driver2].peso += peso_change2
            drivers[driver2].volumen += volumen_change2

            if drivers[driver1].peso < 450 and drivers[driver1].volumen < 2 and drivers[driver2].peso < 450 and drivers[driver2].volumen < 2:

                cur_distance1 = distance_driver(drivers[driver1])
                new_distance1 = distance_driver(drivers[driver1])
                if new_distance1 < cur_distance1:
                    driver1.ruta = opt2(drivers[driver1].ruta)
                
                cur_distance2 = distance_driver(drivers[driver2])
                new_distance2 = distance_driver(drivers[driver2])
                if new_distance2 < cur_distance2:
                    driver2.ruta = opt2(drivers[driver2].ruta)
                
                new_distance = calculate_distance(drivers)

                if new_distance < best_distance:
                    print('--------------------------')
                    print(f'Mejor distancia ahora {new_distance} antes {best_distance}')
                    print('--------------------------')
                    best_distance = new_distance
                    drivers_copy = deepcopy(drivers)
                else:
                    drivers = deepcopy(drivers_copy)

            i+=1
            iteration_list.append(i)
            best_list.append(best_distance)

        except:
                print("El driver ya no tiene ruta")
    
    return [drivers, iteration_list, best_list, i]


def plot_improvement(x, y, name, i):
    plt.plot(x, y)
    
    plt.ylim(600,1000)
    plt.xlim(1,i+100)
    
    plt.xlabel('Iteración')
    plt.ylabel('Mejor solucion')
    
    plt.title(name)
    
    # plt.show()
    plt.savefig(f'simulation_delivery/graph/{name}.png')
