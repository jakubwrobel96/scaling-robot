# -*- coding: cp1250 -*-
#
# Program generalizuje budynki na podstawie długości przekątnych
# skrypt nie działa dla budynków z enklawami

import arcpy
from math import sqrt, atan, acos, cos, sin, pi
arcpy.env.overwriteOutput = True

            
# Funkcja do liczenia azymutu krawędzi budynków:

def azymut(p1,p2):
    try:
        dy = p2[1]-p1[1]
        dx = p2[0]-p1[0]
        if dx == 0:
            czwartak = 0
            if dy>0:
                azymut=100
            if dy<0:
                azymut=300                
        else:
            czwartak=atan(float(abs(dy))/float(abs(dx)))
            czwartak=czwartak*200/math.pi
            if dx>0:
                if dy>0:
                    azymut = czwartak
                if dy<0:
                    azymut = 400 - czwartak
                if dy==0:
                    azymut = 0
            if dx<0:
                if dy>0:
                    azymut = 200 - czwartak
                if dy<0:
                    azymut = 200 + czwartak
                if dy==0:
                    azymut = 200
        return azymut
    finally:
        del(dx,dy,czwartak)


# Funkcja do czytania geometrii:
def czytaj2(geometria):
    try:
        list1 = []
        i = 0
        for part in geometria:
            for pnt in part:
                if pnt:
                    list1.append([pnt.X, pnt.Y])
        i += 1
        return list1
    finally:
        del(i, part, pnt, geometria, list1)


# Funkcja licząca kąty w budynkach:
def angle(az1,az2):
    angle = az2 - az1
    return(angle)



# Funkcja usuwająca wierzchołki budynków z kątami zbliżonymi do 200 gradów (z zadaną 'tolerancją'):

def clear_list(list1):
    delete = []
    for i1 in range(len(list1)):
        previous = i1-1
        nextt = i1+1
        
        if previous == -1:
            previous = len(list1)-2

        if nextt > len(list1)-1:
            nextt = 1
            
        angle1=abs(angle(azymut(list1[i1],list1[previous]),azymut(list1[i1],list1[nextt])))
        
        if (angle1>(200-tolerancja) and angle1<(200+tolerancja)):
            delete.append(i1)

    if len(delete) == 0:
        return(list1)
    else:   
        delete.reverse()
           
        for index in delete:
            list1.pop(index)

        if delete[-1] == 0:
            list1.append(list1[0])

        return(list1)


# Funkcja licząca długość krawędzi budynku:

def length(a,b):
    length = sqrt((a[1]-b[1])**2+(a[0]-b[0])**2)
    return(length)



# Funkcja licząca ilość obiektów na liście między zadanymi indeksami:

def compute_range(length_of_list,x1,x2):
    if x2 - x1 < 0:
        output_range = length_of_list - x1 - 1 + x2
    else:
        output_range = x2 - x1 - 1
    return(output_range)



# Funkcja budująca listę przekatnych:

def create_lista_przek(list1):
    poligon = create_arcpy_polygon(list1)
    length1 = len(list1)-1
    lista_przekatnych = []
    for i1 in range(len(list1)-1):
        for i2 in range(i1+2,len(list1)-1):
            
            # sprawdzanie warunku o ilosci odcinanych punktów (przekątna musi odcinać więcej niż k punktów oraz musi zostać więcej niż k2 wierzchołków)            
            if (((compute_range(length1,i1,i2) == k) and ((length1 - compute_range(length1,i1,i2)) >= k2)) or ((compute_range(length1,i2,i1) == k) and ((length1 - compute_range(length1,i2,i1)) >= k2))):

                # sprawdzenie czy przekatna nie przecina poligonu
                if not create_arcpy_line([list1[i1],list1[i2]]).crosses(poligon):
                    lista_przekatnych.append([length(list1[i1],list1[i2]),i1,i2])                
    return(lista_przekatnych)



# Funkcja znajdująca najkrótszą przekątną:

def search_min_przekatna(list1):
    minimum = list1
    for przekatna in list1:
        if przekatna[0] < minimum[0]:
            minimum = przekatna
            
    return(minimum)



# Funkcja do tworzenia obiektow: glownego i odciętego

def delete_points(lista):
    najkrotsza = search_min_przekatna(create_lista_przek(lista))
    object1 = range(najkrotsza[1],najkrotsza[2]+1)+[najkrotsza[1]]
    object1_1 = [lista[index] for index in object1]
    object2 = range(najkrotsza[2],len(lista)-1)+range(0,najkrotsza[1]+1)+[najkrotsza[2]]
    object2_2 = [lista[index] for index in object2]

    #warunek o wybraniu obiektu do odciecia
    if len(object2) > len(object1):
        odciete = object1_1
        glowny = object2_2
    else:
        odciete = object2_2
        glowny = object1_1
    return([glowny,odciete,najkrotsza])
        


# Funkcja generalizująca (na zmianę usuwanie punktów na liniach i z przekątnych):

def generalizacja(budynek):
    
    ID = budynek[1]
    budynek = budynek[0]
    w = len(budynek)-1

    nr_odcietego = 1 
    lista_odcietych = []
    
    if not len(create_lista_przek(budynek)) == 0:
        
        while w > k2:
            
            # czyszczenie budynku z punktów na prostych
            budynek = clear_list(budynek)

            temp_budynek = budynek
            
            w = len(budynek)-1

            # ponowne (po wyczyszczeniu z niepotrzebnych punktów) sprawdzenie czy lista przekątnych nie jest pusta. Jeżeli jest pusta to break (przerwanie) pętli while dla budynku (brak możliwości dalszej generalizacji)
            if not len(create_lista_przek(budynek)) == 0:

                #sprawdzenie warunku 
                if w > k2:
                    
                        # wywołanie funkcji generalizującej
                        budynek,odciety,przekatna = delete_points(budynek)[0],delete_points(budynek)[1],delete_points(budynek)[2]
                        
                        # sprawdzanie czy odcinany obiekt jest wewnatrz czy na zewnatrz poligonu
                        if create_arcpy_line([temp_budynek[przekatna[1]],temp_budynek[przekatna[2]]]).within(create_arcpy_polygon(temp_budynek)):    
                            odciety = [odciety,nr_odcietego,1]
                        else:
                            odciety = [odciety,nr_odcietego,0]

                        # dodanie odciętego fragmentu do listy odciętych fragmentów
                        lista_odcietych.append(odciety)
                        
                        #dodanie 1 do licznika odciętych fragmentów
                        nr_odcietego = nr_odcietego + 1
            else:
                break
            w = len(budynek)-1

    budynek = [budynek,ID]
    lista_odcietych = [lista_odcietych,ID]
    return(budynek,lista_odcietych)



# Tworzenie obiektu arcpy.Polyline:
def create_arcpy_line(line):
    arcpy_line = arcpy.Polyline(arcpy.Array([arcpy.Point(line[0][0],line[0][1]),arcpy.Point(line[1][0],line[1][1])]))
    return(arcpy_line)



# Tworzenie obiektu arcpy.Polygon
def create_arcpy_polygon(polygon):
    arcpy_polygon = arcpy.Polygon(arcpy.Array([arcpy.Point(ppoint[0],ppoint[1]) for ppoint in polygon]))
    return(arcpy_polygon) 



    

# PARAMETRY:

# tolerancja (w gradach):
tolerancja = 10
# minimalna ilosc usunietych wierzcholkow:
k=1
# ilosc punktow w wyniku:
k2=4



# Wczytanie geometrii:

budynki = r'C:\Users\Admin\Desktop\ppg\Dane.shp'

kursor_czytania = arcpy.da.SearchCursor(budynki, ['SHAPE@', 'OBJECTID'])
lista_budynkow = []
for row_czy in kursor_czytania:  
    geometria = czytaj2(row_czy[0])
    lista2 = [geometria,row_czy[1]]
    lista_budynkow.append(lista2)


# Generalizacja:
wynik_lista = [generalizacja(poligon)[0] for poligon in lista_budynkow]
wynik_lista_odcietych = [generalizacja(poligon)[1] for poligon in lista_budynkow]


# Tworzenie warstw wynikowych:
wynik_shp = arcpy.CreateFeatureclass_management(r'C:\Users\Admin\Desktop\ppg','wynik.shp','POLYGON',budynki)
wynik_shp_odciete = arcpy.CreateFeatureclass_management(r'C:\Users\Admin\Desktop\ppg','wynik_odciete.shp','POLYGON')
arcpy.AddField_management(wynik_shp_odciete,'id_budynku','SHORT')
arcpy.AddField_management(wynik_shp_odciete,'id_odciete','SHORT')
arcpy.AddField_management(wynik_shp_odciete,'In_Out','SHORT')


# Wypisanie geometrii i uzupełnianie tabeli atrybutów
with arcpy.da.InsertCursor(wynik_shp, ['SHAPE@', 'FID']) as cursor:
    for poligon in wynik_lista:
        cursor.insertRow([poligon[0],poligon[1]])

with arcpy.da.InsertCursor(wynik_shp_odciete, ['SHAPE@', 'id_budynku', 'id_odciete','In_Out']) as cursor:
    for budynek in wynik_lista_odcietych:
        for odciety in budynek[0]:
            id_budynku = budynek[1]
            cursor.insertRow([odciety[0],id_budynku,odciety[1],odciety[2]])

