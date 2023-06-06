#!/bin/sh

# Be careful with linefeed characters (should be LF)
PASSWDFILE=/mosquitto/config/passwordfile.txt;
touch $PASSWDFILE
mosquitto_passwd -b $PASSWDFILE $MQTT_USERNAME $MQTT_PASSWORD

exec "$@"
