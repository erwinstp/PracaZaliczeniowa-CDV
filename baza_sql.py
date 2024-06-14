from peewee import *
from komunikacja_z_api import *
from tkinter import messagebox

'''Poniżej następuje łączenie sie z baządanych, 
zdefiniowane sa modele bazy danych poprzez bibliotekę peewee oraz tworzone są tabele w bazie danych'''
db = SqliteDatabase('Stacje.db')

class ModelBazowy(Model):
    class Meta:
        database = db

class Stacja(ModelBazowy):
    id = IntegerField(primary_key=True)
    stationName = CharField()
    gegrLat = CharField()
    gegrLon = CharField()
    cityName = CharField()
    addressStreet = CharField(null=True)

class Czujnik(ModelBazowy):
    id = IntegerField(primary_key=True)
    station = ForeignKeyField(Stacja, backref='sensors')
    paramName = CharField()
    paramCode = CharField()

class Pomiary(ModelBazowy):
    id = AutoField()
    sensor = ForeignKeyField(Czujnik, backref='measurements')
    date = CharField()
    value = FloatField(null=True)

db.connect()
db.create_tables([Stacja, Czujnik, Pomiary])

def pobieranie_danych():
    '''Funkcaj pobierająca oraz zapisująca dane w bazie danych'''
    stacje = pobieranie_wszystkich_stacji()

    for dane_stacji in stacje:
        stacja, zrob = Stacja.get_or_create(
            id=dane_stacji['id'],
            defaults={
                'stationName': dane_stacji['stationName'],
                'gegrLat': dane_stacji['gegrLat'],
                'gegrLon': dane_stacji['gegrLon'],
                'cityName': dane_stacji['city']['name'],
                'addressStreet': dane_stacji.get('addressStreet')
            }
        )

        czujniki = pobierz_stanowiska_pomiarowe(stacja.id)
        for dane_czujnikow in czujniki:
            czujnik, zrob = Czujnik.get_or_create(
                id=dane_czujnikow['id'],
                station=stacja,
                defaults={
                    'paramName': dane_czujnikow['param']['paramName'],
                    'paramCode': dane_czujnikow['param']['paramCode']
                }
            )

            dane_pomiarowe = pobierz_dane(czujnik.id)
            for pomiar in dane_pomiarowe['values']:
                if not Pomiary.select().where(Pomiary.sensor == czujnik, Pomiary.date == pomiar['date']).exists():
                    Pomiary.create(
                        sensor=czujnik,
                        date=pomiar['date'],
                        value=pomiar['value']
                    )
    messagebox.showinfo("Informacja", "Pobieranie danych zakończone!")
if __name__ == '__main__':
    pobieranie_danych()
    db.close()
