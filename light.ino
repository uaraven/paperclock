#define OFF 0
#define ON 1
#define DIMMING 2

#define ON_LENGTH (5*1000)
#define DIMMING_LENGTH (5*1000)

const int led = 3;
const int dist = A0;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  pinMode(dist, INPUT);
  pinMode(led, OUTPUT);
  digitalWrite(led, 0);
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
  if (state == ON && (millis() - on_start) < ON_LENGTH) {
    led_value = 255;
    digitalWrite(led, 1);
  } else if (state == ON && (millis() - on_start) < (ON_LENGTH + DIMMING_LENGTH)) {
    state = DIMMING;
    on_start = millis();
  } else if (state == DIMMING && (millis() - on_start) < DIMMING_LENGTH) {
    analogWrite(led, led_value);
    float dim_pcnt = 1 -  ((float)(millis() - on_start + 1) / DIMMING_LENGTH);
    led_value = (int)(255.0 * dim_pcnt);
   } else {
    state = OFF;
    digitalWrite(led, 0);
  }
  
}
