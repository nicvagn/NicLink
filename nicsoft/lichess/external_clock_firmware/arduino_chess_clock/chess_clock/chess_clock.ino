#define BLACK_TURN "|white|>>|black|"
#define WHITE_TURN "|white|<<|black|"
#define WHITE_WIN "  WHITE Wins!   "
#define BLACK_WIN "  Black Wins!   "
#define DRAW "   0.5/1 0.5/1 "

// buttons
#define DEBOUNCE_DELAY 50


#include <LiquidCrystal.h>

// Button structure to hold all state
struct Button {
  uint8_t pin;
  int curRead;
  int lastState;
  unsigned long lastDebounceTime;
  const char *name;
  bool holdKey;
};

Button greenBtn = {
  6,
  HIGH,
  HIGH,
  0,
  "Red Button",
  false,
};
Button redBtn = {
  7,
  HIGH,
  HIGH,
  0,
  "Red Button",
  false,
};

const int rs = 12, en = 13, d4 = 8, d5 = 9, d6 = 10, d7 = 11;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

// default times
unsigned long INCREMENT = 6000;
unsigned long B_START_TIME = 60000;
unsigned long W_START_TIME = 60000;

unsigned long whiteTime = W_START_TIME;
unsigned long blackTime = B_START_TIME;
unsigned long increment = INCREMENT;

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
    lcd.print(wM);  // Removed leading zero check
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
    lcd.print(bM);  // Removed leading zero check
    lcd.print(":");
    if (bS < 10) lcd.print("0");
    lcd.print(bS);
    lcd.print(".");
    if (bCenti < 10) lcd.print("0");
    lcd.print(bCenti);
  }

  lcd.print("   ");  // Clear any leftover characters
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

  whiteTime = W_START_TIME;
  blackTime = B_START_TIME;
  increment = INCREMENT;
  whiteToPlay = true;
  gameOver = false;
  clockRunning = false;
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("|white|--|black|");
  displayTime();
  Serial.println("CLOCK_RESET");
}

void processSerialCommand(String cmd) {
  cmd.trim();

  // simple move command. The player to move is tracked
  if (cmd == "m") {
    moveMade();
  } else if (cmd.startsWith("TIME:")) {
    // Format: TIME:300:5 (300 seconds + 5 second increment)
    // or TIME:300:0 (300 seconds, no increment)
    int firstColon = cmd.indexOf(':', 5);
    Serial.print("firstColon: ");
    Serial.println(firstColon);
    if (firstColon > 0) {
      String timeStr = cmd.substring(5, firstColon);
      String incStr = cmd.substring(firstColon + 1);

      unsigned long seconds = timeStr.toInt();
      unsigned long incSeconds = incStr.toInt();

      whiteTime = seconds * 1000;
      blackTime = seconds * 1000;
      increment = incSeconds * 1000;

      gameOver = false;
      clockRunning = false;
      whiteToPlay = true;

      lcd.setCursor(0, 0);
      lcd.print("|white|--|black|");
      displayTime();

      Serial.print("TIME_SET:");
      Serial.print(seconds);
      Serial.print(":");
      Serial.println(incSeconds);
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
    Serial.print(whiteTime);
    Serial.print(":");
    Serial.print(blackTime);
    Serial.print(":");
    Serial.print(increment);
    Serial.print(":");
    Serial.print(clockRunning ? "RUNNING" : "STOPPED");
    Serial.print(":");
    Serial.println(whiteToPlay ? "WHITE" : "BLACK");
  } else if (!clockRunning) {
    //  start the clock on any other input
    startClock();
  }
}

void setup() {
  Serial.begin(9600);
  lcd.begin(16, 2);
  lcd.print("|white|--|black|");
  displayTime();
  lastUpdate = millis();
  Serial.println("CLOCK_READY");
  // button pins
  pinMode(redBtn.pin, INPUT_PULLUP);
  pinMode(greenBtn.pin, INPUT_PULLUP);
}

void checkButton(Button &btn) {
  int reading = digitalRead(btn.pin);

  // If the reading changed, reset debounce timer
  if (reading != btn.curRead) {
    btn.lastDebounceTime = millis();
    btn.curRead = reading;
  }

  // If enough time has passed, accept the reading as stable
  if ((millis() - btn.lastDebounceTime) > DEBOUNCE_DELAY) {
    // If the stable state has changed
    if (btn.curRead != btn.lastState) {
      btn.lastState = btn.curRead;

      if (btn.curRead == LOW) {
        Serial.print(btn.name);
        Serial.println(" pressed");

        if (btn.pin == 6) {
          moveMade();
        } else if (btn.pin == 7) {
          reset();
        }
        // the button is not momentary
      } else if (btn.holdKey) {
        Serial.print(btn.name);
        Serial.println(" released");
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
    unsigned long currentTime = millis();

    if (currentTime - lastUpdate >= 50) {
      lastUpdate = currentTime;

      if (whiteToPlay) {
        if (whiteTime > 50) {
          whiteTime -= 50;
        } else {
          whiteTimeOut();
          whiteTime = 0;
          return;
        }
      } else {
        if (blackTime > 50) {
          blackTime -= 50;
        } else {
          blackTimeOut();
          blackTime = 0;
          return;
        }
      }

      displayTime();
    }
  }

  // check buttons
  checkButton(redBtn);

  checkButton(greenBtn);
}