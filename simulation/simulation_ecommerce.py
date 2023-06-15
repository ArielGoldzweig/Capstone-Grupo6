import geopy.distance
from geopy.distance import geodesic
import pandas as pd
import random
import folium
from folium.features import DivIcon
from clases import Driver, Paquete, Ecommerce, Centro
from funciones import calculate_distance, improve_route_aleatory, map_distance, generate_colors, swap_ecommerce, plot_improvement, time_drivers, improve_route_min_max_time
from Opt2_function import distance_driver, opt2

# ------------- Cargar los datos --------------

df_delivery = pd.read_excel("../datos/deliveries_data.xlsx")
df_driver = pd.read_excel("../datos/driver_origins_data.xlsx")
df_center = pd.read_excel("../datos/centers_data.xlsx")
df_ecommerce = pd.read_excel("../datos/e-commerce_data.xlsx")


# # ------------- Separar por dias --------------
days = []
amountDays = []

for i in range(df_delivery['delivery_day'].size):
    days.append(df_delivery['delivery_day'].iat[i].day)

for i in range(30):
    value = days.count(i + 1)
    amountDays.append(value)

# ---------- Instanciar los centros ---------- 
centros = []
for i in range(df_center['id'].size):
    centro = Centro(df_center['id'].iat[i], [df_center['latitude'].iat[i], df_center['longitude'].iat[i]])
    centros.append(centro)

# ---------- Instanciar los drivers ---------- 
drivers = []
for i in range(df_driver['id'].size):
    driver = Driver(df_driver['id'].iat[i], [df_driver['latitude'].iat[i], df_driver['longitude'].iat[i]])
    drivers.append(driver)

# ---------- Instanciar los ecommerce ---------- 
ecommerces = []
for i in range(df_ecommerce['id'].size):
    ecommerce = Ecommerce(df_ecommerce['id'].iat[i], [df_ecommerce['latitude'].iat[i], df_ecommerce['longitude'].iat[i]])
    ecommerces.append(ecommerce)

# ----------  Instanciar los paquetes ---------- 
paquetes = []
for i in range(df_delivery['id'].size):
    paquete = Paquete(df_delivery['id'].iat[i], df_delivery['weight (kg)'].iat[i], [df_delivery['latitude'].iat[i], df_delivery['longitude'].iat[i]], df_delivery['x1 (largo en cm)'].iat[i], df_delivery['x2 (ancho en cm)'].iat[i], df_delivery['x3 (alto en cm)'].iat[i], df_delivery['delivery_day'].iat[i].day, df_delivery['e-commerce_id'].iat[i])
    paquetes.append(paquete)

# ---------- Paquetes dia 1 ----------
paquetes_dia_1 = paquetes[:amountDays[0]]   

# ---------- Agregar paquetes a los ecommerce para el dia 1 ----------
for paquete in paquetes_dia_1:
    for ecommerce in ecommerces:
        if paquete.ecommerce == ecommerce.id:
            ecommerce.agregar_paquete(paquete)


# ---------- Creamos el mapa ----------
coordinate_center = [-33.4369436, -70.634449]
m = folium.Map(location=(coordinate_center[0], coordinate_center[1]))
# folium.CircleMarker(coordinate_center, color='red', radius=5, fill=True).add_to(m)


# --------- Ordenamos los driver por cercania a un punto ------------------- 
driver_order = []
driver_id_order = []


for j in range(len(drivers)):
    distance = 1000000
    for i in range(len(drivers)):
        if drivers[i].id not in driver_id_order:
            if distance >= geopy.distance.geodesic(coordinate_center, drivers[i].origen).km:
                distance = geopy.distance.geodesic(coordinate_center, drivers[i].origen).km
                driver = drivers[i]

    driver_id_order.append(driver.id)
    driver_order.append(driver)

drivers = driver_order

drivers.reverse()

# -------- Comenzamos a simular ---------- 
ecommerce_visited = []
centro = centros[3].ubicacion

for j in range(len(drivers)):
    route = []

    distance = 100000000000

    for i in range(len(ecommerces)):
        if ecommerces[i].id not in ecommerce_visited:
            if drivers[j].peso < 450 and drivers[j].volumen < 2:
                if distance >= geopy.distance.geodesic(drivers[j].origen, ecommerces[i].ubicacion).km:
                    distance = geopy.distance.geodesic(drivers[j].origen, ecommerces[i].ubicacion).km
                    ecommerce = ecommerces[i]

    # Agregamos punto a la ruta
    drivers[j].agregar_ecommerce(ecommerce)
    ecommerce_visited.append(ecommerce.id)

    if j < 12:
        n = 6
    else:
        n = 5
    while len(drivers[j].ruta) < n:
        distance = 100000
        # Guardamos la minima distancia entre los puntos
        for i in range(len(ecommerces)):
            # Revisamos si el nodo ya esta en la ruta
            if ecommerces[i].id not in ecommerce_visited:
                # Revisamos condicion de peso y dimensiones
                if drivers[j].peso < 450 and drivers[j].volumen < 2:
                    if distance >= geopy.distance.geodesic(drivers[j].ruta[-1], ecommerces[i].ubicacion).km:
                        distance = geopy.distance.geodesic(drivers[j].ruta[-1], ecommerces[i].ubicacion).km
                        ecommerce = ecommerces[i] 
        # Add to route 
        drivers[j].agregar_ecommerce(ecommerce)
        ecommerce_visited.append(ecommerce.id)
    
    # Agrego la ubicacion inical del driver y la bodega
    drivers[j].ruta.insert(0, drivers[j].origen)
    drivers[j].ruta.append(centro)

# ----- Generamos los colores --------
colors = generate_colors(len(drivers))


best_distance = calculate_distance(drivers)
# print(best_distance)

# --------------------------------------------------------------------------------------
#                     Mejorar aleatoriamente el caso base

# driver_improve = improve_route_aleatory(drivers, ecommerces, best_distance)
# best_distance = calculate_distance(driver_improve[0])
# plot_improvement(driver_improve[1], driver_improve[2], 'Aleatory improvement', driver_improve[3])


# --------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------
#                                   2 OPT
# for d in drivers:
#     d.ruta = opt2(d.ruta)
# best_distance = calculate_distance(drivers)
# print(f'Best distance with 2opt ---> {best_distance}')


# --------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------
#                                   SWAP
# driver_improve = swap_ecommerce(drivers, ecommerces, best_distance)
# driver_improve = swap_ecommerce(driver_improve[0], ecommerces, best_distance, driver_improve[3], driver_improve[1], driver_improve[2])
# plot_improvement(driver_improve[1], driver_improve[2], 'Aleatory improvement and Swap', driver_improve[3])

# --------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------
#                  Mejorar aleatoriamente el caso base y  SWAP
# driver_improve = improve_route_aleatory(drivers, ecommerces, best_distance)
# best_distance = calculate_distance(driver_improve[0])
# print(f'CHANGE METHODD best distance {best_distance}')
# driver_improve = swap_ecommerce(driver_improve[0], ecommerces, best_distance, driver_improve[3], driver_improve[1], driver_improve[2])
# plot_improvement(driver_improve[1], driver_improve[2], 'Aleatory improvement and Swap', driver_improve[3])

# --------------------------------------------------------------------------------------
#                  DRIVER IMPROVE CHOOSING DRIVERS WITH MORE AND LESS TIME
driver_improve = improve_route_aleatory(drivers, ecommerces, best_distance)
drivers = driver_improve[0]

print()
print('TIEMPOOOO')
print()
driver_improve = improve_route_min_max_time(drivers, ecommerces, best_distance)
best_distance = calculate_distance(driver_improve)
#print(f'BEST DISTANCE = {best_distance}')
print('BEST DISTANCE = {}'.format(best_distance))
for d in drivers:
    #print(f'{d.id} ---- tiempo {d.tiempo}')
    print('{} ---- tiempo {}'.format(d.id, d.tiempo))



# ----------------------------------------------------------------------------
# Imprimir tiempos

# t_prom = 0
# d_prom = 0
# for d in driver_improve:
#     dis = distance_driver(d)
#     tiempo_recoleccion = (dis/30)*60
#     print(f'{d.id} ---- Distancia {dis} ---- tiempo {d.tiempo + tiempo_recoleccion}')
#     t_prom += d.tiempo + tiempo_recoleccion
#     d_prom += dis
#     print()
# print(f'Tiempo promedio = {t_prom/18}')
# print(f'Distancia promedio = {d_prom/18}')

# g = folium.Map(location=coordinate_center)
# for i in range(len(driver_improve)):
#     if i == 0:
#         folium.CircleMarker(driver_improve[i].origen, color='black', radius=4, fill=True).add_to(g)
#         folium.PolyLine(driver_improve[i].ruta, color=colors[i], weight=3, opacity=1).add_to(g)
#     elif i == len(drivers) - 1:
#         folium.CircleMarker(driver_improve[i].origen, color='black', radius=4, fill=True).add_to(g)
#         folium.PolyLine(driver_improve[i].ruta, color=colors[i], weight=3, opacity=1).add_to(g)
# g.save("simulation/maps/ecommerce_reverse_aleatory_swap_2drivers.html")

contador_driver = 1
cantidad_paquetes = 0
lista_distancias_paquetes = []

# iteracion sobre la lista drivers
for driver in drivers:
    print("PAQUETES DRIVER " + str(contador_driver))
    #Creo una lista con las coordenadas que debe recorrer el driver instanciando driver.ruta
    driver_ruta = driver.ruta
    print("Cantidad de coordenadas: " + str(len(driver_ruta)))
    driver_ruta.pop(0)
    largo = len(driver_ruta)
    print("Cantidad de paquetes por driver: " + str(largo-1))
    cantidad_paquetes += (largo-1)
    contador = 0

    #while va iterando sobre cada paquete que tenga el driver
    while contador < largo-1:
        distance_total = 0
        #for va calculando la distancia total que recorre el paquete 
        # desde que se recoge hasta que llega a destino final.
        for i in range(contador, len(driver_ruta) - 1):
            coord1 = driver_ruta[i]
            coord2 = driver_ruta[i + 1]
            distance = geopy.distance.distance(coord1, coord2).km
            #suma la distancia por tramo que va recorriendo el paquete
            distance_total += distance
        print("Distancia paquete " + str(contador + 1) + ": " + str(distance_total) + " km")
        lista_distancias_paquetes.append(distance_total)
        contador += 1
        distance_total = 0
    contador_driver += 1


suma = 0
for element in lista_distancias_paquetes:
    suma += element

promedio = suma/len(lista_distancias_paquetes)

print("Suma total distancias poaquetes: " + str(suma))
print("Cantidad total de paquetes: " + str(len(lista_distancias_paquetes)))
print("Promedio distancia recorrida por paquete: " + str(promedio) + " kms")






    
