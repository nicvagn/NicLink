/*
#  chess_clock is a part of NicLink
#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.
*/

#define RESIGN_BUTTON 2
#define SEEK_BUTTON 3
#define LCD_CLEAR_BUTTON  4
#define BUZZER_PIN 6
#define RESIGN_SIG "^^^"
#define SEEK_SIG "(})"
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
const int rs = 12, en = 11, d4 = 10, d5 = 9, d6 = 8, d7 = 7;
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

// defnined here so it can be used below
void buzzer();

//case '1' clearLCD
void clearLCD() {
    lcd.clear();
    Serial.println("lcd cleared");
}
// case '2'
void signalGameOver() {
  lcd.clear();
  gameOver = true;
  lcd.setCursor(0, 0);
  lcd.print("%%% GAMEOVER %%%");
  buzzer();
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
    for(int i=0; i < 16; i++) {
      if(i <= (mes_len - 16)) {
        lcd_ln_2_buff[i] = message[(16 + i)]; // only chars >= 16
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

  Serial.flush();
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
  buzzer();
}

//case '7'
void black_won() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("%%%% WINNER %%%%");
  lcd.setCursor(0, 1);
  lcd.print("= black victor =");
  buzzer();
}

// case '8'
void drawn_game() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("%%% GAMEOVER %%%");
  lcd.setCursor(0, 1);
  lcd.print("<<<<< DRAW >>>>>");
  buzzer();
}
// buzzer - activate noise case 9 
void buzzer() {
  //buzzer high
  digitalWrite(BUZZER_PIN, HIGH);
  delay(500);
  digitalWrite(BUZZER_PIN, LOW);
}
//bound to button interupt
void resignGame() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("%%% GAMEOVER %%%");
  lcd.setCursor(0, 1);
  lcd.print("<<< RESIGNED >>>");
  Serial.println(RESIGN_SIG);
  Serial.flush();
}
//bound to button interupt
void seekGame() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("///// SEEK /////");
  lcd.setCursor(0, 1);
  lcd.print("  FINDING GAME  ");
  Serial.println(SEEK_SIG);
  Serial.flush();
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

  //set up interupt pins TODO python side etc
  pinMode(RESIGN_BUTTON, INPUT_PULLUP);
  // trigger when button pressed, but not when released
  attachInterrupt(digitalPinToInterrupt(RESIGN_BUTTON), resignGame, FALLING);

  //SEEK button
  pinMode(SEEK_BUTTON, INPUT_PULLUP);
  // trigger when button pressed, but not when released
  attachInterrupt(digitalPinToInterrupt(SEEK_BUTTON), clearLCD, FALLING);

  //clear button (non interupt)
  pinMode(LCD_CLEAR_BUTTON, INPUT_PULLUP);

  //buzzer pin
  pinMode(BUZZER_PIN, OUTPUT);

  byte clear_sig = 1;
  while(true) //(gameOver == false)
  {
    while(Serial.available() == false){
      // do nothing
    }

    Serial.readBytesUntil(SEPERATOR, what_to_do, 1);

    switch (what_to_do[0]) {
      case '1':
        lcd.clear();
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
      case '9':
        // activate buzzer
        buzzer();
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
