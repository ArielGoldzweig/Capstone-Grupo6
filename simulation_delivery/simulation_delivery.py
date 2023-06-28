import geopy.distance
import pandas as pd
import random
import folium
from folium.features import DivIcon
from clases import Driver, Paquete, Ecommerce, Centro
from funciones import calculate_distance, distance_driver, improve_route_aleatory, plot_improvement, generate_colors, time_drivers_delivery, order_drivers_time


# ------------- Cargar los datos --------------

df_delivery = pd.read_excel("datos/deliveries_data.xlsx")
df_driver = pd.read_excel("datos/driver_origins_data.xlsx")
df_center = pd.read_excel("datos/centers_data.xlsx")
df_ecommerce = pd.read_excel("datos/e-commerce_data.xlsx")


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

# dia = 2
# index = 0
# for i in range(dia):
#     index += amountDays[i]

# paquetes_dia = paquetes[index:index+amountDays[dia]]
paquetes_dia = paquetes[:amountDays[0]]   

# ---------- Agregar paquetes a los ecommerce para el dia 1 ----------
for paquete in paquetes_dia:
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
            if distance >= geopy.distance.geodesic(centros[-1].ubicacion, drivers[i].origen).km:
                distance = geopy.distance.geodesic(centros[-1].ubicacion, drivers[i].origen).km
                driver = drivers[i]

    driver_id_order.append(driver.id)
    driver_order.append(driver)

drivers = driver_order

drivers.reverse()


# -------- Comenzamos a simular ---------- 
paquetes_delivered = []
centro = centros[3].ubicacion

for j in range(len(drivers)):
    route = []

    distance = 100000000000

    for i in range(len(paquetes_dia)):
        if paquetes_dia[i].id not in paquetes_delivered:
            if drivers[j].peso < 450 and drivers[j].volumen < 2:
                if distance >= geopy.distance.geodesic(drivers[j].origen, paquetes_dia[i].destino).km:
                    distance = geopy.distance.geodesic(drivers[j].origen, paquetes_dia[i].destino).km
                    paquete = paquetes_dia[i]

    # Agregamos punto a la ruta
    drivers[j].agregar_paquete(paquete)
    paquetes_delivered.append(paquete.id)

    if j < 6:
        n = 22
    else:
        n = 50
    while len(drivers[j].ruta) < n:
        distance = 100000
        # Guardamos la minima distancia entre los puntos
        for i in range(len(paquetes_dia)):
            # Revisamos si el nodo ya esta en la ruta
            if paquetes_dia[i].id not in paquetes_delivered:
                # Revisamos condicion de peso y dimensiones
                if drivers[j].peso < 450 and drivers[j].volumen < 2:
                    if distance >= geopy.distance.geodesic(drivers[j].ruta[-1], paquetes_dia[i].destino).km:
                        distance = geopy.distance.geodesic(drivers[j].ruta[-1], paquetes_dia[i].destino).km
                        paquete = paquetes_dia[i] 
        # Add to route 
        drivers[j].agregar_paquete(paquete)
        paquetes_delivered.append(paquete.id)
    
    # Agrego la ubicacion inical del driver y la bodega
    drivers[j].ruta.insert(0, centro)
    drivers[j].ruta.append(drivers[j].origen)

# # # ----- Generamos los colores --------
# # colors = generate_colors(len(drivers))

def remove(driver, deliveries):
    distance = 0
    coord = None
    for i in range(1, len(driver.ruta)-1):
        dis = geopy.distance.geodesic(driver.ruta[i], driver.ruta[i+1]).km + geopy.distance.geodesic(driver.ruta[i], driver.ruta[i-1]).km
        if distance < dis:
            distance = dis
            coord = driver.ruta[i]
    
    if coord != None:
        for d in deliveries:
            if d.destino == coord:
                del_remove = d
        driver.eliminar_paquete(del_remove)
        return del_remove
    return None

drivers = time_drivers_delivery(drivers)

not_asign_list = []
for d in drivers:
    while d.tiempo > 360:
        drivers = time_drivers_delivery(drivers)
        ecom = remove(d, paquetes_dia)
        if ecom == None:
            break
        not_asign_list.append(ecom)

for d in drivers:
    if d.tiempo > 360:
        drivers = time_drivers_delivery(drivers)
        ecom = remove(d, paquetes_dia)
        if ecom == None:
            break
        not_asign_list.append(ecom)

print('Paquetes no entregados', not_asign_list, len(not_asign_list))
best_distance = calculate_distance(drivers)
print(f'DIstancia Total {best_distance}')

drivers = order_drivers_time(drivers)
paquetes = 0
for d in drivers:
    dis = distance_driver(d)
    paquetes += (len(d.ruta) - 2)
    print(f'{d.id} --> Distancia {dis} ---- Tiempo {d.tiempo} ---- N Paquetes {len(d.ruta) - 2} ---- Peso {round(d.peso, 2)} ---- Dimensiones {round(d.volumen, 2)} ---- Holgura tiempo {round(360-d.tiempo, 2)}')
print(f'Paquetes entregados {paquetes}')

# --------------------------------------------------------------------------------------
#                     Mejorar aleatoriamente el caso base

# driver_improve = improve_route_aleatory(drivers, paquetes, best_distance)
# best_distance = calculate_distance(driver_improve[0])
# # plot_improvement(driver_improve[1], driver_improve[2], 'Aleatory improvement', driver_improve[3])

# colors = generate_colors(len(drivers))
# # ---------- Creamos el mapa ----------
# coordinate_center = [-33.4369436, -70.634449]
# m = folium.Map(location=coordinate_center)

# drivers = driver_improve[0]

# for i in range(len(drivers)):
#     folium.CircleMarker(drivers[i].origen, color='black', radius=4, fill=True).add_to(m) 
#     folium.PolyLine(drivers[i].ruta, color=colors[i], weight=3, opacity=1).add_to(m)


# # m.save("simulation_delivery/maps/improve_aleatory.html")

#  # ----------------------------------------------------------------------------
# # Imprimir tiempos

# t_prom = 0
# d_prom = 0
# for d in drivers:
#     dis = distance_driver(d)
#     tiempo_recoleccion = (dis/30)*60
#     print(f'{d.id} ---- Distancia {dis} ---- tiempo {d.tiempo + tiempo_recoleccion}')
#     t_prom += d.tiempo + tiempo_recoleccion
#     d_prom += dis
#     print()
# print(f'Tiempo promedio = {t_prom/18}')
# print(f'Distancia promedio = {d_prom/18}')