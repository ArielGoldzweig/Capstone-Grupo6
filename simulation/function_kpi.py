import geopy.distance
from geopy.distance import geodesic


def calculate_kpi_package(drivers): #drivers es una lista de drivers
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

    promedio = suma/len(lista_distancias_paquetes) #(km)
    tiempo = promedio / 30 #el 30 corresponde a la velocidad promedio a lo que manejan los drivers (30 km/hr)

    mayor_distancia = max(lista_distancias_paquetes)
    mayor_tiempo = mayor_distancia/30 #30 corresponde a la velocidad promedio
    menor_distancia = min(lista_distancias_paquetes)
    menor_tiempo = menor_distancia/30

    print(" ")
    print("Suma total distancias paquetes: " + str(suma) + " kms")
    print("Cantidad total de paquetes: " + str(len(lista_distancias_paquetes)))
    print("KPI --> PROMEDIO DISTANCIA RECORRIDA POR PAQUETE: " + str(promedio) + " KMS")
    print("KPI --> PROMEDIO TIEMPO RECORRIDO POR PAQUETE: " + str(tiempo) + " HR")
    print("Mayor distancia que recorre un paquete: " + str(mayor_distancia) + " KMS")
    print("Menor distancia que recorre un paquete: " + str(menor_distancia) + " KMS")
    print("Mayor tiempo que recorre un paquete: " + str(mayor_tiempo) + " HR")
    print("Menor tiempo que recorre un paquete: " + str(menor_tiempo) + " HR")    




                
