#include "DHT.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>
#include <BH1750.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#define DHTPIN 4        // Pin cyfrowy 4, do którego podłączyliśmy DATA
#define DHTTYPE DHT22   // Definiujemy, że używamy dokładniejszej wersji DHT22
#define SOIL_PIN 3  // Pin analogowy podłączony do czujnika pojemnosciowego
#define ONEWIRE_PIN 5 // Pin cyfrowy z czujnikiem temperatury korzeni

#define I2C_SDA 1     // Pin G1
#define I2C_SCL 0     // Pin G0

// Stworzenie obiektu "dht"
DHT dht(DHTPIN, DHTTYPE);

// zmienne do pojemnosciowego czujnika wilgotnosci
const int wartoscSucho = 3300; 
const int wartoscMokro = 1400;

// Konfiguracja obiektow dla czujnika korzeni
OneWire oneWire(ONEWIRE_PIN);
DallasTemperature czujnikGleby(&oneWire);

// natezenie swiatla
BH1750 miernikSwiatla;


// Konfiguracja polaczenia z internetem
const char* ssid = "Redmi 12";
const char* password = "qwertyuiop001";

// Adresy do serwera
const char* loginUrl = "http://192.168.1.100:8000/auth/jwt/login";
const char* metricsUrl = "http://192.168.1.100:8000/metrics";
// Twoje dane konta
const char* emailUzytkownika = "mojadoniczka@test.pl";
const char* hasloUzytkownika = "mojeTrudneHaslo123";

String aktualnyToken = "";

void setup() {
  // Inicjalizacja portu szeregowego
  Serial.begin(115200);
  delay(2000); // Czas na połączenie USB
  
  Serial.println("Start systemu SmartPot");
  // inicjalizacja pinu pojemnosciowego czujnika wilgotnosci
  pinMode(SOIL_PIN, INPUT);

  // Inicjalizacja czujnika
  dht.begin();
  
  // Uruchomienie czujnika temperatury koerzeni
  czujnikGleby.begin();

  // 4. Inicjalizacja magistrali I2C na konkretnych pinach (BARDZO WAŻNE!)
  Wire.begin(I2C_SDA, I2C_SCL);

  // 5. Uruchomienie czujnika BH1750
  // begin() domyślnie ustawia czujnik w tryb ciągłego pomiaru wysokiej rozdzielczości
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

  // WERYFIKACJA INTERNETU
  testujDostepDoInternetu();
}

void loop() {

Serial.println("\n--- Rozpoczynam nowy pomiar ---");

  // 1. Odczyt z DHT22
  float tempPow = dht.readTemperature();
  float wilgPow = dht.readHumidity();

  // 2. Odczyt z czujnika gleby (przeliczenie na procenty)
  int surowaGleba = analogRead(SOIL_PIN);
  int wilgGleby = map(surowaGleba, wartoscSucho, wartoscMokro, 0, 100);
  wilgGleby = constrain(wilgGleby, 0, 100); // Ucięcie do 0-100%

  // 3. Odczyt z czujnika korzeni DS18B20 ----NIE DZIALA
  // czujnikGleby.requestTemperatures();
  // float tempKorz = czujnikGleby.getTempCByIndex(0);

  // 4. Odczyt światła z BH1750
  float swiatlo = miernikSwiatla.readLightLevel();

  // Opcjonalnie: Wypisanie na ekran, żebyś widział, co się dzieje
  Serial.print("Wysylam: Temp.Pow: "); Serial.print(tempPow);
  Serial.print("C | Wilg.Pow: "); Serial.print(wilgPow);
  // Serial.print("% | Temp.Korz: "); Serial.print(tempKorz);
  Serial.print("C | Wilg.Gleby: "); Serial.print(wilgGleby);
  Serial.print("% | Swiatlo: "); Serial.print(swiatlo);
  Serial.println(" lux");

  //wyslijDaneDoSerwera(tempPow, wilgPow, tempKorz, wilgGleby, swiatlo);
  testujDostepDoInternetu();

  delay(50000);
}

// ==========================================
// FUNKCJE
// ==========================================
void odczytajWarunkiPowietrza() {
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

void odczytajWilgotnoscGleby() {
  // 1. Odczyt surowej wartości z przetwornika (0 - 4095)
  int surowaWartosc = analogRead(SOIL_PIN);
  
  // 2. Przeliczenie surowej wartości na procenty (0% - 100%)
  // Funkcja map(zmienna, od_Min, od_Max, do_Min, do_Max)
  int procentWilgotnosci = map(surowaWartosc, wartoscSucho, wartoscMokro, 0, 100);
  
  // 3. Zabezpieczenie przed przekroczeniem skali (np. -5% albo 105%)
  // Jeśli odczyt wyjdzie poza kalibrację, ucinamy go do ram 0-100
  procentWilgotnosci = constrain(procentWilgotnosci, 0, 100);

  // 4. Wypisanie wyników do Monitora Szeregowego
  Serial.print("Gleba - Wartosc surowa: ");
  Serial.print(surowaWartosc);
  Serial.print("  |  Wilgotnosc: ");
  Serial.print(procentWilgotnosci);
  Serial.println(" %");
}

void odczytajTemperatureKorzeni() {
  // 1. Wysłanie żądania do czujnika, aby dokonał pomiaru (to chwilę trwa)
  int liczbaCzujnikow = czujnikGleby.getDeviceCount();
  
  Serial.print("Liczba wykrytych czujnikow DS18B20: ");
  Serial.println(liczbaCzujnikow);
  
  czujnikGleby.requestTemperatures(); 
  
  // 2. Pobranie zmierzonej temperatury (indeks 0, bo na jednym kablu może być wiele czujników!)
  float temperaturaKorzeni = czujnikGleby.getTempCByIndex(0);
  
  // 3. Sprawdzenie błędów
  // Biblioteka DallasTemperature zwraca -127.00, jeśli czujnik jest odłączony
  if (temperaturaKorzeni == DEVICE_DISCONNECTED_C) {
    Serial.println("Blad: Nie wykryto czujnika DS18B20!");
    Serial.println("Sprawdz polaczenie kabli i czy dodales REZYSTOR 4.7k Ohm!");
    return; // Przerwij funkcję
  }

  // 4. Wypisanie wyników do Monitora Szeregowego
  Serial.print("Temperatura gleby (korzeni): ");
  Serial.print(temperaturaKorzeni);
  Serial.println(" °C");
}

void odczytajNatezenieSwiatla() {
  float poziomSwiatla = miernikSwiatla.readLightLevel();
  
  // 2. Wypisanie wyników do Monitora Szeregowego
  Serial.print("Natezenie swiatla: ");
  Serial.print(poziomSwiatla);
  Serial.print(" lux  |  Ocena warunkow: ");
  
  // 3.Prosta logika, jak roślina "widzi" to światło (do testow)
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
    
    // Używamy darmowego serwera, który służy inżynierom do testowania połączeń
    String adresTestowy = "http://httpbin.org/get";
    http.begin(adresTestowy);
    
    // Wykonujemy zapytanie (tak samo, jak Twoja przeglądarka wchodząca na stronę)
    int kodOdpowiedzi = http.GET();
    
    // Kod większy od 0 oznacza, że serwer nam odpowiedział
    if (kodOdpowiedzi > 0) {
      Serial.print("Odpowiedz serwera otrzymana! Kod HTTP: ");
      Serial.println(kodOdpowiedzi);
      
      // Kod 200 (OK) to standardowa odpowiedź sukcesu w Internecie
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
    
    // Zwalniamy pamięć
    http.end(); 
  } else {
    Serial.println("Blad: Zerwano polaczenie Wi-Fi.");
  }
}

bool zalogujDoSerwera() {
  Serial.println("Proba logowania do serwera...");
  
  HTTPClient http;
  http.begin(loginUrl);
  
  // Mówimy serwerowi, że wypełniamy klasyczny "formularz"
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");

  // Sklejamy e-mail i hasło (zwróć uwagę, że pole nazywa się "username", tak wymaga FastAPI)
  String daneLogowania = "username=" + String(emailUzytkownika) + "&password=" + String(hasloUzytkownika);

  // Wysyłamy żądanie POST z danymi do logowania
  int kodOdpowiedzi = http.POST(daneLogowania);

  if (kodOdpowiedzi == 200) {
    // Sukces! Serwer nas wpuścił. Pobieramy odpowiedź.
    String odpowiedzSerwera = http.getString();
    
    // Odpowiedź to JSON, musimy z niej wyciągnąć pole "access_token"
    StaticJsonDocument<512> doc;
    DeserializationError blad = deserializeJson(doc, odpowiedzSerwera);
    
    if (!blad) {
      // Zapisujemy wyciągnięty token do naszej globalnej zmiennej
      aktualnyToken = doc["access_token"].as<String>();
      Serial.println("Logowanie udane! Zdobylem token JWT.");
      http.end();
      return true;
    }
  } else {
    Serial.print("Blad logowania! Kod HTTP: ");
    Serial.println(kodOdpowiedzi);
    Serial.println(http.getString()); // Wypisze szczegóły błędu
  }
  
  http.end();
  return false;
}

void wyslijDaneDoSerwera(float tempPow, float wilgPow, float tempKorz, int wilgGleby, float swiatlo) {
  // Jeśli z jakiegoś powodu nie mamy tokena (np. restart doniczki), spróbuj się zalogować
  if (aktualnyToken == "") {
    if (!zalogujDoSerwera()) {
      Serial.println("Przerywam wysylanie danych - nie udalo sie zalogowac!");
      return; // Wychodzimy z funkcji, bo bez logowania i tak nas odrzuci (błąd 401)
    }
  }

  // Reszta leci standardowo
  HTTPClient http;
  http.begin(metricsUrl);
  
  http.addHeader("Content-Type", "application/json");
  // Tutaj ESP32 wkleja token, który przed chwilą zdobyło z funkcji logującej:
  http.addHeader("Authorization", "Bearer " + aktualnyToken);

  StaticJsonDocument<200> doc;
  doc["device_id"] = 1; 
  doc["air_temp"] = tempPow;
  doc["air_hum"] = wilgPow;
  doc["root_temp"] = tempKorz;
  doc["soil_hum"] = wilgGleby;
  doc["light_lux"] = swiatlo;

  String jsonPayload;
  serializeJson(doc, jsonPayload);

  int httpResponseCode = http.POST(jsonPayload);

  if (httpResponseCode == 201 || httpResponseCode == 200) {
    Serial.println("Sukces! Pomiary zapisane w bazie.");
  } else if (httpResponseCode == 401) {
    // Jeśli po jakimś czasie token wygasł (np. minęły 24 godziny),
    // czyścimy stary token, aby w kolejnej pętli ESP32 zalogowało się na nowo!
    Serial.println("Serwer odrzucil token (prawdopodobnie wygasl). Kasuje z pamieci.");
    aktualnyToken = ""; 
  } else {
    Serial.print("Blad wysylania pomiarow: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}