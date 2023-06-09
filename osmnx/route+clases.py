import geopy.distance
import pandas as pd
import osmnx as ox
import networkx as nx
import random
import itertools
import folium
from folium.features import DivIcon
from copy import deepcopy

random.seed(343545)

peso_maximo = 450
volumen_maximo = 2

class Driver:
    def __init__(self, id, origen, ubicacion_actual):
        self.id = id
        self.peso_max = 450
        self.peso = 0
        self.volumen_max = 2
        self.volumen = 0
        self.origen = origen
        self.ruta = []
        self.ubicaion_actual = []

    def agregar_ecommerce(self, ecommerce):
        self.peso += ecommerce.peso
        self.volumen += ecommerce.volumen
        self.ruta.append(ecommerce.ubicacion)
        self.ubicacion_actual = ecommerce.ubicacion
    
    def eliminar_ecommerce(self, ecommerce):
        self.peso -= ecommerce.peso
        self.volumen -= ecommerce.volumen
        self.ruta.remove(ecommerce.ubicacion)
        self.ubicacion_actual = ecommerce.ubicacion


class Ecommerce:
    def __init__(self, id, ubicacion):
        self.id = id
        self.peso = 0
        self.volumen = 0
        self.ubicacion = ubicacion
        self.paquetes = []
        self.recogido = False

    def agregar_paquete(self, paquete):
        self.paquetes.append(paquete)
        self.peso += paquete.peso
        self.volumen += paquete.volumen
    
    def eliminar_paquete(self, paquete):
        self.paquetes.remove(paquete)
        self.peso -= paquete.peso
        self.volumen -= paquete.volumen
    
    def recoger(self):
        self.recogido = True

class Paquete:
    def __init__(self, id, peso, destino, x1,x2,x3, delivery_day, ecommerce):
        self.id = id
        self.peso = peso
        self.x1 = x1 / 100
        self.x2 = x2 / 100
        self.x3 = x3 / 100
        self.volumen = self.x1*self.x2*self.x3
        self.destino = destino
        self.dia = delivery_day
        self.ecommerce = ecommerce

class Centro:
    def __init__(self, id, ubicacion):
        self.id = id
        self.ubicacion = ubicacion


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

coordinate_center = [-33.4369436, -70.634449]


# instanciar los centros

centros = []
for i in range(df_center['id'].size):
    centro = Centro(df_center['id'].iat[i], [df_center['latitude'].iat[i], df_center['longitude'].iat[i]])
    centros.append(centro)

# instanciar los drivers 

drivers = []
for i in range(df_driver['id'].size):
    driver = Driver(df_driver['id'].iat[i], df_driver['latitude'].iat[i], df_driver['longitude'].iat[i])
    drivers.append(driver)

# instanciar los ecommerce

ecommerces = []
for i in range(df_ecommerce['id'].size):
    ecommerce = Ecommerce(df_ecommerce['id'].iat[i], [df_ecommerce['latitude'].iat[i], df_ecommerce['longitude'].iat[i]])
    ecommerces.append(ecommerce)

# instanciar los paquetes

paquetes = []
for i in range(df_delivery['id'].size):
    paquete = Paquete(df_delivery['id'].iat[i], df_delivery['weight (kg)'].iat[i], [df_delivery['latitude'].iat[i], df_delivery['longitude'].iat[i]], df_delivery['x1 (largo en cm)'].iat[i], df_delivery['x2 (ancho en cm)'].iat[i], df_delivery['x3 (alto en cm)'].iat[i], df_delivery['delivery_day'].iat[i].day, df_delivery['e-commerce_id'].iat[i])
    paquetes.append(paquete)


# paquetes dia 1

paquetes_dia_1 = paquetes[:amountDays[0]]   

# -------------------------------------------------------------------------

# Agregar paquetes a los ecommerce para el dia 1

for paquete in paquetes_dia_1:
    for ecommerce in ecommerces:
        if paquete.ecommerce == ecommerce.id:
            ecommerce.agregar_paquete(paquete)

# -------------------------------------------------------------------------

route_drivers_ecommerce = [
    [[-33.42475869783682, -70.61891438686266], [-33.42225103306093, -70.62423686702182], [-33.41804072178575, -70.63004838032934], [-33.41959484504883, -70.63717244522564], [-33.41906417517651, -70.64188176896492], [-33.42371884079868, -70.64125894640664], [-33.42507612353619, -70.64258599831957], [-33.42691073042271, -70.64415831944888], [-33.4539817210464, -70.61069318480818]],
    [[-33.45722836021753, -70.62438544407914], [-33.45300814597829, -70.62300812423292], [-33.44472149190693, -70.62222263019136], [-33.43536241228873, -70.63107898015966], [-33.43354910513401, -70.62734062089002], [-33.42941631825704, -70.62153410752785], [-33.42705967739409, -70.63248278616064], [-33.43451020093692, -70.64076610696773], [-33.4539817210464, -70.61069318480818]],
    [[-33.46013666537667, -70.62931733834137], [-33.46296153651627, -70.64126370220644], [-33.46897788151509, -70.63975194749847], [-33.47204426156802, -70.6395023423376], [-33.46935673947043, -70.64885867101242], [-33.47377070155471, -70.6627205089658], [-33.47653747259751, -70.6648393967031], [-33.48164142462833, -70.65482679504186], [-33.4539817210464, -70.61069318480818]],
    [[-33.4634739471992, -70.65173974688014], [-33.45675463531489, -70.64457749554776], [-33.44777992030463, -70.65402717921269], [-33.44255523923142, -70.66273985880713], [-33.44545612858779, -70.66843349034228], [-33.44279270425711, -70.6729228991528], [-33.44766500516289, -70.6752172599372], [-33.46039773073053, -70.67398694026748], [-33.4539817210464, -70.61069318480818]],
    [[-33.4133469072509, -70.65980346442899], [-33.41016826706196, -70.66344354190433], [-33.40612571206832, -70.67199957579226], [-33.40347661398336, -70.67358753877849], [-33.41478272146048, -70.6742437135735], [-33.41496462548562, -70.6731067333152], [-33.41766240678623, -70.67690725199964], [-33.41674155884687, -70.67944684094084], [-33.4539817210464, -70.61069318480818]],
    [[-33.45653392572637, -70.67544164389567], [-33.44522815834824, -70.69205562009128], [-33.44350646609591, -70.69390004498842], [-33.43816671587052, -70.68849544071024], [-33.43703424767286, -70.68493135713516], [-33.42277433459014, -70.67880556422887], [-33.42002884942843, -70.68485811750296], [-33.41443943634508, -70.68738264601713], [-33.4539817210464, -70.61069318480818]],
    [[-33.47143247178571, -70.61119989509753], [-33.49179685621576, -70.59517011891866], [-33.51362555647748, -70.58652885085768], [-33.56347864815567, -70.56050612499578], [-33.55281227134447, -70.66815747530303], [-33.52132423783303, -70.667832719485], [-33.51015932387511, -70.66037629317103], [-33.47258488163212, -70.68588283495964], [-33.4539817210464, -70.61069318480818]],
    [[-33.47865877907687, -70.64883335191256], [-33.4359600497046, -70.65382735061853], [-33.43461615917355, -70.6575511430273], [-33.43175178187915, -70.65847697847583], [-33.43314103093541, -70.66283437796147], [-33.42393744312063, -70.66329651644179], [-33.42574811057705, -70.6473484454851], [-33.41015098235179, -70.64057440015769], [-33.4539817210464, -70.61069318480818]],
    [[-33.4547994230244, -70.68177856856285], [-33.44131893637633, -70.70875807480459], [-33.42972331002353, -70.71702247619181], [-33.42389055938657, -70.71529153808049], [-33.42714952781416, -70.72358069130146], [-33.41172351784213, -70.73535204314098], [-33.40287427577779, -70.75911556209257], [-33.37921008584436, -70.75040888558641], [-33.4539817210464, -70.61069318480818]],
    [[-33.39966089929759, -70.6842984482419], [-33.39621398184207, -70.69356608627393], [-33.4104245282393, -70.69122758657889], [-33.41155714921368, -70.69624488379604], [-33.41999584236511, -70.70309171315336], [-33.40663129690812, -70.70903832605143], [-33.41484105662393, -70.67948895981704], [-33.41510871738915, -70.67919429954803], [-33.4539817210464, -70.61069318480818]],
    [[-33.40305370397851, -70.56314652160252], [-33.40520156005478, -70.5782452221826], [-33.40596600611256, -70.5922301943772], [-33.39638237927585, -70.60916095361034], [-33.3881622792935, -70.61198011629779], [-33.4539817210464, -70.61069318480818]],
    [[-33.47203031583582, -70.72389642030014], [-33.46870555407397, -70.71461401604897], [-33.54652694767388, -70.71945727408685], [-33.57557822073572, -70.73218574230273], [-33.45433606120825, -70.58555386524164], [-33.4539817210464, -70.61069318480818]],
    [[-33.37556001890029, -70.53998268769418], [-33.38946739734604, -70.59903888960336], [-33.41043552087503, -70.61599240287983], [-33.40753788433872, -70.62534312784236], [-33.4106915933427, -70.62919746252082], [-33.4539817210464, -70.61069318480818]],
    [[-33.34920223485847, -70.69221188547029], [-33.3512090204138, -70.68431301345639], [-33.3371310413377, -70.70265134737791], [-33.32238615870009, -70.71855257404529], [-33.29180024577838, -70.68971246279766], [-33.4539817210464, -70.61069318480818]],
    [[-33.56015803680171, -70.59316542172161], [-33.45311159946192, -70.5544374228378], [-33.42703703597657, -70.57993168269843], [-33.43336047747307, -70.60619302530729], [-33.4194025395777, -70.60645706294905], [-33.4539817210464, -70.61069318480818]],
    [[-33.51034443414655, -70.77580774678871], [-33.40631224916182, -70.65374228536189], [-33.40658158417009, -70.644099508857], [-33.39820692720235, -70.64349718484715], [-33.39765943103141, -70.64560259170514], [-33.4539817210464, -70.61069318480818]],
    [[-33.57125040135713, -70.56995081110463], [-33.40913937319159, -70.6307756375712], [-33.39566969010603, -70.64718196630001], [-33.3906616343177, -70.65618253716687], [-33.37661615187089, -70.66077264744143], [-33.4539817210464, -70.61069318480818]],
    [[-33.59470558033697, -70.70209182052085], [-33.37975999558638, -70.63581892182225], [-33.34537910208673, -70.63071147700214], [-33.32761600207031, -70.6096126339093], [-33.27097821915391, -70.68667313279227], [-33.4539817210464, -70.61069318480818]],
]



route_driver_class = []


for route_driver in route_drivers_ecommerce:
    route = []
    for i in range(len(route_driver)):
        if i == 0:
            for j in range(len(drivers)):
                if route_driver[i][0] == drivers[j].origen:
                    route.append(drivers[j])
        if i == len(route_driver) - 1:
            for k in range(len(centros)):
                if route_driver[i] == centros[k].ubicacion:
                    route.append(centros[k])
        for e in range(len(route_driver[i])):
            for w in range(len(ecommerces)):
                if route_driver[i] == ecommerces[w].ubicacion:
                    route.append(ecommerces[w])
    route_driver_class.append(route)

print(len(route_driver_class))
for route in route_driver_class:
    dimension = 0
    for i in range(1, len(route)-1):
        dimension += route[i].volumen
    if dimension > 2:
        print("se excede")
    print(dimension)
