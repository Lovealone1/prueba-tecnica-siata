Se dejará el usuario creado como admin por defecto para practicidad de la prueba tecnica

Para temas prácticos de la prueba técnica, no se definirán ambientes de trabajo, existirá un único ambiente que será el productivo, el código se testeará individualmente en cada rama indivudual del feature a desarrollar

No se aplicará ratelimiting para el contexto de la prueba técnica

La dirección se guardó como string pero se puede crear otra tabla llamada address detail, para almacenar tema de detalles de la ubicación, como lo puede ser # de casa o indicaciones extras, por contexto de la prueba tecnica se dejó la solución que no agregase complejidad muy extensa a la prueba

Se implementó una paginación básica basada en offset (page/size). Es importante evaluar el volumen de datos en el futuro; si el volumen de envíos o registros aumenta significativamente, se debería considerar migrar a una paginación basada en cursores (cursor pagination) para mantener el rendimiento y la consistencia en datasets grandes.