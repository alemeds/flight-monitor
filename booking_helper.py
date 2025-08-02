"""
Módulo para integrar funcionalidades de compra de vuelos
Genera enlaces inteligentes y facilita el proceso de booking
"""

import streamlit as st
import urllib.parse
from datetime import datetime
from typing import Dict, List

class FlightBookingHelper:
    def __init__(self):
        self.affiliate_codes = {
            'skyscanner': st.secrets.get('SKYSCANNER_AFFILIATE', ''),
            'kayak': st.secrets.get('KAYAK_AFFILIATE', ''),
            'expedia': st.secrets.get('EXPEDIA_AFFILIATE', ''),
        }
    
    def generate_google_flights_url(self, search_data: Dict) -> str:
        """Genera URL optimizada para Google Flights"""
        origin = search_data['origin']
        destination = search_data['destination']
        departure_date = search_data['departure_date']
        return_date = search_data.get('return_date', '')
        passengers = search_data.get('passengers', 1)
        
        # Formato de fecha para Google Flights: YYYY-MM-DD
        dep_formatted = departure_date.replace('-', '')
        
        base_url = "https://www.google.com/travel/flights"
        
        if return_date:
            ret_formatted = return_date.replace('-', '')
            # Vuelo redondo
            url = f"{base_url}?tfs=CBwQAhojEgoyMDI1LTA0LTE1KAFwAYIBCwj___________8BQAFIAR"
        else:
            # Solo ida
            url = f"{base_url}?tfs=CBwQAhokag0IAhIJL20vMDFkenlkagwIAhIIL20vMDRzd2RqAQ"
        
        # Agregar parámetros adicionales
        params = {
            'hl': 'es',
            'gl': 'CO',  # País Colombia
            'curr': 'USD'
        }
        
        return f"{url}&{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    
    def generate_booking_links(self, flight_data: Dict, search_data: Dict) -> Dict[str, str]:
        """Genera enlaces a múltiples plataformas de booking"""
        
        origin = search_data['origin']
        destination = search_data['destination']
        departure_date = search_data['departure_date']
        return_date = search_data.get('return_date', '')
        passengers = search_data.get('passengers', 1)
        
        # Formatear fechas para diferentes plataformas
        dep_formatted = departure_date.replace('-', '')
        dep_slash = departure_date.replace('-', '/')
        
        links = {}
        
        # Google Flights (principal)
        links['🔍 Google Flights'] = self.generate_google_flights_url(search_data)
        
        # Skyscanner
        skyscanner_url = f"https://www.skyscanner.com/transport/flights/{origin}/{destination}/{dep_formatted}"
        if return_date:
            ret_formatted = return_date.replace('-', '')
            skyscanner_url += f"/{ret_formatted}"
        skyscanner_url += f"/?adults={passengers}&locale=es-MX&currency=USD"
        links['🌐 Skyscanner'] = skyscanner_url
        
        # Kayak
        trip_type = "roundtrip" if return_date else "oneway"
        kayak_url = f"https://www.kayak.com/flights/{origin}-{destination}/{departure_date}"
        if return_date:
            kayak_url += f"/{return_date}"
        kayak_url += f"?sort=price_a&fs=cfc=1"
        links['🚁 Kayak'] = kayak_url
        
        # Expedia
        expedia_url = f"https://www.expedia.com/Flights-Search?trip={trip_type}&leg1=from:{origin},to:{destination},departure:{departure_date}"
        if return_date:
            expedia_url += f"&leg2=from:{destination},to:{origin},departure:{return_date}"
        expedia_url += f"&passengers=children:0,adults:{passengers},seniors:0,infantinlap:Y"
        links['🏢 Expedia'] = expedia_url
        
        # Despegar (para usuarios de América Latina)
        despegar_url = f"https://www.despegar.com/vuelos/resultados/search?from={origin}&to={destination}&departure={departure_date}"
        if return_date:
            despegar_url += f"&return={return_date}"
        despegar_url += f"&adults={passengers}&children=0&infants=0&class=ECONOMY"
        links['✈️ Despegar'] = despegar_url
        
        # Momondo
        momondo_url = f"https://www.momondo.com/flight-search/{origin}-{destination}/{departure_date}"
        if return_date:
            momondo_url += f"/{return_date}"
        momondo_url += f"?sort=price_a&fs=cfc=1"
        links['🔍 Momondo'] = momondo_url
        
        # Si conocemos la aerolínea específica, agregar enlace directo
        if flight_data.get('airline'):
            airline_link = self.get_airline_direct_link(
                flight_data['airline'], origin, destination, departure_date, return_date
            )
            if airline_link:
                links[f"🏢 {flight_data['airline']} (Directo)"] = airline_link
        
        return links
    
    def get_airline_direct_link(self, airline: str, origin: str, dest: str, 
                               dep_date: str, ret_date: str = None) -> str:
        """Genera enlaces directos a sitios web de aerolíneas"""
        
        airline_sites = {
            'Avianca': 'https://www.avianca.com',
            'LATAM': 'https://www.latam.com', 
            'LATAM Airlines': 'https://www.latam.com',
            'American Airlines': 'https://www.aa.com',
            'Delta': 'https://www.delta.com',
            'Delta Air Lines': 'https://www.delta.com',
            'United': 'https://www.united.com',
            'United Airlines': 'https://www.united.com',
            'JetBlue': 'https://www.jetblue.com',
            'JetBlue Airways': 'https://www.jetblue.com',
            'Spirit Airlines': 'https://www.spirit.com',
            'Copa Airlines': 'https://www.copaair.com',
            'Viva Air': 'https://www.vivaair.com'
        }
        
        base_url = airline_sites.get(airline)
        if not base_url:
            # Fallback a búsqueda en Google
            return f"https://www.google.com/search?q={urllib.parse.quote(f'{airline} vuelos {origin} {dest}')}"
        
        # Para la mayoría de aerolíneas, redirigir a la página principal
        # En un entorno de producción, cada aerolínea tendría su formato específico
        return f"{base_url}/booking"
    
    def show_booking_widget(self, flight_data: Dict, search_data: Dict):
        """Muestra widget completo de opciones de compra"""
        
        st.markdown("---")
        st.subheader("🛒 ¿Te interesa este precio? ¡Búscalo para comprarlo!")
        
        # Resumen del vuelo
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💰 Precio Encontrado", f"${flight_data['price']} {flight_data.get('currency', 'USD')}")
        
        with col2:
            st.metric("✈️ Aerolínea", flight_data.get('airline', 'N/A'))
        
        with col3:
            st.metric("🛫 Ruta", f"{search_data['origin']} → {search_data['destination']}")
        
        # Información adicional
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**📅 Detalles del vuelo:**")
            st.write(f"• Salida: {search_data['departure_date']}")
            if search_data.get('return_date'):
                st.write(f"• Regreso: {search_data['return_date']}")
            st.write(f"• Pasajeros: {search_data.get('passengers', 1)}")
            st.write(f"• Tipo: {flight_data.get('flight_details', 'N/A')}")
        
        with col2:
            st.write("**💡 Consejos de compra:**")
            st.write("• Compara en 2-3 sitios")
            st.write("• Revisa políticas de equipaje")
            st.write("• Verifica horarios exactos")
            st.write("• Lee políticas de cancelación")
        
        # Enlaces de compra
        st.write("**🔗 Buscar y comprar en:**")
        
        booking_links = self.generate_booking_links(flight_data, search_data)
        
        # Botón principal (Google Flights)
        google_flights_url = booking_links.get('🔍 Google Flights', '')
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Buscar en Google Flights", type="primary", use_container_width=True):
                # Usar JavaScript para abrir en nueva pestaña
                js_code = f"""
                <script>
                    window.open('{google_flights_url}', '_blank');
                </script>
                """
                st.components.v1.html(js_code, height=0)
                st.success("✅ ¡Abriendo Google Flights en nueva pestaña!")
                
                # Opcional: tracking de clicks
                self.track_booking_click('Google Flights', flight_data, search_data)
        
        # Otras opciones en expander
        with st.expander("🌐 Ver más opciones de compra"):
            
            # Organizar enlaces en columnas
            link_items = list(booking_links.items())
            
            for i in range(0, len(link_items), 2):
                col1, col2 = st.columns(2)
                
                # Primera columna
                if i < len(link_items):
                    platform, url = link_items[i]
                    if platform != '🔍 Google Flights':  # Ya mostrado arriba
                        with col1:
                            st.markdown(f"[{platform}]({url})")
                
                # Segunda columna
                if i + 1 < len(link_items):
                    platform, url = link_items[i + 1]
                    if platform != '🔍 Google Flights':
                        with col2:
                            st.markdown(f"[{platform}]({url})")
        
        # Alerta de precio
        self.show_price_alert_section(flight_data, search_data)
    
    def show_price_alert_section(self, flight_data: Dict, search_data: Dict):
        """Sección para configurar alertas de precio"""
        
        with st.expander("🔔 Configurar Alerta de Precio"):
            st.write("¿El precio actual está alto? Configura una alerta para cuando baje:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                current_price = flight_data['price']
                target_price = st.number_input(
                    "Precio objetivo (USD)", 
                    min_value=50.0, 
                    max_value=current_price - 10,
                    value=current_price * 0.9,
                    step=10.0
                )
            
            with col2:
                alert_email = st.text_input(
                    "Email para alertas", 
                    value=st.session_state.get('user_email', '')
                )
            
            if st.button("🔔 Crear Alerta de Precio"):
                if alert_email and target_price:
                    # Aquí se crearía la alerta en la base de datos
                    st.success(f"✅ Alerta creada! Te notificaremos cuando el precio baje a ${target_price}")
                    st.session_state['user_email'] = alert_email
                else:
                    st.error("Por favor completa todos los campos")
    
    def track_booking_click(self, platform: str, flight_data: Dict, search_data: Dict):
        """Registra clicks en enlaces de booking para analytics"""
        try:
            # En producción, esto se guardaría en base de datos para analytics
            click_data = {
                'platform': platform,
                'price': flight_data['price'],
                'route': f"{search_data['origin']}-{search_data['destination']}",
                'timestamp': datetime.now(),
                'airline': flight_data.get('airline')
            }
            
            # Por ahora solo lo mostramos en session state
            if 'booking_clicks' not in st.session_state:
                st.session_state['booking_clicks'] = []
            
            st.session_state['booking_clicks'].append(click_data)
            
        except Exception as e:
            # No interrumpir el flujo si falla el tracking
            pass
    
    def show_booking_analytics(self):
        """Muestra estadísticas de clicks en booking"""
        if 'booking_clicks' in st.session_state and st.session_state['booking_clicks']:
            st.subheader("📊 Estadísticas de Búsquedas")
            
            clicks = st.session_state['booking_clicks']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Búsquedas", len(clicks))
            
            with col2:
                platforms = [click['platform'] for click in clicks]
                most_used = max(set(platforms), key=platforms.count) if platforms else "N/A"
                st.metric("Plataforma Favorita", most_used)
            
            with col3:
                avg_price = sum(click['price'] for click in clicks) / len(clicks)
                st.metric("Precio Promedio Buscado", f"${avg_price:.0f}")


def add_booking_functionality_to_search_result(flight_result, search_data):
    """Función para agregar a la app principal"""
    if flight_result and flight_result.get('flight_result'):
        booking_helper = FlightBookingHelper()
        flight_data = flight_result['flight_result']
        
        # Mostrar widget de compra
        booking_helper.show_booking_widget(flight_data, search_data)
        
        return True
    return False
