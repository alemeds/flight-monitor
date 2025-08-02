# 🚀 Guía de Inicio Rápido

## ⚡ Opción 1: Prueba Inmediata (Datos Simulados)

### 1. Descargar archivos
```bash
# Descarga estos archivos a una carpeta:
- flight_monitor.py
- flight_api_connector.py  
- booking_helper.py
- requirements.txt
```

### 2. Instalar y ejecutar
```bash
pip install streamlit pandas plotly requests
streamlit run flight_monitor.py
```

### 3. ¡Usar la app!
- Se abre en `http://localhost:8501`
- Funciona con datos simulados realistas
- Todas las funcionalidades disponibles

---

## 🌐 Opción 2: Deploy en Streamlit Cloud (Recomendado)

### 1. Subir a GitHub
```bash
git init
git add .
git commit -m "Flight Price Monitor App"
# Crear repo en GitHub y hacer push
```

### 2. Deploy en Streamlit Cloud
1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Conecta GitHub
3. Selecciona tu repo
4. Main file: `flight_monitor.py`
5. ¡Deploy!

### 3. Configurar notificaciones (Opcional)
En **App Settings → Secrets**:
```toml
EMAIL_USER = "tu_email@gmail.com"
EMAIL_PASSWORD = "tu_password_de_aplicacion"
```

---

## 💰 Opción 3: Datos Reales de Vuelos

### Para Amadeus API (2,000 consultas gratis/mes):

1. **Registro**: [developers.amadeus.com](https://developers.amadeus.com)
2. **Crear App**: Obtén API Key y Secret
3. **Configurar en Streamlit Secrets**:
```toml
AMADEUS_API_KEY = "tu_amadeus_key"
AMADEUS_API_SECRET = "tu_amadeus_secret"
```

### Para RapidAPI (100-500 consultas gratis/mes):

1. **Registro**: [rapidapi.com](https://rapidapi.com)
2. **Buscar**: "Skyscanner Flight Search"
3. **Suscribirse**: Plan gratuito
4. **Configurar**:
```toml
RAPIDAPI_KEY = "tu_rapidapi_key"
```

---

## 📋 Estructura de Archivos Final

```
flight-price-monitor/
├── flight_monitor.py          # App principal ⭐
├── flight_api_connector.py    # Conector APIs ⭐  
├── booking_helper.py          # Funcionalidad compra ⭐
├── requirements.txt           # Dependencias ⭐
├── README.md                 # Documentación
├── DEPLOYMENT.md             # Guía deployment
├── .env.example              # Variables ejemplo
├── .gitignore               # Git ignore
└── .streamlit/
    └── config.toml          # Configuración
```

**⭐ = Archivos esenciales**

---

## 🧪 Testing Rápido

Una vez ejecutando la app:

1. **Crear búsqueda**: BOG → MIA, próxima semana
2. **Buscar manualmente**: Botón "Buscar Ahora" 
3. **Ver gráficos**: Pestaña "Análisis"
4. **Probar APIs**: Pestaña "APIs" → "Test Rápido"
5. **🆕 Probar compra**: Cuando encuentres precio, clic "🚀 Buscar en Google Flights"

---

## 🔧 Troubleshooting

### App no carga
- Verificar que todos los archivos estén en la misma carpeta
- Instalar dependencias: `pip install -r requirements.txt`

### APIs no funcionan
- Verificar credentials en Secrets
- Usar pestaña "APIs" para diagnosticar
- La app funciona sin APIs (modo simulación)

### Notificaciones no llegan
- Verificar email en Secrets
- Usar "contraseña de aplicación" de Gmail, no la normal
- Habilitar 2FA primero

### Funcionalidad de compra no aparece
- Verificar que `booking_helper.py` esté en la carpeta
- Reiniciar la aplicación

---

## 💡 Tips de Uso

- **Precio objetivo**: Define tu presupuesto máximo
- **Múltiples búsquedas**: Monitorea varios destinos
- **Análisis**: Revisa tendencias antes de comprar
- **Notificaciones**: Configura email para alertas automáticas
- **🆕 Compra rápida**: 1 clic desde la app a Google Flights

---

## 🎯 URLs Importantes

- **Demo live**: `https://tu-app.streamlit.app`
- **Amadeus**: https://developers.amadeus.com
- **RapidAPI**: https://rapidapi.com
- **Streamlit Cloud**: https://share.streamlit.io

---

¡**En 5 minutos tienes tu monitor de vuelos funcionando con compra integrada!** ✈️💰
