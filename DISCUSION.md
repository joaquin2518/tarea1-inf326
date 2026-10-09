# Discusión – Tarea 1 INF326

## 1. Diseño de mensajes

El mensaje publicado contiene la información necesaria para que cada suscriptor determine si el sismo es de su interés y pueda solicitar su detalle. Se utiliza JSON, con tres campos:

```json
{
  "event_id": "sismo-001",
  "latitud": -18.9,
  "longitud": -70.2
}
```

| Campo | Tipo | Justificación |
|---|---|---|
| `event_id` | Cadena de texto | Identifica el registro del sismo en el servicio HTTP y permite solicitarlo mediante `GET /sismos/{event_id}`. |
| `latitud` | Número | Junto con la longitud, permite ubicar el epicentro y calcular la distancia a la ciudad del suscriptor. |
| `longitud` | Número | Completa las coordenadas necesarias para calcular la distancia geodésica. |

Las coordenadas se expresan en grados decimales. Cada suscriptor conoce previamente las coordenadas de su ciudad y utiliza `geopy.distance.geodesic` para calcular la distancia al epicentro. Solicita el detalle únicamente cuando esa distancia es estrictamente menor que 500 km; si es igual o mayor, descarta la notificación sin consultar el servicio HTTP.

Los tres campos tienen un uso concreto. Si se enviara solamente el identificador, los suscriptores tendrían que consultar la API para conocer la ubicación antes de decidir su interés, incluso para sismos lejanos. Si se enviaran solamente las coordenadas, podrían aplicar el filtro, pero no contarían con el identificador requerido por el endpoint para recuperar el registro correspondiente. Por ello, esta combinación es suficiente para las dos operaciones del flujo implementado: filtrar y solicitar el detalle.

La magnitud, la profundidad, las fechas, la referencia geográfica y la agencia se mantienen en el servicio HTTP. Estos datos forman parte del detalle del sismo, pero no intervienen en la regla de interés definida para la tarea, que depende exclusivamente de la distancia. En particular, no se utiliza la magnitud para decidir si se solicita información. Enviar el registro completo a todos los suscriptores distribuiría datos que los suscriptores lejanos terminarían descartando. Mantenerlos en la API permite obtenerlos bajo demanda y conserva la combinación de publish-subscribe con el modelo pull solicitada.

Tampoco se incluyen la ciudad destinataria, las coordenadas de cada suscriptor ni una distancia precalculada. Estos datos dependen del receptor y cada suscriptor puede obtener la distancia a partir de su configuración local. El publicador emite la misma notificación al exchange `sismos`, de tipo `fanout`, y cada suscriptor recibe una copia a través de su propia cola vinculada. Así, el publicador no necesita conocer las ciudades ni decidir cuáles están interesadas. La distribución a las colas vinculadas corresponde al funcionamiento descrito en la [documentación de RabbitMQ](https://www.rabbitmq.com/tutorials/tutorial-three-python).

JSON permite representar el identificador y las coordenadas de forma legible y compatible con los componentes implementados. El publicador serializa el cuerpo y declara `application/json` como tipo de contenido. Esta propiedad del transporte describe el formato y no agrega campos al contenido del evento.

El diseño supone que el registro ya existe en el servicio HTTP y que su identificador y coordenadas coinciden con los de la notificación. En el modo de demostración, el publicador obtiene esos valores de los mismos datos de prueba utilizados por la API. La estructura del detalle incluye campos presentes en los [informes del Centro Sismológico Nacional](https://www.sismologia.cl/sismicidad/informes/2026/10/385983.html), aunque los seis registros del proyecto son datos de prueba. El costo de separar la notificación del detalle es una consulta HTTP adicional para los suscriptores interesados y la dependencia de que ese servicio esté disponible, aspectos tratados en la sección de trade-offs.


## 2. Trade-offs de la arquitectura

El diseño propuesto para el sistema de notificación de sismos conlleva los siguientes compromisos técnicos o *trade-offs*, cuya relevancia varía según las características de este dominio:

- **Payload mínimo + Pull HTTP vs. Payload completo en el broker:** Enviar solo la información mínima hace que la mensajería sea extremadamente veloz y ligera. El *trade-off* es que obliga a los suscriptores interesados a realizar una petición HTTP adicional al servicio de FastAPI para obtener los detalles, agregando latencia y una dependencia extra. En este dominio, pesa más lo positivo: como los sismos relevantes para cada nodo (a menos de 500 km) son pocos, la gran mayoría de los mensajes se descartan rápido sin malgastar ancho de banda.
- **Desacoplamiento (Fanout) vs. Eficiencia de red (Topic):** Usar un exchange tipo *fanout* permite un desacoplamiento total donde el publicador no necesita saber quién ni dónde está suscrito. El *trade-off* es que genera tráfico redundante, ya que nodos lejanos (ej. Punta Arenas recibiendo sismos de Arica) procesan mensajes irrelevantes. En este dominio con solo 5 suscriptores, el gasto de red es insignificante, por lo que la simplicidad del *fanout* vale la pena frente a implementar un ruteo geográfico complejo en el broker.
- **Datos en memoria vs. Persistencia:** Mantener los datos en memoria simplifica la implementación y es suficiente para los registros de prueba de esta tarea. En esta versión, los seis registros se cargan desde el código cada vez que inicia la API, por lo que vuelven a estar disponibles después de un reinicio. La limitación es que no existe persistencia para cambios o nuevos registros incorporados durante la ejecución; en un sistema real sería necesario un almacenamiento persistente.
- **Desacoplamiento vs. Broker como punto único de falla (SPOF):** Aunque el publicador y los suscriptores operan de forma completamente independiente a través de RabbitMQ, el *trade-off* es que la arquitectura entera depende de este componente central. Si el broker se cae, el sistema colapsa. En el dominio de las emergencias, la alta disponibilidad pesa mucho, por lo que en un escenario real se requeriría configurar el broker en un clúster con colas durables.

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