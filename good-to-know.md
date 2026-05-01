Se dejará el usuario creado como admin por defecto para practicidad de la prueba tecnica

Para temas prácticos de la prueba técnica, no se definirán ambientes de trabajo, existirá un único ambiente que será el productivo, el código se testeará individualmente en cada rama indivudual del feature a desarrollar

No se aplicará ratelimiting para el contexto de la prueba técnica

La dirección se guardó como string pero se puede crear otra tabla llamada address detail, para almacenar tema de detalles de la ubicación, como lo puede ser # de casa o indicaciones extras, por contexto de la prueba tecnica se dejó la solución que no agregase complejidad muy extensa a la prueba

Se implementó una paginación básica basada en offset (page/size). Es importante evaluar el volumen de datos en el futuro; si el volumen de envíos o registros aumenta significativamente, se debería considerar migrar a una paginación basada en cursores (cursor pagination) para mantener el rendimiento y la consistencia en datasets grandes.

En el módulo de productos, se implementó el campo 'size' como un Enum (SMALL, MEDIUM, LARGE, EXTRA_LARGE). Si bien la logística real suele requerir cálculos de peso volumétrico (Largo x Ancho x Alto / Factor), se optó por una escala enumerada para equilibrar la velocidad de desarrollo con la lógica de negocio para esta prueba técnica.

Este enfoque es práctico para:
1. Estandarizar rápidamente las categorías de envío.
2. Simplificar el cálculo de costos basado en umbrales.
3. Asegurar la integridad de los datos a nivel de base de datos.

El campo 'transport_mode' (LAND/MARITIME) es el enrutador principal para el flujo logístico. 
Asegura que los productos estén correctamente asociados con 'Almacenes' o 'Puertos' en 
módulos posteriores, cumpliendo con el requisito de gestión logística diferenciada.

Los campos 'storage_capacity' y 'current_occupancy' se omitieron intencionadamente 
de las entidades Warehouse y SeaPort por las siguientes razones:

1. Los requisitos empresariales actuales 
   se centran en el registro e identificación de los nodos logísticos en lugar 
   de la gestión de inventarios o la optimización volumétrica.

2. En un ecosistema logístico complejo, la 'Capacidad' es 
   a menudo un valor dinámico calculado por un 'Servicio de Inventario' especializado 
   en lugar de un atributo estático de la infraestructura física.

3. Para garantizar una implementación CRUD robusta y limpia dentro del 
   plazo de la prueba, el enfoque se centró en la integridad estructural y 
   standardization of location data (City/Country/Address).

Cada compañía posee sus propios estándares de codificación y reglas de linting/formateo (Black, Ruff, Pylint, etc.). Por el contexto y agilidad de esta prueba técnica, se ha optado por omitir la imposición de una configuración de análisis estático específica en el CI, favoreciendo la legibilidad natural y la consistencia manual del código.