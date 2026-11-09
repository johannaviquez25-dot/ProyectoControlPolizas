"""Capa de arranque: crea y configura la aplicación Flask."""

from flask import Flask

from controllers.polizas_controller import bp

# La app usa views/ para las plantillas HTML y public/static para el CSS.
app = Flask(
    __name__,
    template_folder="views",
    static_folder="public/static",
    static_url_path="/static",
)

# Registramos las rutas del controlador.
app.register_blueprint(bp)

if __name__ == "__main__":
    # Puerto 5001: en esta Mac el 5000 lo usa AirPlay y la app no puede arrancar.
    # Escucha solo en 127.0.0.1, así que la app queda disponible en:
    # http://127.0.0.1:5001
    app.run(debug=True, port=5001)
