import requests
import sqlite3
import datetime
import time
import threading
from flask import Flask, jsonify

# --- Konfiguracja ---
# 1. Zdobądź DARMOWY klucz API rejestrując się na https://openweathermap.org/
API_KEY = "WPISZ_SWOJ_KLUCZ_API_Z_OPENWEATHERMAP" 

# 2. Wprowadź współrzędne dla swojej lokalizacji
#    Możesz je znaleźć np. na https://www.latlong.net/
LATITUDE = 0.0  # WPISZ SZEROKOŚĆ GEOGRAFICZNĄ (np. 52.2297 dla Warszawy)
LONGITUDE = 0.0 # WPISZ DŁUGOŚĆ GEOGRAFICZNĄ (np. 21.0122 dla Warszawy)

# 3. Nazwa bazy danych i interwał
DB_NAME = "weather_data.db" # Nazwa pliku bazy danych
COLLECT_INTERVAL = 1800 # 1800 sekund = 30 minut

# --- Inicjalizacja Aplikacji Flask ---
app = Flask(__name__)

# === CZĘŚĆ 1: LOGIKA BAZY DANYCH I ZBIERANIA DANYCH ===

def init_db():
    """Inicjalizuje bazę danych SQLite, jeśli nie istnieje."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL,
            feels_like REAL,
            humidity INTEGER,
            pressure INTEGER,
            description TEXT,
            wind_speed REAL
        )
    """)
    conn.commit()
    conn.close()

def fetch_and_save_weather():
    """Pobiera dane z OpenWeatherMap i zapisuje je do bazy danych."""
    
    # Sprawdzenie czy użytkownik ustawił klucz API i lokalizację
    if API_KEY == "WPISZ_SWOJ_KLUCZ_API_Z_OPENWEATHERMAP" or (LATITUDE == 0.0 and LONGITUDE == 0.0):
        print(f"[{datetime.datetime.now()}] BŁĄD: Nie skonfigurowano API_KEY, LATITUDE lub LONGITUDE na górze pliku!")
        print("Proszę edytować plik i ustawić te wartości.")
        # Czekamy dłużej przed kolejną próbą, aby nie spamować logów
        time.sleep(COLLECT_INTERVAL / 3) 
        return

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "appid": API_KEY,
        "units": "metric",
        "lang": "pl"
    }
    print(f"[{datetime.datetime.now()}] Próba pobrania danych pogodowych dla ({LATITUDE}, {LONGITUDE})...")
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status() # Sprawdza błędy HTTP (np. 401 - zły klucz API)
        data = response.json()
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        temperature = data['main']['temp']
        feels_like = data['main']['feels_like'] 
        humidity = data['main']['humidity']
        pressure = data['main']['pressure']
        description = data['weather'][0]['description']
        wind_speed = data['wind']['speed'] 

        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO weather (timestamp, temperature, feels_like, humidity, pressure, description, wind_speed) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (timestamp, temperature, feels_like, humidity, pressure, description, wind_speed)
        )
        conn.commit()
        conn.close()
        print(f"[{datetime.datetime.now()}] Dane zapisane: Temp: {temperature}°C, Wiatr: {wind_speed} m/s")
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 401:
            print(f"[{datetime.datetime.now()}] BŁĄD KRYTYCZNY: Błąd autoryzacji (401). Sprawdź swój API_KEY.")
        else:
            print(f"[{datetime.datetime.now()}] Błąd HTTP podczas pobierania: {http_err}")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Błąd podczas pobierania lub zapisu: {e}")

def background_collector():
    """Wątek działający w tle, który cyklicznie pobiera dane."""
    init_db()
    print(f"Zainicjowano bazę danych: {DB_NAME}")
    while True:
        fetch_and_save_weather()
        time.sleep(COLLECT_INTERVAL)

# === CZĘŚĆ 2: LOGIKA SERWERA WWW (FLASK) ===

@app.route('/data.json')
def get_data_as_json():
    """Zwraca WSZYSTKIE dane pogodowe w formacie JSON dla wykresów."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row # Umożliwia dostęp do kolumn po nazwie
    cursor = conn.cursor()
    
    # Pobieramy WSZYSTKIE dane z bazy
    cursor.execute(
        "SELECT timestamp, temperature, feels_like, humidity, pressure, description, wind_speed FROM weather ORDER BY timestamp ASC"
    )
    rows = cursor.fetchall()
    conn.close()

    timestamps = []
    temperatures = []
    feels_like_list = []
    humidities = []
    pressures = []
    descriptions = []
    wind_speed_list = []

    # Domyślne wartości, jeśli baza jest pusta
    latest_data = {
        "latest_temp": "N/A",
        "latest_feels_like": "N/A",
        "latest_hum": "N/A",
        "latest_pres": "N/A",
        "latest_desc": "Brak danych",
        "latest_wind_speed": "N/A",
        "latest_time": "Oczekuję..."
    }

    if rows:
        for row in rows:
            # Formatowanie timestampu dla osi X wykresu
            ts_formatted = datetime.datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M")
            timestamps.append(ts_formatted)
            
            temperatures.append(row['temperature'])
            feels_like_list.append(row['feels_like'])
            humidities.append(row['humidity'])
            pressures.append(row['pressure'])
            descriptions.append(row['description'])
            wind_speed_list.append(row['wind_speed'])

        # Ustawiamy najnowsze dane (z ostatniego wiersza)
        latest_row = rows[-1]
        latest_data = {
            "latest_temp": latest_row['temperature'],
            "latest_feels_like": latest_row['feels_like'],
            "latest_hum": latest_row['humidity'],
            "latest_pres": latest_row['pressure'],
            "latest_desc": latest_row['description'],
            "latest_wind_speed": latest_row['wind_speed'],
            "latest_time": datetime.datetime.strptime(latest_row['timestamp'], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M")
        }

    chart_data = {
        "timestamps": timestamps,
        "temperatures": temperatures,
        "feels_like": feels_like_list,
        "humidities": humidities,
        "pressures": pressures,
        "wind_speed": wind_speed_list
    }
    return jsonify(latest_data=latest_data, chart_data=chart_data)


@app.route('/')
def index():
    """Główna strona aplikacji - serwuje wbudowany HTML."""
    
    html_content = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lokalna Stacja Pogodowa RPi</title>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/hammer.js/2.0.8/hammer.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.1/dist/chartjs-plugin-zoom.min.js"></script>
    
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
    
    <style>
        body { 
            font-family: 'Roboto', sans-serif; 
            margin: 0;
            padding: 20px;
            background-color: #f4f7f6; 
            color: #333; 
        }
        .container { max-width: 1400px; margin: auto; padding: 20px; }
        h1, h2 { text-align: center; color: #2c3e50; font-weight: 700; }
        h2 { font-weight: 400; color: #34495e; margin-top: 40px; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }

        /* --- NOWOCZESNE KARTY --- */
        .grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .data-card {
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            padding: 25px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .card-title { font-size: 1.2em; font-weight: 700; color: #34495e; margin-bottom: 15px; display: flex; align-items: center; }
        .card-icon { font-size: 1.5em; margin-right: 10px; }
        .card-value { font-size: 2.2em; font-weight: 700; color: #2c3e50; margin-bottom: 10px; }
        .card-value-small { font-size: 1.5em; font-weight: 400; color: #2c3e50; }
        .card-note { font-size: 1em; font-weight: 300; color: #555; }

        /* --- WYKRESY --- */
        .chart-container { 
            margin-bottom: 30px; 
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            padding: 20px;
            height: 500px; 
            position: relative; /* Ważne dla przycisku resetu */
        }
        
        .reset-zoom-btn {
            position: absolute;
            top: 15px;
            right: 20px;
            z-index: 10; 
            padding: 5px 12px;
            font-size: 13px;
            font-weight: 700;
            color: #34495e;
            background: #ecf0f1;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            opacity: 0.7;
            transition: opacity 0.2s, background 0.2s;
        }
        .reset-zoom-btn:hover {
            background: #bdc3c7;
            opacity: 1;
        }
        
        canvas { padding: 10px; }
        footer { text-align: center; margin-top: 40px; font-size: 0.9em; color: #7f8c8d; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Lokalna Stacja Pogodowa</h1>
        
        <h2>Aktualne dane (<span id="latest_time">...</span>)</h2>
        <div class="grid-container">
            <div class="data-card">
                <div class="card-title"><span class="card-icon">🌡️</span>Temperatura</div>
                <div>
                    <div class="card-value"><span id="latest_temp">...</span>°C</div>
                    <div class="card-note">Odczuwalna: <span id="latest_feels_like">...</span>°C</div>
                </div>
            </div>
            
            <div class="data-card">
                <div class="card-title"><span class="card-icon">🌬️</span>Wiatr i Pogoda</div>
                <div>
                    <div class="card-value-small"><span id="latest_wind_speed">...</span> m/s</div>
                    <div class="card-note">Opis: <span id="latest_desc">...</span></div>
                </div>
            </div>

            <div class="data-card">
                <div class="card-title"><span class="card-icon">💧</span>Atmosfera</div>
                <div>
                    <div class="card-value-small"><span id="latest_hum">...</span>%</div>
                    <div class="card-note">Ciśnienie: <span id="latest_pres">...</span> hPa</div>
                </div>
            </div>
        </div>

        <h2>Dane Historyczne (Cały okres)</h2>

        <div class="chart-container">
            <button class="reset-zoom-btn" onclick="charts['temperatureChart'].resetZoom()">Resetuj zoom</button>
            <canvas id="temperatureChart"></canvas>
        </div>
        
        <div class="chart-container">
            <button class="reset-zoom-btn" onclick="charts['windChart'].resetZoom()">Resetuj zoom</button>
            <canvas id="windChart"></canvas>
        </div>

        <div class="chart-container">
            <button class="reset-zoom-btn" onclick="charts['humidityChart'].resetZoom()">Resetuj zoom</button>
            <canvas id="humidityChart"></canvas>
        </div>

        <div class="chart-container">
            <button class="reset-zoom-btn" onclick="charts['pressureChart'].resetZoom()">Resetuj zoom</button>
            <canvas id="pressureChart"></canvas>
        </div>

        <footer><p>Dane z OpenWeatherMap | Generowane przez Raspberry Pi (lub inny serwer)</p></footer>
    </div>

    <script>
        // Globalny obiekt do przechowywania instancji wykresów
        let charts = {};

        /**
         * Rysuje lub aktualizuje wykres Chart.js
         * @param {string} canvasId - ID elementu <canvas>
         * @param {string} chartTitle - Tytuł dla osi Y
         * @param {Array} datasets - Tablica obiektów dataset dla Chart.js
         * @param {Array} timestamps - Tablica etykiet (czasów) dla osi X
         */
        function drawChart(canvasId, chartTitle, datasets, timestamps) {
            const ctx = document.getElementById(canvasId).getContext('2d');
            
            // Jeśli wykres już istnieje, zniszcz go przed narysowaniem nowego
            if (charts[canvasId]) {
                charts[canvasId].destroy();
            }
            
            charts[canvasId] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: timestamps,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false, 
                    scales: {
                        x: { display: true },
                        y: { display: true, title: { display: true, text: chartTitle } }
                    },
                    plugins: {
                        zoom: {
                            pan: { 
                                enabled: true, 
                                mode: 'xy' // Umożliwia przesuwanie w obu osiach
                            },
                            zoom: {
                                wheel: { enabled: true },
                                pinch: { enabled: true },
                                mode: 'xy', // Umożliwia zoomowanie w obu osiach
                            }
                        },
                        legend: {
                            // Pokazuj legendę tylko jeśli jest więcej niż 1 zestaw danych
                            display: datasets.length > 1 
                        }
                    }
                }
            });
        }

        /**
         * Główna funkcja pobierająca dane z endpointu /data.json i aktualizująca stronę
         */
        async function updateData() {
            try {
                const response = await fetch('/data.json');
                if (!response.ok) {
                    throw new Error(`Błąd HTTP: ${response.status}`);
                }
                const data = await response.json();

                // --- 1. Aktualizacja kart z najnowszymi danymi ---
                document.getElementById('latest_time').innerText = data.latest_data.latest_time;
                document.getElementById('latest_temp').innerText = data.latest_data.latest_temp;
                document.getElementById('latest_feels_like').innerText = data.latest_data.latest_feels_like;
                document.getElementById('latest_wind_speed').innerText = data.latest_data.latest_wind_speed;
                document.getElementById('latest_hum').innerText = data.latest_data.latest_hum;
                document.getElementById('latest_pres').innerText = data.latest_data.latest_pres;
                
                // Formatowanie opisu (pierwsza litera duża)
                let desc = data.latest_data.latest_desc;
                if (typeof desc === 'string' && desc.length > 0) {
                     document.getElementById('latest_desc').innerText = desc.charAt(0).toUpperCase() + desc.slice(1);
                } else {
                     document.getElementById('latest_desc').innerText = desc;
                }

                const ts = data.chart_data.timestamps;

                // --- 2. Definiowanie i rysowanie wykresów ---

                // Wykres Temperatury
                const tempDatasets = [
                    {
                        label: 'Temperatura (°C)',
                        data: data.chart_data.temperatures,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1,
                        fill: false
                    },
                    {
                        label: 'Odczuwalna (°C)',
                        data: data.chart_data.feels_like,
                        borderColor: 'rgb(255, 159, 64)',
                        backgroundColor: 'rgba(255, 159, 64, 0.2)',
                        tension: 0.1,
                        fill: false,
                        borderDash: [5, 5] // Linia kreskowana
                    }
                ];
                drawChart('temperatureChart', 'Temperatura (°C)', tempDatasets, ts);

                // Wykres Wiatru
                const windDatasets = [
                    {
                        label: 'Prędkość wiatru (m/s)',
                        data: data.chart_data.wind_speed,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1,
                        fill: true
                    }
                ];
                drawChart('windChart', 'Prędkość wiatru (m/s)', windDatasets, ts);
                
                // Wykres Wilgotności
                const humidityDatasets = [
                    {
                        label: 'Wilgotność (%)',
                        data: data.chart_data.humidities,
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        tension: 0.1,
                        fill: true
                    }
                ];
                drawChart('humidityChart', 'Wilgotność (%)', humidityDatasets, ts);

                // Wykres Ciśnienia
                const pressureDatasets = [
                    {
                        label: 'Ciśnienie (hPa)',
                        data: data.chart_data.pressures,
                        borderColor: 'rgb(153, 102, 255)',
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
                        tension: 0.1,
                        fill: true
                    }
                ];
                drawChart('pressureChart', 'Ciśnienie (hPa)', pressureDatasets, ts);

            } catch (error) {
                console.error('Błąd podczas pobierania lub przetwarzania danych:', error);
                document.getElementById('latest_desc').innerText = "Brak danych lub błąd ładowania...";
            }
        }

        // Uruchom pobieranie danych przy załadowaniu strony
        window.addEventListener('load', updateData);
        
    </script>
</body>
</html>
    """
    return html_content

# === CZĘŚĆ 3: URUCHOMIENIE APLIKACJI ===

if __name__ == '__main__':
    # Uruchomienie wątku zbierającego dane w tle
    # daemon=True sprawia, że wątek zakończy się automatycznie po zamknięciu głównego programu
    collector_thread = threading.Thread(target=background_collector, daemon=True)
    collector_thread.start()
    
    print("Uruchamianie serwera Flask (Lokalna Stacja Pogodowa) na http://0.0.0.0:5000")
    print(f"Dane będą zbierane co {COLLECT_INTERVAL} sekund.")
    print("Aby uzyskać dostęp z innych urządzeń w sieci, użyj adresu IP serwera, np. http://192.168.1.10:5000")
    
    # Uruchomienie serwera Flask
    # host='0.0.0.0' sprawia, że serwer jest dostępny z zewnątrz (nie tylko z localhost)
    app.run(host='0.0.0.0', port=5000)
