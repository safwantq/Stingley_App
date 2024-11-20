#include <WiFi.h>
#include <PubSubClient.h>
#include <driver/timer.h>

// Define GPIO Pins
#define Env1 37
#define Red 19
#define Yel 21
#define Grn 22
#define ADDR_PIN_1 13
#define ADDR_PIN_2 12
#define ADDR_PIN_3 14
#define ADDR_PIN_4 27
#define ADDR_PIN_5 26

#define BLINK_INTERVAL 200          // Blink interval in milliseconds
#define PAUSE_INTERVAL 1500         // Pause interval in milliseconds

// Global variable to store the node ID
int nodeID;

const int LED_PIN = 19;             // Define LED pin (change to the actual pin connected to LED)
volatile int blinkCount = 0;        // Tracks the current blink count in each cycle
volatile bool blinkState = LOW;     // Current LED state (on[LOW] or off[HIGH])
volatile bool blinkPause = false;   // Flag to indicate if the pause period is active

hw_timer_t *timer = NULL;           // Pointer to the hardware timer

//int blinkState = LOW;
int totalSamples = 0; 
int count = 0;
int sampleLvl = 0;
int noiseLvl = 0;
int avgnoiseLvl = 0;

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
  }

  // Blink LED's twice to indicate Wifi connected & disable timer interrupt (nodeID blink interrupt)
  blink_all();
  delay(500);
  blink_all();
  timerAlarmDisable(timer);  // Temporarily disables the timer interrupt
  
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

// ***************************************Interrupt Routine to Blink LEDs to indicate the nodeID*****************************
// Interrupt service routine for the nodeID blink timer
void IRAM_ATTR onTimer() {
  if (!blinkPause) {
    // If we are not in pause mode, toggle LED up to `nodeID` times with BLINK_INTERVAL
    if (blinkCount < nodeID) {
      blinkState = !blinkState;           // Toggle the LED state (on/off)
      digitalWrite(LED_PIN, blinkState);
      
      // Increase the blink count only when LED is turned on
      if (blinkState) {
        blinkCount++;                 // Increment blink count each on-cycle
      }
    } else {
      // If `x` blinks are completed, enter pause state
      blinkPause = true;                 // Set pause flag
      blinkCount = 0;                 // Reset blink count for the next cycle
      blinkState = LOW;                 // Turn off the LED
      digitalWrite(LED_PIN, blinkState);
      
      // Set timer to PAUSE_INTERVAL for the pause duration
      timerWrite(timer, 0);           // Reset the timer count
      timerAlarmWrite(timer, PAUSE_INTERVAL * 1000, false);  // Set to pause interval in microseconds
      timerAlarmEnable(timer);        // Enable timer for the pause interval
    }
  } else {
    // If in pause mode, reset to blinking mode after PAUSE_INTERVAL
    blinkPause = false;                  // Exit pause state
    timerWrite(timer, 0);             // Reset timer count
    timerAlarmWrite(timer, BLINK_INTERVAL * 1000, true);  // Set timer back to blink interval in microseconds
  }
}
// ************************************************************************

void setup() {
  // Initialize each address pin as input with pull-up resistor
  pinMode(ADDR_PIN_1, INPUT_PULLUP);
  pinMode(ADDR_PIN_2, INPUT_PULLUP);
  pinMode(ADDR_PIN_3, INPUT_PULLUP);
  pinMode(ADDR_PIN_4, INPUT_PULLUP);
  pinMode(ADDR_PIN_5, INPUT_PULLUP);
  
  // Determine the node ID once during setup
  nodeID = determineNodeID();
    
  Serial.begin(115200);
  pinMode(Env1, INPUT);
  pinMode(Red, OUTPUT);
  pinMode(Yel, OUTPUT);
  pinMode(Grn, OUTPUT);
  digitalWrite(Red, LOW);   // Test & Ensure ALL LED's start in the off state
  digitalWrite(Grn, HIGH);
  delay(500);
  digitalWrite(Grn, LOW);
  digitalWrite(Yel, HIGH);
  delay(500);
  digitalWrite(Yel, LOW);

  Serial.println("");
  Serial.print("***TABLE #" + String(nodeID) + "***");

  // Initialize the timer interrupt with a BLINK_INTERVAL & Node ID flash sequence
  timer = timerBegin(0, 80, true);                      // Use timer 0, prescaler 80, count up
  timerAttachInterrupt(timer, &onTimer, true);          // Attach onTimer function to timer interrupt
  timerAlarmWrite(timer, BLINK_INTERVAL * 1000, true);  // Set timer to BLINK_INTERVAL in microseconds
  timerAlarmEnable(timer);                              // Enable the timer alarm

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

/*
 * determineNodeID() - Reads the binary states of five GPIO pins to calculate a unique node ID.
 * Each pin represents a binary digit, with GPIO13 as the most significant bit (MSB)
 * and GPIO26 as the least significant bit (LSB). The function combines these
 * states to produce a unique ID in the range of 0-31, based on pin states.
 */
int determineNodeID() {
  // Read each pin and shift its binary position accordingly
  int id = (!digitalRead(ADDR_PIN_5) << 4) | 
           (!digitalRead(ADDR_PIN_4) << 3) | 
           (!digitalRead(ADDR_PIN_3) << 2) | 
           (!digitalRead(ADDR_PIN_2) << 1) | 
           (!digitalRead(ADDR_PIN_1) << 0);
  
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
  timerAlarmEnable(timer);                  // Enable the timer alarm
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect(("ESP32Client" + String(nodeID)).c_str())) {
    //if (client.connect("ESP32Client" + String(nodeID)))  {  //Change client to Table #
      Serial.println("connected");
      // Subscribe to a topic (optional)
      //client.subscribe("test/topic" + String(nodeID));      //Change topic to Table #
      client.subscribe(("test/topic" + String(nodeID)).c_str());
    } else {
      timerAlarmEnable(timer);              // renable the nodeID Blink timer alarm until a sucessful MQTT connection
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      for (int i = 0; i < 5; i++) {         //Delay should add up to about 5 seconds, 2x500 ms 5 times per reconnect
        //blink_all();
        delay(500);
      }
      timerAlarmDisable(timer);             // Temporarily disables the nodeID Blink timer alarm (interrupt routine)
      blink_all();                          // Blink once then ensure all LEDs are OFF
    }
  }
  // Blink LED's twice to indicate Wifi reconnect & disable timer interrupt (nodeID blink interrupt)
  blink_all();
  delay(500);
  blink_all();
  timerAlarmDisable(timer);  // Temporarily disables the timer interrupt
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
    client.publish("test/topic4", msg.c_str()); //Change topic to table #
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
