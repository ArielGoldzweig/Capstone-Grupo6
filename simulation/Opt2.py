import geopy.distance
import pandas as pd
import random
import folium
from copy import deepcopy
from folium.features import DivIcon
from clases import Driver, Paquete, Ecommerce, Centro
from Opt2_function import opt2, distance_driver
from funciones import calculate_distance, generate_colors
import time


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
paquetes_dia_1 = paquetes[:amountDays[0]]   

# ---------- Agregar paquetes a los ecommerce para el dia 1 ----------
for paquete in paquetes_dia_1:
    for ecommerce in ecommerces:
        if paquete.ecommerce == ecommerce.id:
            ecommerce.agregar_paquete(paquete)


# ------------ Simular -------------------
best_distance = float('inf') 
drivers_copy = deepcopy(drivers)


t_end = time.time() + 60 * 5

while time.time() < t_end:

    elementos = [i for i in range(102)]
    lista_elementos = []
    i = 0
    for d in drivers:
        if i < 12:
            elem = random.sample(elementos, 6)
        else:
            elem = random.sample(elementos, 5)
        lista_elementos.append(elem)
        for e in elem:
            d.agregar_ecommerce(ecommerces[e])
            elementos.remove(e)
        i+=1


    for d in drivers:
        if d.peso <= 450 and d.volumen <= 2:
            d.ruta.insert(0, d.origen)
            d.ruta.append(centros[3].ubicacion)
            cur_distance = distance_driver(d)
            d.ruta = opt2(d.ruta)
            new_distance = distance_driver(d)
        # print(f'La distancia del driver {d.id} era {cur_distance} y ahora es {new_distance} {d.peso} {d.volumen}')

    if best_distance > calculate_distance(drivers):
        best_distance = calculate_distance(drivers)
        drivers_copy = deepcopy(drivers)

    for d in drivers:
        d.peso = 0
        d.ruta = []
        d.volumen = 0
        d.tiempo = 0


print(f'Best Distance {best_distance}')
# for d in drivers_copy:
#     distance = distance_driver(d)
#     print(f'{d.id} --> tiempo de {d.tiempo} y distancia {distance}')
t_prom = 0
d_prom = 0
for d in drivers_copy:
    dis = distance_driver(d)
    tiempo_recoleccion = (dis/30)*60
    print(f'{d.id} ---- Distancia {dis} ---- tiempo {d.tiempo + tiempo_recoleccion}')
    t_prom += d.tiempo + tiempo_recoleccion
    d_prom += dis
    print()
print(f'Tiempo promedio = {t_prom/18}')
print(f'Distancia promedio = {d_prom/18}')

# -------- Guardamos ruta en TXT ------------
with open(r'simulation/txt/ruta_aleatorio_2opt.txt', 'w') as fp:
    for driver in drivers_copy:
        fp.write("%s " % driver.ruta)
        fp.write("\n")

# ----- Generamos los colores --------
colors = generate_colors(len(drivers))

# ------ Graficamos los puntos --------------
# ---------- Creamos el mapa ----------
# coordinate_center = [-33.4369436, -70.634449]
# m = folium.Map(location=coordinate_center)
# g = folium.Map(location=coordinate_center)
# for i in range(len(drivers_copy)):
#     folium.CircleMarker(drivers_copy[i].origen, color='black', radius=4, fill=True).add_to(m) 
#     folium.PolyLine(drivers_copy[i].ruta, color=colors[i], weight=3, opacity=1).add_to(m)

# for i in range(len(drivers_copy)):
#     if i == 0:
#         folium.CircleMarker(drivers_copy[i].origen, color='black', radius=4, fill=True).add_to(g)
#         folium.PolyLine(drivers_copy[i].ruta, color=colors[i], weight=3, opacity=1).add_to(g)
#     elif i == len(drivers) - 1:
#         folium.CircleMarker(drivers_copy[i].origen, color='black', radius=4, fill=True).add_to(g)
#         folium.PolyLine(drivers_copy[i].ruta, color=colors[i], weight=3, opacity=1).add_to(g)

# m.save("simulation/maps/ruta_aleatoria_2opt.html")
# g.save("simulation/maps/ruta_aleatoria_2opt_2drivers.html")