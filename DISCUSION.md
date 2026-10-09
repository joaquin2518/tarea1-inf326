# Discusión – Tarea 1 INF326

## 1. Diseño de mensajes
(Pendiente: lo completa la Persona 3.)

## 2. Trade-offs de la arquitectura

El diseño propuesto para el sistema de notificación de sismos conlleva los siguientes compromisos técnicos o *trade-offs*, cuya relevancia varía según las características de este dominio:

- **Payload mínimo + Pull HTTP vs. Payload completo en el broker:** Enviar solo la información mínima hace que la mensajería sea extremadamente veloz y ligera[cite: 1]. El *trade-off* es que obliga a los suscriptores interesados a realizar una petición HTTP adicional al servicio de FastAPI[cite: 2] para obtener los detalles, agregando latencia y una dependencia extra. En este dominio, pesa más lo positivo: como los sismos relevantes para cada nodo (a menos de 500 km[cite: 1]) son pocos, la gran mayoría de los mensajes se descartan rápido sin malgastar ancho de banda.
- **Desacoplamiento (Fanout) vs. Eficiencia de red (Topic):** Usar un exchange tipo *fanout* permite un desacoplamiento total donde el publicador no necesita saber quién ni dónde está suscrito. El *trade-off* es que genera tráfico redundante, ya que nodos lejanos (ej. Punta Arenas recibiendo sismos de Arica[cite: 1]) procesan mensajes irrelevantes. En este dominio con solo 5 suscriptores[cite: 1], el gasto de red es insignificante, por lo que la simplicidad del *fanout* vale la pena frente a implementar un ruteo geográfico complejo en el broker.
- **Datos en memoria vs. Persistencia:** Mantener el registro de sismos en memoria en el endpoint HTTP simplifica el desarrollo y cumple con los requisitos del sistema[cite: 2], logrando tiempos de respuesta de lectura casi inmediatos. El *trade-off* es que se sacrifica por completo la durabilidad; si el servicio falla o se reinicia, se pierde el historial. En un sistema de alerta sismológica real, la confiabilidad es crítica, por lo que este *trade-off* no sería aceptable en producción y requeriría una base de datos persistente.
- **Desacoplamiento vs. Broker como punto único de falla (SPOF):** Aunque el publicador y los suscriptores operan de forma completamente independiente a través de RabbitMQ[cite: 2], el *trade-off* es que la arquitectura entera depende de este componente central. Si el broker se cae, el sistema colapsa. En el dominio de las emergencias, la alta disponibilidad pesa mucho, por lo que en un escenario real se requeriría configurar el broker en un clúster con colas durables.

## 3. Uso del "Back of the Envelope"

El enunciado indica que no se debe calcular, solo explicar cómo se podría estimar el uso del sistema con la información disponible sobre el fenómeno que se notifica. A continuación se describe el procedimiento.

### 3.1 Datos de entrada que se necesitan

- **Frecuencia de eventos:** cuántos sismos se reportan por día o por año. Se obtiene del catálogo histórico del Centro Sismológico Nacional (sismologia.cl). Conviene distinguir entre el promedio diario y los días pico.
- **Picos de actividad:** tras un sismo grande ocurren réplicas, que concentran muchos eventos en pocas horas. El sistema debe dimensionarse por este caso y no solo por el promedio.
- **Tamaño del mensaje publicado:** el mensaje contiene tres campos (`event_id`, `latitud`, `longitud`), por lo que pesa muy pocos bytes. Se puede medir serializando un ejemplo.
- **Tamaño de la respuesta HTTP:** el detalle del sismo (fechas, profundidad, magnitud, referencia geográfica) pesa más que el mensaje, pero sigue siendo pequeño. También se puede medir con un ejemplo real.
- **Cantidad de subscribers:** 5 en este caso.
- **Fracción de subscribers interesados:** se estima con la geografía. Chile es largo y angosto, y el radio de interés es de 500 km. Por eso, un sismo típico interesa solo a uno o dos subscribers, y muchos no interesan a ninguno.

### 3.2 Estimaciones que se pueden derivar

- **Mensajes entregados por segundo en el broker:** eventos por segundo × 5 subscribers, porque el exchange es de tipo fanout y cada subscriber recibe una copia.
- **Consultas HTTP por segundo:** eventos por segundo × número promedio de subscribers interesados por sismo. Es bastante menor que el número de mensajes entregados.
- **Ancho de banda:** (mensajes por segundo × tamaño del mensaje) + (consultas HTTP por segundo × tamaño de la respuesta).
- **Almacenamiento:** si los mensajes son persistentes, el espacio ocupado en disco depende de cuántos mensajes quedan en cola sin consumir. En condiciones normales es casi nulo, porque los subscribers los consumen de inmediato.
- **Memoria del servicio HTTP:** número de sismos almacenados × tamaño de cada registro.

### 3.3 Cómo se usa esto para justificar la arquitectura

- Si el resultado en el escenario de pico es del orden de pocas decenas de mensajes por segundo, un solo broker RabbitMQ y un solo servicio FastAPI son suficientes, y no se justifica una arquitectura más compleja (clúster, particionado por zona, caché distribuido).
- Si la fracción de subscribers interesados es baja, el costo de que todos reciban todos los mensajes (fanout) es despreciable. Con muchos más subscribers, o con muchos más eventos, convendría filtrar en el broker usando un exchange de tipo topic con una clave por zona geográfica.
- Si en el pico muchos subscribers consultan el detalle al mismo tiempo, se puede evaluar agregar una caché al servicio HTTP. Esto se decide comparando la estimación de consultas por segundo con la capacidad de un solo servicio.
- Al estimar el tamaño del mensaje frente al de la respuesta HTTP, se justifica que el mensaje sea mínimo y el detalle se pida solo cuando el sismo es de interés.