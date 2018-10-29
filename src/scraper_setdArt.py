import requests
import re
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup


# Busquem categories de subhasta
def busca_categorias(url):
    pag = requests.get(url)
    soup = BeautifulSoup(pag.content, "html.parser")
    categorias = []
    articles = soup.find_all("article")
    for article in articles:
        articlePare = article.parent
        if articlePare.get("class")[0] == "col_7":
            article_as = article.find_all("a")
            for a in article_as:
                categorias.append(a.get("href"))
                print(a.get("href"))
    return categorias

# Busquem lots de cada categoria de subhasta
def busca_lots(categorias, url):
    lotes = []
    i = 1
    for categoria in categorias:
        existeix_pagina = True
        i = 1
        while existeix_pagina:
            if i == 1:
                cat_pag = requests.get(url + categoria)
            else:
                cat_pag = requests.get(url + categoria + "page=" + str(i) + "/")
            cat_soup = BeautifulSoup(cat_pag.content, "html.parser")
            tables = cat_soup.find_all("table")
            for table in tables:
                if table.get("id") != None:
                    table_id = table["id"]
                    if table_id == "opentable":
                        table_content = table.contents[1]
                        table_a = table_content.find_all("a")
                        for a in table_a:
                            actua_a = a.get("href")
                            if ''.join(lotes[-1:]) != actua_a:
                                patron = re.compile("page=")
                                carpetas = actua_a.split("/")
                                url_pag = [x for x in carpetas if patron.match(x)]
                                if url_pag == []:
                                    lotes.append(actua_a)
            i += 1
            existeix_pagina = seg_pagina(url + categoria + "page=" + str(i) + "/")
    return lotes

# Busquem les licitacions
def busca_pujas(lotes, url):
    pujas = pd.DataFrame(columns=["lote","descripcion","categoria","valor_estimado","puja","fecha_puja"])
    i = 1
    for lote in lotes:
        puja = {"lote":"","descripcion":"","categoria":"","valor_estimado":"","puja":"","fecha_puja":""}
        lot_pag = requests.get(url + lote)
        lot_soup = BeautifulSoup(lot_pag.content, "html.parser")
        divs = lot_soup.find_all("div")
        for div in divs:
            if div.get("id") == "breadcrumb":
                for child in div.children:
                    for child2 in child.find_next_sibling().children:
                        cat = child2.get_text()
                        #pujas.append([{'categoria':cat}], ignore_index=True)
                        puja["categoria"] = cat
                        break
                    break
            if div.get("class") != None:    
                if div.get("class")[0] == "lotetitle":
                    num_lote = div.get_text()
                    #pujas.append([{'lote':num_lote}], ignore_index=True)
                    puja["lote"] = num_lote
            if div.get("itemprop") == "offerDetails":
                val_est = div.get_text()
                #pujas.append([{'valor_estimado':val_est}], ignore_index=True)
                puja["valor_estimado"] = val_est
            if div.get("itemprop") == "description":
                for child in div.children:
                    desc = child.get_text()
                    #pujas.append([{'descripcion':desc}], ignore_index=True)
                    puja["descripcion"] = desc
                    break
            if div.get("id") == "bidcontent":
                for child in div.find_next().children:
                    historial = child.get("src")
                    pujas, i = busca_historial_pujas(historial, pujas, puja, i)
                    break

    return pujas

# Busquem l'historial de licitacions del lot
def busca_historial_pujas(historial, pujas, puja, i):
    #print(historial)
    his_pujas_pag = requests.get(historial)
    his_pujas_soup = BeautifulSoup(his_pujas_pag.content, "html.parser")
    divs = his_pujas_soup.find_all("div")
    puja_simple = puja
    j = i
    if divs == []:
        puja_simple["puja"] = 0
        pujas = pujas.append(puja_simple, ignore_index=True)
    for div in divs:
        #print(div)
        #print(puja_simple)
        if j != i:
            puja_simple = puja
            #pujas[j][2:4] = pujas[i][2:4]
        if puja_simple["lote"] == "Lote: 35176024":
            print(div)
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
    descripcion = pujas["descripcion"]
    print(descripcion)
    valor_estimado = pujas["valor_estimado"]
    print(valor_estimado)
    puja = pujas["puja"]
    print(puja)
    fecha_puja = pujas["fecha_puja"]
    print[fecha_puja]

       