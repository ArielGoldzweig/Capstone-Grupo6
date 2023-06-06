import math
import geopy.distance
import random
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
            d.tiempo += random.randint(8, 15)
        tiempo_recoleccion = (dis/50)*60
        d.tiempo += tiempo_recoleccion
    drivers.sort(key=lambda x: x.tiempo)
    return drivers


def best_removal(driver, ecommerces):
    print()
    print(111111, driver.ruta)
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
    print()
    print(f'Se ha eliminado {value_return}')
    print()
    driver.peso -= weight
    driver.volumen -= volume
    driver.tiempo -= random.randint(8, 15)
    driver.ruta = min_distance_gurobi(driver)

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
    print()
    print(f'Al driver {driver_take.id} se le ha agrego {new_point} y la distancia aumento en {min_increment_distance}')
    print()
    driver_take.peso += weigth
    driver_take.volumen += volume
    driver_take.tiempo += random.randint(8, 15)