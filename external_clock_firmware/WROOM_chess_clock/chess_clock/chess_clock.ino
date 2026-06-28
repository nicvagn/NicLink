// file: /data/git/niclink/external_clock_firmware/WROOM_chess_clock/chess_clock/chess_clock2.ino
#include <LiquidCrystal_I2C.h>
#include <Wire.h>

#define DEBUG T
//#define DEBUG_TICK T
// messages
#define WHITE_BLACK "|white|-|black| "
#define BLACK_TURN "|white|>|black| "
#define WHITE_TURN "|white|<|black| "
#define WHITE_WIN "  WHITE  WINS!   "
#define BLACK_WIN "  BLACK  WINS!   "
#define DRAW "  0.5/1  DRAW  "
#define GAME_OVER "   GAME  OVER   "
#define TIME_UP "   TIME'S UP!   "
// buttons
#define DEBOUNCE_DELAY 10
#define SDA_PIN 13
#define SCL_PIN 14
#define LCD_ADDR 0x27
#define LCD_ROWS 16
#define LCD_COL 2

// default times
#define B_START_TIME 600000
#define W_START_TIME 600000
#define W_START_INC 6000
#define B_START_INC 6000

// button bins
#define RESET_BTN_PIN 4
#define MOVE_MADE_PIN 5

/**
 * LiquidCrystal_I2C  Constructor
 *
 * @param LCD_ADDR	I2C slave address of the LCD display. Most likely
 * printed on the LCD circuit board, or look in the supplied LCD documentation.
 * @param LCD_COLS	Number of columns your LCD display has.
 * @param LCD_ROWS	Number of rows your LCD display has.
 */
LiquidCrystal_I2C lcd(LCD_ADDR, LCD_ROWS, LCD_COL);

// Button structure to hold all state
struct Button {
  uint8_t pin;
  int8_t curRead;
  int8_t lastState;
  uint32_t lastDebounceTime;
  const char *name;
};

Button resetBtn = {
  RESET_BTN_PIN,
  HIGH,
  HIGH,
  0,
  "Reset Button",
};

Button moveBtn = {
  MOVE_MADE_PIN,
  HIGH,
  HIGH,
  0,
  "Move Button",
};


// init times
uint32_t whiteStartingTimeMs = B_START_TIME;
uint32_t whiteStartingIncMs = W_START_INC;
uint32_t blackStartingTimeMs = B_START_TIME;
uint32_t blackStartingIncMs = B_START_INC;
// current times
uint32_t whiteTimeMs = whiteStartingTimeMs;
uint32_t whiteIncMs = whiteStartingIncMs;
uint32_t blackTimeMs = blackStartingTimeMs;
uint32_t blackIncMs = blackStartingIncMs;

bool connected = false;
bool whiteToPlay = true;
bool clockRunning = false;
uint32_t lastUpdate = 0;

void setup() {
  Wire.begin(SDA_PIN, SCL_PIN);
  // start serial connection
  Serial.begin(9600);
  while (!Serial) {
    delay(10);
  }

  lcd.init();
  lcd.backlight();
  reset();
  displayTime();
  lastUpdate = millis();
#ifdef DEBUG
  Serial.println("CLOCK READY");
#endif
  // button pins
  pinMode(moveBtn.pin, INPUT_PULLUP);
  pinMode(resetBtn.pin, INPUT_PULLUP);
}

// reset chess clock
void reset() {
  clockRunning = false;
  whiteToPlay = true;
  lastUpdate = 0;

  whiteTimeMs = whiteStartingTimeMs;
  whiteIncMs = whiteStartingIncMs;
  blackTimeMs = blackStartingTimeMs;
  blackIncMs = blackStartingIncMs;
  lcd.setCursor(0, 0);
  lcd.print(WHITE_BLACK);

  Serial.println("CLOCK RESET");
}


void displayWhiteTurn() {
  lcd.setCursor(0, 0);
  lcd.print(WHITE_TURN);
}
void doWhiteTurn(bool addInc) {
  displayBlackTurn();
  if (addInc) {
    whiteTimeMs += whiteIncMs;
  }
  whiteToPlay = false;
}
void displayBlackTurn() {
  lcd.setCursor(0, 0);
  lcd.print(BLACK_TURN);
}
void doBlackTurn(bool addInc) {
  displayWhiteTurn();
  if (addInc) {
    blackTimeMs += blackIncMs;
  }
  whiteToPlay = true;
}

void gameDone() {
  clockRunning = false;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(GAME_OVER);
  lcd.setCursor(0, 1);
  lcd.print(GAME_OVER);
  Serial.println("GAME_OVER");
}

void checkButton(Button &btn) {
  int reading = digitalRead(btn.pin);
  // If the reading changed, reset debounce timer
  if (reading != btn.curRead) {
    btn.lastDebounceTime = millis();
    btn.curRead = reading;
    // If enough time has passed, accept the reading as stable
    if ((millis() - btn.lastDebounceTime) > DEBOUNCE_DELAY) {
      // If the stable state has changed
      if (btn.curRead != btn.lastState) {
        btn.lastState = btn.curRead;
        if (btn.curRead == LOW) {
#ifdef DEBUG
          Serial.print(btn.name);
          Serial.println(" pressed");
#endif
          if (btn.pin == MOVE_MADE_PIN) {
            Serial.println("TODO move ptn");
            // TODO
          } else if (btn.pin == RESET_BTN_PIN) {
            reset();
          }
        }
      }
    }
  }
}


void secondsToHMS(uint16_t seconds, uint16_t &h, uint16_t &m, uint16_t &s) {
  s = seconds % 60;
  uint16_t minutes = seconds / 60;
  m = minutes % 60;
  h = minutes / 60;
}

void displayTime() {
  // convert from ms to seconds
  uint16_t wTotalSec = whiteTimeMs / 1000;
  uint16_t bTotalSec = blackTimeMs / 1000;

  // White and black hours, minutes and seconds
  uint16_t wH, bH;
  uint16_t wM, wS, bM, bS;
  secondsToHMS(wTotalSec, wH, wM, wS);
  secondsToHMS(bTotalSec, bH, bM, bS);

  lcd.setCursor(0, 1);

  // White time
  if (wH > 0) {
    lcd.print(wH);
    lcd.print(":");
    if (wM < 10)
      lcd.print("0");
    lcd.print(wM);
  } else {
    lcd.print(wM);
    lcd.print(":");
    if (wS < 10)
      lcd.print("0");
    lcd.print(wS);
  }
  // make to clear stale numbers
  lcd.print("   ");

  lcd.setCursor(8, 1);

  // Black time
  if (bH > 0) {
    lcd.print(bH);
    lcd.print(":");
    if (bM < 10)
      lcd.print("0");
    lcd.print(bM);
  } else {
    lcd.print(bM);
    lcd.print(":");
    if (bS < 10)
      lcd.print("0");
    lcd.print(bS);
  }
  // clear stale
  lcd.print("    ");
}


bool parseTime(String token, uint32_t &outTime, uint32_t &outInc) {
  // The string token will be in seconds, we will convert to ms for use with
  // millis
#ifdef DEBUG
  Serial.print("Token string: ");
  Serial.println(token);
#endif
  int plusIdx = token.indexOf('+');
  if (plusIdx > 0) {
    outTime = token.substring(0, plusIdx).toInt() * 1000UL;
    outInc = token.substring(plusIdx + 1).toInt() * 1000UL;
#ifdef DEBUG
    Serial.print("parseTime plusIdx > 0. outTime: ");
    Serial.print(outTime);
    Serial.print(" outInc: ");
    Serial.println(outInc);
#endif
  } else if (token.length() > 0) {
#ifdef DEBUG
    Serial.print("No inc. outTime:");
    Serial.print(outTime);
#endif
    outTime = token.toInt() * 1000UL;
    outInc = 0;
  } else {
#ifdef DEBUG
    Serial.println("Failed to parse token.");
#endif
    return false;
  }
  return true;
}

void processSerialCommand(String cmd) {
  cmd.trim();

#ifdef DEBUG
  Serial.print("Serial cmd: [");
  Serial.print(cmd);
  Serial.println("]");
#endif
  if (cmd.startsWith("TIME:")) {
    // Format: TIME:300+5;W        (both players: 300s + 5s increment; White to play)
    //         TIME:300+5,600+10;B (white: 300s+5s, black: 600s+10s;Black to play)
    //         TIME:300,600;B      (white: 300s, black: 600s, no increment; Black to play)
    int8_t commaIdx = cmd.indexOf(',');
    int8_t semiCommaIdx = cmd.indexOf(';');
    uint32_t wTime = 0, wInc = 0, bTime = 0, bInc = 0;
    bool valid = false;

    // figure out who is to play, W or B
    char toPlay = cmd.charAt(semiCommaIdx + 1);
    // increment does not need to be added
    if (toPlay == 'W') {
      doWhiteTurn(false);
    } else if (toPlay == 'B') {
      doBlackTurn(false);
    }

    if (commaIdx > 0) {
#ifdef DEBUG
      Serial.println("commaIdx > 0, [TIME:(black time)+(black inc),(white "
                     "time)+(white inc)] form");
#endif
      // Two separate tokens — white,black
      String whiteTime = cmd.substring(5, commaIdx);

#ifdef DEBUG
      Serial.print("whiteTime token: ");
      Serial.println(whiteTime);
      Serial.print("blackTime token: ");
#endif
      String blackTime = cmd.substring(commaIdx + 1, semiCommaIdx);

#ifdef DEBUG
      Serial.println(blackTime);
#endif
      valid = parseTime(whiteTime, wTime, wInc) && parseTime(blackTime, bTime, bInc);
    } else {
      // Single token - same time for both players
      String time = cmd.substring(5, semiCommaIdx);
      valid = parseTime(time, wTime, wInc);
      if (valid) {
        bTime = wTime;
        bInc = wInc;
      }
    }

    if (valid) {
      clockRunning = true;
      whiteTimeMs = wTime;
      blackTimeMs = bTime;
      whiteIncMs = wInc;
      blackIncMs = bInc;

      displayTime();
#ifdef DEBUG
      Serial.print("valid token: (");
      Serial.print(cmd);
      Serial.print(")");
#endif
    } else {
      Serial.println("ERROR: Invalid time");
    }
  } else if (cmd == "m") {
    clockRunning = true;
    if (whiteToPlay) {
      doWhiteTurn(true);
    } else {
      doBlackTurn(true);
    }
  } else if (cmd == "START") {
    reset();
    displayWhiteTurn();
    clockRunning = true;
  } else if (cmd == "BWON") {
    gameDone();
  } else if (cmd == "WWON") {
    gameDone();
  } else if (cmd == "DRAW") {
    gameDone();
  } else if (cmd == "OVER") {
    gameDone();
  } else if (cmd == "STOP" || cmd == "PAUSE") {
    clockRunning = false;

#ifdef DEBUG
    Serial.println("CLOCK_STOPPED");
#endif
  } else if (cmd == "RESET") {
    reset();
  } else if (cmd == "STATUS") {
    Serial.print("STATUS:");
    Serial.print(whiteTimeMs / 1000UL);
    Serial.print("+");
    Serial.print(whiteIncMs / 1000UL);
    Serial.print(":");
    Serial.print(blackTimeMs / 1000UL);
    Serial.print("+");
    Serial.print(blackIncMs / 1000UL);
    Serial.print(";");
    Serial.println(whiteToPlay ? "W" : "B");
    Serial.print("clock is: ");
    Serial.println(clockRunning ? "RUNNING" : "STOPPED");
  }
#ifdef DEBUG
  else {
    Serial.print("ERROR: cmd '");
    Serial.print(cmd);
    Serial.println("' not known.");
  }
#endif
}


void loop() {
  // Process serial commands
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    processSerialCommand(cmd);
  }
#ifdef DEBUG_TICK
  Serial.print("clockRunning is: ");
  Serial.println(clockRunning);
  Serial.print("!gameOver is: ");
  Serial.println(!gameOver);

  Serial.println("delay 5000");
  delay(5000);
  Serial.println("delay out");
#endif
  // Update time only if clock is running and game not over
  if (clockRunning) {
    uint32_t currentTime = millis();

    if (currentTime - lastUpdate >= 50) {
      lastUpdate = currentTime;

      if (whiteToPlay) {
        if (whiteTimeMs > 50) {
          whiteTimeMs -= 50;
        } else {
          gameDone();
          return;
        }
      } else {
        if (blackTimeMs > 50) {
          blackTimeMs -= 50;
        } else {
          gameDone();
          blackTimeMs = 0;
          return;
        }
      }
      displayTime();
    }
  }
  // check buttons
  checkButton(moveBtn);
  checkButton(resetBtn);
}

//  LocalWords:  WWON BWON
