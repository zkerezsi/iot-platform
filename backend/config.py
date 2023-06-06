import os
import logging

logging.basicConfig(
    format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.DEBUG)
logger = logging.getLogger()

mqtt_hostname = os.environ["MQTT_HOSTNAME"]
mqtt_password = os.environ["MQTT_PASSWORD"]
mqtt_username = os.environ["MQTT_USERNAME"]
mqtt_port = int(os.environ["MQTT_PORT"])

port = int(os.environ["PORT"])

postgres_password = os.environ["POSTGRES_PASSWORD"]
postgres_user = os.environ["POSTGRES_USER"]
postgres_db = os.environ["POSTGRES_DB"]
postgres_port = int(os.environ["POSTGRES_PORT"])
postgres_host = os.environ["POSTGRES_HOST"]
