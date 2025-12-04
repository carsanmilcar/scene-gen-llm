# Imagen base ligera para QLC+
FROM debian:stable-slim

# TODO: Instalar QLC+ y habilitar el servidor web.

EXPOSE 9999

# Ejemplo de comando para iniciar QLC+ con web y abrir un proyecto.
CMD ["qlcplus", "-w", "--open", "/QLC/qlc.qxw"]
