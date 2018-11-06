import requests
import re
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup


# Busquem categories de subhasta
def busca_categorias(url):
    # Descarreguem l'html de la pàgina principal
    print('Downloading: ', url)
    pag = requests.get(url)
    soup = BeautifulSoup(pag.content, "html.parser")
    categorias = []
    # Busquem tots les etiquetes "article"
    articles = soup.find_all("article")
    for article in articles:
        # Per cada etiqueta "article", busquem si la seva etiqueta pare és igual a "col_12", i si
        # la etiqueta pare d'aquesta és igual a "dropdown_6columns"
        # Cal revisar el codi html font de la web principal degut que el dropdown de categories pot
        # canviar de etiquetes pare
        articlePare = article.parent
        articleAvi = articlePare.parent
        if articlePare.get("class")[0] == "col_12" and articleAvi.get("class")[0] == "dropdown_6columns":
            # Busquem totes les etiquetes "a" que conté l'etiqueta "article" 
            article_as = article.find_all("a")
            for a in article_as:
                # Per cada etiqueta "a", desem el link de cada categoria
                categorias.append(a.get("href"))
                #print(a.get("href"))
    return categorias

# Busquem lots de cada categoria de subhasta
def busca_lots(categorias, url):
    lotes = []
    i = 1
    for categoria in categorias:
        existeix_pagina = True
        i = 1
        while existeix_pagina:
            # Per cada categoria i mentre existeixi pagines de lots, ens descarreguem el codi html
            # de cada pàgina
            if i == 1:
                # En la primera crida de cada categoria es descarrega la primera pàgina
                print('Downloading: ', url + categoria)
                cat_pag = requests.get(url + categoria)
            else:
                # La resta de crides de cada categoria es descarreguen les pàgines successives
                print('Downloading: ', url + categoria + "page=" + str(i) + "/")
                cat_pag = requests.get(url + categoria + "page=" + str(i) + "/")
            cat_soup = BeautifulSoup(cat_pag.content, "html.parser")
            # Busquem totes les etiquetes "table" de la pàgina de lots
            tables = cat_soup.find_all("table")
            for table in tables:
                # En el cas que la etiqueta "table" tingui l'atribut "id"
                if table.get("id") != None:
                    table_id = table["id"]
                    # En el cas que l'atribut "id" sigui igual a "opentable"
                    if table_id == "opentable":
                        table_content = table.contents[1]
                        # Busquem totes les etiquetes "a" del contingut de l'etiqueta "table"
                        table_a = table_content.find_all("a")
                        for a in table_a:
                            # Per cada etiqueta "a" desem el link del lot
                            actua_a = a.get("href")
                            # En el cas que el link no estigui desat amb anterioritat
                            if ''.join(lotes[-1:]) != actua_a:
                                # Desem el link del lot i excloem el link que navega a la següent 
                                # pàgina de lots
                                patron = re.compile("page=")
                                carpetas = actua_a.split("/")
                                url_pag = [x for x in carpetas if patron.match(x)]
                                if url_pag == []:
                                    lotes.append(actua_a)
            # Revisem si existeix següent pàgina de lots
            i += 1
            existeix_pagina = seg_pagina(url + categoria + "page=" + str(i) + "/")
    return lotes

# Busquem les licitacions
def busca_pujas(lotes, url):
    # Creem el Dataframe que contindrà totes les dades extretes
    pujas = pd.DataFrame(columns=["lote","descripcion","categoria","valor_estimado","puja","fecha_puja"])
    i = 1
    for lote in lotes:
        # Per cada lot creem un diccionari amb les mateixes columnes que el Dataframe
        puja = {"lote":"","descripcion":"","categoria":"","valor_estimado":"","puja":"","fecha_puja":""}
        # Per cad lot ens descarreguem el codi html
        print('Downloading: ', url + lote)
        lot_pag = requests.get(url + lote)
        lot_soup = BeautifulSoup(lot_pag.content, "html.parser")
        # Busquem totes les etiquetes "div" de la pàgina del lot
        divs = lot_soup.find_all("div")
        for div in divs:
            # Per cada etiqueta "div", si té un atribut "id" amb el valor "breadcrumb", la etiqueta filla
            # de la seva filla conté la categoria del lot
            if div.get("id") == "breadcrumb":
                for child in div.children:
                    for child2 in child.find_next_sibling().children:
                        cat = child2.get_text()
                        #pujas.append([{'categoria':cat}], ignore_index=True)
                        puja["categoria"] = cat
                        break
                    break
            # Per cada etiqueta "div", si té un atribut "class" amb el valor "lotetitle",
            # conté el número de lot
            if div.get("class") != None:    
                if div.get("class")[0] == "lotetitle":
                    num_lote = div.get_text()
                    #pujas.append([{'lote':num_lote}], ignore_index=True)
                    puja["lote"] = num_lote
            # Per cada etiqueta "div", si té un atribut "itemprop" amb el valor "offerDetails",
            # conté el valor estimat del lot
            if div.get("itemprop") == "offerDetails":
                val_est = div.get_text()
                #pujas.append([{'valor_estimado':val_est}], ignore_index=True)
                puja["valor_estimado"] = val_est
            # Per cada etiqueta "div", si té un atribut "itemprop" amb el valor "description",
            # la etiqueta filla conté la descripció del lot
            if div.get("itemprop") == "description":
                for child in div.children:
                    desc = child.get_text()
                    #pujas.append([{'descripcion':desc}], ignore_index=True)
                    puja["descripcion"] = desc
                    break
            # Per cada etiqueta "div", si té un atribut "id" amb el valor "bidcontent", la etiqueta filla
            # conté el link amb l'historial de licitacions del lot
            if div.get("id") == "bidcontent":
                for child in div.find_next().children:
                    historial = child.get("src")
                    pujas, i = busca_historial_pujas(historial, pujas, puja, i)
                    break

    return pujas

# Busquem l'historial de licitacions del lot
def busca_historial_pujas(historial, pujas, puja, i):
    #print(historial)
    # Descarreguem el codi html de l'historial de licitacions del lot
    print('Downloading: ', historial)
    his_pujas_pag = requests.get(historial)
    his_pujas_soup = BeautifulSoup(his_pujas_pag.content, "html.parser")
    # Busquem totes les etiques "div" de la pàgina de l'historial del lot
    divs = his_pujas_soup.find_all("div")
    # Creem un diccionari auxiliar amb les dades generals del lot
    puja_simple = puja
    j = i
    # En el cas que no hi hagi etiquetes "div", indica que no hi ha licitacions per aquest lot
    if divs == []:
        puja_simple["puja"] = 0
        pujas = pujas.append(puja_simple, ignore_index=True)
    for div in divs:
        #print(div)
        #print(puja_simple)
        # En el cas de ulteriors iteracions, s'inicialitza el diccionari auxiliar
        if j != i:
            puja_simple = puja
            #pujas[j][2:4] = pujas[i][2:4]
        # En el cas que la subasta no estigui finalizada, desem el valor de la licitació i la data
        if div.get_text()[:18] != "SUBASTA FINALIZADA":    
            valor = div.find_next().find_next()
            #pujas[j][5] = input.get("value")
            puja_simple["puja"] = valor.get("value")
            fecha = valor.find_next()
            #pujas[j][6] = input.get("value")
            puja_simple["fecha_puja"] = fecha.get("value")
            pujas = pujas.append(puja_simple, ignore_index=True)
            j += 1
    return pujas, j
                
# Busquem si existeix la seguent pagina de lots
def seg_pagina(url):
    existeix_pagina = True
    pag = requests.get(url)
    response_code = pag.status_code                
    if response_code != 200:
        existeix_pagina = False
    return existeix_pagina

# Estandarditzem les dades
def estandard_datos(pujas):
    # Eliminem l'string "Lote: " de la columna "lote" del Dataframe
    pujas["lote"] = pujas["lote"].str.replace("Lote: ", "")
    #print(pujas["lote"])
    # Eliminem els salts de línia i els retorns de carro de la columna "descripcion" del Dataframe
    pujas["descripcion"] = pujas["descripcion"].str.replace("\r", "")
    pujas["descripcion"] = pujas["descripcion"].str.replace("\n", " ")
    #print(pujas["descripcion"])
    # Eliminem els salts de línia i l'string "Valor estimado: " de la columna "descripcion" del Dataframe
    pujas["valor_estimado"] = pujas["valor_estimado"].str.replace("Valor estimado: ", "")
    pujas["valor_estimado"] = pujas["valor_estimado"].str.replace("\n", "")
    #pujas["valor_estimado"] = pujas["valor_estimado"].str.replace(" \u20ac", "")
    # Per cada registre del Dataframe, eliminem tot l'string després del primer espai de la columna
    # "valor_estimado" del Dataframe
    for index, row in pujas.iterrows():
        #print(row[3])
        valor = row[3]
        #print(valor)
        valor2 = valor.split(" ")[0]
        #print(valor2)
        row[3] = valor2
        #print(row[3])
    #print(pujas["valor_estimado"])
    # Eliminem el simbol "€" de la columna "puja" del Dataframe
    pujas["puja"] = pujas["puja"].str.replace("\u20ac", "")
    #print(pujas["puja"])
    # Posem nom a la columna que conté l'index dels registres del Dataframe
    pujas.index.name = "index"
    return pujas

# Escrivim csv
def escribir_CSV(pujas):
    pujas.to_csv("../csv/licitacions_setdArt.csv", header = True, index = True, sep = ";", encoding = "utf-8")
