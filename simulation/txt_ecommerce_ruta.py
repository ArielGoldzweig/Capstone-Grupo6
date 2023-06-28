import pandas as pd
import geopy.distance

from clases import Driver, Paquete, Ecommerce, Centro

import gurobipy as gp
from gurobipy import GRB

import networkx as nx
import matplotlib.pyplot as plt

from funciones import calculate_distance, map_distance
from Opt2_function import opt2
from funciones_gurobi import min_distance_gurobi, order_drivers_time, remove_insert_if_time, distance_driver
from function_kpi import calculate_kpi_package

# ------------- Cargar los datos --------------

df_delivery = pd.read_excel("datos/deliveries_data.xlsx")
df_driver = pd.read_excel("datos/driver_origins_data.xlsx")
df_center = pd.read_excel("datos/centers_data.xlsx")
df_ecommerce = pd.read_excel("datos/e-commerce_data.xlsx")

f = open("simulation/txt/Ecommerce.txt", "a")


# # ------------- Separar por dias --------------
days = []
amountDays = []

for i in range(df_delivery['delivery_day'].size):
    days.append(df_delivery['delivery_day'].iat[i].day)

for i in range(30):
    value = days.count(i + 1)
    amountDays.append(value)



dia = 29
index = 0
for i in range(dia):
    index += amountDays[i]



df_delivery = df_delivery[index:index+amountDays[dia]]
df_delivery['dimensiones'] = df_delivery['x1 (largo en cm)']/100 * df_delivery['x2 (ancho en cm)']/100 * df_delivery['x3 (alto en cm)']/100 


f.write('\n')
f.write('\n')
f.write(f'Simulacion para dia {dia}')
f.write('\n\n')

# ------ Craer dataframe con suma de dimensiones y peso
df_dim = df_delivery.groupby('e-commerce_id').agg({'dimensiones': ['count', 'sum'], 'weight (kg)': 'sum'})
df_dim.columns = ['count', 'dimension', 'weight']
list_dim = df_dim.values.tolist()

# Creamos lista con peso y volumen ecommerces
peso_total_punto = []
volumen_total_punto = []
for count, volumen, peso in list_dim:
    peso_total_punto.append(peso)
    volumen_total_punto.append(volumen)

# Cantidad de Drivers y Ecommerces
numero_puntos = df_ecommerce['longitude'].size
numero_drivers = df_driver['longitude'].size

puntos = range(numero_puntos)
drivers = range(numero_drivers)

# Distancia entre punto de inicio de cada driver y ecommerce
distancia = []

list_drivers = df_driver[['latitude', 'longitude']].values.tolist()
list_ecommerces = df_ecommerce[['latitude', 'longitude']].values.tolist()

for pos_driver in list_drivers:
    lista_dis = []
    for pos_ecommerce in list_ecommerces:
        lista_dis.append(geopy.distance.geodesic(pos_driver, pos_ecommerce).km)
    distancia.append(lista_dis)


WMAX = 450  # peso maximo por conductor
VMAX = 2  # volumen maximo por conductor
NMIN = 5   # paquetes minimos
NMAX = 7   # paquetes maximos


## No tocar ##

model = gp.Model()
x = model.addVars(drivers, puntos, vtype=GRB.BINARY)

for k in drivers:
    model.addConstr(gp.quicksum(x[k, i] * volumen_total_punto[i] for i in puntos) <= VMAX)
    model.addConstr(gp.quicksum(x[k, i] * peso_total_punto[i] for i in puntos) <= WMAX)
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
lista_paquetes = []
for i in range(df_delivery['id'].size):
    paquete = Paquete(df_delivery['id'].iat[i], df_delivery['weight (kg)'].iat[i], [df_delivery['latitude'].iat[i], df_delivery['longitude'].iat[i]], df_delivery['x1 (largo en cm)'].iat[i], df_delivery['x2 (ancho en cm)'].iat[i], df_delivery['x3 (alto en cm)'].iat[i], df_delivery['delivery_day'].iat[i].day, df_delivery['e-commerce_id'].iat[i])
    lista_paquetes.append(paquete)

# ---------- Paquetes dia 1 ----------
lista_deliveries = lista_paquetes[:amountDays[0]]   

# ---------- Agregar paquetes a los ecommerce para el dia 1 ----------
for paquete in lista_deliveries:
    for ecommerce in lista_ecommerces:
        if paquete.ecommerce == ecommerce.id:
            ecommerce.agregar_paquete(paquete)


# Agregamos los ecommmerce a la ruta de los drivers
for i in range(len(lista_drivers)):
    for punto in puntos:
        if x[i, punto].X == 1:
            lista_drivers[i].agregar_ecommerce(lista_ecommerces[punto])
    lista_drivers[i].ruta.append(lista_centros[-1].ubicacion)
    lista_drivers[i].ruta.insert(0, lista_drivers[i].origen)


for d in lista_drivers:
    min_distance_gurobi(d)



not_asign = remove_insert_if_time(lista_drivers, lista_ecommerces, lista_deliveries, 90, 'e')

f.write('\n')
paquetes_no_entregados = 0
for e in not_asign:
    paquetes_no_entregados += len(e.paquetes)

f.write('\n')
f.write(f'Distancia total recorrida {calculate_distance(lista_drivers)}')
f.write('\n')

f.write(f'Paquetes no entregados {paquetes_no_entregados}')
f.write('\n')


lista_drivers = order_drivers_time(lista_drivers)
paquetes = 0

for d in lista_drivers:
    dis = distance_driver(d)
    for e in d.ecommerce:
        paquetes += len(e.paquetes)
    f.write(f'{d.id} --> Distancia {dis} ---- Tiempo {d.tiempo} ---- N Paquetes {len(d.ruta) - 2} ---- Peso {round(d.peso, 2)} ---- Dimensiones {round(d.volumen, 2)} ---- Holgura tiempo {round(90-d.tiempo, 2)}')
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