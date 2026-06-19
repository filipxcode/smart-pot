#include "DHT.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>
#include <BH1750.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WebServer.h>

#define DHTPIN 4        // Pin cyfrowy 4 DHT
#define DHTTYPE DHT22
#define SOIL_PIN 3  // Pin analogowy podłączony do czujnika pojemnosciowego
#define ONEWIRE_PIN 5 // Pin cyfrowy z czujnikiem temperatury korzeni

#define I2C_SDA 1     // Pin G1
#define I2C_SCL 0     // Pin G0

// Zmienne do obsługi czasu (bez blokowania procesora)
unsigned long czasOstatniegoWyslania = 0; // Pamięta, kiedy ostatnio wysłano dane
const unsigned long interwalWysylania = 120000; // 120 000 ms = 2 minuty

DHT dht(DHTPIN, DHTTYPE);

// zmienne do pojemnosciowego czujnika wilgotnosci
const int wartoscSucho = 3300; 
const int wartoscMokro = 1400;

// Konfiguracja obiektow dla czujnika korzeni
OneWire oneWire(ONEWIRE_PIN);
DallasTemperature czujnikGleby(&oneWire);

// natezenie swiatla
BH1750 miernikSwiatla;

//pompka
const int pinPompki = 7; 
const int buttonPin = 9;


const String KOD_URZADZENIA = "2137";

// Konfiguracja polaczenia z internetem
const char* ssid = "Redmi 12";
const char* password = "qwertyuiop001";

// Adresy do serwera
const char* loginUrl = "http://10.12.229.105:8000/auth/jwt/login";
const char* metricsUrl = "http://10.12.229.105:8000/metrics";
// Twoje dane konta
const char* emailUzytkownika = "mojadoniczka@test.pl";
const char* hasloUzytkownika = "mojeTrudneHaslo123";

String aktualnyToken = "";

WebServer server(80);

void setup() {
  // Inicjalizacja portu szeregowego
  Serial.begin(115200);
  delay(2000); // Czas na połączenie USB
  
  pinMode(pinPompki, OUTPUT);
  analogWrite(pinPompki, 255);
  pinMode(buttonPin, INPUT_PULLUP);

  Serial.println("Start systemu SmartPot");
  // inicjalizacja pinu pojemnosciowego czujnika wilgotnosci
  pinMode(SOIL_PIN, INPUT);

  // Inicjalizacja czujnika
  dht.begin();
  
  // Uruchomienie czujnika temperatury koerzeni
  czujnikGleby.begin();

  Wire.begin(I2C_SDA, I2C_SCL);

  if (miernikSwiatla.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println("Czujnik BH1750 zainicjowany poprawnie.");
  } else {
    Serial.println("BLAD: Nie mozna znalezc czujnika BH1750!");
    Serial.println("Sprawdz kable SDA i SCL.");
  }


  Serial.print("Laczenie z siecia: ");
  Serial.println(ssid);

  // Próba połączenia się z siecią
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nSUKCES! Polaczono z routerem!");
  Serial.print("Lokalny adres IP Twojej doniczki to: ");
  Serial.println(WiFi.localIP());


  server.on("/", HTTP_POST, obsluzZadaniePodlewania);
  server.begin();
  Serial.println("Serwer ESP32 uruchomiony. Nasluchuje na komendy...");

  // WERYFIKACJA INTERNETU
  testujDostepDoInternetu();

  zalogujDoSerwera();
}

void loop() {

  unsigned long aktualnyCzas = millis();

  server.handleClient();

  if (aktualnyCzas - czasOstatniegoWyslania >= interwalWysylania) {
    
    czasOstatniegoWyslania = aktualnyCzas; 

    Serial.println("\n--- Rozpoczynam nowy pomiar ---");

    // Odczyt z DHT22
    float tempPow = dht.readTemperature();
    float wilgPow = dht.readHumidity();

    // Odczyt z czujnika gleby
    int surowaGleba = analogRead(SOIL_PIN);
    int wilgGleby = map(surowaGleba, wartoscSucho, wartoscMokro, 0, 100);
    wilgGleby = constrain(wilgGleby, 0, 100);

    // Odczyt światła z BH1750
    float swiatlo = miernikSwiatla.readLightLevel();

    // Wypisanie na ekran (TESTOWANIE)
    Serial.print("Wysylam: Temp.Pow: "); Serial.print(tempPow);
    Serial.print("C | Wilg.Pow: "); Serial.print(wilgPow);
    Serial.print("% | Wilg.Gleby: "); Serial.print(wilgGleby);
    Serial.print("% | Swiatlo: "); Serial.print(swiatlo);
    Serial.println(" lux");

    wyslijDaneDoSerwera(tempPow, wilgPow, wilgGleby, swiatlo);
  }

  if (digitalRead(buttonPin) == LOW) {
    // Zabezpieczenie przed fizycznym drganiem blaszki w przycisku (debounce)
    delay(50);
    
    if (digitalRead(buttonPin) == LOW) { 
      Serial.println("\n[PRZYCISK WCIŚNIĘTY] -> Uruchamiam manualne podlewanie!");
      podlejRosline(3000); 
      
      while (digitalRead(buttonPin) == LOW) {
        delay(10);
      }
    }
  }
}

// ==========================================
// FUNKCJE
// ==========================================
void obsluzZadaniePodlewania() {
  Serial.println("\n[OTRZYMANO ZAPYTANIE Z BACKENDU]");

  // Sprawdzanie klucza bezpieczeństwa w parametrze linku (api-key)
  if (!server.hasArg("api-key") || server.arg("api-key") != KOD_URZADZENIA) {
    Serial.println("Odmowa dostepu: zly klucz API!");
    server.send(401, "text/plain", "Brak autoryzacji - niepoprawny klucz (api-key)");
    return;
  }

  // Pobieranie JSON, który przysłał Backend
  if (server.hasArg("plain") == false) {
    server.send(400, "text/plain", "Brak danych JSON w zapytaniu");
    return;
  }
  String payload = server.arg("plain");
  
  // Rozkodowywanie JSON
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, payload);

  if (error) {
    server.send(400, "text/plain", "Blad parsowania JSON");
    return;
  }

  // Pobieranie z JSONa czasu podlewania (zgodnie z device.py: {"duration_sec": watering_time})
  int czasWSekundach = doc["duration_sec"];
  
  if (czasWSekundach > 0 && czasWSekundach <= 60) { // Zabezpieczenie np. max 60 sekund
    Serial.print("Backend poprosil o podlewanie przez: ");
    Serial.print(czasWSekundach);
    Serial.println(" sekund.");

    // Informujemy backend, ze przyjelismy polecenie, ZANIM zaczniemy podlewac,
    // zeby backend nie dostał bledu timeout i sie nie rozlaczyl.
    server.send(200, "application/json", "{\"status\":\"success\", \"message\":\"Podlewanie rozpoczete\"}");
    
    podlejRosline(czasWSekundach * 1000);
  } else {
    server.send(400, "text/plain", "Nieprawidlowy czas podlewania");
  }
}

void odczytajWarunkiPowietrza() { // TEST
  // Odczyt wilgotności (w procentach)
  float wilgotnosc = dht.readHumidity();
  
  // Odczyt temperatury (w stopniach Celsjusza)
  float temperatura = dht.readTemperature();

  // Sprawdzenie, czy odczyt się powiódł
  // (funkcja isnan sprawdza, czy wynik "nie jest liczbą" - Not a Number)
  if (isnan(wilgotnosc) || isnan(temperatura)) {
    Serial.println("Blad: Nie mozna odczytac danych z czujnika DHT22!");
    return; // Przerwij funkcję, jeśli jest błąd
  }

  // Wypisanie wyników do Monitora Szeregowego
  Serial.print("Temperatura powietrza: ");
  Serial.print(temperatura);
  Serial.print(" °C  |  ");
  
  Serial.print("Wilgotnosc powietrza: ");
  Serial.print(wilgotnosc);
  Serial.println(" %");
}

void odczytajWilgotnoscGleby() { // TEST
  // Odczyt surowej wartości z przetwornika (0 - 4095)
  int surowaWartosc = analogRead(SOIL_PIN);
  
  // Przeliczenie surowej wartości na procenty (0% - 100%)
  // Funkcja map(zmienna, od_Min, od_Max, do_Min, do_Max)
  int procentWilgotnosci = map(surowaWartosc, wartoscSucho, wartoscMokro, 0, 100);
  
  // Zabezpieczenie przed przekroczeniem skali (np. -5% albo 105%)
  // Jeśli odczyt wyjdzie poza kalibrację, ucinamy go do ram 0-100
  procentWilgotnosci = constrain(procentWilgotnosci, 0, 100);

  // Wypisanie wyników do Monitora Szeregowego
  Serial.print("Gleba - Wartosc surowa: ");
  Serial.print(surowaWartosc);
  Serial.print("  |  Wilgotnosc: ");
  Serial.print(procentWilgotnosci);
  Serial.println(" %");
}

void odczytajTemperatureKorzeni() { // TEST
  // Wysłanie żądania do czujnika, aby dokonał pomiaru
  int liczbaCzujnikow = czujnikGleby.getDeviceCount();
  
  Serial.print("Liczba wykrytych czujnikow DS18B20: ");
  Serial.println(liczbaCzujnikow);
  
  czujnikGleby.requestTemperatures(); 
  
  // Pobranie zmierzonej temperatury (indeks 0, bo na jednym kablu może być wiele czujników!)
  float temperaturaKorzeni = czujnikGleby.getTempCByIndex(0);
  
  // Sprawdzenie błędów
  // Biblioteka DallasTemperature zwraca -127.00, jeśli czujnik jest odłączony
  if (temperaturaKorzeni == DEVICE_DISCONNECTED_C) {
    Serial.println("Blad: Nie wykryto czujnika DS18B20!");
    Serial.println("Sprawdz polaczenie kabli i czy dodales REZYSTOR 4.7k Ohm!");
    return; // Przerwij funkcję
  }

  // Wypisanie wyników do Monitora Szeregowego
  Serial.print("Temperatura gleby (korzeni): ");
  Serial.print(temperaturaKorzeni);
  Serial.println(" °C");
}

void odczytajNatezenieSwiatla() { // TEST
  float poziomSwiatla = miernikSwiatla.readLightLevel();
  
  // Wypisanie wyników do Monitora Szeregowego
  Serial.print("Natezenie swiatla: ");
  Serial.print(poziomSwiatla);
  Serial.print(" lux  |  Ocena warunkow: ");
  
  if (poziomSwiatla < 50) {
    Serial.println("Gleboki cien (Za ciemno!)");
  } else if (poziomSwiatla < 500) {
    Serial.println("Polcien (Dobre dla paproci)");
  } else if (poziomSwiatla < 2000) {
    Serial.println("Jasno (Jasny pokoj, swiatlo rozproszone)");
  } else {
    Serial.println("Bardzo jasno / Bezposrednie slonce");
  }
}

void testujDostepDoInternetu() {
  Serial.println("\nSprawdzam, czy ESP32 ma wyjscie do prawdziwego Internetu...");
  
  // Upewniamy się, że nie zerwało nam połączenia z routerem
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    
    String adresTestowy = "http://httpbin.org/get";
    http.begin(adresTestowy);
    
    // Wykonujemy zapytanie
    int kodOdpowiedzi = http.GET();
    
    // Kod większy od 0 oznacza, że serwer nam odpowiedział
    if (kodOdpowiedzi > 0) {
      Serial.print("Odpowiedz serwera otrzymana! Kod HTTP: ");
      Serial.println(kodOdpowiedzi);
      
      if (kodOdpowiedzi == 200) {
        Serial.println("-> TEST ZDANY! Internet dziala PERFEKCYJNIE.");
        Serial.println("-> ESP32 jest w 100% gotowe do wysylania danych do AI i serwera!");
      } else {
        Serial.println("-> Polaczono z internetem, ale serwer zwrocil inny kod bledu.");
      }
    } else {
      // Jeśli kod jest na minusie, oznacza to brak internetu lub blokadę przez router
      Serial.print("-> BLAD: Serwer nie odpowiada. Prawdopodobny brak internetu. Szczegoly: ");
      Serial.println(http.errorToString(kodOdpowiedzi).c_str());
    }
    
    // Zwalnianie pamięci
    http.end(); 
  } else {
    Serial.println("Blad: Zerwano polaczenie Wi-Fi.");
  }
}

bool zalogujDoSerwera() {
  Serial.println("Proba logowania do serwera...");
  
  HTTPClient http;
  http.begin(loginUrl);
  
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");

  String daneLogowania = "username=" + String(emailUzytkownika) + "&password=" + String(hasloUzytkownika);

  int kodOdpowiedzi = http.POST(daneLogowania);

  if (kodOdpowiedzi == 200) {
    String odpowiedzSerwera = http.getString();
    
    StaticJsonDocument<512> doc;
    DeserializationError blad = deserializeJson(doc, odpowiedzSerwera);
    
    if (!blad) {
      aktualnyToken = doc["access_token"].as<String>();
      Serial.println("Logowanie udane! Zdobylem token JWT.");
      http.end();
      return true;
    }
  } else {
    Serial.print("Blad logowania! Kod HTTP: ");
    Serial.println(kodOdpowiedzi);
    Serial.println(http.getString());
  }
  
  http.end();
  return false;
}

void wyslijDaneDoSerwera(float tempPow, float wilgPow, int wilgGleby, float swiatlo) {
  if (aktualnyToken == "") {
    if (!zalogujDoSerwera()) {
      Serial.println("Przerywam wysylanie danych - nie udalo sie zalogowac!");
      return;
    }
  }

  HTTPClient http;
  http.begin(metricsUrl);
  
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", "Bearer " + aktualnyToken);

  StaticJsonDocument<200> doc;
  doc["device_id"] = 1; 
  doc["air_temp"] = tempPow;
  doc["air_hum"] = wilgPow;
  doc["soil_hum"] = wilgGleby;
  doc["light_lux"] = swiatlo;

  String jsonPayload;
  serializeJson(doc, jsonPayload);

  int httpResponseCode = http.POST(jsonPayload);

  if (httpResponseCode == 201 || httpResponseCode == 200) {
    Serial.println("Sukces! Pomiary zapisane w bazie.");
  } else if (httpResponseCode == 401) {
    // Jeśli po jakimś czasie token wygasł (np. minęły 24 godziny),
    // czyścimy stary token, aby w kolejnej pętli ESP32 zalogowało się na nowo
    Serial.println("Serwer odrzucil token (prawdopodobnie wygasl). Kasuje z pamieci.");
    aktualnyToken = ""; 
  } else {
    Serial.print("Blad wysylania pomiarow: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

void podlejRosline(int czasPodlewaniaMs) {
  for (int moc = 0; moc <= 255; moc++) {
    analogWrite(pinPompki, 255 - moc);
    delay(2);
  }
  analogWrite(pinPompki, 0);
  delay(czasPodlewaniaMs);

  analogWrite(pinPompki, 255); 
}
