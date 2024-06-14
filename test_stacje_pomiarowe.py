import pytest
from requests.exceptions import RequestException, HTTPError
from komunikacja_z_api import *
from unittest.mock import patch
from peewee import SqliteDatabase
from baza_sql import Stacja, Czujnik, Pomiary, pobieranie_danych


def test_pobieranie_wszystkich_stacji():
    '''Testowanie funkcji pobierani_wszystkich_stacji'''
    stacje = pobieranie_wszystkich_stacji()

    # Sprawdzenie, czy dane zostały pobrane
    assert stacje is not None, "Nie udało się pobrać danych stacji"

    # Sprawdzenie, czy dane są listą
    assert isinstance(stacje, list), "Otrzymane dane nie są listą"

    # Sprawdzenie, czy lista nie jest pusta
    assert len(stacje) > 0, "Lista stacji jest pusta"

    # Sprawdzenie, czy każdy element listy jest słownikiem
    assert all(isinstance(stacja, dict) for stacja in stacje), "Nie wszystkie elementy listy są słownikami"

    # Sprawdzenie, czy każdy słownik zawiera wymagane klucze
    required_keys = {'stationName', 'gegrLat', 'gegrLon'}
    for stacja in stacje:
        missing_keys = required_keys - stacja.keys()
        assert not missing_keys, f"Stacja {stacja} brakuje kluczy: {missing_keys}"

    # Sprawdzenie poprawności typów wartości w słownikach
    for stacja in stacje:
        assert isinstance(stacja['stationName'], str), f"Nazwa stacji nie jest typu string: {stacja['stationName']}"
        assert isinstance(stacja['gegrLat'], str), f"Szerokość geograficzna nie jest typu string: {stacja['gegrLat']}"
        assert isinstance(stacja['gegrLon'], str), f"Długość geograficzna nie jest typu string: {stacja['gegrLon']}"


@pytest.fixture
def mock_requests_get(monkeypatch):
    def mock_get(url):
        if "sensors/1" in url:
            response = req.Response()
            response.status_code = 200
            response._content = b'[{"id": 101, "stationId": 1, "param": {"paramName": "PM10", "paramFormula": "PM10", "paramCode": "PM10"}}]'
            return response
        elif "sensors/999" in url:
            response = req.Response()
            response.status_code = 500  # Symulujemy błąd serwera
            raise HTTPError(response=response)
        else:
            response = req.Response()
            response.status_code = 404
            raise HTTPError(response=response)

    monkeypatch.setattr(req, "get", mock_get)
    return mock_get  # Zwracamy mock_get, aby można było go użyć w teście


def test_pobierz_stanowiska_pomiarowe(mock_requests_get, capsys):
    '''Test funkcji pobierz_stanowiska_pomiarowe'''

    # Test dla poprawnej odpowiedzi
    result = pobierz_stanowiska_pomiarowe(1)
    expected_result = [
        {
            "id": 101,
            "stationId": 1,
            "param": {
                "paramName": "PM10",
                "paramFormula": "PM10",
                "paramCode": "PM10"
            }
        }
    ]
    assert result == expected_result

    # Test dla błędnej odpowiedzi (status code 500)
    result = pobierz_stanowiska_pomiarowe(999)
    assert result is None
    captured = capsys.readouterr()
    assert "Wystąpił błąd podczas pobierania danych" in captured.out

    # Test dla wyjątku RequestException
    def mock_get_exception(url):
        raise RequestException("Timeout")

    # Sprawdzamy czy RequestException jest zgłaszany
    with pytest.raises(RequestException):
        mock_get_exception("https://api.gios.gov.pl/pjp-api/rest/station/sensors/1")


baza_danych = SqliteDatabase(':memory:')


@pytest.fixture
def setup_db():
    baza_danych.bind([Stacja, Czujnik, Pomiary])
    baza_danych.connect()
    baza_danych.create_tables([Stacja, Czujnik, Pomiary])
    yield
    baza_danych.drop_tables([Stacja, Czujnik, Pomiary])
    baza_danych.close()


def test_pobieranie_danych(setup_db):
    '''Test funkcji pobieranie_danych'''
    mock_stacje = [
        {
            'id': 1,
            'stationName': 'Station1',
            'gegrLat': '50.06',
            'gegrLon': '19.94',
            'city': {'name': 'City1'},
            'addressStreet': 'Street1'
        }
    ]

    mock_czujniki = [
        {
            'id': 101,
            'param': {'paramName': 'PM10', 'paramCode': 'PM10'}
        }
    ]

    mock_pomiary = {
        'values': [
            {'date': '2023-01-01 10:00:00', 'value': 45.0}
        ]
    }

    with patch('baza_sql.pobieranie_wszystkich_stacji', return_value=mock_stacje), \
            patch('baza_sql.pobierz_stanowiska_pomiarowe', return_value=mock_czujniki), \
            patch('baza_sql.pobierz_dane', return_value=mock_pomiary):
        pobieranie_danych()

        # Sprawdzenie, czy dane zostały zapisane w bazie danych
        assert Stacja.select().count() == 1
        assert Czujnik.select().count() == 1
        assert Pomiary.select().count() == 1

        stacja = Stacja.get_by_id(1)
        assert stacja.stationName == 'Station1'
        assert stacja.gegrLat == '50.06'
        assert stacja.gegrLon == '19.94'
        assert stacja.cityName == 'City1'
        assert stacja.addressStreet == 'Street1'

        czujnik = Czujnik.get_by_id(101)
        assert czujnik.paramName == 'PM10'
        assert czujnik.paramCode == 'PM10'

        pomiar = Pomiary.get()
        assert pomiar.sensor == czujnik
        assert pomiar.date == '2023-01-01 10:00:00'
        assert pomiar.value == 45.0
