"""
AIR-GUARD
=========
Premium Environmental Intelligence Platform

Backend:
- Flask
- Open-Meteo Geocoding API
- Open-Meteo Air Quality API
- Open-Meteo Weather API

Features:
- City/location search
- Air quality intelligence
- Weather intelligence
- AQI analysis
- Pollutant information
- Health/environment guidance
- Built-in SVG logo
- Security headers
- Health endpoint
- API error handling
- Production-friendly structure

Run:
    python app.py

Then open:
    http://127.0.0.1:5000
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import wraps
from typing import Any

import requests
from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
)

# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

APP_NAME = "AIR-GUARD"
APP_VERSION = "1.0.0"

OPEN_METEO_GEOCODING = (
    "https://geocoding-api.open-meteo.com/v1/search"
)

OPEN_METEO_REVERSE_GEOCODING = (
    "https://geocoding-api.open-meteo.com/v1/reverse"
)

OPEN_METEO_AIR = (
    "https://air-quality-api.open-meteo.com/v1/air-quality"
)

OPEN_METEO_WEATHER = (
    "https://api.open-meteo.com/v1/forecast"
)

REQUEST_TIMEOUT = 15


app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)

app.config.update(
    JSON_SORT_KEYS=False,
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
)


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()

session.headers.update(
    {
        "User-Agent": (
            "AIR-GUARD/1.0 "
            "(Environmental Intelligence Platform)"
        )
    }
)


# ============================================================
# LOGO
# ============================================================

LOGO_SVG = r'''<svg
xmlns="http://www.w3.org/2000/svg"
viewBox="0 0 760 180"
role="img"
aria-labelledby="title desc"
>

<title id="title">AIR-GUARD Logo</title>

<desc id="desc">
AIR-GUARD environmental intelligence logo.
</desc>

<defs>

    <linearGradient
        id="guardGradient"
        x1="0"
        y1="0"
        x2="1"
        y2="1"
    >
        <stop offset="0%" stop-color="#55DDFF"/>
        <stop offset="55%" stop-color="#28A9FF"/>
        <stop offset="100%" stop-color="#1767D9"/>
    </linearGradient>

    <linearGradient
        id="textGradient"
        x1="0"
        y1="0"
        x2="1"
        y2="0"
    >
        <stop offset="0%" stop-color="#EFFFFF"/>
        <stop offset="100%" stop-color="#75DFFF"/>
    </linearGradient>

    <filter
        id="glow"
        x="-50%"
        y="-50%"
        width="200%"
        height="200%"
    >

        <feGaussianBlur
            stdDeviation="5"
            result="blur"
        />

        <feMerge>

            <feMergeNode in="blur"/>

            <feMergeNode in="SourceGraphic"/>

        </feMerge>

    </filter>

</defs>


<!-- Shield -->

<path
    d="
    M88 12
    L151 34
    V82
    C151 121 126 145 88 160
    C50 145 25 121 25 82
    V34
    Z
    "
    fill="rgba(40,169,255,.08)"
    stroke="url(#guardGradient)"
    stroke-width="7"
    filter="url(#glow)"
/>


<!-- Air waves -->

<path
    d="M50 72
       C62 60 76 60 88 72
       C100 84 114 84 126 72"
    fill="none"
    stroke="#55DDFF"
    stroke-width="7"
    stroke-linecap="round"
/>

<path
    d="M47 91
       C60 79 75 79 88 91
       C101 103 116 103 129 91"
    fill="none"
    stroke="#28A9FF"
    stroke-width="7"
    stroke-linecap="round"
/>


<!-- Check -->

<path
    d="M64 112 L82 128 L113 96"
    fill="none"
    stroke="#48E3A5"
    stroke-width="8"
    stroke-linecap="round"
    stroke-linejoin="round"
/>


<!-- Brand -->

<text
    x="190"
    y="92"
    fill="url(#textGradient)"
    font-family="Inter,Arial,sans-serif"
    font-size="67"
    font-weight="800"
    letter-spacing="3"
>
AIR
</text>

<text
    x="330"
    y="92"
    fill="#55DDFF"
    font-family="Inter,Arial,sans-serif"
    font-size="67"
    font-weight="800"
    letter-spacing="3"
>
-GUARD
</text>


<!-- Tagline -->

<text
    x="193"
    y="125"
    fill="#8CA8BB"
    font-family="Inter,Arial,sans-serif"
    font-size="15"
    font-weight="600"
    letter-spacing="4"
>
ENVIRONMENTAL INTELLIGENCE
</text>

</svg>'''


# ============================================================
# SECURITY HEADERS
# ============================================================

@app.after_request
def security_headers(response: Response) -> Response:
    """
    Add security and caching headers to every response.
    """

    response.headers["X-Content-Type-Options"] = "nosniff"

    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    response.headers[
        "Referrer-Policy"
    ] = "strict-origin-when-cross-origin"

    response.headers[
        "Permissions-Policy"
    ] = (
        "geolocation=(self), "
        "microphone=(), "
        "camera=()"
    )

    response.headers[
        "Content-Security-Policy"
    ] = (
        "default-src 'self'; "
        "img-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "connect-src 'self' https://*.open-meteo.com; "
        "frame-ancestors 'self';"
    )

    return response


# ============================================================
# REQUEST HELPERS
# ============================================================

def safe_float(
    value: Any,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    """
    Safely convert input into float and optionally validate range.
    """

    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError("Invalid numeric value.")

    if minimum is not None and number < minimum:
        raise ValueError("Numeric value is below allowed range.")

    if maximum is not None and number > maximum:
        raise ValueError("Numeric value is above allowed range.")

    return number


def external_get(
    url: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """
    Safely call an external API.
    """

    try:

        response = session.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    except requests.Timeout as exc:

        raise RuntimeError(
            "Environmental data service timed out."
        ) from exc

    except requests.RequestException as exc:

        raise RuntimeError(
            "Environmental data service is unavailable."
        ) from exc

    except ValueError as exc:

        raise RuntimeError(
            "Environmental data service returned invalid data."
        ) from exc


def api_error(message: str, status: int = 400):
    """
    Standard API error response.
    """

    return jsonify(
        {
            "success": False,
            "error": message,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }
    ), status


# ============================================================
# AQI INTELLIGENCE
# ============================================================

def calculate_aqi_profile(aqi: float) -> dict[str, Any]:
    """
    Convert US AQI into an AIR-GUARD risk profile.
    """

    aqi = max(0, float(aqi))

    if aqi <= 50:

        return {
            "level": "Good",
            "title": "Air looks good",
            "color": "#48E3A5",
            "score": aqi,
            "risk": "Low",
            "message": (
                "Air pollution is low. "
                "Outdoor activity is generally comfortable "
                "for most people."
            ),
            "outdoor_activity": (
                "Normal outdoor activity is generally reasonable."
            ),
        }

    if aqi <= 100:

        return {
            "level": "Moderate",
            "title": "Air is acceptable",
            "color": "#FFD166",
            "score": aqi,
            "risk": "Moderate",
            "message": (
                "Air quality is acceptable, although sensitive "
                "people may notice some effects."
            ),
            "outdoor_activity": (
                "Sensitive people may prefer lighter outdoor activity."
            ),
        }

    if aqi <= 150:

        return {
            "level": "Unhealthy for Sensitive Groups",
            "title": "Take some care",
            "color": "#FF9F43",
            "score": aqi,
            "risk": "Elevated",
            "message": (
                "Sensitive groups may experience health effects. "
                "Reduce prolonged or heavy outdoor exertion."
            ),
            "outdoor_activity": (
                "Sensitive groups should reduce prolonged outdoor exertion."
            ),
        }

    if aqi <= 200:

        return {
            "level": "Unhealthy",
            "title": "Reduce exposure",
            "color": "#FF6F61",
            "score": aqi,
            "risk": "High",
            "message": (
                "Health effects are possible for everyone. "
                "Consider reducing prolonged outdoor exposure."
            ),
            "outdoor_activity": (
                "Reduce prolonged or strenuous outdoor activity."
            ),
        }

    if aqi <= 300:

        return {
            "level": "Very Unhealthy",
            "title": "Protect yourself",
            "color": "#C77DFF",
            "score": aqi,
            "risk": "Very High",
            "message": (
                "Health alert conditions are possible. "
                "Limit outdoor exposure and follow local guidance."
            ),
            "outdoor_activity": (
                "Avoid prolonged outdoor activity where possible."
            ),
        }

    return {
        "level": "Hazardous",
        "title": "Stay protected",
        "color": "#FF5C72",
        "score": aqi,
        "risk": "Critical",
        "message": (
            "Health risks are elevated. Avoid prolonged outdoor "
            "exposure and follow local public-health guidance."
        ),
        "outdoor_activity": (
            "Avoid prolonged outdoor exposure."
        ),
    }


# ============================================================
# POLLUTANT INTELLIGENCE
# ============================================================

POLLUTANT_LIMITS = {
    "pm2_5": (12, 35, 55),
    "pm10": (54, 154, 254),
    "nitrogen_dioxide": (100, 200, 400),
    "ozone": (100, 160, 240),
    "carbon_monoxide": (4000, 10000, 30000),
    "sulphur_dioxide": (40, 100, 200),
}


def pollutant_level(
    pollutant: str,
    value: float,
) -> str:
    """
    Return a simple pollutant risk label.
    """

    thresholds = POLLUTANT_LIMITS.get(
        pollutant,
        (50, 150, 300),
    )

    if value <= thresholds[0]:
        return "Low"

    if value <= thresholds[1]:
        return "Moderate"

    if value <= thresholds[2]:
        return "High"

    return "Very High"


# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def home():
    """
    Main AIR-GUARD application.
    """

    return render_template(
        "index.html",
        app_name=APP_NAME,
        app_version=APP_VERSION,
    )


@app.get("/logo.svg")
def logo():
    """
    Official AIR-GUARD vector logo.
    """

    return Response(
        LOGO_SVG,
        mimetype="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=86400"
        },
    )


@app.get("/health")
def health():
    """
    Application health check.
    """

    return jsonify(
        {
            "success": True,
            "application": APP_NAME,
            "version": APP_VERSION,
            "status": "operational",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }
    )


@app.get("/api/search")
def search():

    query = (
        request.args
        .get("q", "")
        .strip()
    )

    if len(query) < 2:
        return api_error(
            "Search query must contain at least 2 characters."
        )

    if len(query) > 100:
        return api_error(
            "Search query is too long."
        )

    try:

        data = external_get(
            OPEN_METEO_GEOCODING,
            {
                "name": query,
                "count": 8,
                "language": "en",
                "format": "json",
            },
        )

        return jsonify(
            {
                "success": True,
                "results": data.get(
                    "results",
                    [],
                ),
            }
        )

    except RuntimeError as exc:

        return api_error(
            str(exc),
            502,
        )


@app.get("/api/reverse")
def reverse_location():

    try:

        latitude = safe_float(
            request.args.get("latitude"),
            -90,
            90,
        )

        longitude = safe_float(
            request.args.get("longitude"),
            -180,
            180,
        )

    except ValueError as exc:

        return api_error(
            str(exc)
        )

    try:

        data = external_get(
            OPEN_METEO_REVERSE_GEOCODING,
            {
                "latitude": latitude,
                "longitude": longitude,
                "language": "en",
                "format": "json",
            },
        )

        return jsonify(
            {
                "success": True,
                "results": data.get(
                    "results",
                    [],
                ),
            }
        )

    except RuntimeError as exc:

        return api_error(
            str(exc),
            502,
        )


@app.get("/api/environment")
def environment():

    try:

        latitude = safe_float(
            request.args.get("latitude"),
            -90,
            90,
        )

        longitude = safe_float(
            request.args.get("longitude"),
            -180,
            180,
        )

    except ValueError as exc:

        return api_error(
            str(exc)
        )


    try:

        air = external_get(
            OPEN_METEO_AIR,
            {
                "latitude": latitude,
                "longitude": longitude,

                "current": (
                    "us_aqi,"
                    "pm2_5,"
                    "pm10,"
                    "carbon_monoxide,"
                    "nitrogen_dioxide,"
                    "sulphur_dioxide,"
                    "ozone"
                ),

                "hourly": (
                    "us_aqi,"
                    "pm2_5,"
                    "pm10"
                ),

                "forecast_hours": 24,
                "timezone": "auto",
            },
        )


        weather = external_get(
            OPEN_METEO_WEATHER,
            {
                "latitude": latitude,
                "longitude": longitude,

                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "wind_speed_10m,"
                    "weather_code"
                ),

                "hourly": (
                    "temperature_2m,"
                    "uv_index"
                ),

                "forecast_hours": 24,
                "timezone": "auto",
            },
        )


        current_air = air.get(
            "current",
            {},
        )


        raw_aqi = current_air.get(
            "us_aqi",
            0,
        )


        try:

            aqi = float(raw_aqi or 0)

        except (TypeError, ValueError):

            aqi = 0


        profile = calculate_aqi_profile(
            aqi
        )


        pollutants = {}


        pollutant_names = [
            "pm2_5",
            "pm10",
            "nitrogen_dioxide",
            "ozone",
            "carbon_monoxide",
            "sulphur_dioxide",
        ]


        for pollutant in pollutant_names:

            raw_value = current_air.get(
                pollutant
            )

            try:

                value = float(
                    raw_value
                    if raw_value is not None
                    else 0
                )

            except (TypeError, ValueError):

                value = 0


            pollutants[pollutant] = {
                "value": value,
                "level": pollutant_level(
                    pollutant,
                    value,
                ),
            }


        return jsonify(
            {
                "success": True,

                "application": APP_NAME,

                "version": APP_VERSION,

                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                },

                "aqi": {
                    "value": round(aqi),
                    "profile": profile,
                },

                "pollutants": pollutants,

                "air": air,

                "weather": weather,

                "updated_at": datetime.now(
                    timezone.utc
                ).isoformat(),

                "source": {
                    "provider": "Open-Meteo",
                    "type": "modeled environmental data",
                },
            }
        )


    except RuntimeError as exc:

        return api_error(
            str(exc),
            502,
        )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):

    if request.path.startswith("/api/"):

        return api_error(
            "API endpoint not found.",
            404,
        )

    return (
        render_template(
            "index.html",
            app_name=APP_NAME,
            app_version=APP_VERSION,
        ),
        404,
    )


@app.errorhandler(405)
def method_not_allowed(error):

    return api_error(
        "HTTP method not allowed.",
        405,
    )


@app.errorhandler(413)
def request_too_large(error):

    return api_error(
        "Request payload is too large.",
        413,
    )


@app.errorhandler(500)
def internal_error(error):

    app.logger.exception(
        "Unhandled application error"
    )

    return api_error(
        "AIR-GUARD encountered an internal error.",
        500,
    )


# ============================================================
# DEVELOPMENT SERVER
# ============================================================

if __name__ == "__main__":

    host = os.getenv(
        "HOST",
        "127.0.0.1",
    )

    port = int(
        os.getenv(
            "PORT",
            "5000",
        )
    )

    debug = (
        os.getenv(
            "FLASK_DEBUG",
            "false",
        ).lower()
        == "true"
    )

    print()
    print("=" * 62)
    print("                 AIR-GUARD")
    print("        ENVIRONMENTAL INTELLIGENCE")
    print("=" * 62)
    print()
    print(f"Version : {APP_VERSION}")
    print(f"Server  : http://{host}:{port}")
    print("Logo    : /logo.svg")
    print("Health  : /health")
    print()
    print("Status  : READY")
    print("=" * 62)
    print()

    app.run(
        host=host,
        port=port,
        debug=debug,
)
