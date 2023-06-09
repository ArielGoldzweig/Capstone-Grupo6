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
from Opt2_function import opt2, distance_driver


# random.seed(343545)

def calculate_distance(drivers):
    distance = 0
    for i in range(len(drivers)):
        for j in range(len(drivers[i].ruta)):
            if j != len(drivers[i].ruta) - 1:
                distance += geopy.distance.geodesic(drivers[i].ruta[j], drivers[i].ruta[j+1]).km
    return distance


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


def plot_improvement(x, y, name, i):
    plt.plot(x, y)
    
    plt.ylim(250,380)
    plt.xlim(1,i+100)
    
    plt.xlabel('Iteración')
    plt.ylabel('Mejor solucion')
    
    plt.title(name)
    
    # plt.show()
    plt.savefig(f'simulation/graph/{name}.png')


def improve_route_aleatory(drivers, ecommerces, best_distance):

    i = 0
    best_list = []
    iteration_list = []
    iteration_list.append(i)
    best_list.append(best_distance)
    

    drivers_copy = deepcopy(drivers)

    t_end = time.time() + 60 * 0.1

    while time.time() < t_end:
        try:
            driver_take = random.randint(0, len(drivers) - 1)
            driver_give = random.randint(0, len(drivers) - 1)
            

            # Asegurarse que son distinto drivers
            while driver_take == driver_give:
                driver_take = random.randint(0, len(drivers) - 1)
                driver_give = random.randint(0, len(drivers) - 1)

            if len(drivers[driver_take].ruta) >= 4 and len(drivers[driver_give].ruta) <= 9:
                
                # Posicion que se cambia
                pos_change = random.randint(1, len(drivers[driver_take].ruta) - 2)
                
                # Guardo el punto a cambiar, lo elimino de un driver y lo inserto en otro
                value_change = drivers[driver_take].ruta[pos_change]
                drivers[driver_give].ruta.insert(-1, value_change)
                drivers[driver_take].ruta.pop(pos_change)
                

                # Entrega nuevas listas con la minima distancia
                bodega = drivers[driver_take].ruta[-1]
                driver_take_coor = drivers[driver_take].ruta[0]
                driver_give_coor = drivers[driver_give].ruta[0]

                # Actualizo peso y dimension de cada driver
                for e in ecommerces:
                    if e.ubicacion == value_change:
                        peso_change = e.peso
                        volumen_change = e.volumen
                drivers[driver_take].peso -= peso_change
                drivers[driver_take].volumen -= volumen_change
                drivers[driver_take].tiempo -= random.randint(8, 15)
                drivers[driver_give].peso += peso_change
                drivers[driver_give].volumen += volumen_change
                drivers[driver_give].tiempo += random.randint(8, 15)
                
                if drivers[driver_give].peso < 450 and drivers[driver_give].volumen < 2 and drivers[driver_take].peso < 450 and drivers[driver_take].volumen < 2:

                    # Revisar nueva ruta para el driver que se le quita un ecommerce
                    if len(drivers[driver_take].ruta) > 2:
                        route_take = min_route(drivers[driver_take].ruta[1:-1], drivers[driver_take])
                        # Agregamos la direccion del driver y bodega
                        drivers[driver_take].ruta = route_take
                        drivers[driver_take].ruta.insert(0, driver_take_coor)
                        drivers[driver_take].ruta.append(bodega)
                        
                    else:
                        route_take = drivers[driver_take].ruta
                    
                    # Revisar nueva ruta para el driver que se le da un ecommerce
                    if len(drivers[driver_give].ruta) > 2: 
                        route_give = min_route(drivers[driver_give].ruta[1:-1], drivers[driver_give])
                        drivers[driver_give].ruta = route_give
                        drivers[driver_give].ruta.insert(0, driver_give_coor)
                        drivers[driver_give].ruta.append(bodega)
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
            print("El driver ya no tiene ruta")
        
    # # -------- Guardamos ruta en TXT ------------
    # with open(r'simulation/txt/ruta_ecommerce_mejorada.txt', 'w') as fp:
    #     for driver in drivers:
    #         fp.write("%s " % driver.ruta)
    #         fp.write("\n")

    
    return [drivers, iteration_list, best_list, i]


def generate_colors(n):
    # Generate color palette for coordinates
    colors = cm.rainbow(np.linspace(0, 1, n))
    colors_new = []
    for el in colors:
        hex = cl.to_hex(el)
        colors_new += [hex]
    return colors_new


def map_distance(drivers, name):

    coordinate_center = [-33.4369436, -70.634449]

    m = folium.Map(location=(coordinate_center[0], coordinate_center[1]))
    colors = generate_colors(len(drivers))

    for i in range(len(drivers)):
        folium.CircleMarker(drivers[i].origen, color='black', radius=4, fill=True).add_to(m) 
        folium.PolyLine(drivers[i].ruta, color=colors[i], weight=3, opacity=1).add_to(m)

    m.save(name)


def swap_ecommerce(drivers, ecommerces, best_distance, i, iteration_list, best_list):

    drivers_copy = deepcopy(drivers)
    t_end = time.time() + 60 * 0.2

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
                elif e.ubicacion == value_change2:
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
    
    # -------- Guardamos ruta en TXT ------------
    # with open(r'simulation/txt/ruta_ecommerce_swap.txt', 'w') as fp:
    #     for driver in drivers:
    #         fp.write("%s " % driver.ruta)
    #         fp.write("\n")
    
    # return drivers
    return [drivers, iteration_list, best_list, i]


def vecindad(ecommerces):
    for e in ecommerces:
        while len(e.vecindad) < 5:
            min_dis = 100000
            for i in range(len(ecommerces)):
                if e != ecommerces[i]:
                    if ecommerces[i] not in e.vecindad:
                        if min_dis >= geopy.distance.geodesic(e.ubicacion, ecommerces[i].ubicacion).km:
                            min_dis = geopy.distance.geodesic(e.ubicacion, ecommerces[i].ubicacion).km
                            ecom_add = ecommerces[i]
            e.vecindad.append(ecom_add)


def time_drivers(drivers):
    for d in drivers:
        dis = distance_driver(d)
        d.tiempo = 0
        for k in range(len(d.ruta) - 2):
            d.tiempo += random.randint(8, 15)
        tiempo_recoleccion = (dis/50)*60
        d.tiempo += tiempo_recoleccion
    drivers.sort(key=lambda x: x.tiempo)
    return drivers


def best_removal(driver, ecommerces):
    original_distance = distance_driver(driver)
    original_route = deepcopy(driver.ruta)
    best_diference_length = 0

    for k in range(1, len(driver.ruta)-1):
        driver.ruta.pop(k)
        new_distance = distance_driver(driver)
        new_diference_length = original_distance - new_distance
        if (new_diference_length > best_diference_length):
            best_diference_length = new_diference_length
            best_removal = k
            value_return = original_route[k]
        driver.ruta = deepcopy(original_route)
    
    for e in ecommerces:
        if e.ubicacion == value_return:
            weight = e.peso
            volume = e.volumen
    driver.ruta.pop(best_removal)
    driver.peso -= weight
    driver.volumen -= volume
    driver.tiempo -= random.randint(8, 15)
    driver.ruta = opt2(driver.ruta)

    return value_return, weight, volume


def best_insert(drivers, driver, new_point, weigth, volume):
    min_increment_distance = float('inf')
    best_list = []
    while len(best_list) < 4:
        for d in drivers:
            new_weigth = 0
            new_volume = 0
            if d != driver and d not in best_list:
                new_weigth = d.peso + weigth
                new_volume = d.volumen + volume
                if new_weigth < 450 and new_volume < 2 and len(d.ruta) < 9:
                    original_distance = distance_driver(d)
                    d.ruta.insert(-1, new_point)
                    d.ruta = opt2(d.ruta)
                    new_distance = distance_driver(d)
                    difference_distance = new_distance - original_distance
                    if(difference_distance < min_increment_distance):
                        dis = difference_distance - min_increment_distance
                        min_increment_distance = difference_distance
                        best_driver = d
                        
                    d.ruta.remove(new_point)
                
                best_list.append(best_driver)

    driver_take = random.choice(best_list)
    driver_take.ruta.insert(-1, new_point)
    driver_take.ruta = opt2(driver_take.ruta)
    driver_take.peso += weigth
    driver_take.volumen += volume
    driver_take.tiempo += random.randint(8, 15)

    return driver_take


def improve_route_min_max_time(drivers, ecommerces, best_distance):

    t_end = time.time() + 60 * 2

    while time.time() < t_end:
        try:
            
            drivers = time_drivers(drivers)
            driver_give = drivers[-1]

            if len(driver_give.ruta) >= 4:
                
                pos, weight, volume = best_removal(driver_give, ecommerces)
                driver_take = best_insert(drivers, driver_give, pos, weight, volume)

        except:
            print("El driver ya no tiene ruta")
        
    return drivers
