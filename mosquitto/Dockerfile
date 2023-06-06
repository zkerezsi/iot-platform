FROM eclipse-mosquitto:2.0.15

COPY ./mosquitto.conf /mosquitto/config/mosquitto.conf

COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN echo "Starting /entrypoint.sh"
ENTRYPOINT ["/entrypoint.sh"]

CMD ["/usr/sbin/mosquitto", "-c", "/mosquitto/config/mosquitto.conf"]