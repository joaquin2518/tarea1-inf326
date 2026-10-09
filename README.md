# Tarea 1 INF326 – Notificación de sismos (Publish-Subscribe)

# integrantes
| Joaquín Navarro 202173125-3| 
| Vicente Vizcarra 202173036-2| 
| Felipe Zagal  202121082-2| 

# descripción
Un publisher notifica sismos con un mensaje mínimo (`event_id`, `latitud`, `longitud`) a un exchange fanout de RabbitMQ. 5 subscribers (Arica, Coquimbo, Valparaíso, Concepción, Punta Arenas) calculan la distancia geodésica a su ciudad y, si es menor a 500 km, consultan el detalle al servicio HTTP.

# prerrequisitos
- Docker Desktop (con Docker Compose)
- (Ejecución local) Python 3.10+

# ejecución con Docker (recomendada)
1. `docker compose up --build -d`
2. `docker compose run --rm publisher` esperar a que los 5 subscribers muestren `Esperando sismos...` en los logs antes de ejecutar el publisher. (publica los 6 sismos de prueba) 
3. `docker compose logs sub-arica sub-coquimbo sub-valparaiso sub-concepcion sub-punta-arenas`
4. `docker compose down`

# ejecución local
1. `python -m venv .venv` y activar; `pip install -r requirements.txt`
2. `docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management`
3. `uvicorn api.main:app --port 8000`
4. Un subscriber por terminal: `python -m subscriber.subscriber <arica|coquimbo|valparaiso|concepcion|punta_arenas>`
5. `python -m publisher.publisher --demo`  (o `--id X --lat Y --lon Z`)

# consideraciones de la implementación
- Mensaje: solo `event_id`, `latitud`, `longitud`.
- Exchange `sismos` (fanout) y una cola durable por subscriber (`sub.<ciudad>`).
- Los subscribers deben estar corriendo antes de publicar (con fanout, sin cola el mensaje se pierde).
- Ack manual; si falla el HTTP o el mensaje es inválido se hace `nack` sin reencolar.
- Distancia: `geopy.distance.geodesic`; interés si < 500 km.
- Datos de sismos en memoria (`api/data.py`), con estructura inspirada en sismologia.cl.
- Panel de RabbitMQ: http://localhost:15672 (guest/guest). Docs de la API: http://localhost:8000/docs
- Discusión de trade-offs y Back of the Envelope: ver `DISCUSION.md`.