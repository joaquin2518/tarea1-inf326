import os

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

EXCHANGE_NAME = "sismos"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
RADIO_INTERES_KM = 500

CIUDADES = {
    "arica":        {"nombre": "Arica",        "lat": -18.4746,  "lon": -70.29792},
    "coquimbo":     {"nombre": "Coquimbo",     "lat": -29.95332, "lon": -71.33947},
    "valparaiso":   {"nombre": "Valparaíso",   "lat": -33.036,   "lon": -71.62963},
    "concepcion":   {"nombre": "Concepción",   "lat": -36.82699, "lon": -73.04977},
    "punta_arenas": {"nombre": "Punta Arenas", "lat": -53.16282, "lon": -70.90922},
}