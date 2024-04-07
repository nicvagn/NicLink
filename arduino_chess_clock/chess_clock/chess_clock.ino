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

const float TIMEOUT = 80.0;  // slightly shorter than python timeout
const float MSGTIMEOUT = 50000000.0;
const unsigned long BAUDRATE = 115200;
bool gameOver = false;

void setup() {
  lcd.begin(16, 2);
  Serial.setTimeout(TIMEOUT);  // in milli seconds

  // This must be the same baud rate as specified in the python serial object constructor
  Serial.begin(BAUDRATE);

  // show splash screen on startup
  //niclink_splash();

  niclink_splash();
}


// case '1'
void showTimestamp() {
  // Check if there is something to receive
  if (Serial.available()) {
    lcd.clear();
    // NicLink will first send whites time, then in a seperate transmission send black's time
    String line_1 = Serial.readStringUntil('*');
    lcd.setCursor(1, 0);
    lcd.print(line_1);
  }

  //signal that we are ready for black's time
  Serial.write(1);

  if (Serial.available()) {
    String line_2 = Serial.readStringUntil('*');
    lcd.setCursor(1, 1);
    lcd.print(line_2);
  }

  return;
}

// case '2'
void signalGameOver() {
  lcd.clear();
  gameOver = true;
  lcd.setCursor(0, 0);
  lcd.print("%%% GAME OVER %%%");

  return;
}

// case '3' print a String to the LCD
void printSerialMessage() {

  lcd.clear();
  String message = Serial.readString();
  lcd.setCursor(1, 0);
  lcd.print(message);
  delay(MSGTIMEOUT);  // PAUSE FOR TIME TO READ MSG
  return;
}
// case '4' start a new game
void newGame() {
  lcd.clear();
  niclink_splash();
  gameOver = false;
  return;
}

// case '5'show the nl chessclock splash screan
void niclink_splash() {
  lcd.setCursor(0, 0);
  lcd.print("=== Nic-Link ===");
  lcd.setCursor(0, 1);
  lcd.print("]External Clock[");
  return;
}

//case '6'
void white_won() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("%%%% WINNER %%%%");
  lcd.setCursor(0, 1);
  lcd.print("= white victor =");
  return;
}

//case '7'
void black_won() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("%%%% WINNER %%%%");
  lcd.setCursor(0, 1);
  lcd.print("= black victor =");
  return;
}

// case '8'
void drawn_game() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("%%% GAMEOVER %%%");
  lcd.setCursor(0, 1);
  lcd.print("<<<<< DRAW >>>>>");
  return;
}

void loop() {

  char whatToDo = 'x';

  whatToDo = Serial.read();


  switch (whatToDo) {
    case '1':
      // asking for time
      if (gameOver) {  // if the game is over, do not update ts
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
    case '5':
      // show the splay
      niclink_splash();
      break;
    case '6':
      // white one, and the game is over
      white_won();
      break;
    case '7':
      // black won the game
      black_won();
      break;
    case '8':
      // game is a draw
      drawn_game();
      break;
    case '@':
      //say hello
      lcd.clear();
      lcd.setCursor(1, 0);
      lcd.print("Hi there");
      break;
  }
}
