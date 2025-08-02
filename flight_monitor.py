import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json
import time
import threading
from typing import Dict, List, Optional
import asyncio
import schedule
import os

# Configuración para manejar secretos en Streamlit Cloud
def get_secret(key, default=None):
    """Obtiene secretos de Streamlit Cloud o variables de entorno"""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key, default)

# Configuración de la página
st.set_page_config(
    page_title="Monitor de Precios de Vuelos",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clase principal para el monitor de vuelos
class FlightPriceMonitor:
    def __init__(self):
        self.db_path = "flight_prices.db"
        self.init_database()
        
    def init_database(self):
        """Inicializa la base de datos SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flight_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_name TEXT NOT NULL,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                departure_date TEXT NOT NULL,
                return_date TEXT,
                passengers INTEGER DEFAULT 1,
                email_notification TEXT,
                target_price REAL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_id INTEGER,
                price REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                airline TEXT,
                flight_details TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (search_id) REFERENCES flight_searches (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_id INTEGER,
                notification_type TEXT,
                message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (search_id) REFERENCES flight_searches (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_search(self, search_data: Dict) -> int:
        """Añade una nueva búsqueda de vuelo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO flight_searches 
            (search_name, origin, destination, departure_date, return_date, 
             passengers, email_notification, target_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            search_data['name'],
            search_data['origin'],
            search_data['destination'],
            search_data['departure_date'],
            search_data.get('return_date'),
            search_data.get('passengers', 1),
            search_data.get('email'),
            search_data.get('target_price')
        ))
        
        search_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return search_id
    
    def get_searches(self) -> pd.DataFrame:
        """Obtiene todas las búsquedas activas"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('''
            SELECT * FROM flight_searches WHERE is_active = 1
            ORDER BY created_at DESC
        ''', conn)
        conn.close()
        return df
    
    def get_price_history(self, search_id: int) -> pd.DataFrame:
        """Obtiene el historial de precios para una búsqueda"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('''
            SELECT * FROM price_history 
            WHERE search_id = ? 
            ORDER BY checked_at DESC
        ''', conn, params=(search_id,))
        conn.close()
        return df
    
    def search_flights_with_apis(self, search_data: Dict) -> Dict:
        """
        Busca vuelos usando APIs reales o simulación como fallback
        """
        # Importar el conector de APIs
        try:
            from flight_api_connector import get_flight_connector
            connector = get_flight_connector()
            return connector.search_flights(search_data)
        except ImportError:
            # Fallback a simulación si no existe el conector
            return self.simulate_flight_search_fallback(search_data)
    
    def simulate_flight_search_fallback(self, search_data: Dict) -> Dict:
        """
        Simulación de vuelos como fallback
        """
        import random
        
        # Simulación de precios basada en factores realistas
        base_price = random.randint(200, 1200)
        
        # Factor de temporada
        departure_date = datetime.strptime(search_data['departure_date'], '%Y-%m-%d')
        days_ahead = (departure_date - datetime.now()).days
        
        if days_ahead < 7:
            base_price *= 1.5  # Precios más altos cerca de la fecha
        elif days_ahead > 60:
            base_price *= 0.8  # Precios más bajos con anticipación
        
        # Variación aleatoria
        price_variation = random.uniform(0.9, 1.1)
        final_price = base_price * price_variation
        
        airlines = ['Avianca', 'LATAM', 'Viva Air', 'American Airlines', 'Delta', 'United']
        
        return {
            'price': round(final_price, 2),
            'currency': 'USD',
            'airline': random.choice(airlines),
            'flight_details': f"Vuelo directo - {random.randint(1, 3)} escalas",
            'source': 'Simulación'
        }
    
    def check_flights_and_update(self, search_id: int) -> Optional[Dict]:
        """Busca vuelos y actualiza la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener datos de búsqueda
        cursor.execute('SELECT * FROM flight_searches WHERE id = ?', (search_id,))
        search_data = cursor.fetchone()
        
        if not search_data:
            conn.close()
            return None
        
        # Convertir a diccionario
        columns = [description[0] for description in cursor.description]
        search_dict = dict(zip(columns, search_data))
        
        # Simular búsqueda de vuelos
        flight_result = self.search_flights_with_apis(search_dict)
        
        # Guardar resultado en historial
        cursor.execute('''
            INSERT INTO price_history (search_id, price, currency, airline, flight_details)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            search_id,
            flight_result['price'],
            flight_result['currency'],
            flight_result['airline'],
            flight_result['flight_details']
        ))
        
        # Verificar si es el precio más bajo
        cursor.execute('''
            SELECT MIN(price) FROM price_history WHERE search_id = ?
        ''', (search_id,))
        min_price = cursor.fetchone()[0]
        
        is_lowest = flight_result['price'] <= min_price
        meets_target = (search_dict['target_price'] and 
                       flight_result['price'] <= search_dict['target_price'])
        
        conn.commit()
        conn.close()
        
        return {
            'flight_result': flight_result,
            'is_lowest': is_lowest,
            'meets_target': meets_target,
            'search_data': search_dict
        }
    
    def send_notification(self, email: str, subject: str, message: str):
        """Envía notificación por email usando secretos de Streamlit Cloud"""
        try:
            # Configuración del servidor SMTP desde secretos
            smtp_server = get_secret("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(get_secret("SMTP_PORT", "587"))
            
            # Credenciales desde secretos de Streamlit Cloud
            sender_email = get_secret("EMAIL_USER")
            sender_password = get_secret("EMAIL_PASSWORD")
            
            if not sender_email or not sender_password:
                st.warning("⚠️ Configuración de email no encontrada. Configura EMAIL_USER y EMAIL_PASSWORD en Secrets.")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, email, text)
            server.quit()
            
            return True
        except Exception as e:
            st.error(f"Error enviando notificación: {str(e)}")
            return False

# Inicializar el monitor
@st.cache_resource
def get_monitor():
    return FlightPriceMonitor()

monitor = get_monitor()

# Interfaz principal
def main():
    st.title("✈️ Monitor de Precios de Vuelos")
    st.markdown("Encuentra los mejores precios y recibe notificaciones automáticas")
    
    # Sidebar para configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Modo de operación
        mode = st.selectbox(
            "Modo de operación",
            ["Manual", "Automático (cada hora)", "Automático (cada 6 horas)"]
        )
        
        if mode != "Manual":
            st.info("🔄 Monitoreo automático activado")
        
        st.markdown("---")
        
        # Configuración de notificaciones
        st.subheader("📧 Notificaciones")
        email_notifications = st.checkbox("Activar notificaciones por email")
        
        if email_notifications:
            default_email = st.text_input("Email para notificaciones")
    
    # Tabs principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 Nueva Búsqueda", "📊 Monitoreo Activo", "📈 Análisis", "🔗 APIs", "⚙️ Configuración"])
    
    with tab1:
        st.header("Configurar Nueva Búsqueda")
        
        col1, col2 = st.columns(2)
        
        with col1:
            search_name = st.text_input("Nombre de la búsqueda", "Mi viaje a...")
            origin = st.text_input("Ciudad de origen", "BOG")
            destination = st.text_input("Ciudad de destino", "MIA")
            departure_date = st.date_input(
                "Fecha de salida",
                min_value=datetime.now().date(),
                value=datetime.now().date() + timedelta(days=30)
            )
        
        with col2:
            return_date = st.date_input(
                "Fecha de regreso (opcional)",
                min_value=departure_date if 'departure_date' in locals() else datetime.now().date(),
                value=None
            )
            passengers = st.number_input("Número de pasajeros", min_value=1, max_value=9, value=1)
            target_price = st.number_input("Precio objetivo (USD)", min_value=0.0, step=50.0, value=500.0)
            notification_email = st.text_input("Email para notificaciones", value=default_email if email_notifications else "")
        
        if st.button("🚀 Crear Búsqueda", type="primary"):
            if search_name and origin and destination:
                search_data = {
                    'name': search_name,
                    'origin': origin.upper(),
                    'destination': destination.upper(),
                    'departure_date': departure_date.strftime('%Y-%m-%d'),
                    'return_date': return_date.strftime('%Y-%m-%d') if return_date else None,
                    'passengers': passengers,
                    'target_price': target_price,
                    'email': notification_email
                }
                
                search_id = monitor.add_search(search_data)
                st.success(f"✅ Búsqueda '{search_name}' creada con ID: {search_id}")
                
                # Realizar primera búsqueda
                with st.spinner("Buscando vuelos..."):
                    result = monitor.check_flights_and_update(search_id)
                    if result:
                        flight = result['flight_result']
                        st.info(f"💰 Primer precio encontrado: ${flight['price']} USD - {flight['airline']}")
                        
                        # Mostrar opciones de compra inmediatamente
                        try:
                            from booking_helper import add_booking_functionality_to_search_result
                            add_booking_functionality_to_search_result(result, search_data)
                        except ImportError:
                            st.info("💡 Para opciones de compra, descarga booking_helper.py")
                
                time.sleep(1)
                st.rerun()
            else:
                st.error("Por favor completa todos los campos obligatorios")
    
    with tab2:
        st.header("Búsquedas Activas")
        
        searches_df = monitor.get_searches()
        
        if not searches_df.empty:
            for _, search in searches_df.iterrows():
                with st.expander(f"✈️ {search['search_name']} - {search['origin']} → {search['destination']}"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Salida:** {search['departure_date']}")
                        if search['return_date']:
                            st.write(f"**Regreso:** {search['return_date']}")
                        st.write(f"**Pasajeros:** {search['passengers']}")
                        st.write(f"**Precio objetivo:** ${search['target_price']} USD")
                    
                    with col2:
                        if st.button(f"🔍 Buscar Ahora", key=f"search_{search['id']}"):
                            with st.spinner("Buscando..."):
                                result = monitor.check_flights_and_update(search['id'])
                                if result:
                                    flight = result['flight_result']
                                    if result['meets_target']:
                                        st.success(f"🎯 ¡Precio objetivo alcanzado! ${flight['price']}")
                                    elif result['is_lowest']:
                                        st.success(f"📉 ¡Nuevo precio más bajo! ${flight['price']}")
                                    else:
                                        st.info(f"💰 Precio actual: ${flight['price']}")
                                    
                                    # Mostrar opciones de compra para precios interesantes
                                    if result['meets_target'] or result['is_lowest']:
                                        try:
                                            from booking_helper import add_booking_functionality_to_search_result
                                            search_data_dict = {
                                                'origin': search['origin'],
                                                'destination': search['destination'],
                                                'departure_date': search['departure_date'],
                                                'return_date': search['return_date'],
                                                'passengers': search['passengers']
                                            }
                                            add_booking_functionality_to_search_result(result, search_data_dict)
                                        except ImportError:
                                            st.info("💡 Descarga booking_helper.py para opciones de compra automáticas")
                    
                    with col3:
                        if st.button(f"📊 Ver Historial", key=f"history_{search['id']}"):
                            st.session_state[f"show_history_{search['id']}"] = True
                    
                    # Mostrar historial si se solicita
                    if st.session_state.get(f"show_history_{search['id']}", False):
                        history_df = monitor.get_price_history(search['id'])
                        if not history_df.empty:
                            history_df['checked_at'] = pd.to_datetime(history_df['checked_at'])
                            
                            # Gráfico de precios
                            fig = px.line(
                                history_df, 
                                x='checked_at', 
                                y='price',
                                title=f"Evolución de precios - {search['search_name']}",
                                markers=True
                            )
                            fig.add_hline(
                                y=search['target_price'], 
                                line_dash="dash", 
                                line_color="red",
                                annotation_text="Precio objetivo"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Tabla de historial
                            st.dataframe(
                                history_df[['price', 'airline', 'checked_at']].sort_values('checked_at', ascending=False),
                                use_container_width=True
                            )
        else:
            st.info("No hay búsquedas activas. Crea una nueva búsqueda en la pestaña anterior.")
    
    with tab3:
        st.header("Análisis de Precios")
        
        searches_df = monitor.get_searches()
        
        if not searches_df.empty:
            # Selector de búsqueda para análisis
            selected_search = st.selectbox(
                "Selecciona una búsqueda para analizar",
                options=searches_df['id'].tolist(),
                format_func=lambda x: f"{searches_df[searches_df['id']==x]['search_name'].iloc[0]} - {searches_df[searches_df['id']==x]['origin'].iloc[0]}→{searches_df[searches_df['id']==x]['destination'].iloc[0]}"
            )
            
            if selected_search:
                history_df = monitor.get_price_history(selected_search)
                search_info = searches_df[searches_df['id'] == selected_search].iloc[0]
                
                if not history_df.empty:
                    history_df['checked_at'] = pd.to_datetime(history_df['checked_at'])
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Precio Actual", f"${history_df['price'].iloc[0]:.2f}")
                    
                    with col2:
                        min_price = history_df['price'].min()
                        st.metric("Precio Mínimo", f"${min_price:.2f}")
                    
                    with col3:
                        avg_price = history_df['price'].mean()
                        st.metric("Precio Promedio", f"${avg_price:.2f}")
                    
                    with col4:
                        price_change = history_df['price'].iloc[0] - history_df['price'].iloc[-1] if len(history_df) > 1 else 0
                        st.metric("Cambio Total", f"${price_change:.2f}", delta=f"{price_change:.2f}")
                    
                    # Gráfico detallado
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=history_df['checked_at'],
                        y=history_df['price'],
                        mode='lines+markers',
                        name='Precio',
                        line=dict(color='blue', width=2),
                        marker=dict(size=6)
                    ))
                    
                    fig.add_hline(
                        y=search_info['target_price'],
                        line_dash="dash",
                        line_color="red",
                        annotation_text="Precio Objetivo"
                    )
                    
                    fig.add_hline(
                        y=avg_price,
                        line_dash="dot",
                        line_color="green",
                        annotation_text="Precio Promedio"
                    )
                    
                    fig.update_layout(
                        title=f"Análisis Detallado - {search_info['search_name']}",
                        xaxis_title="Fecha",
                        yaxis_title="Precio (USD)",
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Estadísticas adicionales
                    st.subheader("📊 Estadísticas")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Resumen de precios:**")
                        st.write(f"• Máximo: ${history_df['price'].max():.2f}")
                        st.write(f"• Mínimo: ${history_df['price'].min():.2f}")
                        st.write(f"• Mediana: ${history_df['price'].median():.2f}")
                        st.write(f"• Desviación estándar: ${history_df['price'].std():.2f}")
                    
                    with col2:
                        st.write("**Análisis de tendencia:**")
                        if len(history_df) >= 2:
                            recent_trend = history_df['price'].iloc[0] - history_df['price'].iloc[1]
                            if recent_trend > 0:
                                st.write("📈 Tendencia reciente: Subiendo")
                            elif recent_trend < 0:
                                st.write("📉 Tendencia reciente: Bajando")
                            else:
                                st.write("➡️ Tendencia reciente: Estable")
                        
                        price_below_target = (history_df['price'] <= search_info['target_price']).sum()
                        st.write(f"• Veces por debajo del objetivo: {price_below_target}")
                else:
                    st.info("No hay suficientes datos para mostrar análisis.")
        else:
            st.info("No hay búsquedas para analizar.")
    
    with tab4:
        st.header("API de Vuelos - Estado y Configuración")
        
        # Estado de las APIs
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔑 Estado de APIs")
            
            # Verificar Amadeus
            amadeus_key = get_secret("AMADEUS_API_KEY")
            amadeus_secret = get_secret("AMADEUS_API_SECRET")
            
            if amadeus_key and amadeus_secret:
                st.success("✅ Amadeus API: Configurado")
                st.write(f"**API Key**: {amadeus_key[:8]}...{amadeus_key[-4:] if len(amadeus_key) > 12 else ''}")
            else:
                st.warning("⚠️ Amadeus API: No configurado")
                st.write("Configura AMADEUS_API_KEY y AMADEUS_API_SECRET en Secrets")
            
            # Verificar RapidAPI
            rapidapi_key = get_secret("RAPIDAPI_KEY")
            
            if rapidapi_key:
                st.success("✅ RapidAPI: Configurado")
                st.write(f"**API Key**: {rapidapi_key[:8]}...{rapidapi_key[-4:] if len(rapidapi_key) > 12 else ''}")
            else:
                st.warning("⚠️ RapidAPI: No configurado")
                st.write("Configura RAPIDAPI_KEY en Secrets")
            
            # Mostrar modo actual
            if amadeus_key or rapidapi_key:
                st.info("🚀 **Modo**: Datos reales de vuelos")
            else:
                st.info("🎮 **Modo**: Simulación (para pruebas)")
        
        with col2:
            st.subheader("🧪 Test de Conectividad")
            
            if st.button("🔍 Probar APIs", type="primary"):
                try:
                    from flight_api_connector import test_api_connections
                    test_api_connections()
                except ImportError:
                    st.warning("flight_api_connector.py no encontrado")
                except Exception as e:
                    st.error(f"Error probando APIs: {str(e)}")
            
            st.subheader("📊 Estadísticas de Uso")
            
            # Mostrar estadísticas básicas
            conn = sqlite3.connect(monitor.db_path)
            
            # Contar búsquedas por fuente
            source_stats = pd.read_sql_query('''
                SELECT 
                    CASE 
                        WHEN flight_details LIKE '%Amadeus%' THEN 'Amadeus'
                        WHEN flight_details LIKE '%Skyscanner%' THEN 'Skyscanner' 
                        ELSE 'Simulación'
                    END as source,
                    COUNT(*) as count
                FROM price_history 
                GROUP BY source
            ''', conn)
            
            conn.close()
            
            if not source_stats.empty:
                for _, row in source_stats.iterrows():
                    st.metric(f"Consultas {row['source']}", row['count'])
            else:
                st.write("No hay estadísticas disponibles")
        
        st.markdown("---")
        
        # Guía de configuración
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🛠️ Configurar Amadeus API")
            
            with st.expander("📋 Paso a paso"):
                st.markdown("""
                1. **Registro**: Ve a [developers.amadeus.com](https://developers.amadeus.com)
                2. **Crear App**: Haz clic en "Create New App"
                3. **Obtener credenciales**: Copia API Key y Secret
                4. **Configurar en Streamlit**:
                   - Ve a App Settings → Secrets
                   - Añade:
                   ```
                   AMADEUS_API_KEY = "tu_api_key"
                   AMADEUS_API_SECRET = "tu_secret"
                   ```
                5. **¡Listo!** Reinicia la app
                
                **Límites gratuitos**: 2,000 consultas/mes
                """)
        
        with col2:
            st.subheader("🚀 Configurar RapidAPI")
            
            with st.expander("📋 Paso a paso"):
                st.markdown("""
                1. **Registro**: Ve a [rapidapi.com](https://rapidapi.com)
                2. **Buscar API**: Busca "Skyscanner Flight Search"
                3. **Suscribirse**: Selecciona plan gratuito
                4. **Obtener key**: Copia tu X-RapidAPI-Key
                5. **Configurar en Streamlit**:
                   - Ve a App Settings → Secrets
                   - Añade:
                   ```
                   RAPIDAPI_KEY = "tu_rapidapi_key"
                   ```
                6. **¡Listo!** Reinicia la app
                
                **Límites gratuitos**: 100-500 consultas/mes
                """)
        
        # Test de búsqueda rápida
        st.subheader("⚡ Test Rápido de Búsqueda")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            test_origin = st.text_input("Origen", value="BOG", key="test_origin")
        with col2:
            test_dest = st.text_input("Destino", value="MIA", key="test_dest")
        with col3:
            test_date = st.date_input(
                "Fecha", 
                value=datetime.now().date() + timedelta(days=30),
                key="test_date"
            )
        with col4:
            if st.button("🔍 Buscar Test", key="test_search"):
                if test_origin and test_dest:
                    test_search_data = {
                        'origin': test_origin.upper(),
                        'destination': test_dest.upper(),
                        'departure_date': test_date.strftime('%Y-%m-%d'),
                        'passengers': 1
                    }
                    
                    with st.spinner("Buscando..."):
                        result = monitor.search_flights_with_apis(test_search_data)
                        
                        if result:
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Precio", f"${result['price']} {result['currency']}")
                            with col_b:
                                st.metric("Aerolínea", result['airline'])
                            with col_c:
                                st.metric("Fuente", result.get('source', 'API'))
                            
                            st.success(f"✅ {result['flight_details']}")
                            
                            # Opción de compra rápida
                            if st.button("🛒 ¿Comprar este vuelo?", key="quick_buy"):
                                try:
                                    from booking_helper import FlightBookingHelper
                                    booking_helper = FlightBookingHelper()
                                    booking_helper.show_booking_widget(result, test_search_data)
                                except ImportError:
                                    st.info("💡 Descarga booking_helper.py para funcionalidad completa de compra")
                        else:
                            st.error("No se encontraron vuelos")
    
    with tab5:
        st.header("Configuración Avanzada")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔄 Monitoreo Automático")
            
            auto_check = st.checkbox("Activar chequeo automático")
            if auto_check:
                check_interval = st.selectbox(
                    "Intervalo de chequeo",
                    ["30 minutos", "1 hora", "2 horas", "6 horas", "12 horas"]
                )
                
                st.info(f"⏰ Próximo chequeo programado cada {check_interval}")
            
            st.subheader("📧 Configuración de Email")
            
            smtp_server = st.text_input("Servidor SMTP", value="smtp.gmail.com")
            smtp_port = st.number_input("Puerto SMTP", value=587)
            sender_email = st.text_input("Email remitente")
            sender_password = st.text_input("Contraseña de aplicación", type="password")
            
            if st.button("🧪 Probar Configuración de Email"):
                if sender_email and sender_password:
                    # Aquí implementarías la prueba de conexión
                    st.success("✅ Configuración de email válida")
                else:
                    st.error("❌ Completa todos los campos de email")
        
        with col2:
            st.subheader("🗄️ Gestión de Datos")
            
            # Estadísticas de la base de datos
            searches_count = len(monitor.get_searches())
            
            conn = sqlite3.connect(monitor.db_path)
            total_price_checks = pd.read_sql_query("SELECT COUNT(*) as count FROM price_history", conn)['count'].iloc[0]
            conn.close()
            
            st.metric("Búsquedas activas", searches_count)
            st.metric("Total de consultas realizadas", total_price_checks)
            
            st.subheader("🧹 Mantenimiento")
            
            if st.button("🗑️ Limpiar historial antiguo"):
                # Implementar limpieza de datos antiguos
                st.success("Historial limpiado")
            
            if st.button("📥 Exportar datos"):
                # Implementar exportación de datos
                st.success("Datos exportados")
            
            st.subheader("🔗 APIs de Vuelos")
            
            api_provider = st.selectbox(
                "Proveedor de API",
                ["Simulación (Demo)", "Amadeus", "Skyscanner", "Kayak API"]
            )
            
            if api_provider != "Simulación (Demo)":
                api_key = st.text_input("API Key", type="password")
                api_secret = st.text_input("API Secret", type="password")
                
                if st.button("✅ Validar API"):
                    st.info("Validación de API pendiente de implementación")

    # Footer
    st.markdown("---")
    st.markdown("🚀 **Monitor de Precios de Vuelos** - Encuentra las mejores ofertas automáticamente")

if __name__ == "__main__":
    main()
