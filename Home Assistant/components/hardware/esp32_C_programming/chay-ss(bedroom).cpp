#include <Arduino.h>
#include <WiFi.h>
#include <DHT.h>
#include <FirebaseESP32.h>

// --- Cảm biến ---
#define dhtpin 4
#define dhttype DHT22

// --- Đèn LED ---
#define led 2 // LED On/Off
#define PWM_LED_PIN 25 //LED PWM
#define PWM_CHANNEL 0
#define PWM_FREQ 5000
#define PWM_RESOLUTION 8

// --- WiFi & Firebase ---
#define WF_SSID "Thanh Tung"
#define WF_PASS "0988913074" 
#define FB_HOST "https://tro-ly-ao-22e6a-default-rtdb.firebaseio.com/"
#define FB_AUTH "AIzaSyBPCE8k4wrPWf6utQEbVnWPUL2gnp32KmA"

// --- Khởi tạo ---
DHT dht(dhtpin, dhttype);
FirebaseData fbDataSend;    // Tạo một đối tượng FirebaseData riêng cho việc gửi
FirebaseData fbDataReceive; // Tạo một đối tượng FirebaseData riêng cho việc nhận
FirebaseAuth fbAuth;
FirebaseConfig fbConfig;

// TASK 1: TÁC VỤ GỬI DỮ LIỆU LÊN FIREBASE
void taskSendData(void *parameter) {
  for (;;) { // Vòng lặp vô tận cho tác vụ
    float temp = dht.readTemperature();
    float humi = dht.readHumidity();

    // Gửi nhiệt độ
    if(Firebase.setFloat(fbDataSend, "/bedroom/sensor/temperature", temp)) {
      Serial.printf("[Task Send] Temp sent: %.2f C\n", temp);
    } else {
      Serial.printf("[Task Send] Failed to send Temp: %s\n", fbDataSend.errorReason().c_str());
    }

    // Gửi độ ẩm
    if(Firebase.setFloat(fbDataSend, "/bedroom/sensor/humidity", humi)) {
      Serial.printf("[Task Send] Humi sent: %.2f %%\n", humi);
    } else {
      Serial.printf("[Task Send] Failed to send Humi: %s\n", fbDataSend.errorReason().c_str());
    }
    
    // Tạm dừng tác vụ này trong 1 giây
    // vTaskDelay là cách "delay" của FreeRTOS, không làm block CPU
    vTaskDelay(1000 / portTICK_PERIOD_MS); 
  }
}

// TASK 2: TÁC VỤ NHẬN DỮ LIỆU TỪ FIREBASE
void taskReceiveData(void *parameter) {
  for (;;) { // Vòng lặp vô tận cho tác vụ
    // Điều khiển LED On/Off bằng chuỗi
    if(Firebase.getString(fbDataReceive, "/bedroom/device/lights")) {
      String ledCommand = fbDataReceive.stringData();
      if (ledCommand == "on") {
        digitalWrite(led, HIGH);
      } else if (ledCommand == "off") {
        digitalWrite(led, LOW);
      }
      Serial.printf("[Task Receive] Led command: %s -> Led is %s\n", ledCommand.c_str(), (ledCommand == "on" ? "ON" : "OFF"));
    } else {
      Serial.printf("[Task Receive] Failed to get Led command: %s\n", fbDataReceive.errorReason().c_str());
    }

    // Điều khiển LED PWM
    if(Firebase.getInt(fbDataReceive, "/bedroom/device/lamp")) {
      int pwmValue = fbDataReceive.intData();
      pwmValue = constrain(pwmValue, 0, 100);
      int dutyCycle = map(pwmValue, 0, 100, 0, 255);
      ledcWrite(PWM_CHANNEL, dutyCycle);
      Serial.printf("[Task Receive] PWM Value: %d -> Duty Cycle: %d\n", pwmValue, dutyCycle);
    } else {
      Serial.printf("[Task Receive] Failed to get PWM Value: %s\n", fbDataReceive.errorReason().c_str());
    }
    
    // Tạm dừng tác vụ này trong 500 mili-giây
    vTaskDelay(500 / portTICK_PERIOD_MS);
  }
}

void setup() {
  Serial.begin(9600);
  dht.begin();
  pinMode(led, OUTPUT);

  ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION);
  ledcAttachPin(PWM_LED_PIN, PWM_CHANNEL);

  WiFi.begin(WF_SSID, WF_PASS);
  Serial.print("Connecting Wifi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(300);
  }
  Serial.println("\nConnected.");

  fbConfig.host = FB_HOST;
  fbConfig.signer.tokens.legacy_token = FB_AUTH;
  Firebase.begin(&fbConfig, &fbAuth);
  Firebase.reconnectWiFi(true);

  // --- TẠO 2 TASK CHẠY SONG SONG ---
  xTaskCreatePinnedToCore(
      taskSendData,     // Hàm của tác vụ
      "SendDataTask",   // Tên tác vụ (để debug)
      10000,            // Kích thước stack (bộ nhớ) cho tác vụ
      NULL,             // Tham số truyền vào
      1,                // Mức độ ưu tiên
      NULL,             // Handle của tác vụ
      0);               // Chạy trên Core 0

  xTaskCreatePinnedToCore(
      taskReceiveData,
      "ReceiveDataTask",
      10000,
      NULL,
      1,
      NULL,
      1);               // Chạy trên Core 1
}

void loop() {

}