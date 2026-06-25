// file: /data/git/niclink/standalone_chessclock/external_clock_firmware/WROOM_chess_clock/chess_clock/chess_clock.ino
#include <LiquidCrystal_I2C.h>
#include <Wire.h>

//define DEBUG T
// messages
#define WHITE_BLACK "|white|-|black| "
#define BLACK_TURN "|white|>|black| "
#define WHITE_TURN "|white|<|black| "
#define WHITE_WIN "  WHITE  Wins!   "
#define BLACK_WIN "  BLACK  Wins!   "
#define DRAW "  0.5/1  DRAW  "
#define GAMEOVER "   GAME  OVER   "
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
#define W_INCREMENT 6000
#define B_INCREMENT 6000

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

enum Colour { white,
              black };

// Button structure to hold all state
struct Button {
  uint8_t pin;
  int curRead;
  int lastState;
  unsigned long lastDebounceTime;
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


uint32_t whiteTimeMs = W_START_TIME;
uint32_t whiteIncMs = W_INCREMENT;
uint32_t blackTimeMs = B_START_TIME;
uint32_t blackIncMs = B_INCREMENT;

bool connected = false;
bool whiteToPlay = true;
uint32_t lastUpdate = 0;
bool gameOver = false;
bool clockRunning = false;

void startClock() {
  clockRunning = true;
  gameOver = false;
  lastUpdate = millis();
  lcd.setCursor(0, 0);
  lcd.print(WHITE_TURN);
#ifdef DEBUG
  Serial.println("CLOCK_STARTED");
#endif
}

void secondsToHMS(uint32_t seconds, uint16_t &h, uint16_t &m, uint16_t &s) {
  s = seconds % 60;
  uint32_t minutes = seconds / 60;
  m = minutes % 60;
  h = minutes / 60;
}

void blackMoved() {
  whiteToPlay = true;
  lcd.setCursor(0, 0);
  lcd.print(WHITE_TURN);
  blackTimeMs = blackTimeMs + blackIncMs;
}

void whiteMoved() {
  whiteToPlay = false;
  lcd.setCursor(0, 0);
  lcd.print(BLACK_TURN);
  whiteTimeMs = whiteTimeMs + whiteIncMs;
}

void whiteTimeOut() {
  whiteTimeMs = 0;
  gameOver = true;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(TIME_UP);
  lcd.setCursor(0, 1);
  lcd.print(BLACK_WIN);
  Serial.println("Game Over: Black wins on time");
}

void blackTimeOut() {
  whiteTimeMs = 0;
  gameOver = true;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(TIME_UP);
  lcd.setCursor(0, 1);
  lcd.print(WHITE_WIN);
  Serial.println("Game Over: White wins on time");
}

void whiteCheckmated() {
  gameOver = true;
  clockRunning = false;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("   CHECKMATE   ");
  lcd.setCursor(0, 1);
  lcd.print(BLACK_WIN);
  Serial.println("Game over: black wins by checkmate.");
}

void blackCheckmated() {
  gameOver = true;
  clockRunning = false;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("   CHECKMATE   ");
  lcd.setCursor(0, 1);
  lcd.print("  White Wins!   ");
  Serial.println("Game over: white wins by checkmate.");
}

void draw() {
  gameOver = true;
  clockRunning = false;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(DRAW);
  lcd.setCursor(0, 1);
  lcd.print(DRAW);
  Serial.println("Game over: Draw");
}

void gameDone() {
  // if game is over, do not process
  if (gameOver) {
    return;
  }
  gameOver = true;
  clockRunning = false;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(GAMEOVER);
  lcd.setCursor(0, 1);
  lcd.print(GAMEOVER);
  Serial.println("GAME_OVER:UNKNOWN");
}

void displayTime() {
  // convert from ms to seconds
  uint32_t wTotalSec = whiteTimeMs / 1000;
  uint32_t bTotalSec = blackTimeMs / 1000;

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

void moveMade() {
  if (gameOver) {
    gameOver = false;
  }

  if (!clockRunning) {
    startClock();
    return;
  }
  if (whiteToPlay) {
    whiteMoved();
  } else if (!gameOver) {
    blackMoved();
  }
}

void reset() {
  whiteTimeMs = W_START_TIME;
  blackTimeMs = B_START_TIME;
  whiteIncMs = W_INCREMENT;
  blackIncMs = B_INCREMENT;
  whiteToPlay = true;
  gameOver = false;
  clockRunning = false;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(WHITE_BLACK);
  displayTime();
#ifdef DEBUG
  Serial.println("CLOCK_RESET");
#endif
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

  // simple move command. The player to move is tracked
  if (cmd == "m") {
    moveMade();
    // set time for both players
  } else if (cmd.startsWith("TIME:")) {
    // Format: TIME:300+5        (both players: 300s + 5s increment)
    //         TIME:300+5,600+10 (white: 300s+5s, black: 600s+10s)
    //         TIME:300,600      (white: 300s, black: 600s, no increment)
    int commaIndex = cmd.indexOf(',');
    uint32_t wTime = 0, wInc = 0, bTime = 0, bInc = 0;
    bool valid = false;

    if (commaIndex > 0) {
#ifdef DEBUG
      Serial.println("commaIndex > 0, [TIME:(black time)+(black inc),(white "
                     "time)+(white inc)] form");
#endif
      // Two separate tokens — white,black
      String whiteTime = cmd.substring(5, commaIndex);

#ifdef DEBUG
      Serial.print("whiteTime token: ");
      Serial.println(whiteTime);
      Serial.print("blackTime token: ");
#endif
      String blackTime = cmd.substring(commaIndex + 1);
#ifdef DEBUG
      Serial.println(blackTime);
#endif
      valid = parseTime(whiteTime, wTime, wInc) && parseTime(blackTime, bTime, bInc);
    } else {
      // Single token - same time for both players
      String time = cmd.substring(5);
      valid = parseTime(time, wTime, wInc);
      if (valid) {
        bTime = wTime;
        bInc = wInc;
      }
    }

    if (valid) {
      whiteTimeMs = wTime;
      blackTimeMs = bTime;
      whiteIncMs = wInc;
      blackIncMs = bInc;

      lcd.setCursor(0, 0);
      displayTime();
#ifdef DEBUG
      Serial.println("valid token.");
      Serial.print("TIME_SET:W=");
      Serial.print(wTime);
      Serial.print("+");
      Serial.print(wInc);
      Serial.print(",B=");
      Serial.print(bTime);
      Serial.print("+");
      Serial.println(bInc);
#endif
    } else {
      Serial.println("ERROR: Invalid time");
    }
  } else if (cmd == "BMATE") {
    blackCheckmated();
  } else if (cmd == "WMATE") {
    whiteCheckmated();
  } else if (cmd == "DRAW") {
    draw();
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
    Serial.print(":");
    Serial.print(clockRunning ? "RUNNING" : "STOPPED");
    Serial.print(":");
    Serial.println(whiteToPlay ? "WHITE" : "BLACK");
  } else if (cmd == "OVER") {
    gameDone();
  }
#ifdef DEBUG
  else {
    Serial.print("ERROR: cmd '");
    Serial.print(cmd);
    Serial.println("' not known.");
  }
#endif
}

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
  Serial.println("CLOCK_READY");
#endif
  // button pins
  pinMode(moveBtn.pin, INPUT_PULLUP);
  pinMode(resetBtn.pin, INPUT_PULLUP);
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
            moveMade();
          } else if (btn.pin == RESET_BTN_PIN) {
            reset();
          }
        }
      }
    }
  }
}

void loop() {
  // Process serial commands
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    processSerialCommand(cmd);
  }

  // Update time only if clock is running and game not over
  if (clockRunning && !gameOver) {
    uint32_t currentTime = millis();

    if (currentTime - lastUpdate >= 50) {
      lastUpdate = currentTime;

      if (whiteToPlay) {
        if (whiteTimeMs > 50) {
          whiteTimeMs -= 50;
        } else {
          whiteTimeOut();
          return;
        }
      } else {
        if (blackTimeMs > 50) {
          blackTimeMs -= 50;
        } else {
          blackTimeOut();
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

//  LocalWords:  BMATE commaIndex addr greenBtn outTime outInc
//  LocalWords:  whiteTime blackTime parseTime
