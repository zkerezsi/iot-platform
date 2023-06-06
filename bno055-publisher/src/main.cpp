#include <Wire.h>
#include <Arduino.h>
#include <PubSubClient.h>
#include <Client.h>
#include <FFT.h>
#include "Secrets.h"

#if defined(ARDUINO_ARCH_ESP8266)
#include <ESP8266WiFi.h>
#elif defined(ARDUINO_ARCH_ESP32)
// Not tested yet but the program should work with esp32 the same way as with esp8266
#include <WiFi.h>
#endif

#define NUMBER_OF_SAMPLES 128

const uint8_t BNO_055_ADDRESS = 0x29;
const uint8_t OPR_MODE_REG = 0x3d;
// Operation Mode: Accelerometer only
const uint8_t OPR_MODE_VAL_ACCONLY = 0b00000001;
// Operation Mode: Config Mode
const uint8_t OPR_MODE_VAL_CONFIGMODE = 0b00000000;
const uint8_t ACC_CONFIG_REG = 0x08;
// Operation Mode: Normal
// Bandwidth: 1000Hz
// G Range: 16G
const uint8_t ACC_CONFIG_VAL = 0b00011111;

WiFiClient wifi_client;
PubSubClient mqtt_client(wifi_client);
unsigned char sensor_buffer[NUMBER_OF_SAMPLES * 6];
int i = 0;
int offset = 0;
uint8_t mqtt_buffer[(NUMBER_OF_SAMPLES / 2) * sizeof(float) * 4];

void setup_wifi()
{
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.print("\nSSID: ");
  Serial.println(WiFi.SSID());
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.print("Signal strength (RSSI): ");
  Serial.print(WiFi.RSSI());
  Serial.println("dBm");
}

void setup_bno055()
{
  Wire.begin();
  Wire.setClock(400000);

  Wire.beginTransmission(BNO_055_ADDRESS);
  Wire.write(OPR_MODE_REG);
  Wire.write(OPR_MODE_VAL_CONFIGMODE);
  Wire.endTransmission();
  // From other mode to config mode: 19ms
  delay(100);

  Wire.beginTransmission(BNO_055_ADDRESS);
  Wire.write(ACC_CONFIG_REG);
  Wire.write(ACC_CONFIG_VAL);
  Wire.endTransmission();
  delay(100);

  Wire.beginTransmission(BNO_055_ADDRESS);
  Wire.write(OPR_MODE_REG);
  Wire.write(OPR_MODE_VAL_ACCONLY);
  Wire.endTransmission();
  // From config mode to other mode: 7ms
  delay(100);

  Wire.beginTransmission(BNO_055_ADDRESS);
  Wire.write(0x08);
  Wire.endTransmission();
  delay(100);
}

void appendFloatToBuffer(uint8_t *buffer, int *index, float a)
{
  buffer[*index] = ((char *)&a)[0];
  buffer[*index + 1] = ((char *)&a)[1];
  buffer[*index + 2] = ((char *)&a)[2];
  buffer[*index + 3] = ((char *)&a)[3];
  *index += sizeof(float) * 4;
}

void reconnect()
{
  while (!mqtt_client.connected())
  {
    mqtt_client.setServer(MQTT_HOST, MQTT_PORT);
    mqtt_client.setBufferSize(sizeof(mqtt_buffer));
    if (USE_MQTT_USER_AND_PASSWORD ? mqtt_client.connect("bno055", MQTT_USER, MQTT_PASSWORD) : mqtt_client.connect("bno055"))
    {
      Serial.print("Successfully connected to MQTT host: ");
      Serial.println(MQTT_HOST);
    }
    else
    {
      Serial.print("Failed to connect to MQTT host: ");
      Serial.println(MQTT_HOST);
      delay(500);
    }
  }
}

void print_mqtt_buffer()
{
  for (i = 0; i < sizeof(mqtt_buffer); i += 16)
  {
    Serial.printf("%02x %02x %02x %02x  ", mqtt_buffer[i + 0], mqtt_buffer[i + 1], mqtt_buffer[i + 2], mqtt_buffer[i + 3]);
    Serial.printf("%02x %02x %02x %02x  ", mqtt_buffer[i + 4], mqtt_buffer[i + 5], mqtt_buffer[i + 6], mqtt_buffer[i + 7]);
    Serial.printf("%02x %02x %02x %02x  ", mqtt_buffer[i + 8], mqtt_buffer[i + 9], mqtt_buffer[i + 10], mqtt_buffer[i + 11]);
    Serial.printf("%02x %02x %02x %02x\n", mqtt_buffer[i + 12], mqtt_buffer[i + 13], mqtt_buffer[i + 14], mqtt_buffer[i + 15]);
  }
}

void setup()
{
  Serial.begin(9600);
  Serial.println();
  setup_wifi();
  setup_bno055();
}

void loop()
{
  if (!mqtt_client.connected())
  {
    reconnect();
  }
  mqtt_client.loop();

  unsigned long start = micros();
  for (i = 0, offset = 0; i < NUMBER_OF_SAMPLES; i++)
  {
    offset = i * 6;
    // Sometimes when you load a new program into the mcu and interrupt the currently running measurement, the sensor
    // might get stuck here. Remove the power and wait some time, then you can reconnect and everything should work
    Wire.requestFrom(BNO_055_ADDRESS, (byte)6);
    Wire.readBytes(sensor_buffer + offset, 6);
  }
  unsigned long stop = micros();
  unsigned long total_time_ms = (stop - start) * 1.0 / 1000;
  Serial.printf("%lums\n", total_time_ms);
  int frequency_buffer_index = sizeof(float) * 4;
  int x_axis_buffer_index = sizeof(float) * 5;
  int y_axis_buffer_index = sizeof(float) * 6;
  int z_axis_buffer_index = sizeof(float) * 7;

  // FFT for x axis
  fft_config_t *real_fft_plan = fft_init(NUMBER_OF_SAMPLES, FFT_REAL, FFT_FORWARD, NULL, NULL);
  for (i = 0, offset = 0; i < NUMBER_OF_SAMPLES; i++)
  {
    offset = i * 6;
    int16_t x = ((int16_t)sensor_buffer[offset]) | (((int16_t)sensor_buffer[offset + 1]) << 8);
    real_fft_plan->input[i] = x / 100.0;
  }
  fft_execute(real_fft_plan);
  for (i = 1; i < real_fft_plan->size / 2; i++)
  {
    float frequency = i * 1000.0 / total_time_ms;
    appendFloatToBuffer(mqtt_buffer, &frequency_buffer_index, frequency);
    float x_amplitude = sqrt(pow(real_fft_plan->output[2 * i], 2) + pow(real_fft_plan->output[2 * i + 1], 2)) / 1;
    appendFloatToBuffer(mqtt_buffer, &x_axis_buffer_index, x_amplitude);
  }
  fft_destroy(real_fft_plan);

  // FFT for y axis
  real_fft_plan = fft_init(NUMBER_OF_SAMPLES, FFT_REAL, FFT_FORWARD, NULL, NULL);
  for (i = 0, offset = 0; i < NUMBER_OF_SAMPLES; i++)
  {
    offset = i * 6;
    int16_t y = ((int16_t)sensor_buffer[offset + 2]) | (((int16_t)sensor_buffer[offset + 3]) << 8);
    real_fft_plan->input[i] = y / 100.0;
  }
  fft_execute(real_fft_plan);
  for (i = 1; i < real_fft_plan->size / 2; i++)
  {
    float y_amplitude = sqrt(pow(real_fft_plan->output[2 * i], 2) + pow(real_fft_plan->output[2 * i + 1], 2)) / 1;
    appendFloatToBuffer(mqtt_buffer, &y_axis_buffer_index, y_amplitude);
  }
  fft_destroy(real_fft_plan);

  // FFT for z axis
  real_fft_plan = fft_init(NUMBER_OF_SAMPLES, FFT_REAL, FFT_FORWARD, NULL, NULL);
  for (i = 0, offset = 0; i < NUMBER_OF_SAMPLES; i++)
  {
    offset = i * 6;
    int16_t z = ((int16_t)sensor_buffer[offset + 4]) | (((int16_t)sensor_buffer[offset + 5]) << 8);
    real_fft_plan->input[i] = z / 100.0;
  }
  fft_execute(real_fft_plan);
  for (i = 1; i < real_fft_plan->size / 2; i++)
  {
    float z_amplitude = sqrt(pow(real_fft_plan->output[2 * i], 2) + pow(real_fft_plan->output[2 * i + 1], 2)) / 1;
    appendFloatToBuffer(mqtt_buffer, &z_axis_buffer_index, z_amplitude);
  }
  fft_destroy(real_fft_plan);

  mqtt_client.beginPublish(MQTT_TOPIC, sizeof(mqtt_buffer), false);
  mqtt_client.write(mqtt_buffer, sizeof(mqtt_buffer));
  mqtt_client.endPublish();
  delay(800);
}
