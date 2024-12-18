#include <WiFi.h>
#include <PubSubClient.h>

// Define GPIO pins
#define Env1 37
#define Red 19
#define Yel 22
#define Grn 21

// Define the address pins
#define ADDR_PIN_1 13
#define ADDR_PIN_2 12
#define ADDR_PIN_3 14
#define ADDR_PIN_4 27
#define ADDR_PIN_5 26

int blinkState = LOW;
int totalSamples = 0; 
int count = 0;
int sampleLvl = 0;
int noiseLvl = 0;
int avgnoiseLvl = 0;

// Global variable to store the node ID (Table #)
int nodeID;

// Replace with your network credentials
const char* ssid = "Stingley_noise_meter";
const char* password = "BusyBee1962!";

// Replace with your MQTT broker IP address (the Raspberry Pi IP)
const char* mqtt_server = "10.42.0.1"; // Replace with Raspberry Pi's IP

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.setMinSecurity(WIFI_AUTH_WPA_PSK);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    blink_all();
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

int averageNoiseLvl(){
        sampleLvl = noiseLvl;
        totalSamples+= sampleLvl;
        count += 1;
        return totalSamples/count;
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  pinMode(Env1, INPUT);
  pinMode(Red, OUTPUT);
  pinMode(Yel, OUTPUT);
  pinMode(Grn, OUTPUT);

  // Initialize each address pin as input with pull-up resistor
  pinMode(ADDR_PIN_1, INPUT_PULLUP);
  pinMode(ADDR_PIN_2, INPUT_PULLUP);
  pinMode(ADDR_PIN_3, INPUT_PULLUP);
  pinMode(ADDR_PIN_4, INPUT_PULLUP);
  pinMode(ADDR_PIN_5, INPUT_PULLUP);
  
  // Determine the node ID once during setup
  nodeID = determineNodeID();

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

int determineNodeID() {
  // Read each pin and shift its binary position accordingly
  int id = (digitalRead(ADDR_PIN_1) << 4) | 
           (digitalRead(ADDR_PIN_2) << 3) | 
           (digitalRead(ADDR_PIN_3) << 2) | 
           (digitalRead(ADDR_PIN_4) << 1) | 
           (digitalRead(ADDR_PIN_5) << 0);
  
  return id;
}

void blink_all() {
  digitalWrite(Red, HIGH);
  digitalWrite(Yel, HIGH);
  digitalWrite(Grn, HIGH);
  delay(500);
  digitalWrite(Red, LOW);
  digitalWrite(Yel, LOW);
  digitalWrite(Grn, LOW);
}
void blink_led(int col, int delay) {
  static unsigned long lastBlink = 0;
  unsigned long curBlink = millis();
  if (curBlink - lastBlink > delay) {
        lastBlink = curBlink;

      // if the LED is off turn it on and vice-versa:
      if (blinkState == LOW) {
        blinkState = HIGH;
      } else {
        blinkState = LOW;
      }

      // set the LED with the ledState of the variable:
      digitalWrite(col, blinkState);
  }
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("ESP32Client" + char(nodeID)))  { //Change client to Table #
      Serial.println("connected");
      // Subscribe to a topic (optional)
      client.subscribe("test/topic" + char(nodeID)); //Change topic to Table #
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      for (int i = 0; i < 5; i++) { //Delay should add up to about 5 seconds, 2x500 ms 5 times per reconnect
        blink_all();
        delay(500);
      }
      //blink_all();
      //delay(4500);
    }
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  // debug mic
  //Serial.print(analogRead(Env1));
  //delay(2000);
  // Publish a message every 5 seconds
  static unsigned long lastMsg = 0;
  unsigned long now = millis();
  int mn = 1024;
  int mx = 0;
  int sum = 0;

  for (int i = 0; i < 10000; i++) {
    int val = analogRead(Env1);
    // sum += val;
    mn = min(mn, val);
    mx = max(mx, val);
  }
  // int avgnoiseLvl = (sum/10000);
  noiseLvl = (mx - mn);
  
  if (now - lastMsg > 1000) {
    lastMsg = now;
    //Change Table # in string
    String msg = "Table " + String(nodeID) + ", noise_level: " + String(noiseLvl) + ", average: " + String(avgnoiseLvl) + ", max: " + String(mx) + ", min: " + String(mn);    Serial.print("Publishing message: ");
    Serial.println(msg);
    client.publish("test/topic" + char(nodeID), msg.c_str()); //Change topic to table #
    totalSamples = 0;
    count = 0;
  }
  else{
    avgnoiseLvl = averageNoiseLvl();
  }

  if (client.connected()) {
    if(noiseLvl < 300){
      digitalWrite(Red, LOW);
      digitalWrite(Yel, LOW);
      blink_led(Grn, 50);
    }
    else if(noiseLvl >= 300 && noiseLvl < 500){
      digitalWrite(Red, LOW);
      digitalWrite(Grn, LOW);
      blink_led(Yel, 50);
    }
    else if(noiseLvl > 500){
      digitalWrite(Grn, LOW);
      digitalWrite(Yel, LOW);
      blink_led(Red, 50);
    }
  }
}
