# STYLEGUIDE-bridge 

Code for the bridge of the [STYLEGUIDE](https://github.com/SaverioNapolitano/STYLEGUIDE.git) project.

## Purpose 

The bridge acts as a go-between the [microcontroller](https://github.com/SaverioNapolitano/STYLEGUIDE-micro.git), the [mobile app](https://github.com/SaverioNapolitano/STYLEGUIDE-app.git) and the [server](https://github.com/SaverioNapolitano/STYLEGUIDE-server.git). It serves both as MQTT client (receiving messages from the mobile app) and HTTP client (building packets and sending them to the server and updating the current state).

The bridge also allows the user to control their lights using their voice.

## How it works 

The bridge and the microcontroller talk to each other over a serial connection, the communication with the mobile app happens over MQTT while the communication with the server exploits the HTTP protocol.

### Serial Protocol

The bridge waits for messages from the micro on the serial (more details [here](https://github.com/SaverioNapolitano/STYLEGUIDE-micro?tab=readme-ov-file#serial-protocol)) and then processes them. 

#### Process Message

When the bridge receives a message from the micro, four things can happen:
1. the bridge has to build (and send) a packet, start the timer and update the current state
2. the bridge has to build (and send) a packet and update the current state
3. the bridge has to start the timer and update the current state
4. the bridge has to update the current state

These cases are described by the following finite state machine (FSM) based on the type of the messages (since the update of the current state is always executed it is not shown). Both the current received message and the previous received message are evaluated to decide what to do: ![](images/message_fsm.png)

### MQTT 

The bridge receives MQTT messages from the mobile application regarding the light status, its color and intensity (or about whether to enable or disable the auto mode) and processes them in order to obtain the command to forward to the microcontroller over serial communication.

### HTTP 

The bridge builds and sends data packets to the server to store info about user habits and consumption, the server uses these info to compute relevant data for the user (see [here](https://github.com/SaverioNapolitano/STYLEGUIDE-server?tab=readme-ov-file#styleguide-server))

Data packets are basically rows of the database and their format is the following: ![](images/data.png)

Furthermore, the bridge updates the current state of the house by sending the server the following information: ![](images/state.png)

### Voice Assistant

To control the light status and color using only your voice, the bridge features the voice assistant **Chuck** ([why Chuck? (Italian)](https://www.barzellette.net/frasi-chuck-norris.html)). 

Just call it (`Hey Chuck` or simply `Chuck`) and ask it to turn on/off your lights or to change the color of a light. 

Currently Chuck understands the following commands:
- turn on a light 
- turn off a light 
- change the light color to `COLOR`

and supports the following colors:
- white 
- red 
- green 
- blue 
- pink 
- purple
- yellow
- orange 

> [!NOTE]
> Chuck speaks only English.
