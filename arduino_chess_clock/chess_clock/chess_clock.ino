#include <LiquidCrystal.h>
#include <Arduino.h>


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
//const float MSGTIMEOUT = 50000000.0;
const unsigned long BAUDRATE = 115200;
bool gameOver = false;

const char* SEPERATOR = '*';
const char* READYMESSAGE = "READY";
const char* ACKMESSAGE = "ACK";
const unsigned long TRANSMITINTERVAL = 1e6;

// what to do
char what_to_do[1] = "n"; // default to not doing anything

// FOR CUSTOM MESSAGES
// for the ascii to be displayed on the first ln
char lcd_ln_1_buff[16];
// and the second
char lcd_ln_2_buff[16];

// case '2'
void signalGameOver() {
  lcd.clear();
  gameOver = true;
  lcd.setCursor(0, 0);
  lcd.print("%%% GAMEOVER %%%");
}

// case '3' print a String to the LCD
void printSerialMessage() {

  lcd.clear();
  String message = Serial.readString();
  int mes_len = message.length();
  if( mes_len > 16 ) {
    //get the first line
    for(int i=0; i < 16; i++) {
      lcd_ln_1_buff[i] = message[i];
    }
    for(int i=0; i< 16; i++) {
      if(i <= (mes_len - 16)) {
        lcd_ln_2_buff[i] = message[(16 + i)]; // only chars >= 16
      } else {
        lcd_ln_2_buff[i];
      }
    }
    // ln 1
    lcd.setCursor(0,0);
    lcd.print(lcd_ln_1_buff);
    // ln 2
    lcd.setCursor(0,1);
    lcd.print(lcd_ln_2_buff);
  } else {
    // just print on one ln
    lcd.setCursor(0, 0);
    lcd.print(message);
  }
}
// case '4' start a new game
void newGame() {
  lcd.clear();
  gameOver = false;
  lcd.setCursor(0, 0);
  lcd.print("=== Nic-Link ===");
  lcd.setCursor(0, 1);
  lcd.print("$$$ New Game $$$");
}

// case '5'show the nl chessclock splash screan
void niclink_splash() {
  lcd.setCursor(0, 0);
  lcd.print("=== Nic-Link ===");
  lcd.setCursor(0, 1);
  lcd.print("]External Clock[");
}

//case '6'
void white_won() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("%%%% WINNER %%%%");
  lcd.setCursor(0, 1);
  lcd.print("= white victor =");
}

//case '7'
void black_won() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("%%%% WINNER %%%%");
  lcd.setCursor(0, 1);
  lcd.print("= black victor =");
}

// case '8'
void drawn_game() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("%%% GAMEOVER %%%");
  lcd.setCursor(0, 1);
  lcd.print("<<<<< DRAW >>>>>");
}

// initialize lcd and show splash
void lcd_init()
{
  lcd.begin(16, 2);
  Serial.setTimeout(TIMEOUT);  // in milli seconds

  // This must be the same baud rate as specified in the python serial object constructor
  Serial.begin(BAUDRATE);

  // show splash screen on startup
  niclink_splash();
}

int main() {
  // setup ardino and some house keeping idk
  init();

  // and lcd, and ardino Serial connect
  lcd_init();

  while(true) //(gameOver == false)
  {
    while(Serial.available() == false){
      // do nothing
    }

    Serial.readBytesUntil(SEPERATOR, what_to_do, 1);

    switch (what_to_do[0]) {
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
}
