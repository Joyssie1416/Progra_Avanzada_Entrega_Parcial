# Descargamos librerías necesarías para todo el proceso
import requests
import sys
from bs4 import BeautifulSoup
import pandas as pd
import re

def extraer_tabla_emergencias(url):
    """
    Extrae ID, Fecha, Tipo y Dirección/Distrito de la tabla principal
    en una sola solicitud HTTP.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"[*] Conectando a {url} y extrayendo datos de la tabla principal...")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"[❌] ERROR al obtener la página principal: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Buscamos una tabla que contenga "table-bordered" en su clase (flexible)
    tabla = soup.find('table', class_=lambda c: c and 'table-bordered' in c.split())

    if not tabla:
        print("[❌] ERROR: No se encontró la tabla de emergencias. (Verifica la clase de la tabla)")
        return None

    datos_finales = []
    # Busca todas las filas de la tabla principal
    filas = tabla.find('tbody').find_all('tr')
    
    for fila in filas:
        celdas = fila.find_all(['th', 'td'])
        
        # Las celdas se indexan de 0 a 7. Necesitamos las celdas 1, 2, 3 y 4
        # [0: #] [1: Nro Parte] [2: Fecha y hora] [3: Dirección / Distrito] [4: Tipo]
        if len(celdas) >= 5: 
            datos_fila = {}
            
            # Columna 1: Nro Parte -> ID único (celda[1])
            nro_parte_element = celdas[1].find('span')
            datos_fila['ID Mapa (Nro Parte)'] = nro_parte_element.get_text().strip() if nro_parte_element else "N/A"
            
            # Columna 2: Fecha y hora (celda[2])
            fecha_hora_element = celdas[2].find('span')
            datos_fila['Fecha y hora'] = fecha_hora_element.get_text().strip() if fecha_hora_element else "N/A"
            
            # Columna 3: Dirección / Distrito (celda[3]) - Extraemos el texto completo
            # Limpiamos todo el texto dentro de la celda, eliminando tags como <canvas>
            direccion = celdas[3].get_text().strip()
            datos_fila['Dirección / Distrito'] = re.sub(r'\s{2,}', ' ', direccion).strip()

            # Columna 4: Tipo (celda[4])
            tipo_element = celdas[4].find('span')
            tipo = tipo_element.get_text().strip() if tipo_element else celdas[4].get_text().strip()
            datos_fila['Tipo'] = re.sub(r'\s{2,}', ' ', tipo).strip() # Limpiamos espacios
            
            datos_finales.append(datos_fila)
            
    return pd.DataFrame(datos_finales)


# --- Bloque Principal de Ejecución ---
if __name__ == "__main__":
    url_objetivo = "https://sgonorte.bomberosperu.gob.pe/24horas" 
    
    print("--- INICIO DE EXTRACCIÓN SIMPLE DE DATOS ---")

    # Ejecutamos la función de extracción simplificada
    df_final = extraer_tabla_emergencias(url_objetivo)

    if df_final is not None and not df_final.empty:
        print("\n" + "="*70)
        print("✅ EXTRACCIÓN EXITOSA. DATAFRAME SIMPLE GENERADO.")
        print("="*70)
        
        # Mostramos las primeras 5 filas del DataFrame final
        print("Primeras 5 filas del DataFrame:")
        print(df_final.head(5))
        
        print(f"\n[INFO] Total de registros procesados: {len(df_final)}")
        
        # Ahora el DataFrame se llama df_final y está listo para filtrar

        # --- CÓDIGO DE FILTRADO PARA ACCIDENTES DE TRÁNSITO ---
        
        def filtrar_accidentes_de_transito(df):
            """
            Filtra el DataFrame para incluir solo incidentes relacionados con vehículos de tránsito.
            """
            patrones_vehiculos = 'AUTOMOVIL|CAMIONETA|MOTO|VEHICULAR|DESPISTE|ATROPELLO|COLISIÓN'
            
            df_filtrado = df[
                df['Tipo'].str.contains(patrones_vehiculos, case=False, na=False)
            ].copy()

            return df_filtrado

        df_transito = filtrar_accidentes_de_transito(df_final)

        print("\n" + "*"*60)
        print(f"TABLA DE ACCIDENTES DE TRÁNSITO ENCONTRADOS ({len(df_transito)} registros)")
        print("*"*60)

        if not df_transito.empty:
            print(df_transito[['Fecha y hora', 'Tipo', 'Dirección / Distrito']])
        else:
            print("No se encontraron registros de accidentes de tránsito con los patrones definidos.")

    else:
        print("\nProceso de extracción fallido.")

    print("\n--- FIN DEL PROCESO ---")
