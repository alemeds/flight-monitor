"""
Conector para APIs reales de vuelos
Integra Amadeus, Skyscanner y otras APIs
"""

import requests
import streamlit as st
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random

class FlightAPIConnector:
    def __init__(self):
        self.amadeus_token = None
        self.amadeus_token_expires = None
        
    def get_secret(self, key: str, default=None):
        """Obtiene secretos de Streamlit Cloud o variables de entorno"""
        try:
            return st.secrets[key]
        except (KeyError, FileNotFoundError):
            import os
            return os.getenv(key, default)
    
    def get_amadeus_token(self) -> Optional[str]:
        """Obtiene token de acceso de Amadeus API"""
        try:
            # Verificar si el token actual sigue siendo válido
            if (self.amadeus_token and self.amadeus_token_expires and 
                datetime.now() < self.amadeus_token_expires):
                return self.amadeus_token
            
            # Obtener credenciales
            api_key = self.get_secret("AMADEUS_API_KEY")
            api_secret = self.get_secret("AMADEUS_API_SECRET")
            
            if not api_key or not api_secret:
                return None
            
            # Solicitar nuevo token
            auth_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': api_key,
                'client_secret': api_secret
            }
            
            response = requests.post(auth_url, data=auth_data, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                self.amadeus_token = token_data['access_token']
                # Token válido por 30 minutos, renovar 5 minutos antes
                self.amadeus_token_expires = datetime.now() + timedelta(minutes=25)
                return self.amadeus_token
            else:
                st.error(f"Error autenticando con Amadeus: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Error obteniendo token Amadeus: {str(e)}")
            return None
    
    def search_flights_amadeus(self, search_data: Dict) -> Optional[Dict]:
        """Busca vuelos usando Amadeus API"""
        try:
            token = self.get_amadeus_token()
            if not token:
                return None
            
            # Configurar búsqueda
            search_url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'originLocationCode': search_data['origin'],
                'destinationLocationCode': search_data['destination'], 
                'departureDate': search_data['departure_date'],
                'adults': search_data.get('passengers', 1),
                'max': 10,  # Máximo 10 ofertas
                'currencyCode': 'USD'
            }
            
            # Añadir fecha de regreso si existe
            if search_data.get('return_date'):
                params['returnDate'] = search_data['return_date']
            
            response = requests.get(search_url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and len(data['data']) > 0:
                    # Encontrar la oferta más barata
                    cheapest_offer = min(data['data'], 
                                       key=lambda x: float(x['price']['total']))
                    
                    # Extraer información del vuelo
                    price = float(cheapest_offer['price']['total'])
                    currency = cheapest_offer['price']['currency']
                    
                    # Información de la aerolínea
                    airline_code = cheapest_offer['itineraries'][0]['segments'][0]['carrierCode']
                    airline_name = self.get_airline_name(airline_code)
                    
                    # Detalles del vuelo
                    segments = cheapest_offer['itineraries'][0]['segments']
                    stops = len(segments) - 1
                    
                    if stops == 0:
                        flight_details = "Vuelo directo"
                    else:
                        flight_details = f"{stops} escala{'s' if stops > 1 else ''}"
                    
                    return {
                        'price': price,
                        'currency': currency,
                        'airline': airline_name,
                        'flight_details': flight_details,
                        'source': 'Amadeus',
                        'raw_data': cheapest_offer
                    }
                else:
                    return None
            else:
                st.warning(f"Amadeus API error: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Error buscando vuelos en Amadeus: {str(e)}")
            return None
    
    def search_flights_skyscanner(self, search_data: Dict) -> Optional[Dict]:
        """Busca vuelos usando Skyscanner via RapidAPI"""
        try:
            rapidapi_key = self.get_secret("RAPIDAPI_KEY")
            if not rapidapi_key:
                return None
            
            # Configurar búsqueda
            country = "US"
            currency = "USD"
            locale = "en-US"
            
            origin = search_data['origin']
            destination = search_data['destination']
            departure_date = search_data['departure_date']
            
            # URL para búsqueda de citas
            url = f"https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices/browsequotes/v1.0/{country}/{currency}/{locale}/{origin}/{destination}/{departure_date}"
            
            # Añadir fecha de regreso si existe
            if search_data.get('return_date'):
                url += f"/{search_data['return_date']}"
            
            headers = {
                "X-RapidAPI-Key": rapidapi_key,
                "X-RapidAPI-Host": "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com"
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Quotes' in data and len(data['Quotes']) > 0:
                    # Encontrar la cita más barata
                    cheapest_quote = min(data['Quotes'], 
                                       key=lambda x: x['MinPrice'])
                    
                    price = cheapest_quote['MinPrice']
                    
                    # Obtener información de la aerolínea
                    carrier_id = cheapest_quote['OutboundLeg']['CarrierIds'][0]
                    airline_name = "Aerolínea"
                    
                    # Buscar nombre de aerolínea en carriers
                    if 'Carriers' in data:
                        for carrier in data['Carriers']:
                            if carrier['CarrierId'] == carrier_id:
                                airline_name = carrier['Name']
                                break
                    
                    # Información de escalas
                    stops = len(cheapest_quote['OutboundLeg'].get('StopIds', [])) 
                    if stops == 0:
                        flight_details = "Vuelo directo"
                    else:
                        flight_details = f"{stops} escala{'s' if stops > 1 else ''}"
                    
                    return {
                        'price': price,
                        'currency': currency,
                        'airline': airline_name,
                        'flight_details': flight_details,
                        'source': 'Skyscanner',
                        'raw_data': cheapest_quote
                    }
                else:
                    return None
            else:
                st.warning(f"Skyscanner API error: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Error buscando vuelos en Skyscanner: {str(e)}")
            return None
    
    def get_airline_name(self, airline_code: str) -> str:
        """Convierte código de aerolínea a nombre"""
        airline_codes = {
            'AA': 'American Airlines',
            'DL': 'Delta Air Lines', 
            'UA': 'United Airlines',
            'AV': 'Avianca',
            'LA': 'LATAM Airlines',
            'VV': 'Viva Air',
            'NK': 'Spirit Airlines',
            'F9': 'Frontier Airlines',
            'B6': 'JetBlue Airways',
            'WN': 'Southwest Airlines',
            'AS': 'Alaska Airlines',
            'HA': 'Hawaiian Airlines',
            'G4': 'Allegiant Air',
            'SY': 'Sun Country Airlines'
        }
        return airline_codes.get(airline_code, f"Aerolínea {airline_code}")
    
    def simulate_flight_search(self, search_data: Dict) -> Dict:
        """Simulación mejorada de búsqueda de vuelos"""
        # Factores realistas para simulación
        base_prices = {
            ('BOG', 'MIA'): 350,
            ('BOG', 'JFK'): 450,
            ('BOG', 'LAX'): 550,
            ('MDE', 'MIA'): 320,
            ('CLO', 'BOG'): 150,
            ('CTG', 'BOG'): 180,
        }
        
        route = (search_data['origin'], search_data['destination'])
        reverse_route = (search_data['destination'], search_data['origin'])
        
        # Precio base
        if route in base_prices:
            base_price = base_prices[route]
        elif reverse_route in base_prices:
            base_price = base_prices[reverse_route]
        else:
            # Estimar basado en distancia aproximada
            base_price = random.randint(200, 800)
        
        # Factores de variación
        departure_date = datetime.strptime(search_data['departure_date'], '%Y-%m-%d')
        days_ahead = (departure_date - datetime.now()).days
        
        # Factor de anticipación
        if days_ahead < 7:
            price_factor = 1.4  # Más caro último momento
        elif days_ahead > 90:
            price_factor = 0.9  # Más barato con anticipación
        else:
            price_factor = 1.0
        
        # Factor día de la semana
        weekday = departure_date.weekday()
        if weekday in [4, 5, 6]:  # Viernes, sábado, domingo
            price_factor *= 1.15
        
        # Factor temporada
        month = departure_date.month
        if month in [12, 1, 6, 7]:  # Temporada alta
            price_factor *= 1.25
        
        # Variación aleatoria
        price_factor *= random.uniform(0.85, 1.15)
        
        final_price = base_price * price_factor
        
        airlines = [
            'Avianca', 'LATAM Airlines', 'Viva Air', 'American Airlines', 
            'Delta Air Lines', 'United Airlines', 'JetBlue Airways', 'Copa Airlines'
        ]
        
        # Probabilidad de escalas
        if random.random() < 0.3:
            flight_details = "Vuelo directo"
        else:
            stops = random.choice([1, 1, 2])  # Más probable 1 escala
            flight_details = f"{stops} escala{'s' if stops > 1 else ''}"
        
        return {
            'price': round(final_price, 2),
            'currency': 'USD',
            'airline': random.choice(airlines),
            'flight_details': flight_details,
            'source': 'Simulación'
        }
    
    def search_flights(self, search_data: Dict) -> Dict:
        """Método principal que intenta múltiples APIs y fallback a simulación"""
        
        # Intentar APIs en orden de preferencia
        apis_to_try = []
        
        # Verificar qué APIs están disponibles
        if self.get_secret("AMADEUS_API_KEY") and self.get_secret("AMADEUS_API_SECRET"):
            apis_to_try.append(('Amadeus', self.search_flights_amadeus))
        
        if self.get_secret("RAPIDAPI_KEY"):
            apis_to_try.append(('Skyscanner', self.search_flights_skyscanner))
        
        # Intentar cada API disponible
        for api_name, api_function in apis_to_try:
            try:
                st.info(f"🔍 Buscando en {api_name}...")
                result = api_function(search_data)
                
                if result:
                    st.success(f"✅ Datos obtenidos de {api_name}")
                    return result
                else:
                    st.warning(f"⚠️ {api_name}: No se encontraron vuelos")
                    
            except Exception as e:
                st.warning(f"⚠️ Error en {api_name}: {str(e)}")
                continue
        
        # Si todas las APIs fallan, usar simulación
        st.info("🎮 Usando datos simulados (APIs no disponibles)")
        return self.simulate_flight_search(search_data)


# Clase Rate Limiter para APIs
class APIRateLimiter:
    def __init__(self, max_calls_per_minute: int = 10):
        self.max_calls = max_calls_per_minute
        self.calls = []
    
    def can_make_call(self) -> bool:
        """Verifica si se puede hacer una llamada a la API"""
        now = datetime.now()
        
        # Remover llamadas de hace más de 1 minuto
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < timedelta(minutes=1)]
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False
    
    def time_until_next_call(self) -> int:
        """Tiempo en segundos hasta que se pueda hacer la próxima llamada"""
        if len(self.calls) < self.max_calls:
            return 0
        
        oldest_call = min(self.calls)
        next_available = oldest_call + timedelta(minutes=1)
        wait_time = (next_available - datetime.now()).total_seconds()
        
        return max(0, int(wait_time))


# Test de conectividad de APIs
def test_api_connections():
    """Prueba la conectividad con las APIs configuradas"""
    connector = FlightAPIConnector()
    results = {}
    
    st.subheader("🧪 Test de Conectividad de APIs")
    
    # Test Amadeus
    if connector.get_secret("AMADEUS_API_KEY"):
        with st.spinner("Probando Amadeus API..."):
            token = connector.get_amadeus_token()
            if token:
                st.success("✅ Amadeus API: Conectado")
                results['Amadeus'] = True
            else:
                st.error("❌ Amadeus API: Error de conexión")
                results['Amadeus'] = False
    else:
        st.info("ℹ️ Amadeus API: No configurado")
        results['Amadeus'] = None
    
    # Test RapidAPI
    if connector.get_secret("RAPIDAPI_KEY"):
        st.info("ℹ️ RapidAPI: Configurado (test requiere consulta real)")
        results['RapidAPI'] = None
    else:
        st.info("ℹ️ RapidAPI: No configurado")
        results['RapidAPI'] = None
    
    return results


# Función para usar en la app principal
def get_flight_connector():
    """Factory function para obtener el conector de APIs"""
    if 'flight_connector' not in st.session_state:
        st.session_state.flight_connector = FlightAPIConnector()
    return st.session_state.flight_connector
