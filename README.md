# Gra Sieciowa Chomp

Projekt realizowany w ramach przedmiotu Programowanie Współbieżne. Jest to implementacja gry logicznej "Chomp" (gra w czekoladę) działająca w architekturze klient-serwer.

## Opis projektu

Aplikacja umożliwia rozgrywkę pomiędzy dwoma graczami na oddzielnych komputerach (lub w osobnych procesach). Projekt wykorzystuje gniazda sieciowe (sockets) do komunikacji oraz wielowątkowość do obsługi wielu gier jednocześnie i zapewnienia płynności interfejsu graficznego.

### Główne funkcjonalności
* **Architektura Klient-Serwer:** Pełna synchronizacja stanu gry zarządzana przez serwer.
* **System Lobby:** Możliwość tworzenia pokoi, przeglądania listy dostępnych gier i dołączania do nich.
* **Dynamiczna plansza:** Gracz tworzący pokój decyduje o wymiarach planszy (od 2x2 do 10x10).
* **Interfejs Graficzny:** Proste GUI wykonane w bibliotece `tkinter`.
* **Obsługa błędów:** Wykrywanie rozłączenia przeciwnika, automatyczne czyszczenie pustych pokoi.
* **System restartu:** Mechanizm głosowania za ponownym rozpoczęciem gry po jej zakończeniu.

## Technologie

Projekt został napisany w czystym języku **Python 3** i wykorzystuje wyłącznie biblioteki standardowe:
* `socket` - komunikacja sieciowa (TCP/IP).
* `threading` - obsługa wielowątkowości (serwer, odbiór danych w kliencie).
* `tkinter` - interfejs graficzny.
* `uuid` - generowanie unikalnych ID dla pokoi.
