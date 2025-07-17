import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import { APP_CONFIG } from './config/appConfig'

// Actualizar el título del documento con el nombre de la aplicación
document.title = APP_CONFIG.app.name

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)