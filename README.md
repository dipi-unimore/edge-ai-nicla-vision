# Anomaly Detection using Arduino's *Nicla Vision*

Anomaly detection prototype for standalone usage with the *Nicla Vision* board.

## Roadmap of the project

<p align="center">
    <img style="height: 500px" src="./assets/sketch.jpeg"/>
</p>

> Project's original sketch

### Areas of development

The project's development will be split into 3 areas:
* Connectivity
* Exploring the boards sensors
* Machine Vision

Future updates regarding the development will be made here.

## Connectivity

The board comes equipped with an antenna, and can connect to Bluetooth and WiFi. For our project, we chose to use MQTT and the *mosquitto* broker to subscribe and publish messages.

The design of the communication architecture can be seen below.

<p align="center">
    <img src="./assets/mqtt.png"/>
</p>

### Local broker

As seen in our repo's *mqtt_pub.py* code, the broker may run on the same machine as the board, where it can subscribe to any topic of choice. This can be done running ``mosquitto_sub -h localhost -t "<topic-name>" -v`` on a terminal, and, in your code, connecting to your machine's local ip address.

### External broker

To connect to a broker already running in a different machine, you'd connect to their local IP address (if the board and the machine are on the same WiFi), or you'd connect to their public IP or domain (if they are running on different connections), as can be seen on the example below.

> ``client = MQTTClient("openmv", "broker.university.edu", port=1883)``  
> ``client.connect()``

## Notes
* Since this is a didatic research, lots of "dead" code may be seen on the repository, as a means of registering the steps taken to achieve the final results. The file names and this documentation will always reflect this choice.

## Authorship
* Development: [Otávio Sbampato Andrade](https://github.com/otaviosbampato)
* Advisor: [Marco Picone](https://github.com/piconem)