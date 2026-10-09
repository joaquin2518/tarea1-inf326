import argparse
import json
import time

import pika

from api.data import SISMOS
from common import config
from common.messaging import get_connection, declarar_exchange


def publicar(canal, event_id, lat, lon):
    mensaje = {"event_id": event_id, "latitud": lat, "longitud": lon}
    canal.basic_publish(
        exchange=config.EXCHANGE_NAME,
        routing_key="",
        body=json.dumps(mensaje),
        properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
    )
    print(f"Publicado: {mensaje}")


def main():
    parser = argparse.ArgumentParser(description="Notificador de sismos")
    parser.add_argument("--id")
    parser.add_argument("--lat", type=float)
    parser.add_argument("--lon", type=float)
    parser.add_argument("--demo", action="store_true", help="publica los sismos de prueba")
    args = parser.parse_args()

    conexion = get_connection()
    canal = conexion.channel()
    declarar_exchange(canal)

    if args.demo:
        for s in SISMOS.values():
            publicar(canal, s["id"], s["latitud"], s["longitud"])
            time.sleep(1)
    elif args.id and args.lat is not None and args.lon is not None:
        publicar(canal, args.id, args.lat, args.lon)
    else:
        parser.error("Usa --demo, o bien --id, --lat y --lon")

    conexion.close()


if __name__ == "__main__":
    main()