# 🌦️ Lokalna Stacja Pogodowa na Raspberry Pi

Prosta, elegancka stacja pogodowa z interfejsem webowym, która zbiera dane z OpenWeatherMap i wyświetla je na interaktywnych wykresach. Idealna do uruchomienia na Raspberry Pi!

## ✨ Funkcje

- 📊 **Interaktywne wykresy** temperatury, wiatru, wilgotności i ciśnienia
- 🔄 **Automatyczne zbieranie danych** co 30 minut
- 💾 **Lokalna baza danych SQLite** - wszystkie dane zapisywane są lokalnie
- 📱 **Responsywny interfejs** - działa na telefonach, tabletach i komputerach
- 🔍 **Zoom i przesuwanie wykresów** - szczegółowa analiza danych
- 🌐 **Dostęp z sieci lokalnej** - sprawdzaj pogodę z dowolnego urządzenia w domu

## 📋 Wymagania

- Raspberry Pi (dowolny model z dostępem do internetu)
- Python 3.7 lub nowszy
- Dostęp do internetu
- Darmowe konto OpenWeatherMap

## 🚀 Instalacja

### 1. Pobierz projekt

```bash
git clone https://github.com/gazda12345kamil-dotcom/stacja-pogodowa.git
cd stacja-pogodowa
```

### 2. Zainstaluj wymagane biblioteki

```bash
pip3 install flask requests
```

### 3. Zdobądź klucz API z OpenWeatherMap

1. Przejdź na stronę: **https://openweathermap.org/api**
1. Kliknij **“Get API Key”** lub **“Sign Up”**
1. Załóż darmowe konto (wystarczy email i hasło)
1. Po zalogowaniu przejdź do sekcji **“API keys”**
1. Skopiuj swój klucz API (ciąg znaków, np. `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p8`)

> ⏰ **Uwaga:** Aktywacja klucza API może potrwać do 2 godzin!

### 4. Znajdź współrzędne swojej lokalizacji

Opcja A - Szybka metoda:

1. Wejdź na: **https://www.latlong.net/**
1. Wpisz swoją miejscowość lub adres
1. Skopiuj wartości **Latitude** (szerokość) i **Longitude** (długość)

Opcja B - Google Maps:

1. Otwórz Google Maps
1. Kliknij prawym na swoją lokalizację
1. Pierwsze dwie liczby to współrzędne (np. `52.2297, 21.0122`)

**Przykładowe współrzędne:**

- Warszawa: `52.2297, 21.0122`
- Kraków: `50.0647, 19.9450`
- Gdańsk: `54.3520, 18.6466`
- Wrocław: `51.1079, 17.0385`
- Poznań: `52.4064, 16.9252`

### 5. Skonfiguruj aplikację

Otwórz plik `Stacja_pogodowa.py` w edytorze tekstowym:

```bash
nano Stacja_pogodowa.py
```

Znajdź sekcję **KONFIGURACJA** na górze pliku i wprowadź swoje dane:

```python
# --- Konfiguracja ---
API_KEY = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p8"  # WKLEJ TUTAJ SWÓJ KLUCZ

LATITUDE = 52.2297   # Szerokość geograficzna
LONGITUDE = 21.0122  # Długość geograficzna
```

Zapisz plik (`Ctrl+O`, `Enter`, `Ctrl+X` w nano).

## 🎯 Uruchomienie

### Metoda 1: Proste uruchomienie (sesja)

```bash
python3 Stacja_pogodowa.py
```

Aplikacja uruchomi się na porcie **5000**.

### Metoda 2: Uruchomienie w tle (nohup)

```bash
nohup python3 Stacja_pogodowa.py > weather.log 2>&1 &
```

Aplikacja będzie działać w tle, nawet po zamknięciu terminala.

### Metoda 3: Automatyczne uruchamianie przy starcie (systemd)

Stwórz plik serwisu:

```bash
sudo nano /etc/systemd/system/weather-station.service
```

Wklej zawartość (dostosuj ścieżki):

```ini
[Unit]
Description=Lokalna Stacja Pogodowa
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/stacja-pogodowa
ExecStart=/usr/bin/python3 /home/pi/stacja-pogodowa/Stacja_pogodowa.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Włącz i uruchom serwis:

```bash
sudo systemctl daemon-reload
sudo systemctl enable weather-station.service
sudo systemctl start weather-station.service
```

Sprawdź status:

```bash
sudo systemctl status weather-station.service
```

## 🌐 Dostęp do aplikacji

### Z Raspberry Pi (lokalnie):

```
http://localhost:5000
```

### Z innych urządzeń w sieci lokalnej:

1. Sprawdź adres IP Raspberry Pi:

```bash
hostname -I
```

1. Otwórz w przeglądarce na telefonie/komputerze:

```
http://ADRES_IP_RASPBERRY:5000
```

Przykład: `http://192.168.1.150:5000`

## 🔧 Konfiguracja zaawansowana

### Zmiana interwału zbierania danych

W pliku `Stacja_pogodowa.py` znajdź:

```python
COLLECT_INTERVAL = 1800  # 1800 sekund = 30 minut
```

Przykładowe wartości:

- `600` = 10 minut
- `1800` = 30 minut (zalecane)
- `3600` = 1 godzina

### Zmiana nazwy bazy danych

```python
DB_NAME = "weather_data.db"
```

## 📊 Funkcje interfejsu

- **Karty z aktualnymi danymi** - temperatura, wiatr, wilgotność, ciśnienie
- **Interaktywne wykresy** - możesz:
  - Przybliżać (scroll myszką lub pinch na telefonie)
  - Przesuwać (przeciągnij wykres)
  - Resetować widok (przycisk “Resetuj zoom”)
- **Automatyczne odświeżanie** - wystarczy odświeżyć stronę

## 🛠️ Rozwiązywanie problemów

### Błąd: “BŁĄD KRYTYCZNY: Błąd autoryzacji (401)”

- Sprawdź, czy poprawnie skopiowałeś klucz API
- Upewnij się, że klucz jest aktywny (poczekaj do 2h po rejestracji)
- Sprawdź, czy nie ma spacji na początku lub końcu klucza

### Błąd: “Nie skonfigurowano API_KEY, LATITUDE lub LONGITUDE”

- Upewnij się, że wszystkie trzy wartości są wypełnione w pliku
- Współrzędne muszą być liczbami (nie `0.0`)

### Nie mogę połączyć się z innego urządzenia

- Sprawdź, czy Raspberry Pi i urządzenie są w tej samej sieci Wi-Fi
- Sprawdź firewall na Raspberry Pi
- Upewnij się, że port 5000 nie jest zablokowany

### Baza danych jest pusta

- Poczekaj 30 minut na pierwsze dane
- Sprawdź logi w terminalu lub w pliku `weather.log`

## 📁 Struktura plików

```
stacja-pogodowa/
├── Stacja_pogodowa.py   # Główny program
├── weather_data.db      # Baza danych (tworzona automatycznie)
└── weather.log          # Logi (jeśli używasz nohup)
```

## 🔒 Bezpieczeństwo

- **NIE** udostępniaj swojego klucza API publicznie
- Aplikacja jest dostępna tylko w sieci lokalnej (nie z Internetu)
- Jeśli chcesz dostęp z Internetu, użyj VPN lub reverse proxy (np. Nginx)

## 📝 Licencja

MIT License - możesz swobodnie używać i modyfikować projekt.

## 🤝 Wsparcie

Jeśli masz problemy:

1. Sprawdź sekcję “Rozwiązywanie problemów”
1. Otwórz Issue na GitHubie
1. Dołącz logi z terminala/pliku `weather.log`

## ⭐ Podziękowania

- OpenWeatherMap za darmowe API
- Chart.js za bibliotekę wykresów
- Społeczność Raspberry Pi

-----

**Autor:** [Kamil]  
**Wersja:** 1.0  
**Ostatnia aktualizacja:** Październik 2025
