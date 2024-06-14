import matplotlib.pyplot as plt
from datetime import datetime
from tkcalendar import DateEntry
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from komunikacja_z_api import pobierz_dane
import tkinter as tk
from tkinter import messagebox
from baza_sql import Pomiary
import socket

def dostep_do_internetu():
    '''Funkcja sprawdzająca dostęp do internetu'''
    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        return False

def wyswietl_dane_pomiarowe(sensor_id):
    def pobierz_dane_z_zakresu(id_czujnika, data_poczatkowa, data_koncowa):
        '''Funkcja pobierająca dane pomiarowe do wykresu'''
        if dostep_do_internetu():
            dane = pobierz_dane(id_czujnika)
        else:
            dane = Pomiary.select().where(
                (Pomiary.sensor_id == id_czujnika) &
                (Pomiary.date.between(data_poczatkowa, data_koncowa))
            ).dicts()
            return {'values': list(dane)}
        if not dane or 'values' not in dane:
            return None

        wartosci = [
            dana for dana in dane['values']
            if data_poczatkowa <= datetime.strptime(dana['date'], "%Y-%m-%d %H:%M:%S") <= data_koncowa
        ]
        return {'values': wartosci}

    def pokaz_wykres(dane):
        '''Funkcja tworząca wykres na podstawie pobranych danych, wyswietlajaca wykres oraz wartosci minimalne,
        maksymalne oraz srednią'''
        try:
            daty = []
            wartosci = []
            for dana in dane['values']:
                if isinstance(dana, dict) and 'date' in dana and 'value' in dana:
                    data = datetime.strptime(dana['date'], "%Y-%m-%d %H:%M:%S")
                    wartosc = dana['value']
                    if wartosc is not None:  # Sprawdzanie, czy wartość nie jest None
                        daty.append(data)
                        wartosci.append(wartosc)
                    else:
                        print(f"Wartość None w danych: {dana}")
                else:
                    messagebox.showerror("Błąd", "Błędny format danych.")
                    return

            if not daty or not wartosci:
                messagebox.showerror("Błąd", "Brak poprawnych danych do wyświetlenia.")
                return

            daty, wartosci = zip(*sorted(zip(daty, wartosci)))

            # Tworzenie nowego okna Tkinter dla wykresu
            okno_wykresu = tk.Toplevel()
            okno_wykresu.title("Dane pomiarowe")
            okno_wykresu.geometry('1200x600')

            fig, wykres = plt.subplots()

            # Wykres podstawowy
            wykres.plot(daty, wartosci, marker='o', linestyle='-', label='Wartości')

            # Oznaczenie wartości maksymalnej
            wartosc_max = max(wartosci)
            index_max = wartosci.index(wartosc_max)
            wykres.plot(daty[index_max], wartosc_max, 'ro')
            wykres.annotate(f'Max: {wartosc_max}', xy=(daty[index_max], wartosc_max),
                            xytext=(daty[index_max], wartosc_max * 0.95),
                            arrowprops=dict(facecolor='red', shrink=0.05))

            # Oznaczenie wartości minimalnej
            wartosc_min = min(wartosci)
            index_min = wartosci.index(wartosc_min)
            wykres.plot(daty[index_min], wartosc_min, 'go')
            wykres.annotate(f'Min: {wartosc_min}', xy=(daty[index_min], wartosc_min),
                            xytext=(daty[index_min], wartosc_min * 1.05),
                            arrowprops=dict(facecolor='green', shrink=0.05))

            # Oznaczenie wartości średniej
            wartosc_srednia = sum(wartosci) / len(wartosci)
            wykres.axhline(y=wartosc_srednia, color='blue', linestyle='--', label=f'Średnia: {wartosc_srednia:.2f}')
            wykres.text(daty[0], wartosc_srednia + (wartosc_srednia * 0.05), f'Średnia: {wartosc_srednia:.2f}',
                        color='blue')

            # Dodatkowe ustawienia wykresu
            wykres.set(xlabel='Data', ylabel='Wartość', title='Dane pomiarowe')
            wykres.legend()
            wykres.grid()

            # Tworzenie płótna dla wykresu
            wykres = FigureCanvasTkAgg(fig, master=okno_wykresu)
            wykres.draw()
            wykres.get_tk_widget().pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

            narzedzia = NavigationToolbar2Tk(wykres, okno_wykresu)
            narzedzia.update()
            wykres.get_tk_widget().pack()

            def zamykanie_wykresu():
                plt.close(fig)
                okno_wykresu.destroy()

            okno_wykresu.protocol("WM_DELETE_WINDOW", zamykanie_wykresu)

        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas wyświetlania danych: {e}")

    def pokaz_okno_wyboru():
        '''Funkcja tworzaca okno do wyboru daty oraz zakresu godzin z jakich mają zostać pobrane dane pomiarowe dla
        wybranego czujnika'''
        def zatwierdz_wybor():
            start_date = data_poczatkowa.get_date()
            start_time = czas_poczatkowy.get()
            end_date = data_koncowa.get_date()
            end_time = czas_koncowy.get()

            try:
                start_datetime = datetime.strptime(f"{start_date} {start_time}:00", "%Y-%m-%d %H:%M:%S")
                end_datetime = datetime.strptime(f"{end_date} {end_time}:00", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                messagebox.showerror("Błąd", "Niepoprawny format daty.")
                return

            dane = pobierz_dane_z_zakresu(sensor_id, start_datetime, end_datetime)
            if not dane or 'values' not in dane:
                messagebox.showerror("Błąd",
                                     f"Nie można pobrać danych dla sensora o ID: {sensor_id} w podanym zakresie.")
                return

            pokaz_wykres(dane)
            okno_wyboru.destroy()

        okno_wyboru = tk.Toplevel()
        okno_wyboru.title("Wybierz zakres dat i godzin")
        okno_wyboru.attributes('-topmost', True)

        tk.Label(okno_wyboru, text="Data początkowa:").grid(row=0, column=0, padx=10, pady=10)
        data_poczatkowa = DateEntry(okno_wyboru, date_pattern='yyyy-mm-dd')
        data_poczatkowa.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(okno_wyboru, text="Godzina początkowa (HH:MM):").grid(row=1, column=0, padx=10, pady=10)
        czas_poczatkowy = tk.Entry(okno_wyboru)
        czas_poczatkowy.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(okno_wyboru, text="Data końcowa:").grid(row=2, column=0, padx=10, pady=10)
        data_koncowa = DateEntry(okno_wyboru, date_pattern='yyyy-mm-dd')
        data_koncowa.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(okno_wyboru, text="Godzina końcowa (HH:MM):").grid(row=3, column=0, padx=10, pady=10)
        czas_koncowy = tk.Entry(okno_wyboru)
        czas_koncowy.grid(row=3, column=1, padx=10, pady=10)

        przycisk_zatwierdzajacy = tk.Button(okno_wyboru, text="Zatwierdź", command=zatwierdz_wybor)
        przycisk_zatwierdzajacy.grid(row=4, column=0, columnspan=2, pady=10)

        screen_width = okno_wyboru.winfo_screenwidth()
        screen_height = okno_wyboru.winfo_screenheight()
        window_width = 400
        window_height = 250
        position_top = int(screen_height / 2 - window_height / 2)
        position_right = int(screen_width / 2 - window_width / 2)
        okno_wyboru.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

    pokaz_okno_wyboru()