import time
import urequests  as requests
import network
import Config
import gc


class Logger():
    
    def __init__(self):
        pass
    
    def begin(self):
        self.url = Config.FIREBASE_URL
        
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            print("Conectando a Wi-Fi...")
            wlan.connect(Config.WIFI_SSID, Config.WIFI_PASSWORD)
            while not wlan.isconnected():
                time.sleep_ms(500)
        print("¡Wi-Fi Conectado exitosamente!")
        
        
    def send_data(self, emergency, pwm, sensors, steering, x, y, sentido):
        
        gc.collect() # Vacía variables residuales de la RAM
    
        car_json = {
            "emergency": emergency,
            "motor_pwm": pwm,
            "sensors": sensors,
            "steering_deg": steering,
            "timestamp": time.time(),
            "x": x,
            "y": y,
            "sentido": sentido
        }
        
        print(car_json)
    

        try: 
            print("Enviando datos...")
            response = requests.put(self.url, json=car_json)

            print(f"Status Code: {response.status_code}")
            print(response.text)
            
            response.close()
         
        except Exception as e:
            print("Error en la petición:", e)
