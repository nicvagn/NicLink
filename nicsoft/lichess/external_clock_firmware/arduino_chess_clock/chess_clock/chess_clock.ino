/*
#  chess_clock is a part of NicLink
#
#  NicLink is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or ( at your option ) any later version.
#
#  NicLink is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with NicLink. If not, see <https://www.gnu.org/licenses/>.
*/
#define BLACK_TURN "|white|>>|black|"
#define WHITE_TURN "|white|<<|black|"

#include <LiquidCrystal.h>

const int rs = 12, en = 13, d4 = 8, d5 = 9, d6 = 10, d7 = 11;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

unsigned long whiteTime = 60000;
unsigned long blackTime = 60000;
unsigned long increment = 6000;
bool whiteToPlay = true;
unsigned long lastUpdate = 0;
bool gameOver = false;

void secondsToHMS(const uint32_t seconds, uint16_t &h, uint8_t &m, uint8_t &s) {
  s = seconds % 60;
  uint32_t minutes = seconds / 60;
  m = minutes % 60;
  h = minutes / 60;
}

void blackMoved() {
  whiteToPlay = true;
  lcd.setCursor(0, 0);
  lcd.print(WHITE_TURN);
  blackTime = blackTime + increment;
}

void whiteMoved() {
  whiteToPlay = false;
  lcd.setCursor(0, 0);
  lcd.print(BLACK_TURN);
  whiteTime = whiteTime + increment;
}

void whiteTimeOut() {
  gameOver = true;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("  TIME'S UP!  ");
  lcd.setCursor(0, 1);
  lcd.print("  Black Wins! ");
  Serial.println("Game Over: Black wins on time");
}

void blackTimeOut() {
  gameOver = true;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("  TIME'S UP!  ");
  lcd.setCursor(0, 1);
  lcd.print("  White Wins! ");
  Serial.println("Game Over: White wins on time");
}

void whiteCheckmated() {
  gameOver = true;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("   CHECKMATE   ");
  lcd.setCursor(0, 1);
  lcd.print("  Black Wins!   ");
  Serial.println("Game Over: White checkmated");
}

void blackCheckmated() {
  gameOver = true;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("   CHECKMATE   ");
  lcd.setCursor(0, 1);
  lcd.print("  White Wins!   ");
  Serial.println("Game Over: Black checkmated");
}

void displayTime() {
  unsigned int wTotalSec = whiteTime / 1000;
  unsigned int bTotalSec = blackTime / 1000;
  
  uint16_t wH, bH;
  uint8_t wM, wS, bM, bS;
  secondsToHMS(wTotalSec, wH, wM, wS);
  secondsToHMS(bTotalSec, bH, bM, bS);
  
  lcd.setCursor(0, 1);
  
  // White time
  if (wH > 0) {
    lcd.print(wH);
    lcd.print(":");
    if (wM < 10) lcd.print("0");
    lcd.print(wM);
    lcd.print(":");
    if (wS < 10) lcd.print("0");
    lcd.print(wS);
  } else {
    unsigned int wCenti = (whiteTime / 10) % 100;
    if (wM < 10) lcd.print("0");
    lcd.print(wM);
    lcd.print(":");
    if (wS < 10) lcd.print("0");
    lcd.print(wS);
    lcd.print(".");
    if (wCenti < 10) lcd.print("0");
    lcd.print(wCenti);
  }
  
  lcd.print("|");
  
  // Black time
  if (bH > 0) {
    lcd.print(bH);
    lcd.print(":");
    if (bM < 10) lcd.print("0");
    lcd.print(bM);
    lcd.print(":");
    if (bS < 10) lcd.print("0");
    lcd.print(bS);
  } else {
    unsigned int bCenti = (blackTime / 10) % 100;
    if (bM < 10) lcd.print("0");
    lcd.print(bM);
    lcd.print(":");
    if (bS < 10) lcd.print("0");
    lcd.print(bS);
    lcd.print(".");
    if (bCenti < 10) lcd.print("0");
    lcd.print(bCenti);
  }
  
  lcd.print("   "); // Clear any leftover characters
}

void setup() {
  Serial.begin(9600);
  lcd.begin(16, 2);
  lcd.print("|white|--|black|");
  lastUpdate = millis();
}

void loop() {
  // If game is over, stop processing
  if (gameOver) {
    return;
  }
  
  unsigned long currentTime = millis();
  
  if (Serial.available() > 0) {
    String msg = Serial.readString();
    if (whiteToPlay) {
      whiteMoved();
    } else {
      blackMoved();
    }
    lastUpdate = currentTime; // Reset timer after move
  }
  
  // Update time every 50ms
  if (currentTime - lastUpdate >= 50) {
    lastUpdate = currentTime;
    
    if (whiteToPlay) {
      if (whiteTime > 50) {
        whiteTime -= 50;
      } else {
        whiteTime = 0;
        whiteTimeOut();
        return;
      }
      Serial.print("w");
      Serial.println(whiteTime);
    } else {
      if (blackTime > 50) {
        blackTime -= 50;
      } else {
        blackTime = 0;
        blackTimeOut();
        return;
      }
      Serial.print("b");
      Serial.println(blackTime);
    }
    
    displayTime();
  }
}
