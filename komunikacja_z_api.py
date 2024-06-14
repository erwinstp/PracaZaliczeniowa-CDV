import requests as req


def pobieranie_wszystkich_stacji():
    '''Funkcja pobierająca stacje pomiarowe z API'''
    try:
        url = "https://api.gios.gov.pl/pjp-api/rest/station/findAll"
        response = req.get(url)
        response.raise_for_status()
        return response.json()
    except req.exceptions.RequestException as e:
        print(f"Wystąpił błąd podczas pobierania danych: {e}")
        return None


def pobierz_stanowiska_pomiarowe(station_id):
    '''Funkcja pobierająca stanowiska pomiarowe z API'''
    try:
        url = f"https://api.gios.gov.pl/pjp-api/rest/station/sensors/{station_id}"
        response = req.get(url)
        response.raise_for_status()
        return response.json()
    except req.exceptions.RequestException as e:
        print(f"Wystąpił błąd podczas pobierania danych: {e}")
        return None


def pobierz_dane(sensor_id):
    '''Funkcja pobierająca dane pomiarowe z API'''
    try:
        url = f"https://api.gios.gov.pl/pjp-api/rest/data/getData/{sensor_id}"
        response = req.get(url)
        response.raise_for_status()
        return response.json()
    except req.exceptions.RequestException as e:
        print(f"Wystąpił błąd podczas pobierania danych: {e}")
        return None
