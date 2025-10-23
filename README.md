Reloj Multizona (Streamlit + HTML/JS)

Reloj mundial minimalista con tarjetas por zona horaria.
Render inicial en Python (Streamlit) y actualización de segundos 100% en el navegador con JavaScript — sin recargar la página.

🏗️ Arquitectura

Modelo “SSR + Hydration ligera”:

Back (Python/Streamlit)

Sirve una única página con el layout (CSS) y un bloque HTML que incluye JavaScript.

Calcula el payload inicial (lista de zonas, rutas de GIF, etc.).

No hay BD ni API externa: todo es estático.

Front (HTML/CSS/JS dentro de Streamlit)

Se inserta con st.components.v1.html(...).

Usa Intl.DateTimeFormat del navegador para calcular hora/fecha por zona (setInterval(tick, 1000)).

Actualiza el DOM cada segundo; no hay st.rerun() ni render del lado servidor.
