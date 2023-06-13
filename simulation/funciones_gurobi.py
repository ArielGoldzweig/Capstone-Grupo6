import math
import geopy.distance
import random
import time
import numpy as np
from copy import deepcopy

import gurobipy as gp
from gurobipy import GRB

import networkx as nx
import matplotlib.pyplot as plt


def min_distance_gurobi(d):
    n = len(d.ruta)
    G = nx.complete_graph(n, nx.DiGraph())

    my_pos = { i : ( d.ruta[i][0], d.ruta[i][1] ) for i in G.nodes } 

    for i,j in G.edges:
        (x1,y1) = my_pos[i]
        (x2,y2) = my_pos[j]
        # Cambiar distancia en grafo CAMBIAR
        G.edges[i,j]['length'] = math.sqrt( (x1-x2)**2 + (y1-y2)**2 )


    m = gp.Model()
    x = m.addVars(G.edges,vtype=GRB.BINARY)

    m.setObjective( gp.quicksum( G.edges[i,j]['length'] * x[i,j] for i,j in G.edges ), GRB.MINIMIZE )

    # Entrar a cada ciudad una vez excepto la primera
    m.addConstrs( gp.quicksum( x[i,j] for i in G.predecessors(j) ) == 1 for j in G.nodes if j != 0)
    m.addConstrs( gp.quicksum( x[i,j] for i in G.predecessors(j) ) == 0 for j in G.nodes if j == 0)

    # Salir de cada ciudad una vez excepto la ultima
    m.addConstrs( gp.quicksum( x[i,j] for j in G.successors(i) ) == 1 for i in G.nodes if i != n-1)
    m.addConstrs( gp.quicksum( x[i,j] for j in G.successors(i) ) == 0 for i in G.nodes if i == n-1)

    u = m.addVars( G.nodes )

    m.addConstrs( u[i] - u[j] + (n-1) * x[i,j] + (n-3) * x[j,i] <= n-2 for i,j in G.edges if j != 0 if (i,j) in G.edges)

    # Agregar GAP de 5%
    m.setParam('MIPGap', 0.05)

    m.optimize()

    tour_edges = [ e for e in G.edges if x[e].x > 0.5 ]
    # nx.draw(G.edge_subgraph(tour_edges), pos=my_pos)
    # plt.show()


    # Obtenemos un orden para la ruta a partir de la min distancia
    order_route = [0]
    value = 0
    while len(order_route) < len(d.ruta):
        for e in tour_edges:
            if e[0] == value:
                order_route.append(e[1])
                value = e[1]

    new_route = []
    for pos in order_route:
        new_route.append(d.ruta[pos])
    
    d.ruta = new_route


def distance_driver(driver):
    distance = 0
    for j in range(len(driver.ruta)):
        if j != len(driver.ruta) - 1:
            distance += geopy.distance.geodesic(driver.ruta[j], driver.ruta[j+1]).km
    return distance


def time_drivers(drivers):
    for d in drivers:
        dis = distance_driver(d)
        d.tiempo = 0
        for k in range(len(d.ruta) - 2):
            d.tiempo += np.random.uniform(8, 15)
        tiempo_recoleccion = (dis/50)*60
        d.tiempo += tiempo_recoleccion
    drivers.sort(key=lambda x: x.tiempo)
    return drivers

def time_drivers_delivery(drivers):
    for d in drivers:
        dis = distance_driver(d)
        d.tiempo = 0
        for k in range(len(d.ruta) - 2):
            d.tiempo += np.random.uniform(4, 8)
        tiempo_recoleccion = (dis/30)*60
        d.tiempo += tiempo_recoleccion
    drivers.sort(key=lambda x: x.tiempo)
    return drivers

def order_drivers_time(drivers):
    drivers.sort(key=lambda x: x.tiempo)
    return drivers


def best_removal(driver, ecommerces):
    original_distance = distance_driver(driver)
    original_route = deepcopy(driver.ruta)
    best_diference_length = 0

    for k in range(1, len(driver.ruta)-1):
        driver.ruta.pop(k)
        min_distance_gurobi(driver)
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
    min_distance_gurobi(driver)

    return value_return, weight, volume


def best_insert(drivers, new_point, weigth, volume):
    min_increment_distance = float('inf')
    best_list = []
    while len(best_list) < 4:
        for d in drivers:
            if d.tiempo < 90:
                new_weigth = 0
                new_volume = 0
                # if d != driver and d not in best_list:
                if d not in best_list:
                    new_weigth = d.peso + weigth
                    new_volume = d.volumen + volume
                    if new_weigth < 450 and new_volume < 2 and len(d.ruta) < 9:
                        original_distance = distance_driver(d)
                        d.ruta.insert(-1, new_point)
                        min_distance_gurobi(d)
                        new_distance = distance_driver(d)
                        difference_distance = new_distance - original_distance
                        if(difference_distance < min_increment_distance):
                            # dis = difference_distance - min_increment_distance
                            min_increment_distance = difference_distance
                            best_driver = d
                            
                        d.ruta.remove(new_point)
                    
        best_list.append(best_driver)

    driver_take = random.choice(best_list)
    driver_take.ruta.insert(-1, new_point)
    min_distance_gurobi(driver_take)
    driver_take.peso += weigth
    driver_take.volumen += volume
    driver_take.tiempo += random.randint(8, 15)

    return driver_take


def remove_until_time(drivers, ecommerces):
    drivers = order_drivers_time(drivers)
    not_asign_list = []
    for d in drivers:
        if d.tiempo > 90:
            while d.tiempo > 90:
                point, weight, volume = best_removal(d, ecommerces)
                not_asign_list.append([point, weight, volume])
    return not_asign_list


def insert_if_time(drivers, not_asign_list):
    lista_driver = deepcopy(drivers)
    
    for i in range(4):
        no_insert = []
        if len(not_asign_list) > 0:
            for new_point, weigth, volume in not_asign_list:
                driver_take = best_insert(drivers, new_point, weigth, volume)
                if driver_take.tiempo > 100:
                    drivers = deepcopy(lista_driver)
                    no_insert.append([new_point, weigth, volume])
                    driver_take.peso -= weigth
                    driver_take.volumen -= volume
                    driver_take.tiempo -= random.randint(8, 15)
                    min_distance_gurobi(driver_take)
                else:
                    lista_driver = deepcopy(drivers)
            not_asign_list = deepcopy(no_insert)
    
    return not_asign_list


def remove_insert_if_time(drivers, ecommerces):
    for i in range(10):
        lista_drivers = time_drivers(drivers)
        not_asign_list = remove_until_time(lista_drivers, ecommerces)
        if len(not_asign_list) > 0:
            lista_no = insert_if_time(lista_drivers, not_asign_list)
        else:
            return lista_no
    return lista_no

def have_time(drivers, ecommerces):
    order_drivers_time(drivers)

    
    driver_yes = drivers[0]
    driver_no = drivers[-1]

    new_point, weight, volume = best_removal(driver_no, ecommerces)
    min_distance_gurobi(driver_no)
    driver_yes.ruta.insert(-1, new_point)
    driver_yes.peso += weight
    driver_yes.tiempo += random.randint(8, 15)
    driver_yes.volumen += volume
    min_distance_gurobi(driver_yes)



def improve_route_min_max_time(drivers, ecommerces):

    t_end = time.time() + 60*0.1

    while time.time() < t_end:
        try:
            
            # drivers = time_drivers(drivers)
            drivers = order_drivers_time(drivers)
            driver_give = drivers[-1]

            if len(driver_give.ruta) >= 4:
                
                pos, weight, volume = best_removal(driver_give, ecommerces)
                best_insert(drivers[0:3], driver_give, pos, weight, volume)

        except:
            print("El driver ya no tiene ruta")
        
    return drivers


def improve_have_time(drivers, ecommerces):

    t_end = time.time() + 60*0.1

    while time.time() < t_end:
        try:

            # drivers = time_drivers(drivers)
            drivers = order_drivers_time(drivers)
            have_time(drivers, ecommerces)

        except:
            print("El driver ya no tiene ruta")
        
    return drivers
