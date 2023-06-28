import pandas as pd
import geopy.distance

from clases import Driver, Paquete, Ecommerce, Centro

import gurobipy as gp
from gurobipy import GRB

import networkx as nx
import matplotlib.pyplot as plt

from funciones import calculate_distance, map_distance
from Opt2_function import opt2
from funciones_gurobi import min_distance_gurobi, remove_insert_if_time, time_drivers_delivery, best_insert_delivery, remove_until_time, distance_driver


# ------------- Cargar los datos --------------

df_delivery = pd.read_excel("datos/deliveries_data.xlsx")
df_driver = pd.read_excel("datos/driver_origins_data.xlsx")
df_center = pd.read_excel("datos/centers_data.xlsx")
df_ecommerce = pd.read_excel("datos/e-commerce_data.xlsx")

f = open("simulation/txt/Delivery.txt", "a")



# # ------------- Separar por dias --------------
days = []
amountDays = []

for i in range(df_delivery['delivery_day'].size):
    days.append(df_delivery['delivery_day'].iat[i].day)

for i in range(30):
    value = days.count(i + 1)
    amountDays.append(value)


dia = 5
index = 0
for i in range(dia):
    index += amountDays[i]

df_delivery_day = df_delivery[index:index+amountDays[dia]]

f.write('\n')
f.write(f'Simulacion para dia {dia}')
f.write('\n\n')

# Creamos una columna que son las dimensiones en m3
df_delivery_day['dimensiones'] = df_delivery_day['x1 (largo en cm)']/100 * df_delivery_day['x2 (ancho en cm)']/100 * df_delivery_day['x3 (alto en cm)']/100 


lista_volumen = df_delivery_day['dimensiones'].tolist()
lista_peso = df_delivery_day['weight (kg)'].tolist()


# Cantidad de Drivers y Ecommerces
numero_puntos = df_delivery_day['longitude'].size
numero_drivers = df_driver['longitude'].size

puntos = range(numero_puntos)
drivers = range(numero_drivers)

# Distancia entre punto de inicio de cada driver y ecommerce
distancia = []


list_drivers = df_driver[['latitude', 'longitude']].values.tolist()
list_delivery = df_delivery_day[['latitude', 'longitude']].values.tolist()

for pos_driver in list_drivers:
    lista_dis = []
    for pos_delivery in list_delivery:
        lista_dis.append(geopy.distance.geodesic(pos_driver, pos_delivery).km)
    distancia.append(lista_dis)


WMAX = 450  # peso maximo por conductor
VMAX = 2  # volumen maximo por conductor
NMIN = 35   # paquetes minimos
NMAX = 50   # paquetes maximos


## No tocar ##

model = gp.Model()
x = model.addVars(drivers, puntos, vtype=GRB.BINARY)

for k in drivers:
    model.addConstr(gp.quicksum(x[k, i] * lista_volumen[i] for i in puntos) <= VMAX)
    model.addConstr(gp.quicksum(x[k, i] * lista_peso[i] for i in puntos) <= WMAX)
    model.addConstr(gp.quicksum(x[k, i] for i in puntos) >= NMIN)
    model.addConstr(gp.quicksum(x[k, i] for i in puntos) <= NMAX)

for i in puntos:
    model.addConstr(gp.quicksum(x[k, i] for k in drivers) == 1)

model.setObjective(gp.quicksum(x[k, i] * distancia[k][i] for k in drivers for i in puntos), GRB.MINIMIZE)


model.update()


model.optimize()

# Instanciamos las clases

# ---------- Instanciar los centros ---------- 
lista_centros = []
for i in range(df_center['id'].size):
    centro = Centro(df_center['id'].iat[i], [df_center['latitude'].iat[i], df_center['longitude'].iat[i]])
    lista_centros.append(centro)

# ---------- Instanciar los drivers ---------- 
lista_drivers = []
for i in range(df_driver['id'].size):
    d = Driver(df_driver['id'].iat[i], [df_driver['latitude'].iat[i], df_driver['longitude'].iat[i]])
    lista_drivers.append(d)

# ---------- Instanciar los ecommerce ---------- 
lista_ecommerces = []
for i in range(df_ecommerce['id'].size):
    ecommerce = Ecommerce(df_ecommerce['id'].iat[i], [df_ecommerce['latitude'].iat[i], df_ecommerce['longitude'].iat[i]])
    lista_ecommerces.append(ecommerce)

# ----------  Instanciar los paquetes ---------- 
lista_deliveries = []
for i in range(df_delivery_day['id'].size):
    paquete = Paquete(df_delivery_day['id'].iat[i], df_delivery_day['weight (kg)'].iat[i], [df_delivery_day['latitude'].iat[i], df_delivery_day['longitude'].iat[i]], df_delivery_day['x1 (largo en cm)'].iat[i], df_delivery_day['x2 (ancho en cm)'].iat[i], df_delivery_day['x3 (alto en cm)'].iat[i], df_delivery_day['delivery_day'].iat[i].day, df_delivery_day['e-commerce_id'].iat[i])
    lista_deliveries.append(paquete)


# Agregamos los ecommmerce a la ruta de los drivers
for i in range(len(lista_drivers)):
    for punto in puntos:
        if x[i, punto].X == 1:
            lista_drivers[i].agregar_delivery(lista_deliveries[punto])
    lista_drivers[i].ruta.append(lista_centros[-1].ubicacion)
    lista_drivers[i].ruta.insert(0, lista_drivers[i].origen)


for d in lista_drivers:
    min_distance_gurobi(d)


lista_drivers = time_drivers_delivery(lista_drivers)
f.write('\n')
not_asign = remove_insert_if_time(lista_drivers, lista_ecommerces, lista_deliveries, 360, 'd')

f.write('\n')
f.write(f'Distancia total recorrida {calculate_distance(lista_drivers)}')
f.write('\n')

f.write(f'Paquetes no entregados {len(not_asign)}')
f.write('\n')



paquetes = 0
for d in lista_drivers:
    dis = distance_driver(d)
    paquetes += (len(d.ruta) - 2)
    f.write(f'{d.id} --> Distancia {dis} ---- Tiempo {d.tiempo} ---- N Paquetes {len(d.ruta) - 2} ---- Peso {round(d.peso, 2)} ---- Dimensiones {round(d.volumen, 2)} ---- Holgura tiempo {round(360-d.tiempo, 2)}')
    f.write('\n')

f.write('\n')
f.write(f'Cantidad de paquetes entregados {paquetes}')
f.write('\n')

f.write(f'--------------------------')
f.write('\n')
f.write('\n')
f.write('Ruta de cada driver')
f.write('\n')
for d in lista_drivers:
    f.write(f'{d.id} --> {d.ruta}')
    f.write('\n')

f.write(f'--------------------------')
f.close()
