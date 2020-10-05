#define OFF 0
#define ON 1
#define DIMMING 2

#define ON_LENGTH (5*1000)
#define DIMMING_LENGTH (5*1000)

// Use two pins to drive two LEDs. Two leds on one pin are too close to 40 mA draw limit on atmega
const int led1 = 3;
const int led2 = 5;
const int dist = A0;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  pinMode(dist, INPUT);
  pinMode(led1, OUTPUT);
  pinMode(led2, OUTPUT);
  digitalWrite(led1, 0);
  digitalWrite(led2, 0);
}

int state = OFF;
long on_start;
int led_value;

void loop() {
  int distance = analogRead(dist);

  if (distance > 475) {
    state = ON;
    on_start = millis();
  } 
  if (state == ON && (millis() - on_start) < ON_LENGTH) { // LEDs on
    led_value = 255;
    digitalWrite(led1, 1);
    digitalWrite(led2, 1);
  } else if (state == ON && (millis() - on_start) < (ON_LENGTH + DIMMING_LENGTH)) { // Active stage off, start dimming
    state = DIMMING;
    on_start = millis();
  } else if (state == DIMMING && (millis() - on_start) < DIMMING_LENGTH) { // dimming
    analogWrite(led1, led_value);
    analogWrite(led2, led_value);
    float dim_pcnt = 1 -  ((float)(millis() - on_start + 1) / DIMMING_LENGTH);
    led_value = (int)(255.0 * dim_pcnt);
   } else { // turn off of not ON or DIMMING
    state = OFF;
    digitalWrite(led1, 0);
    digitalWrite(led2, 0);
  }
  
}
