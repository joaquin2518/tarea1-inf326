import time
import pika
from common import config


def get_connection(reintentos=10, espera=3):
    credenciales = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASS)
    params = pika.ConnectionParameters(
        host=config.RABBITMQ_HOST, port=config.RABBITMQ_PORT, credentials=credenciales
    )
    for intento in range(1, reintentos + 1):
        try:
            return pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError:
            print(f"RabbitMQ no disponible (intento {intento}/{reintentos}), reintentando en {espera}s...")
            time.sleep(espera)
    raise RuntimeError("No se pudo conectar a RabbitMQ")


def declarar_exchange(channel):
    channel.exchange_declare(exchange=config.EXCHANGE_NAME, exchange_type="fanout", durable=True)