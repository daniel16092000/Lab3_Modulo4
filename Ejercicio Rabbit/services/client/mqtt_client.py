import paho.mqtt.client as mqtt
import time
import numpy
import os

servidor = "localhost"


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("$SYS/#")


def on_message(client, userdata, msg):
    print(msg.topic + str(msg.payload))

client = mqtt.Client()
client.username_pw_set("guest", password="guest")

client.connect(servidor, 1883, 60)
client.loop_start()

while True:
    time.sleep(0.5)
    rng = numpy.random.default_rng()
    value = rng.binomial(n=50000, p=0.2, size=1)
    client.publish("Reloj_inteligente",  "pasos conteo={} ".format(value[0]))
