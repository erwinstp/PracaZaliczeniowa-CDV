from geopy.distance import geodesic
import folium
import webbrowser
from geopy.geocoders import Nominatim
from komunikacja_z_api import *
from wyswietlanie_wykresu import *
from tkinter import simpledialog, messagebox
import socket
from baza_sql import Stacja, Czujnik


def wybieranie_stacji(event):
    '''Funkcja wyswietlająca stanowiska pomiarowe w listboxie GUI'''
    listbox = event.widget
    wybrany_index = listbox.curselection()
    if wybrany_index:
        wybrana_stacja = listbox.get(wybrany_index)
        id_stacji = int(wybrana_stacja.split('(ID: ')[1][:-1])
        wyswietl_stanowiska_pomiarowe(id_stacji)


def sprawdz_dostep_do_internetu():
    '''Jest to funkcja sprawdzjąca dostępnosć do internetu'''
    try:
        # Tworzenie połączenia z serwerem google.com na porcie 80
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        return False

def mapa_stacji():
    '''Funkcja, która wyswietla w przeglądarce mapę z naniesionymi na nią miejscami występowania
    stacji pomiarowych w Polsce po wcisnieciu przycisku na GUI'''
    if sprawdz_dostep_do_internetu():
        stacje = pobieranie_wszystkich_stacji()
        if not stacje:
            messagebox.showerror("Błąd", "Nie można utworzyć mapy z powodu błędów.")
            return

        wsp_lat = sum(float(stacja['gegrLat']) for stacja in stacje) / len(stacje)
        wsp_lon = sum(float(stacja['gegrLon']) for stacja in stacje) / len(stacje)
        center = (wsp_lat, wsp_lon)

        m = folium.Map(location=center, zoom_start=6)
        for stacja in stacje:
            lokalizacja_stacji = (float(stacja['gegrLat']), float(stacja['gegrLon']))
            folium.Marker(
                location=lokalizacja_stacji,
                popup=f"{stacja['stationName']} ({stacja['id']})",
                icon=folium.Icon(color='blue')
            ).add_to(m)
        m.save("mapa_stacji.html")
        webbrowser.open("mapa_stacji.html")
    else:
        messagebox.showerror('Błąd','Brak dostępu do internetu!')

# Funkcja wyswietlajaca stanowiska pomiarowe
def wyswietl_stanowiska_pomiarowe(id_stacji):
    '''Funkcja wyswietlająca stanowiska pomiarowe po wybraniu stacji. W zależnosci od dostepu do internetu
    funkcja pobiera dane z API lub bazy danych, jezeli dane zostały wczesniej pobrane'''
    def stanowiska_api(id_stacji):
        czujniki = pobierz_stanowiska_pomiarowe(id_stacji)
        return czujniki

    def stanowiska_db(id_stacji):
        czujniki = Czujnik.select().where(Czujnik.station_id == id_stacji)
        return czujniki

    internet_dostepny = sprawdz_dostep_do_internetu()

    if internet_dostepny:
        czujniki = stanowiska_api(id_stacji)
        nazwa_czujnika = [f"{sensor['param']['paramName']} (ID: {sensor['id']})" for sensor in czujniki]
    else:
        czujniki = stanowiska_db(id_stacji)
        nazwa_czujnika = [f"{sensor.paramName} (ID: {sensor.id})" for sensor in czujniki]
    if not czujniki:
        messagebox.showerror("Błąd", f"Nie można pobrać sensorów dla stacji o ID: {id_stacji}")
        return

    okno_wyboru = tk.Toplevel()
    okno_wyboru.title("Wybierz sensor")
    okno_wyboru.geometry('400x250')

    screen_width = okno_wyboru.winfo_screenwidth()
    screen_height = okno_wyboru.winfo_screenheight()
    window_width = 400
    window_height = 250
    position_top = int(screen_height / 2 - window_height / 2)
    position_right = int(screen_width / 2 - window_width / 2)
    okno_wyboru.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

    wybor_czujnika = tk.Listbox(okno_wyboru)
    for sensor_name in nazwa_czujnika:
        wybor_czujnika.insert(tk.END, sensor_name)
    wybor_czujnika.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

    def potwierdzenie_stanowiska(event):
        wybrany_index = wybor_czujnika.curselection()
        if wybrany_index:
            wybrany_czujnik = wybor_czujnika.get(wybrany_index)
            id_czujnika = int(wybrany_czujnik.split('(ID: ')[1][:-1])
            wyswietl_dane_pomiarowe(id_czujnika)
        okno_wyboru.destroy()

    # Wybór stanowiska poprzez podwójne kliknięcie lewego przycisku myszy
    wybor_czujnika.bind("<Double-1>", potwierdzenie_stanowiska)

def wyswietl_stacje_w_miescie(root, listbox):
    '''Funkcja wyswietlająca stacje w danym miescie poprzez wpisanie nazwy miasta w oknie. W zależnosci od dostepu do internetu
    funkcja pobiera dane z API lub bazy danych, jezeli dane zostały wczesniej pobrane'''
    def stacje_po_miejscowosci_api(miasto):
        stacje_w_miescie = [stacja for stacja in pobieranie_wszystkich_stacji() if stacja['city']['name'] == miasto]
        return stacje_w_miescie

    def stacje_po_miejscowosci_db(miasto):
        stacje_w_miescie = Stacja.select().where(Stacja.cityName == miasto)
        return stacje_w_miescie

    try:
        nazwa_miasta = simpledialog.askstring("Podaj nazwę miasta", "Wpisz nazwę miasta:")

        if nazwa_miasta:
            internet_dostepny = sprawdz_dostep_do_internetu()
            if internet_dostepny:
                stacje_w_miescie = stacje_po_miejscowosci_api(nazwa_miasta)
                station_names = [f"{station['stationName']} (ID: {station['id']})" for station in stacje_w_miescie]
            else:
                stacje_w_miescie = stacje_po_miejscowosci_db(nazwa_miasta)
                station_names = [f"{station.stationName} (ID: {station.id})" for station in stacje_w_miescie]
            if stacje_w_miescie:
                for widget in root.winfo_children():
                    if isinstance(widget, tk.Button) and widget.cget("text") == "Wybierz":
                        widget.destroy()

                listbox.delete(0, tk.END)

                for nazwa_stacji in station_names:
                    listbox.insert(tk.END, nazwa_stacji)
            else:
                messagebox.showinfo("Brak stacji", f"Brak stacji pomiarowych w miejscowości {nazwa_miasta}")
    except Exception as e:
        messagebox.showerror("Błąd", f"Wystąpił błąd: {e}")

def wyswietl_stacje(root, listbox):
    '''Funkcja wyswietlająca wszystkie stacje. W zależnosci od dostepu do internetu
    funkcja pobiera dane z API lub bazy danych, jezeli dane zostały wczesniej pobrane'''
    listbox.delete(0, tk.END)

    def fetch_stations_from_db():
        stations = Stacja.select()
        return [{"stationName": stacja.stationName, "id": stacja.id, "gegrLat": stacja.gegrLat, "gegrLon": stacja.gegrLon, "city": {"name": stacja.cityName}} for stacja in stations]

    internet_dostepny = sprawdz_dostep_do_internetu()

    if internet_dostepny:
        stations = pobieranie_wszystkich_stacji()
    else:
        stations = fetch_stations_from_db()

    if stations:
        for station in stations:
            station_name = station.get('stationName', 'Brak nazwy')
            station_id = station.get('id', 'Brak ID')
            listbox.insert(tk.END, f"{station_name} (ID: {station_id})")
    else:
        messagebox.showinfo("Informacja", "Brak danych do wyświetlenia.")

def wyswietl_stacje_po_obszarze(root, listbox):
    '''Funkcja wyswietlająca stacje po wpisaniu nazwy miesjca oraz podaniu promienia
    w jakim maja być szukane stacje pomiarowe. W zależnosci od dostepu do internetu
    funkcja pobiera dane z API lub bazy danych, jezeli dane zostały wczesniej pobrane'''
    if sprawdz_dostep_do_internetu():
        def stacje_po_obrebie(lokalizacja, obreb):
            try:
                geolocator = Nominatim(user_agent="weather_station_app")
                location = geolocator.geocode(lokalizacja)
                if not location:
                    print(f"Nie znaleziono lokalizacji: {lokalizacja}")
                    return None

                punkt_poczatkowy = (location.latitude, location.longitude)

                # Filtracja stacji w obrębie zadanego promienia
                stacje_w_obrebie = []
                for stacja in pobieranie_wszystkich_stacji():
                    lokalizacja_stacji = (float(stacja['gegrLat']), float(stacja['gegrLon']))
                    odleglosc = geodesic(punkt_poczatkowy, lokalizacja_stacji).kilometers
                    if odleglosc <= obreb:
                        stacje_w_obrebie.append(stacja)
                return stacje_w_obrebie
            except Exception as e:
                print(f"Wystąpił nieoczekiwany błąd: {e}")
                return None

        try:
            lokalizacja = simpledialog.askstring("Podaj lokalizację", "Wpisz nazwę lokalizacji:", parent=root)
            obszar = simpledialog.askfloat("Podaj promień", "Wpisz promień w kilometrach:", parent=root)

            if lokalizacja and obszar:
                stacje_w_obszarze = stacje_po_obrebie(lokalizacja, obszar)
                if stacje_w_obszarze:
                    # Usuń poprzednie dane z listboxa
                    listbox.delete(0, tk.END)

                    for stacja in stacje_w_obszarze:
                        nazwa_stacji = f"{stacja['stationName']} (ID: {stacja['id']})"
                        listbox.insert(tk.END, nazwa_stacji)
                else:
                    messagebox.showinfo("Brak stacji", "Brak stacji pomiarowych w zadanym obszarze, lub błędnie podana nazwa miejscowosci")

        except ValueError:
            messagebox.showerror("Błąd", "Proszę wpisać prawidłowe wartości.")
    else:
        messagebox.showerror('Błąd!', 'Brak dostepu do internetu!')
