#include <Keypad.h>
#include <EEPROM.h>
#include <Keyboard.h>

const byte ROWS = 3;
const byte COLS = 3;
char keys[ROWS][COLS] = {
  {'1', '2', '3'},
  {'4', '5', '6'},
  {'7', '8', '9'}
};
byte rowPins[ROWS] = {9, 8, 7};
byte colPins[COLS] = {6, 5, 4};

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

#define NUM_KEYS 9
#define MAPPING_SIZE 10
char mappings[NUM_KEYS][MAPPING_SIZE];

void loadMappings() {
  Serial.println("[EEPROM] Loading key mappings...");
  for (int i = 0; i < NUM_KEYS; i++) {
    for (int j = 0; j < MAPPING_SIZE; j++) {
      mappings[i][j] = EEPROM.read(i * MAPPING_SIZE + j);
    }
  }
  Serial.println("[EEPROM] Done.");
}

void saveMappings(char newMappings[NUM_KEYS][MAPPING_SIZE]) {
  Serial.println("[EEPROM] Saving new key mappings...");
  for (int i = 0; i < NUM_KEYS; i++) {
    for (int j = 0; j < MAPPING_SIZE; j++) {
      EEPROM.update(i * MAPPING_SIZE + j, newMappings[i][j]);
    }
  }
  Serial.println("[EEPROM] Save complete.");
}

int getKeyIndex(char k) {
  for (int i = 0; i < NUM_KEYS; i++) {
    if (keys[i / COLS][i % COLS] == k) return i;
  }
  return -1;
}

void processSerialCommand() {
  static char buffer[128];
  static byte idx = 0;

  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      buffer[idx] = '\0';
      Serial.print("[Serial] Received command: ");
      Serial.println(buffer);

      if (strncmp(buffer, "SET", 3) == 0) {
        char newMap[NUM_KEYS][MAPPING_SIZE];
        char* token = strtok(buffer + 4, "|");
        for (int i = 0; i < NUM_KEYS && token != NULL; i++) {
          strncpy(newMap[i], token, MAPPING_SIZE);
          newMap[i][MAPPING_SIZE - 1] = '\0';
          Serial.print("[Config] Button ");
          Serial.print(i + 1);
          Serial.print(": ");
          Serial.println(newMap[i]);
          token = strtok(NULL, "|");
        }
        saveMappings(newMap);
        loadMappings();
        Serial.println("OK");
      } else {
        Serial.println("[Error] Unknown command.");
      }

      idx = 0;
    } else {
      if (idx < sizeof(buffer) - 1) buffer[idx++] = c;
    }
  }
}

void sendShortcut(const char* combo) {
  bool ctrl = false, shift = false, alt = false;
  char mainKey = 0;

  String comboStr(combo);
  comboStr.toUpperCase();

  if (comboStr.indexOf("CTRL") >= 0) ctrl = true;
  if (comboStr.indexOf("SHIFT") >= 0) shift = true;
  if (comboStr.indexOf("ALT") >= 0) alt = true;

  int lastPlus = comboStr.lastIndexOf('+');
  if (lastPlus != -1 && lastPlus < comboStr.length() - 1) {
    mainKey = comboStr.charAt(lastPlus + 1);
  } else if (lastPlus == -1 && comboStr.length() == 1) {
    mainKey = comboStr.charAt(0);
  }

  Serial.print("[HID] Sending: ");
  if (ctrl) Serial.print("CTRL+");
  if (alt) Serial.print("ALT+");
  if (shift) Serial.print("SHIFT+");
  if (mainKey) Serial.print(mainKey);
  Serial.println();

  if (ctrl) Keyboard.press(KEY_LEFT_CTRL);
  if (shift) Keyboard.press(KEY_LEFT_SHIFT);
  if (alt) Keyboard.press(KEY_LEFT_ALT);

  if (mainKey != 0) {
    Keyboard.press(mainKey);
    delay(50);
    Keyboard.release(mainKey);
  }

  delay(50);
  Keyboard.releaseAll();
}

void setup() {
  Serial.begin(9600);
  while (!Serial);  // Wait for serial to connect
  Serial.println("[System] Macro pad starting up...");
  Keyboard.begin();
  loadMappings();
  Serial.println("[System] Ready for commands.");
}

void loop() {
  processSerialCommand();

  char key = keypad.getKey();
  if (key) {
    int index = getKeyIndex(key);
    if (index != -1) {
      Serial.print("[Keypad] Button ");
      Serial.print(index + 1);
      Serial.print(" pressed. Action: ");
      Serial.println(mappings[index]);
      sendShortcut(mappings[index]);
    }
  }
}
