#include <Arduino.h>
#include <WiFi.h>
#include <DHT.h>
#include <FirebaseESP32.h>

//Khai báo chân và loại DHT
#define dhtpin 4
#define dhttype DHT22

//sử dụng led trên esp32
#define lights 2

//Khai báo PWM
#define PWM_LED_PIN 25  // Chân GPIO cho LED PWM
#define PWM_CHANNEL 0   // Kênh PWM (từ 0-15)
#define PWM_FREQ 5000   // Tần số PWM (Hz)
#define PWM_RESOLUTION 8 // Độ phân giải (8 bit = 0-255)

//Thông tin WiFi 
#define  WF_SSID  "Thanh Tung"
#define WF_PASS  "0988913074" 

//Thông tin FireBase
#define FB_HOST "https://tro-ly-ao-22e6a-default-rtdb.firebaseio.com/"
#define FB_AUTH "AIzaSyBPCE8k4wrPWf6utQEbVnWPUL2gnp32KmA"

//Khởi tạo DHT
DHT dht(dhtpin,dhttype);

//Khởi tạo FireBase
FirebaseData fbData;
FirebaseAuth fbAuth;
FirebaseConfig fbConfig;
String path = "/";

void setup() {
  Serial.begin(9600);
  digitalWrite(lights, LOW);

  dht.begin();

  pinMode(lights, OUTPUT);
  
  //cấu hình PWM
  ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RESOLUTION); // Cài đặt kênh PWM
  ledcAttachPin(PWM_LED_PIN, PWM_CHANNEL);          // Gán kênh vào chân GPIO

  WiFi.begin(WF_SSID,WF_PASS);
  Serial.print("Connecting Wifi.");
  while(WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("Connected.");

  //Cấu hình FireBase
  fbConfig.host = FB_HOST;
  fbConfig.signer.tokens.legacy_token = FB_AUTH;

  //Kết nối FireBase
  Firebase.begin(&fbConfig,&fbAuth);
  Firebase.reconnectWiFi(true);
}

void loop() {
  float temp = dht.readTemperature();
  float humi = dht.readHumidity();

  //Gửi nhiệt độ lên Firebase
  if(Firebase.setFloat(fbData,"/kitchen/sensor/temperature",temp))
  {
    Serial.print("Temp is sent to Firebase: ");
    Serial.println(temp);
  }
  else
  {
    Serial.print("Failed to send Temp: ");
    Serial.println(fbData.errorReason());
  }


  //Gửi độ ẩm lên Firebase
  if(Firebase.setFloat(fbData,"/kitchen/sensor/humidity",humi))
  {
    Serial.print("Humi is sent to Firebase: ");
    Serial.println(humi);
  }
  else
  {
    Serial.print("Failed to send Humi: ");
    Serial.println(fbData.errorReason());
  }

  //Nhận lệnh điều khiển lights từ Firebase
  if(Firebase.getString(fbData, "/kitchen/device/lights"))
  {
    String lightsCommand = fbData.stringData();
    Serial.print("Lights command received: ");
    Serial.println(lightsCommand);

    if(lightsCommand == "on")
    {
      digitalWrite(lights,HIGH);
      Serial.println("Lights are on");
    }
    else if(lightsCommand == "off")
    {
      digitalWrite(lights,LOW);
      Serial.println("Lights are off");
    }
  }
  else
  {
    Serial.print("Failed to get lights command: ");
    Serial.println(fbData.errorReason());
  }

  //Nhận giá trị từ firebase để điều khiển pwm
  if(Firebase.getInt(fbData, "/kitchen/device/lamp")) {
    int pwmValue = fbData.intData();

    // Chuyển đổi giá trị 0-100 thành giá trị PWM 0-255
    int dutyCycle = map(pwmValue, 0, 100, 0, 255);

    ledcWrite(PWM_CHANNEL, dutyCycle); // Đặt độ sáng cho LED

    Serial.print("PWM Value from Firebase: ");
    Serial.print(pwmValue);
    Serial.print(" -> Duty Cycle: ");
    Serial.println(dutyCycle);

  } else {
    Serial.print("Failed to get PWM Value: ");
    Serial.println(fbData.errorReason());
  }

  delay(1000);
}
