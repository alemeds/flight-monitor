# ✈️ Monitor de Precios de Vuelos

Una aplicación web construida con Streamlit para monitorear precios de vuelos automáticamente y recibir notificaciones cuando encuentre ofertas.

## 🚀 Características

- **Monitoreo automático**: Chequeo constante de precios 24/7
- **Múltiples búsquedas**: Configura varios destinos simultáneamente
- **Notificaciones inteligentes**: Alertas por email cuando encuentra ofertas
- **Análisis visual**: Gráficos de tendencias y estadísticas de precios
- **Precio objetivo**: Define tu presupuesto y recibe alertas cuando se alcance
- **Historial completo**: Seguimiento de la evolución de precios
- **🛒 NUEVO: Enlaces de compra inteligentes** - Compra vuelos en 1 clic
- **APIs reales**: Integración con Amadeus y Skyscanner para datos precisos
- **Comparación automática**: Ve precios en múltiples plataformas

## 🎯 Demo en Vivo

[Ver Demo](https://tu-app-nombre.streamlit.app) *(disponible una vez deployado)*

## 📊 Capturas de Pantalla

### Panel Principal
![Dashboard](https://via.placeholder.com/800x400?text=Dashboard+Principal)

### Análisis de Precios
![Análisis](https://via.placeholder.com/800x400?text=Análisis+de+Precios)

## 🛠️ Tecnologías Utilizadas

- **Frontend**: Streamlit
- **Visualización**: Plotly
- **Base de datos**: SQLite
- **Notificaciones**: SMTP/Email
- **Análisis**: Pandas
- **APIs**: Amadeus, Skyscanner (configurable)

## 📋 Instalación Local

### Prerequisitos
- Python 3.8+
- pip

### Pasos

1. **Clona el repositorio**
```bash
git clone https://github.com/tu-usuario/flight-price-monitor.git
cd flight-price-monitor
```

2. **Crea un entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instala dependencias**
```bash
pip install -r requirements.txt
```

4. **Configura variables de entorno** (opcional)
```bash
cp .env.example .env
# Edita .env con tus credenciales
```

5. **Ejecuta la aplicación**
```bash
streamlit run flight_monitor.py
```

6. **Abre en tu navegador**
```
http://localhost:8501
```

## ☁️ Deploy en Streamlit Cloud

### Método Rápido

1. **Fork este repositorio** en tu GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu cuenta de GitHub
4. Selecciona el repositorio: `tu-usuario/flight-price-monitor`
5. Archivo principal: `flight_monitor.py`
6. ¡Deploy automático!

### Configuración de Secretos

En Streamlit Cloud, ve a **Settings > Secrets** y añade:

```toml
# API Keys
AMADEUS_API_KEY = "tu_api_key_aqui"
AMADEUS_API_SECRET = "tu_api_secret_aqui"
RAPIDAPI_KEY = "tu_rapidapi_key_aqui"

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "tu_email@gmail.com"
EMAIL_PASSWORD = "tu_password_de_app"

# Optional
DATABASE_URL = "sqlite:///flight_prices.db"
```

## 📧 Configuración de Notificaciones

### Gmail (Recomendado)

1. **Habilita verificación en 2 pasos** en tu cuenta Google
2. **Genera contraseña de aplicación**:
   - Ve a Configuración de cuenta → Seguridad
   - Contraseñas de aplicaciones → Selecciona app
   - Copia la contraseña generada
3. **Configura en la app**:
   - Servidor: `smtp.gmail.com`
   - Puerto: `587`
   - Usuario: tu email
   - Contraseña: la contraseña de aplicación

### Otros Proveedores

| Proveedor | Servidor SMTP | Puerto |
|-----------|---------------|--------|
| Outlook | smtp-mail.outlook.com | 587 |
| Yahoo | smtp.mail.yahoo.com | 587 |
| Hotmail | smtp.live.com | 587 |

## 🔗 Integración con APIs de Vuelos

### Opción 1: Amadeus API (Recomendada)

1. Regístrate en [Amadeus for Developers](https://developers.amadeus.com/)
2. Obtén tu API Key y Secret
3. Añade las credenciales en Secrets
4. ¡La app automáticamente usará datos reales!

### Opción 2: Skyscanner via RapidAPI

1. Regístrate en [RapidAPI](https://rapidapi.com/)
2. Suscríbete a Skyscanner API
3. Obtén tu RapidAPI Key
4. Configura en la aplicación

## 📱 Uso de la Aplicación

### 1. Crear Nueva Búsqueda
- Define origen y destino
- Selecciona fechas de viaje
- Establece precio objetivo
- Configura email para notificaciones

### 2. Monitoreo Automático
- La app busca precios automáticamente
- Recibe notificaciones cuando:
  - Se encuentra el precio más bajo
  - Se alcanza tu precio objetivo
  - Hay cambios significativos

### 3. Análisis de Tendencias
- Visualiza evolución de precios
- Identifica mejores momentos para comprar
- Compara entre diferentes fechas

### 4. Compra Inteligente 🆕
- **Enlaces automáticos** a Google Flights, Skyscanner, Kayak
- **Comparación instantánea** en múltiples plataformas
- **Alertas de precio objetivo** alcanzado
- **Consejos de compra** personalizados

## 🔧 Personalización

### Añadir Nuevos Proveedores de API

```python
def search_flights_custom_api(search_data):
    # Tu implementación aquí
    return {
        'price': price,
        'currency': 'USD',
        'airline': airline,
        'flight_details': details
    }
```

### Configurar Intervalos de Monitoreo

```python
# En la configuración de la app
check_intervals = {
    "30 minutos": 30,
    "1 hora": 60,
    "6 horas": 360
}
```

## 🤝 Contribuir

1. **Fork el proyecto**
2. **Crea una rama** (`git checkout -b feature/nueva-funcionalidad`)
3. **Commit tus cambios** (`git commit -am 'Añade nueva funcionalidad'`)
4. **Push a la rama** (`git push origin feature/nueva-funcionalidad`)
5. **Abre un Pull Request**

## 📈 Roadmap

- [ ] Integración con más APIs de vuelos
- [ ] Notificaciones por WhatsApp/Telegram
- [ ] Predicción de precios con ML
- [ ] App móvil companion
- [ ] Comparación multi-ciudad
- [ ] Alertas de ofertas flash

## 🐛 Reporte de Bugs

Encontraste un bug? [Abre un issue](https://github.com/tu-usuario/flight-price-monitor/issues) con:

- Descripción del problema
- Pasos para reproducir
- Comportamiento esperado vs actual
- Screenshots si aplica

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 👨‍💻 Autor

**Tu Nombre**
- GitHub: [@tu-usuario](https://github.com/tu-usuario)
- Email: tu-email@example.com

## 🙏 Agradecimientos

- [Streamlit](https://streamlit.io/) por la plataforma increíble
- [Plotly](https://plotly.com/) por las visualizaciones
- [Amadeus](https://developers.amadeus.com/) por la API de vuelos
- Comunidad open source por las librerías utilizadas

---

⭐ **¡Si te gusta este proyecto, dale una estrella!** ⭐
