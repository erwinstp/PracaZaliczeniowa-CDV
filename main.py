import tkinter as tk
from tkinter import messagebox
from baza_sql import pobieranie_danych
from funkcje_gui import mapa_stacji,  wyswietl_stacje_po_obszarze, wyswietl_stacje_w_miescie, sprawdz_dostep_do_internetu,  wyswietl_stacje, wybieranie_stacji

def main():
    '''Jest to główna funkcja programu wyswietlajaca GUI, poniżej zostało opisane rozmieszczenie przycisków oraz
    występuje tu warunek, który ma za zadanie sprawdzać dostępnosć do internetu'''
    if not sprawdz_dostep_do_internetu():
        messagebox.showwarning("Brak dostępu do Internetu","Nie masz dostępu do Internetu. Kontynuuj z ograniczoną funkcjonalnoscia używając bazy danych.")
    root = tk.Tk()
    root.geometry('700x280')
    root.title("Stacje Pomiarowe")

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = 700
    window_height = 280
    position_top = int(screen_height / 2 - window_height / 2)
    position_right = int(screen_width / 2 - window_width / 2)
    root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

    root.resizable(False, False)

    # Tworzenie ramki
    frame = tk.Frame(root)
    frame.pack(pady=20, padx=20, fill=tk.Y, side=tk.LEFT)

    # Tworzenie przycisków
    fetch_button = tk.Button(frame, text="Pobierz wszystkie stacje", command=lambda: wyswietl_stacje(root, listbox))
    fetch_button.pack(pady=10, padx=10, fill=tk.X)

    wybieranie_stacji_po_miescie = tk.Button(frame, text="Wyszukaj stacje po nazwie miejscowosci", command=lambda: wyswietl_stacje_w_miescie(root, listbox))
    wybieranie_stacji_po_miescie.pack(pady=10, padx=10, fill=tk.X)

    # Tworzenie Listboxa
    listbox_frame = tk.Frame(root)
    listbox_frame.pack(pady=10, padx=10, fill=tk.NONE, expand=False, side=tk.LEFT)
    scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
    listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, width=55, height=14)
    scrollbar.config(command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.pack(side=tk.TOP, fill=tk.NONE)
    listbox.bind("<Double-1>", wybieranie_stacji)

    if sprawdz_dostep_do_internetu():
        wybieranie_stacji_po_obszarze = tk.Button(frame, text="Wyszukaj stacje w obszarze od podanego punktu", command=lambda: wyswietl_stacje_po_obszarze(root, listbox))
        wybieranie_stacji_po_obszarze.pack(pady=10, padx=10, fill=tk.X)

        pokaz_mape_ze_stacjami = tk.Button(frame, text="Pokaż mapę stacji", command=mapa_stacji)
        pokaz_mape_ze_stacjami.pack(pady=10, padx=10, fill=tk.X)

        pobierz_dane = tk.Button(frame, text="Pobierz dane", command=pobieranie_danych)
        pobierz_dane.pack(pady=10, padx=10, fill=tk.X)
    else:
        None
    root.mainloop()

if __name__ == "__main__":
    main()