// file: /data/git/niclink/standalone_chessclock/external_clock_firmware/WROOM_chess_clock/chess_clock/chess_clock.ino
#include <LiquidCrystal_I2C.h>
#include <Wire.h>

// messages
#define WHITE_BLACK "|white|  |black|"
#define BLACK_TURN "|white|>>|black|"
#define WHITE_TURN "|white|<<|black|"
#define WHITE_WIN "  WHITE Wins!   "
#define BLACK_WIN "  BLACK Wins!   "
#define DRAW "  0.5/1  DRAW  "
#define GAMEOVER "  GAME  OVER   "

// buttons
#define SDA_PIN 13
#define SCL_PIN 14
#define LCD_ADDR 0x27
#define LCD_ROWS 16
#define LCD_COL 2

// default times
#define B_START_TIME  60000
#define W_START_TIME  60000
#define W_INCREMENT  6000
#define B_INCREMENT  6000

#define RESET_BTN_PIN 4
#define MOVE_MADE_PIN 5

/**
 * LiquidCrystal_I2C  Constructor
 *
 * @param LCD_ADDR	I2C slave address of the LCD display. Most likely printed on the
 *					LCD circuit board, or look in the supplied LCD documentation.
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
  bool holdKey;
};

Button resetBtn = {
  RESET_BTN_PIN,
  HIGH,
  HIGH,
  0,
  "Reset Button",
  false,
};
Button moveBtn = {
  MOVE_MADE_PIN,
  HIGH,
  HIGH,
  0,
  "Move Button",
  false,
};

unsigned long whiteTimeMs = W_START_TIME;
unsigned long whiteIncrement = W_INCREMENT;
unsigned long blackTimeMs = B_START_TIME;
unsigned long blackIncrement = B_INCREMENT;

bool connected = false;
bool whiteToPlay = true;
unsigned long lastUpdate = 0;
bool gameOver = false;
bool clockRunning = false;


void startClock() {
  clockRunning = true;
  gameOver = false;
  lastUpdate = millis();
  lcd.setCursor(0, 0);
  lcd.print(WHITE_TURN);
  Serial.println("CLOCK_STARTED");
}

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
  blackTimeMs = blackTimeMs + blackIncrement;
}

void whiteMoved() {
  whiteToPlay = false;
  lcd.setCursor(0, 0);
  lcd.print(BLACK_TURN);
  whiteTimeMs = whiteTimeMs + whiteIncrement;
}

void whiteTimeOut() {
  gameOver = true;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("  TIME'S UP!  ");
  lcd.setCursor(0, 1);
  lcd.print(BLACK_WIN);
  Serial.println("Game Over: Black wins on time");
}

void blackTimeOut() {
  gameOver = true;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("  TIME'S UP!  ");
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
  Serial.println("GAME_OVER:BLACK_WINS");
}

void blackCheckmated() {
  gameOver = true;
  clockRunning = false;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("   CHECKMATE   ");
  lcd.setCursor(0, 1);
  lcd.print("  White Wins!   ");
  Serial.println("GAME_OVER:WHITE_WINS");
}

void draw() {
  gameOver = true;
  clockRunning = false;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(DRAW);
  lcd.setCursor(0, 1);
  lcd.print(DRAW);
  Serial.println("GAME_OVER:DRAW");
}

void gameDone() {
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
  unsigned int wTotalSec = whiteTimeMs / 1000;
  unsigned int bTotalSec = blackTimeMs / 1000;

  //White and black hours, minutes and seconds
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
    unsigned int wCenti = (whiteTimeMs / 10) % 100;
    lcd.print(wM);
    lcd.print(":");
    if (wS < 10) lcd.print("0");
    lcd.print(wS);
    lcd.print(".");
    if (wCenti < 10) lcd.print("0");
    lcd.print(wCenti);
  }

  lcd.print("  ");

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
    unsigned int bCenti = (blackTimeMs / 10) % 100;
    lcd.print(bM);
    lcd.print(":");
    if (bS < 10) lcd.print("0");
    lcd.print(bS);
    lcd.print(".");
    if (bCenti < 10) lcd.print("0");
    lcd.print(bCenti);
  }
}

void moveMade() {
  if (!clockRunning) {
    startClock();
    return;
  }
  if (!gameOver && whiteToPlay) {
    whiteMoved();
  } else if (!gameOver) {
    blackMoved();
  }
}

void reset() {
  whiteTimeMs = W_START_TIME;
  blackTimeMs = B_START_TIME;
  whiteIncrement = W_INCREMENT;
  blackIncrement = B_INCREMENT;
  whiteToPlay = true;
  gameOver = false;
  clockRunning = false;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(WHITE_BLACK);
  displayTime();
  Serial.println("CLOCK_RESET");
}

bool parseTime(String token, unsigned long &outTime, unsigned long &outInc) {
  int plusIdx = token.indexOf('+');
  if (plusIdx > 0) {
    outTime = token.substring(0, plusIdx).toInt() * 1000UL;
    outInc = token.substring(plusIdx + 1).toInt() * 1000UL;
  } else if (token.length() > 0) {
    outTime = token.toInt() * 1000UL;
    outInc = 0;
  } else {
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
    // Format: TIME:{time in milliseconds}+{Increment in milliseconds}
    //         TIME:{w_time in ms}+{w_inc in ms},{b_time in ms}+{b_inc in ms}
    //         TIME:300000+5000,600000+10000 (white: 300s+5s, black: 600s+10s)
    //         TIME:300000,600000   (white: 300s, black: 600s, no increment)
    int commaIndex = cmd.indexOf(',');
    unsigned long wTime = 0, wInc = 0, bTime = 0, bInc = 0;
    bool valid = false;

    if (commaIndex > 0) {
#ifdef DEBUG
      Serial.println("commaIndex > 0, [TIME:(black time)+(black inc),(white time)+(white inc)] form");
#endif
      // Two separate tokens — white,black
      String whiteTime = cmd.substring(5, commaIndex);
      String blackTime = cmd.substring(commaIndex + 1);
      valid = parseTime(whiteTime, wTime, wInc) && parseTime(blackTime, bTime, bInc);
    } else {
      // Single token — same time for both players
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
      whiteIncrement = wInc;
      blackIncrement = bInc;

      lcd.setCursor(0, 0);
      lcd.print(WHITE_BLACK);
      displayTime();
#ifdef DEBUG
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
    Serial.println("CLOCK_STOPPED");
  } else if (cmd == "RESET") {
    reset();
  } else if (cmd == "STATUS") {
    Serial.print("STATUS:");
    Serial.print(whiteTimeMs);
    Serial.print("+");
    Serial.print(whiteIncrement);
    Serial.print(":");
    Serial.print(blackTimeMs);
    Serial.print("+");
    Serial.print(blackIncrement);
    Serial.print(":");
    Serial.print(clockRunning ? "RUNNING" : "STOPPED");
    Serial.print(":");
    Serial.println(whiteToPlay ? "WHITE" : "BLACK");
  } else if (cmd == "OVER") {
    gameDone();
  } else if (!clockRunning) {
    //  start the clock on any other input
    startClock();
  }
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
  Serial.println("CLOCK_READY");
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
  }

  // If the stable state has changed
  if (btn.curRead != btn.lastState) {
    btn.lastState = btn.curRead;

    if (btn.curRead == LOW) {
      Serial.print(btn.name);
      Serial.println(" pressed");

      if (btn.pin == MOVE_MADE_PIN) {
        moveMade();
      } else if (btn.pin == RESET_BTN_PIN) {
        reset();
      }

#ifdef DEBUG
      // the button is not momentary
    } else if (btn.holdKey) {
      Serial.print(btn.name);
      Serial.println(" released");
#endif
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
    unsigned long currentTime = millis();

    if (currentTime - lastUpdate >= 50) {
      lastUpdate = currentTime;

      if (whiteToPlay) {
        if (whiteTimeMs > 50) {
          whiteTimeMs -= 50;
        } else {
          whiteTimeOut();
          whiteTimeMs = 0;
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

//  LocalWords:  BMATE commaIndex addr
