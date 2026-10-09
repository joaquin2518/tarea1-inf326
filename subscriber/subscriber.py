import json
import os
import sys

import pika
import requests
from geopy.distance import geodesic

from common import config
from common.messaging import get_connection, declarar_exchange


def main():
    clave = os.getenv("CIUDAD") or (sys.argv[1] if len(sys.argv) > 1 else None)
    if clave not in config.CIUDADES:
        sys.exit(f"Uso: python -m subscriber.subscriber <{'|'.join(config.CIUDADES)}>")
    ciudad = config.CIUDADES[clave]
    nombre_cola = f"sub.{clave}"

    conexion = get_connection()
    canal = conexion.channel()
    declarar_exchange(canal)
    canal.queue_declare(queue=nombre_cola, durable=True)
    canal.queue_bind(queue=nombre_cola, exchange=config.EXCHANGE_NAME)
    canal.basic_qos(prefetch_count=1)

    def al_recibir(ch, method, properties, body):
        try:
            msg = json.loads(body)
            distancia = geodesic(
                (ciudad["lat"], ciudad["lon"]), (msg["latitud"], msg["longitud"])
            ).km
            if distancia < config.RADIO_INTERES_KM:
                print(f"[{ciudad['nombre']}] {msg['event_id']} a {distancia:.1f} km -> DE INTERÉS, pidiendo detalle...")
                r = requests.get(f"{config.API_BASE_URL}/sismos/{msg['event_id']}", timeout=5)
                r.raise_for_status()
                print(f"[{ciudad['nombre']}] Detalle: {r.json()}")
            else:
                print(f"[{ciudad['nombre']}] {msg['event_id']} a {distancia:.1f} km -> descartado")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except (json.JSONDecodeError, KeyError, requests.RequestException) as e:
            print(f"[{ciudad['nombre']}] Error procesando mensaje: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    canal.basic_consume(queue=nombre_cola, on_message_callback=al_recibir)
    print(f"[{ciudad['nombre']}] Esperando sismos... (Ctrl+C para salir)")
    try:
        canal.start_consuming()
    except KeyboardInterrupt:
        pass
    finally:
        conexion.close()


if __name__ == "__main__":
    main()