import pika, sys, os, math
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class Analitica():
    promedio_lista = [] ##
    conteo_promedio = 0 ##
    promedio_final = 0 ##
    valor_max = -math.inf
    valor_min = math.inf
    mayor10000  = 0 ##
    menor5000 = 0 ##
    mejor = -math.inf
    cont_mejor = 0
    mejor_racha = 0
    influx_bucket = "rabbit"
    influx_token = "token-secreto"
    influx_url = "http://influxdb:8086"
    influx_org = "org"

    def agregar_maximo(self, _medida):
        if _medida > self.valor_max:
            print("nuevo max", flush=True)
            self.valor_max = _medida
            self.escribir("Pasos", "Maximo", _medida)
    
    def agregar_promedio(self, _medida):
        print("promedio", flush=True)
        self.promedio_lista.append(_medida)
        self.conteo_promedio = len(self.promedio_lista)
        self.promedio_final = (sum(self.promedio_lista))/(self.conteo_promedio)
        self.escribir("Pasos", "Promedio", float(self.promedio_final))

    def mayor_diezmil(self, _medida):
        if _medida > 10000:
            self.mayor10000 += 1
            print("Mas de 10000", flush=True)
            self.escribir("Pasos", "+10000", int(self.mayor10000))

    def menor_cincomil(self, _medida):
        if _medida < 5000:
            self.menor5000 +=1
            print("Menos de 5000", flush=True)
            self.escribir("Pasos", "-5000", int(self.menor5000))
        else:
            self.escribir("Pasos", "-5000", int(self.menor5000))

    def mejor_dia(self, _medida):
        if _medida > self.mejor:
            print("Mejora", flush=True)
            self.mejor = _medida
            self.cont_mejor +=1
            self.mejor_racha = self.cont_mejor
            self.escribir("Pasos", "Mejor", int(self.mejor_racha))
        else:
            self.cont_mejor = 0

    def agregar_minimo(self, _medida):
        if _medida < self.valor_min:
            print("nuevo min", flush=True)
            self.valor_min = _medida
            self.escribir("Pasos", "Minimo", _medida)

## ## tomar medidas
    def tomar_medida(self, _mensaje):
        mensaje = _mensaje.split("=")
        medida = float(mensaje[-1])
        print("medida {}".format(medida))
        self.agregar_maximo(medida)
        self.agregar_promedio(medida)
        self.mayor_diezmil(medida)
        self.menor_cincomil(medida)
        self.agregar_minimo(medida)
        self.mejor_dia(medida)


    def escribir(self, tag, variable, valor):

        client = InfluxDBClient(url=self.influx_url, token=self.influx_token, org=self.influx_org)
        write_api = client.write_api(write_options=SYNCHRONOUS)

        punto = Point("Analitica").tag("Descriptivas", tag).field(variable,valor)
        write_api.write(bucket=self.influx_bucket, record=punto)

if __name__ == '__main__':
    analitica = Analitica()
    url = os.environ.get('AMQP_URL','amqp://guest:guest@rabbit:5672/%2f')
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue='mensajes')
    channel.queue_bind(exchange='amq.topic', queue='mensajes', routing_key='#')

    def callback(ch, method, properties, body):
        global analitica
        mensaje = body.decode("utf-8")
        print(" mensaje: {}".format(mensaje),flush=True)
        analitica.tomar_medida(mensaje)

    channel.basic_consume(queue='mensajes', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()
