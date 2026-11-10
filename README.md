# LAB5: proxy inverso y límite de solicitudes

Comparación local de la aplicación original con un escenario protegido por un nuevo contenedor Nginx. El código existente no cambia; la configuración del proxy está integrada en `docker-compose.proxy.yml`.

| Escenario | Recorrido de la API |
|---|---|
| Sin defensa | Navegador → localhost:5000 → Flask → PostgreSQL |
| Con defensa | Navegador → localhost:5000 → Nginx → Flask interno → PostgreSQL |

El frontend conserva su propio Nginx en `http://localhost:8080`. El proxy es un servicio adicional, no una modificación del frontend. En el escenario protegido, Flask y PostgreSQL no publican puertos al equipo.

## Requisitos

Docker Desktop iniciado con contenedores Linux, Docker Compose 2.23.1 o posterior, PowerShell y `curl.exe`. Ejecutar los comandos desde la raíz del repositorio. Los puertos 5000, 8080 y, para el escenario original, 5432 deben estar libres.

Usar un único escenario a la vez y el mismo nombre de proyecto (`lab5`) en todos los comandos. Si ya hay otra instancia del laboratorio ejecutándose, detenerla antes. El Compose original expone servicios sin esta defensa: realizar las pruebas únicamente en un equipo y red de laboratorio controlados.

## 1. Sin proxy: todas las solicitudes llegan a Flask

```powershell
docker compose -p lab5 -f docker-compose.yml up -d --build
```

Esperar a que Flask esté listo. Comprobarlo con:

```powershell
curl.exe -i --max-time 5 -H "Content-Type: application/json" --data-raw '{}' http://localhost:5000/login
```

Debe responder `400` con el mensaje `Faltan datos requeridos`. Este error es intencional: confirma que Flask recibió la petición sin necesitar usuarios ni modificar datos. Si la conexión falla, revisar los logs y repetir la comprobación antes de medir:

```powershell
docker compose -p lab5 -f docker-compose.yml logs --tail=30 backend
```

Ejecutar esta ráfaga local de **20 peticiones como máximo**, sin pausas entre peticiones:

```powershell
Start-Sleep -Seconds 4
$codigos = 1..20 | ForEach-Object {
    curl.exe -sS --max-time 5 -o NUL -w '%{http_code}' -H "Content-Type: application/json" --data-raw '{}' http://localhost:5000/login
}
$codigos
$codigos | Group-Object | Select-Object Name, Count
```

Resultado esperado: 20 respuestas `400`, ninguna `429`. Todas llegan a Flask. Un código `000` indica un fallo de conexión, no una defensa; revisar el arranque antes de continuar.

## 2. Con proxy: Nginx rechaza el exceso

Cambiar de escenario conservando los datos:

```powershell
docker compose -p lab5 -f docker-compose.yml down
docker compose -p lab5 -f docker-compose.proxy.yml up -d --build
docker compose -p lab5 -f docker-compose.proxy.yml exec proxy nginx -t
```

No usar `down -v`: eliminaría el volumen de datos. Apagar solo el proxy en el escenario protegido deja la API inaccesible; para probar sin defensa se debe volver al Compose original.

Repetir la comprobación aislada del apartado anterior hasta obtener el `400` JSON de Flask. Un `502` inicial puede indicar que el backend aún no está listo. Después, ejecutar **el mismo bloque de 20 peticiones**.

Resultado esperado: algunas respuestas `400` y otras `429 Too Many Requests`. El proxy permite una solicitud por segundo por IP, con una pequeña tolerancia inicial (`burst=2`); rechaza el exceso antes de llegar a Flask. La cantidad exacta depende de la velocidad de ejecución. Si no aparece ningún `429`, comprobar que se usa el escenario protegido y que las peticiones se ejecutan a más de una por segundo; no aumentar el total de peticiones.

Comprobar el recorrido:

```powershell
docker compose -p lab5 -f docker-compose.proxy.yml logs --tail=100 proxy backend
docker compose -p lab5 -f docker-compose.proxy.yml ps
```

En los logs del proxy:

- `status=400 upstream=400`: Nginx reenvió la petición y Flask respondió.
- `status=429 upstream=-`: Nginx bloqueó la petición sin enviarla a Flask.

El backend no debe registrar las peticiones rechazadas por Nginx. En `ps`, solo el proxy debe publicar el puerto 5000; el backend puede mostrar `5000/tcp`, pero no una asignación al host como `0.0.0.0:5000->5000/tcp`.

Tras esperar cuatro segundos, el formulario en `http://localhost:8080` debe seguir mostrando respuestas de la aplicación. El JavaScript existente sigue apuntando a `localhost:5000`, ahora atendido por el proxy.

## 3. Volver al escenario original

```powershell
docker compose -p lab5 -f docker-compose.proxy.yml down
docker compose -p lab5 -f docker-compose.yml up -d --build
```

Para dejar el laboratorio apagado, ejecutar `down` con el archivo del escenario activo, sin `-v`.

## Qué demuestra

La ráfaga simula un exceso básico de solicitudes de un único origen local. La defensa es la configuración de limitación de Nginx, no el simple hecho de añadir un proxy. No prueba protección completa frente a fuerza bruta o DDoS, ni corrige el almacenamiento de contraseñas en texto plano. Docker puede hacer que Nginx observe la IP del gateway en vez de la del cliente.

## Validación de archivos

```powershell
docker compose -p lab5 -f docker-compose.yml config --quiet
docker compose -p lab5 -f docker-compose.proxy.yml config --quiet
```

La validación de Compose no sustituye las pruebas con los contenedores encendidos. Ambos escenarios usan el volumen del mismo proyecto; no reutilizar el nombre de otro despliegue con datos ajenos al laboratorio.
