# Community Services Explorer

## Plan de implementación por fases

**Versión:** 1.2\
**Estado:** MVP completado (fases 0--6) y ampliado a nueve comunidades
con cobertura por población. Pendiente: video demostrativo y demo
pública.\
**Última actualización:** 2026-11-02\
**Área de estudio:** inicialmente Yucaipa y Redlands; ahora Colton, Grand
Terrace, Highland, Loma Linda, Mentone, Redlands, Rialto, San Bernardino
y Yucaipa (California)\
**Dedicación estimada:** 4--5 horas por semana\
**Objetivo:** construir un proyecto GIS demostrable para un portafolio
de GIS Developer / Geospatial Software Engineer.

------------------------------------------------------------------------

## Estado de implementación (2026-11-02)

Repositorio: https://github.com/adtorres1987/Community-Services-Explorer

Diferencias respecto al plan original:

-   El repositorio local está en `~/dev/gis-app-web`, no en
    `~/Developer/community-services-explorer`.
-   Python 3.14 (Homebrew): el Python del sistema (3.9) es demasiado
    antiguo para GeoPandas 1.x.
-   La imagen de PostGIS es `imresamu/postgis:17-3.5` (multiarquitectura),
    porque `postgis/postgis` no tiene versión para arm64.
-   Se añadieron los campos `proximity_eligible` y el campo genérico
    `attributes` (JSONB) en `facilities`.
-   Se agregaron un script de descarga con verificación de checksum, el
    GeoPackage procesado en el repositorio, Docker Compose completo
    (db, carga, API, frontend con nginx) e integración continua con
    GitHub Actions.

### Ampliación: nueve comunidades del valle de San Bernardino

Se evaluó todo el condado (565 escuelas, 24 ciudades) y se acotó a nueve
comunidades contiguas: Colton, Grand Terrace, Highland, Loma Linda,
Mentone (CDP, no incorporada), Redlands, Rialto, San Bernardino y Yucaipa.

-   173 escuelas y 612.335 habitantes (Censo 2020).
-   Las escuelas se asignan por límite (unión espacial), no por la ciudad
    de la dirección, que incluye barrios y erratas.
-   Las escuelas a menos de 2 km del área (32, de cualquier condado)
    cuentan para la cobertura, sin efecto de borde.
-   Cobertura por población (bloques del Censo 2020, P.L. 94-171,
    repartidos por área) además de por superficie.
-   Radios: 500 m, 1 km, 1,5 km y 2 km.
-   Migración `002`, tabla `population_units`; GeoPackage de ~3 MB.
-   Desarrollado en la rama `feature/san-bernardino-county`.

Documentación técnica: `README.md` y `docs/`.

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

-   [x] Confirmar versión de macOS y arquitectura Apple Silicon.
-   [x] Confirmar que QGIS abre correctamente.
-   [x] Verificar `python3 --version`.
-   [x] Verificar `git --version`.
-   [x] Verificar que Docker Desktop inicia correctamente.
-   [x] Crear el repositorio local.
-   [x] Crear un entorno virtual Python independiente.
-   [x] Crear `.gitignore`.
-   [x] Crear el primer commit.

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

-   [x] Descargar el dataset oficial.
-   [x] Guardar el archivo original en `data/raw/`.
-   [x] Registrar URL, fecha de descarga y licencia.
-   [x] Abrir el archivo en QGIS.
-   [x] Identificar los campos que representan nombre, ciudad, tipo,
    estado y ubicación.
-   [x] Confirmar cómo están representadas Yucaipa y Redlands en los
    atributos.
-   [x] Revisar cantidad de registros y geometrías nulas o vacías.
-   [x] Registrar dudas sobre calidad y cobertura.

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

-   [x] Crear `scripts/inspect_schools.py`.
-   [x] Inspeccionar columnas, tipos de datos y CRS.
-   [x] Medir valores faltantes y geometrías vacías.
-   [x] Identificar registros duplicados.
-   [x] Confirmar el campo y los valores utilizados para filtrar
    ciudades.
-   [x] Filtrar escuelas de Yucaipa y Redlands.
-   [x] Validar geometrías.
-   [x] Transformar a un CRS proyectado adecuado para mediciones en
    metros.
-   [x] Exportar los datos limpios a GeoPackage.
-   [x] Abrir el resultado en QGIS y comprobarlo visualmente.

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

-   [x] Definir el modelo de datos mínimo.
-   [x] Crear PostgreSQL y PostGIS mediante Docker Compose.
-   [x] Crear la base de datos `community_services`.
-   [x] Crear una tabla de instalaciones.
-   [x] Importar las escuelas procesadas.
-   [x] Crear índices espaciales GiST.
-   [x] Verificar geometrías y SRID.
-   [x] Probar consultas espaciales.

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

-   [x] Crear aplicación FastAPI.
-   [x] Configurar conexión a PostGIS.
-   [x] Definir esquemas de respuesta.
-   [x] Implementar validación de parámetros.
-   [x] Devolver geometrías en GeoJSON cuando corresponda.
-   [x] Manejar errores y respuestas HTTP.
-   [x] Probar endpoints.
-   [x] Documentar API mediante OpenAPI.

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

-   [x] Mostrar un mapa centrado en el área de estudio.
-   [x] Visualizar escuelas como marcadores.
-   [x] Mostrar nombre y atributos en un popup.
-   [x] Filtrar por ciudad.
-   [x] Filtrar por tipo de instalación.
-   [x] Consultar radios de 500 y 1.000 metros.
-   [x] Mostrar estadísticas por ciudad.
-   [x] Manejar estados de carga y errores.

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

-   [x] Escribir pruebas para el procesamiento de datos.
-   [x] Probar endpoints.
-   [x] Verificar consultas espaciales con casos conocidos.
-   [x] Configurar Docker Compose para el entorno completo.
-   [x] Documentar instalación y ejecución.
-   [x] Documentar fuentes y licencias.
-   [x] Documentar limitaciones del análisis.
-   [x] Crear capturas de pantalla.
-   [ ] Crear un video demostrativo breve.
-   [x] Publicar el repositorio en GitHub.
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

-   [x] Crear estructura de carpetas.
-   [x] Inicializar Git.
-   [x] Crear y activar `.venv`.
-   [x] Instalar dependencias de procesamiento.
-   [x] Descargar California Public Schools 2025--26.
-   [x] Abrir el archivo en QGIS.
-   [x] Ejecutar un script de inspección.
-   [x] Registrar nombres reales de campos, CRS y cantidad de registros.
-   [x] Documentar resultados en `docs/data-sources.md`.

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

Todas resueltas (detalle en `docs/data-sources.md`):

1.  Confirmar los campos reales del dataset. **Resuelto:** `CDSCode`,
    `SchoolName`, `City`, `SchoolType`, `Status`, `Virtual`, etc.
2.  Confirmar que existen registros para ambas ciudades. **Resuelto:**
    24 escuelas activas en Redlands y 13 en Yucaipa.
3.  Elegir el CRS de análisis. **Resuelto:** EPSG:26911 (NAD83 / UTM
    zona 11N, metros).
4.  Confirmar la fuente de límites municipales. **Resuelto:** Census
    TIGER/Line 2026 Places. En el MVP se filtró por ciudad de la
    dirección y se marcó `in_city_limits`; en la ampliación a nueve
    comunidades la asignación pasó a ser por límite.
5.  Definir si se incluirán únicamente escuelas públicas o también otras
    instalaciones educativas. **Resuelto:** solo escuelas públicas
    activas (dataset del CDE); las exclusivamente virtuales se excluyen
    del análisis de proximidad.

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
