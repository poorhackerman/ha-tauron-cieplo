# TAURON Ciepło — Home Assistant

![TAURON Ciepło](assets/tauron-cieplo.png)

Nieoficjalna integracja do monitorowania komunikatów o przerwach i awariach ciepła dla wybranego miasta i ulicy. Konfiguracja w interfejsie Home Assistanta, bez YAML, konta Taurona i kluczy API. Częstotliwość sprawdzania ustawiana w opcjach (domyślnie co godzinę); minimalny Home Assistant: 2025.1.

## Instalacja przez HACS

1. Otwórz HACS i wyszukaj **TAURON Ciepło**.
2. Pobierz integrację i uruchom ponownie Home Assistant.
3. Przejdź do: Ustawienia → Urządzenia i usługi → Dodaj integrację → **TAURON Ciepło**.
4. Wpisz minimum 3 znaki nazwy miasta, wybierz właściwe miasto, wpisz fragment nazwy ulicy (minimum 3 znaki) i wybierz ulicę z wyników Taurona. Jeśli brakuje ulicy, zaznacz „Wyszukaj ponownie” i wpisz dłuższy fragment. API Taurona zwraca maksymalnie 150 wyników na zapytanie.

Kolejne ulice dodaje się jako osobne wpisy integracji. Aby zmienić adres, usuń dany wpis i dodaj nowy.

## Instalacja ręczna

1. Skopiuj folder `custom_components/tauron_cieplo` do `/config/custom_components/tauron_cieplo` w Home Assistant. Plik manifestu powinien być pod `/config/custom_components/tauron_cieplo/manifest.json`.
2. Uruchom ponownie Home Assistant.
3. Ustawienia → Urządzenia i usługi → Dodaj integrację → **TAURON Ciepło**.
4. Wpisz minimum 3 znaki nazwy miasta, wybierz właściwe miasto, wpisz fragment nazwy ulicy (minimum 3 znaki) i wybierz ulicę z wyników Taurona. Jeśli brakuje ulicy, zaznacz „Wyszukaj ponownie” i wpisz dłuższy fragment. API Taurona zwraca maksymalnie 150 wyników na zapytanie.

## Częstotliwość śledzenia zmian

Ustawienia → Urządzenia i usługi → TAURON Ciepło → Konfiguruj (lub Opcje) przy wybranym wpisie. W polu **Sprawdzaj co (minuty)** wpisz czas od 5 do 1440 minut, np. 15, 30, 60, 120 lub 1440. Każda ulica może mieć własny harmonogram.

Domyślnie dane są pobierane co **60 minut**, także dla istniejących wpisów, które nie mają jeszcze zapisanych opcji. Zapisanie opcji automatycznie przeładowuje dany wpis i odczytuje dane; nie wymaga restartu całego HA ani ponownego wyboru adresu. Nowe komunikaty i zmiany terminów pojawią się najpóźniej przy kolejnym udanym odczycie. „Aktywna awaria” nadal przełącza się lokalnie o wcześniej pobranych godzinach początku i końca.

## Encje i znaczenie danych

| Encja | Znaczenie |
| --- | --- |
| Zgłoszona awaria | `on`, gdy API Taurona zwraca `Present: true`; `off`, gdy zwraca `false` |
| Aktywna awaria | `on`, gdy teraz trwa dowolny podany przedział: początek ≤ teraz < koniec; `off`, gdy brak komunikatów lub wszystkie rozpoznane przedziały są poza aktualnym czasem; `unknown`, gdy dat nie da się odczytać i żaden znany przedział nie jest aktywny |
| Początek przerwy | Data i godzina początku wybranego komunikatu |
| Przewidywany koniec przerwy | Termin podany przez Tauron, nie potwierdzenie przywrócenia dostaw |
| Komunikat | Treść skrócona do 255 znaków; pełne komunikaty w atrybucie `outages` |

Encje należą do jednego urządzenia dla ulicy. Nazwy identyfikatorów nadaje HA; wybierz je z listy w edytorze automatyzacji. Czujniki dat rozpoznają format `od 21.10.2026 godz. 01:00 do 22.10.2026 godz. 10:00`, z uwzględnieniem strefy Europe/Warsaw. Jeśli dat nie da się jednoznacznie odczytać, wartość to `unknown`, a komunikat nadal jest widoczny.

W atrybucie `outages` dostępne są wszystkie komunikaty: `address`, `reply`, `details`, `start`, `end`. Przy wielu komunikatach czujniki wybierają najpierw trwający lub bez rozpoznanych dat, potem najbliższy przyszły, a ostatecznie ostatni zakończony.

**„Zgłoszona awaria” odzwierciedla publikację Taurona**, także komunikat przyszły lub pozostawiony po terminie. Nie wyłącza się samoczynnie po przewidywanym końcu: upływ terminu nie potwierdza usunięcia awarii. Integracja nie mierzy fizycznej dostawy ciepła i nie filtruje numerów budynków. Komunikat dla ulicy może dotyczyć tylko części budynków — sprawdź pełną treść.

**„Aktywna awaria” określa aktywność według opublikowanego przedziału**, a nie pomiar dostawy. Zmienia stan o godzinie rozpoczęcia i przewidywanego końca również między odczytami API, bez dodatkowych zapytań. Jeśli Tauron przedłuży termin, stan zostanie przeliczony po kolejnym odczycie. Nowa encja jest dodawana automatycznie po aktualizacji i restarcie HA; istniejącej konfiguracji nie trzeba usuwać. Poprawione wyszukiwanie ulic jest dostępne przy dodawaniu kolejnej konfiguracji.

Błąd sieci, limit zapytań, nieprawidłowy JSON lub zmiana formatu API powodują `unavailable`, a nie `off`. Po nieudanym odczycie integracja automatycznie ponawia próbę co 5 minut. Po odzyskaniu połączenia wraca do częstotliwości ustawionej przez użytkownika. Wszystkie encje danej ulicy korzystają z jednego odczytu. Żądania mają limit czasu 25 sekund.

## Ograniczenie źródła

Dane pochodzą z publicznych endpointów używanych przez [wyszukiwarkę Taurona](https://cieplo.tauron.pl/wylaczenia-i-awarie): `city/getcities`, `street/GetStreets`, `warmoutage/getoutages` pod `/iapi/`. To nieudokumentowane API, którego Tauron może zmienić.

Integracja czyta wyniki wyszukiwarki dla ulicy. Ogólne ogłoszenia nad formularzem (np. dla całego miasta lub dzielnic), których Tauron nie wprowadzi do wyników dla ulicy, nie zostaną wykryte. Brak komunikatu w API oznacza brak informacji, nie gwarancję dostawy.

## Weryfikacja

W katalogu projektu: `python -m pip install aiohttp tzdata`, następnie `python -m unittest discover -s tests -v`.

Testy obejmują prawdziwe odpowiedzi API z 22.10.2026 dla przerwy w Dąbrowie Górniczej i braku awarii w Katowicach, błędne odpowiedzi, daty, czas zimowy i wiele komunikatów. Testy parsera i klienta HTTP wykonano lokalnie; nie wykonano jeszcze testu instalacji na działającym Home Assistant ani pobrania przez HACS z opublikowanego repozytorium.

Dokumentacja: [integracje HACS](https://www.hacs.dev/docs/publish/integration/), [pobieranie danych w HA](https://developers.home-assistant.io/docs/integration_fetching_data/).
