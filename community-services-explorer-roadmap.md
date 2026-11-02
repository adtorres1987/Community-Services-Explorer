# Community Services Explorer

## Plan de implementación por fases

**Versión:** 1.0\
**Estado:** Plan inicial\
**Área de estudio:** Yucaipa y Redlands, California\
**Dedicación estimada:** 4--5 horas por semana\
**Objetivo:** construir un proyecto GIS demostrable para un portafolio
de GIS Developer / Geospatial Software Engineer.

------------------------------------------------------------------------

## 1. Visión del proyecto

Community Services Explorer será una aplicación geoespacial para
explorar la distribución de escuelas públicas y, en fases posteriores,
otros servicios comunitarios en Yucaipa y Redlands.

La aplicación permitirá:

-   Visualizar escuelas y servicios comunitarios en un mapa.
-   Filtrar instalaciones por ciudad y categoría.
-   Consultar atributos de cada instalación.
-   Calcular proximidad geográfica de 500 metros y 1 kilómetro.
-   Comparar la distribución de servicios entre las dos ciudades.
-   Presentar estadísticas y explicar las limitaciones del análisis.

> **Alcance y honestidad analítica:** un radio de proximidad representa
> distancia en línea recta. No demuestra accesibilidad real,
> disponibilidad del servicio, capacidad ni calidad. En una fase
> posterior se podrá estudiar accesibilidad mediante redes de calles y
> tiempos de viaje.

## 2. Objetivos técnicos y de aprendizaje

Al terminar el MVP, el repositorio deberá demostrar que el desarrollador
puede:

1.  Obtener y documentar datos geográficos públicos.
2.  Inspeccionar, limpiar y transformar datos con QGIS y Python.
3.  Almacenar y consultar datos espaciales con PostgreSQL/PostGIS.
4.  diseñar una API para entregar información geoespacial.
5.  construir una interfaz web cartográfica.
6.  probar, documentar y ejecutar la solución de forma reproducible.
7.  explicar las decisiones técnicas y las limitaciones del análisis.

## 3. Tecnologías

  -----------------------------------------------------------------------
  Área                    Tecnología              Uso
  ----------------------- ----------------------- -----------------------
  GIS de escritorio       QGIS LTR                Inspección, limpieza y
                                                  validación visual

  Lenguaje de análisis    Python 3                Procesamiento y
                                                  automatización

  Datos vectoriales       GeoPackage, GeoJSON     Intercambio y
                                                  almacenamiento de
                                                  archivos

  Procesamiento           GeoPandas, Shapely,     Lectura, transformación
                          Pyogrio, PyProj         y análisis

  Base de datos           PostgreSQL + PostGIS    Persistencia y
                                                  consultas espaciales

  Backend                 FastAPI                 API REST

  Frontend                React + TypeScript      Interfaz de usuario

  Mapa web inicial        Leaflet + React-Leaflet Visualización
                                                  cartográfica

  Contenedores            Docker Compose          Entorno reproducible

  Control de versiones    Git + GitHub            Historial y portafolio

  Pruebas                 Pytest y pruebas del    Verificación de
                          frontend                comportamiento
  -----------------------------------------------------------------------

**Decisión de alcance:** no incorporar ArcGIS Maps SDK, QGIS Server ni
servicios OGC en el primer MVP. Se evaluarán como ampliaciones después
de completar la aplicación básica. No instalar herramientas adicionales
si el entorno actual ya funciona.

## 4. Arquitectura objetivo del MVP

``` text
                    Usuario
                       |
                       v
             React + TypeScript
              Leaflet / UI
                       |
                  HTTP / JSON
                       |
                       v
                 FastAPI
              Python / GeoJSON
                       |
                  SQL espacial
                       |
                       v
             PostgreSQL + PostGIS
                       ^
                       |
              Datos procesados
                       |
             Python / GeoPandas
                       ^
                       |
                Datos originales
                       |
                 QGIS / CDE
```

QGIS se utilizará inicialmente como herramienta de inspección y
validación, no como servidor de mapas.

## 5. Estructura propuesta del repositorio

``` text
community-services-explorer/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── features/
│   │   ├── maps/
│   │   └── services/
│   └── package.json
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
├── database/
│   ├── migrations/
│   └── sql/
├── docs/
│   ├── architecture.md
│   ├── data-sources.md
│   └── analysis-limitations.md
├── qgis/
├── scripts/
├── tests/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

No se deben subir al repositorio datos grandes, archivos privados,
contraseñas, tokens ni archivos `.env`. Los datos descargables se
documentarán en `data/README.md` y se excluirán de Git, salvo que se
decida expresamente incluir una muestra pequeña y redistribuible.

------------------------------------------------------------------------

# 6. Implementación por fases

## Fase 0 --- Preparación del entorno y repositorio

**Duración estimada:** 1 sesión (45--60 minutos).

### Tareas

-   [ ] Confirmar versión de macOS y arquitectura Apple Silicon.
-   [ ] Confirmar que QGIS abre correctamente.
-   [ ] Verificar `python3 --version`.
-   [ ] Verificar `git --version`.
-   [ ] Verificar que Docker Desktop inicia correctamente.
-   [ ] Crear el repositorio local.
-   [ ] Crear un entorno virtual Python independiente.
-   [ ] Crear `.gitignore`.
-   [ ] Crear el primer commit.

### Comandos iniciales

``` bash
mkdir -p ~/Developer/community-services-explorer
cd ~/Developer/community-services-explorer

git init

mkdir -p data/raw data/processed scripts \
  notebooks docs qgis tests

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Dependencias iniciales:

``` bash
python -m pip install \
  geopandas shapely pyogrio pyproj pandas matplotlib
```

Guardar dependencias:

``` bash
python -m pip freeze > requirements.txt
```

### Criterios de aceptación

-   El entorno virtual se activa sin errores.
-   Se pueden importar GeoPandas y Shapely.
-   Git registra el proyecto.
-   QGIS y Python pueden utilizarse sin modificar el Python interno de
    QGIS.

**Entregable:** repositorio inicial y entorno de desarrollo documentado.

## Fase 1 --- Descubrimiento y adquisición de datos

**Duración estimada:** 1 semana.

### Fuente inicial

California Department of Education --- California Public Schools
2025--26:

https://data.ca.gov/@california-department-of-education/california-public-schools-2025-26

Se debe revisar el recurso disponible y elegir GeoPackage, GeoJSON u
otro formato vectorial apropiado. Confirmar fecha, licencia, campos,
cobertura y sistema de coordenadas antes de procesar.

### Tareas

-   [ ] Descargar el dataset oficial.
-   [ ] Guardar el archivo original en `data/raw/`.
-   [ ] Registrar URL, fecha de descarga y licencia.
-   [ ] Abrir el archivo en QGIS.
-   [ ] Identificar los campos que representan nombre, ciudad, tipo,
    estado y ubicación.
-   [ ] Confirmar cómo están representadas Yucaipa y Redlands en los
    atributos.
-   [ ] Revisar cantidad de registros y geometrías nulas o vacías.
-   [ ] Registrar dudas sobre calidad y cobertura.

### Criterios de aceptación

-   La fuente es oficial y está documentada.
-   El archivo se abre correctamente.
-   Se conocen los nombres reales de los campos.
-   Se conoce el CRS de origen.
-   Se ha confirmado que hay registros relevantes para ambas ciudades.

**Entregable:** inventario de datos y archivo original local.

## Fase 2 --- Inspección, limpieza y preparación

**Duración estimada:** 1--2 semanas.

### Tareas

-   [ ] Crear `scripts/inspect_schools.py`.
-   [ ] Inspeccionar columnas, tipos de datos y CRS.
-   [ ] Medir valores faltantes y geometrías vacías.
-   [ ] Identificar registros duplicados.
-   [ ] Confirmar el campo y los valores utilizados para filtrar
    ciudades.
-   [ ] Filtrar escuelas de Yucaipa y Redlands.
-   [ ] Validar geometrías.
-   [ ] Transformar a un CRS proyectado adecuado para mediciones en
    metros.
-   [ ] Exportar los datos limpios a GeoPackage.
-   [ ] Abrir el resultado en QGIS y comprobarlo visualmente.

### Reglas

-   No inventar nombres de columnas: utilizar los nombres reales del
    dataset.
-   No eliminar registros sin documentar el motivo.
-   Conservar el dataset original sin modificar.
-   Registrar cuántos registros entran, se excluyen y salen del proceso.
-   Verificar que las geometrías estén dentro del área de estudio.

### Criterios de aceptación

-   El procesamiento puede repetirse ejecutando el script.
-   El resultado contiene únicamente los registros que cumplen el filtro
    documentado.
-   Las geometrías son válidas o sus problemas están registrados.
-   El CRS está documentado.
-   QGIS muestra correctamente las entidades.

**Entregable:** GeoPackage procesado y script reproducible.

## Fase 3 --- Modelo de datos y PostGIS

**Duración estimada:** 1 semana.

### Tareas

-   [ ] Definir el modelo de datos mínimo.
-   [ ] Crear PostgreSQL y PostGIS mediante Docker Compose.
-   [ ] Crear la base de datos `community_services`.
-   [ ] Crear una tabla de instalaciones.
-   [ ] Importar las escuelas procesadas.
-   [ ] Crear índices espaciales GiST.
-   [ ] Verificar geometrías y SRID.
-   [ ] Probar consultas espaciales.

### Modelo inicial sugerido

**Tabla `facilities`:**

  Campo           Tipo conceptual         Descripción
  --------------- ----------------------- ----------------------------
  id              BIGINT                  Identificador interno
  source_id       TEXT                    Identificador de la fuente
  name            TEXT                    Nombre de la instalación
  facility_type   TEXT                    Tipo de instalación
  city            TEXT                    Ciudad
  source_name     TEXT                    Fuente de datos
  geom            GEOMETRY(Point, SRID)   Ubicación

El SRID definitivo debe elegirse después de inspeccionar los datos y
definir el CRS de trabajo. No asumir un SRID sin comprobarlo.

### Consultas a implementar

-   `ST_Intersects`
-   `ST_DWithin`
-   `ST_Buffer`
-   `ST_Distance`
-   `ST_Transform`

Crear índice espacial:

``` sql
CREATE INDEX facilities_geom_idx
ON facilities
USING GIST (geom);
```

### Criterios de aceptación

-   La base de datos inicia correctamente.
-   Los datos se importan sin pérdida inexplicada.
-   Las consultas espaciales devuelven resultados verificables.
-   El índice espacial existe.
-   Las distancias se calculan en unidades métricas apropiadas.

**Entregable:** base PostGIS y consultas SQL documentadas.

## Fase 4 --- Backend con FastAPI

**Duración estimada:** 1 semana.

### Endpoints iniciales

  Método   Endpoint                Función
  -------- ----------------------- ------------------------------
  GET      `/health`               Estado de la API
  GET      `/facilities`           Listar instalaciones
  GET      `/facilities/{id}`      Consultar una instalación
  GET      `/cities`               Obtener ciudades disponibles
  GET      `/analysis/proximity`   Consultar proximidad

Parámetros previstos para proximidad:

-   `city`: ciudad.
-   `radius_m`: radio en metros.
-   `facility_type`: categoría opcional.

### Tareas

-   [ ] Crear aplicación FastAPI.
-   [ ] Configurar conexión a PostGIS.
-   [ ] Definir esquemas de respuesta.
-   [ ] Implementar validación de parámetros.
-   [ ] Devolver geometrías en GeoJSON cuando corresponda.
-   [ ] Manejar errores y respuestas HTTP.
-   [ ] Probar endpoints.
-   [ ] Documentar API mediante OpenAPI.

### Criterios de aceptación

-   Los endpoints responden correctamente.
-   Los filtros funcionan.
-   Las consultas se ejecutan en PostGIS.
-   Las respuestas tienen una estructura consistente.
-   Los errores se manejan de forma explícita.

**Entregable:** API funcional y documentada.

## Fase 5 --- Frontend con React y Leaflet

**Duración estimada:** 1--2 semanas.

### Componentes sugeridos

``` text
frontend/src/
├── components/
│   ├── MapView.tsx
│   ├── FilterPanel.tsx
│   ├── FacilityPopup.tsx
│   └── StatisticsPanel.tsx
├── features/
│   └── facilities/
├── services/
│   └── api.ts
└── App.tsx
```

### Funcionalidades

-   [ ] Mostrar un mapa centrado en el área de estudio.
-   [ ] Visualizar escuelas como marcadores.
-   [ ] Mostrar nombre y atributos en un popup.
-   [ ] Filtrar por ciudad.
-   [ ] Filtrar por tipo de instalación.
-   [ ] Consultar radios de 500 y 1.000 metros.
-   [ ] Mostrar estadísticas por ciudad.
-   [ ] Manejar estados de carga y errores.

### Criterios de aceptación

-   El mapa carga los datos de la API.
-   Los filtros actualizan los resultados.
-   Las distancias se presentan correctamente.
-   La interfaz es usable en escritorio y móvil.
-   No se confunde proximidad en línea recta con accesibilidad por
    calles.

**Entregable:** MVP web funcional.

## Fase 6 --- Pruebas, documentación y publicación

**Duración estimada:** 1 semana.

### Tareas

-   [ ] Escribir pruebas para el procesamiento de datos.
-   [ ] Probar endpoints.
-   [ ] Verificar consultas espaciales con casos conocidos.
-   [ ] Configurar Docker Compose para el entorno completo.
-   [ ] Documentar instalación y ejecución.
-   [ ] Documentar fuentes y licencias.
-   [ ] Documentar limitaciones del análisis.
-   [ ] Crear capturas de pantalla.
-   [ ] Crear un video demostrativo breve.
-   [ ] Publicar el repositorio en GitHub.
-   [ ] Publicar una demo si el presupuesto y las condiciones de
    alojamiento lo permiten.

### Criterios de aceptación

Una persona distinta al desarrollador puede seguir el README y ejecutar
el proyecto con los requisitos indicados.

**Entregable:** repositorio público, documentación y demostración.

------------------------------------------------------------------------

# 7. Fases futuras --- Después del MVP

Estas funcionalidades no deben bloquear la primera entrega.

## Fase 7 --- Más servicios comunitarios

Incorporar, después de verificar fuentes y licencias:

-   Parques y espacios recreativos.
-   Bibliotecas.
-   Centros comunitarios.
-   Hospitales y clínicas.
-   Transporte público.

Cada fuente deberá tener fecha, procedencia, licencia y descripción de
sus limitaciones.

## Fase 8 --- Accesibilidad mediante redes

Ampliar el análisis con:

-   Red de calles y caminos.
-   Distancias por ruta.
-   Tiempos estimados de caminata.
-   Áreas de servicio de 5, 10 y 15 minutos.
-   Comparación entre distancia euclidiana y distancia por red.

No presentar estimaciones de viaje como rutas reales si no se utiliza
una red adecuada.

## Fase 9 --- Ecosistema Esri y servicios GIS

Como ampliación profesional:

-   ArcGIS Maps SDK for JavaScript.
-   ArcGIS API for Python.
-   QGIS Server.
-   WMS, WFS y OGC API Features.
-   Comparación entre tecnologías open source y Esri.

------------------------------------------------------------------------

# 8. Organización del trabajo semanal

Dedicación disponible: 4--5 horas.

  Sesión      Actividad                                   Tiempo
  ----------- --------------------------------- ----------------
  1           Estudio y documentación técnica             45 min
  2           Implementación                              90 min
  3           Implementación y pruebas                    90 min
  4           Revisión, Git y documentación               45 min
  **Total**                                       **4 h 30 min**

Trabajar por entregables. No pasar a la siguiente fase hasta cumplir los
criterios de aceptación de la fase actual, salvo que se documente
expresamente una dependencia pendiente.

------------------------------------------------------------------------

# 9. Definition of Done --- Reglas de calidad

Una tarea no se considera terminada solamente porque funciona en la
computadora del desarrollador.

Debe cumplir lo siguiente cuando corresponda:

-   Código organizado y legible.
-   Validación de entradas.
-   Manejo de errores.
-   Pruebas apropiadas.
-   Sin credenciales ni secretos en Git.
-   Dependencias documentadas.
-   Instrucciones reproducibles.
-   Decisiones técnicas justificadas.
-   Limitaciones conocidas y documentadas.

## 10. Primer sprint: comenzar ahora

**Objetivo:** dejar listo el repositorio y confirmar que el dataset
oficial puede procesarse.

-   [ ] Crear estructura de carpetas.
-   [ ] Inicializar Git.
-   [ ] Crear y activar `.venv`.
-   [ ] Instalar dependencias de procesamiento.
-   [ ] Descargar California Public Schools 2025--26.
-   [ ] Abrir el archivo en QGIS.
-   [ ] Ejecutar un script de inspección.
-   [ ] Registrar nombres reales de campos, CRS y cantidad de registros.
-   [ ] Documentar resultados en `docs/data-sources.md`.

### Script inicial de inspección

Crear `scripts/inspect_schools.py`:

``` python
from pathlib import Path
import geopandas as gpd

data_path = (
    Path(__file__).resolve().parents[1]
    / "data/raw/california_schools_2025_26.gpkg"
)

if not data_path.exists():
    raise FileNotFoundError(data_path)

schools = gpd.read_file(data_path)

print("Records:", len(schools))
print("CRS:", schools.crs)
print("Geometry types:")
print(schools.geom_type.value_counts())
print("Columns:")
print(schools.columns.tolist())
print("Null geometries:", schools.geometry.isna().sum())
print("Empty geometries:", schools.geometry.is_empty.sum())

print("\nSample attributes:")
print(schools.drop(columns="geometry").head().to_string())
```

Ejecutar:

``` bash
source .venv/bin/activate
python scripts/inspect_schools.py
```

------------------------------------------------------------------------

## 11. Decisiones pendientes antes de avanzar

1.  Confirmar los campos reales del dataset.
2.  Confirmar que existen registros para ambas ciudades.
3.  Elegir el CRS de análisis.
4.  Confirmar la fuente de límites municipales.
5.  Definir si se incluirán únicamente escuelas públicas o también otras
    instalaciones educativas.

**Regla principal:** primero datos correctos, después análisis espacial,
luego API y finalmente interfaz web. No construir capas de software
antes de comprobar los datos.

------------------------------------------------------------------------

## 12. Resultado esperado del MVP

Al completar las fases 0--6, el proyecto deberá contar con:

-   Un flujo reproducible de preparación de datos.
-   Un conjunto de datos espacial validado.
-   Una base de datos PostgreSQL/PostGIS.
-   Una API REST con consultas espaciales.
-   Una aplicación React con mapa interactivo.
-   Pruebas y documentación.
-   Un repositorio GitHub presentable en entrevistas.

Este proyecto no garantiza un empleo ni sustituye la experiencia
profesional, pero sí proporciona evidencia concreta de habilidades de
desarrollo geoespacial.
