#include <LiquidCrystal.h>


/*
lcd.setCursor(0, 0); // top left

lcd.setCursor(15, 0); // top right

lcd.setCursor(0, 1); // bottom left

lcd.setCursor(15, 1); // bottom right
*/

// initialize the library by associating any needed LCD interface pin
// with the arduino pin number it is connected to
const int rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);



const float TIMEOUT = 100.0;
const float MSGTIMEOUT = 500000.0;
const unsigned long BAUDRATE = 115200;
bool gameOver = false;

void setup() {
  lcd.begin(16, 2);
  Serial.setTimeout(TIMEOUT); // in milli seconds

  // This must be the same baud rate as specified in the python serial object constructor
  Serial.begin(BAUDRATE);

  // show splash screen on startup
  niclink_splash();

}
// show the nl chessclock splash screan
void niclink_splash() {
  lcd.setCursor(0,0);
  lcd.print("=== Nic-Link ===");
  lcd.setCursor(0,1);
  lcd.write(byte(0));  //does the column, idk look's good
  lcd.print("External Clock");
  lcd.write(byte(0));
}

void showTimestamp() {
  // Check if there is something to receive
  if (Serial.available()) {
    lcd.clear();
    // NicLink will first send whites time, then in a seperate transmission send black's time
    String line_1 = Serial.readStringUntil('*');
    lcd.setCursor(1,0);
    lcd.print(line_1);
  }

  //signal that we are ready for black's time
  Serial.write(1);

  if(Serial.available()) {
    String line_2 = Serial.readStringUntil('*');
    lcd.setCursor(1,1);
    lcd.print(line_2);
  }
}

void signalGameOver() {
  gameOver = true;
}
// start a new game
void newGame() {
  lcd.clear();
  niclink_splash();
  gameOver = false;
}

// print a String to the LCD
void printSerialMessage() {

  lcd.clear();
  delay(TIMEOUT);
  if(Serial.available()) {
    String message = Serial.readStringUntil('*');
    lcd.setCursor(1,0);
    lcd.print(message);
  }

  delay(MSGTIMEOUT); // PAUSE FOR TIME TO READ MSG

}

void loop() {

  char whatToDo = 9;

  if (Serial.available()) {
    whatToDo = Serial.read();
  }

  switch (whatToDo) {
    case '1':
      // asking for time
      if(gameOver) { // if the game is over, do not update ts
        break;
      }
      showTimestamp();
      break;
    case '2':
      signalGameOver();
      break;
    case '3':
      // show a str on LED read from Serial
      printSerialMessage();
      break;
    case '4':
      // start a new game
      newGame();
      break;
  }
}

