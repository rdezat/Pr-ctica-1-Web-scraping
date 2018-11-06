from src import scraper_setdArt

# Pagina a investigar
url = "https://www.setdart.com"

# Busquem categories de subasta
categorias = scraper_setdArt.busca_categorias(url)

# Busquem lots de cada categoria de subasta 
lotes = scraper_setdArt.busca_lots(categorias, url)
       
# Recollim dades de les pujes         
pujas = scraper_setdArt.busca_pujas(lotes, url)

# Estandaditzem les dades
pujas = scraper_setdArt.estandard_datos(pujas)

# Escrivim les dades a un fitxer csv
scraper_setdArt.escribir_CSV(pujas)