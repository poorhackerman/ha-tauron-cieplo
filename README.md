# TAURON Ciepło — Home Assistant

Nieoficjalna integracja do monitorowania komunikatów o przerwach i awariach ciepła dla wybranego miasta i ulicy. Konfiguracja w interfejsie Home Assistanta, bez YAML, konta Taurona i kluczy API. Odpytywanie co 5 minut; minimalny Home Assistant: 2025.1.

## Instalacja od razu, bez GitHuba

1. Skopiuj folder `custom_components/tauron_cieplo` do `/config/custom_components/tauron_cieplo` w Home Assistant. Plik manifestu powinien być pod `/config/custom_components/tauron_cieplo/manifest.json`.
2. Uruchom ponownie Home Assistant.
3. Ustawienia → Urządzenia i usługi → Dodaj integrację → **TAURON Ciepło**.
4. Wpisz minimum 3 znaki nazwy miasta, wybierz właściwe miasto i ulicę z list Taurona.

Kolejne ulice dodaje się jako osobne wpisy integracji. Aby zmienić adres, usuń dany wpis i dodaj nowy.

## Instalacja przez HACS

Repozytorium: [poorhackerman/ha-tauron-cieplo](https://github.com/poorhackerman/ha-tauron-cieplo). Integracja jest przeznaczona do instalacji jako repozytorium niestandardowe HACS; nie została zgłoszona do jego domyślnego katalogu.

1. HACS → menu ⋮ → Repozytoria niestandardowe.
2. Wklej `https://github.com/poorhackerman/ha-tauron-cieplo` i wybierz typ **Integracja**.
3. Wyszukaj **TAURON Ciepło**, pobierz i uruchom ponownie Home Assistant.
4. Ustawienia → Urządzenia i usługi → Dodaj integrację → **TAURON Ciepło**.
5. Wybierz miasto i ulicę.

Przy publikowaniu własnej kopii projektu ustaw jej metadane poleceniem `python configure_repository.py OWNER/REPO`.

Instalacja jako repozytorium niestandardowe nie oznacza obecności w domyślnym katalogu HACS. Pełna publikacja w katalogu wymaga także spełnienia aktualnych zasad HACS, m.in. materiałów marki.

## Encje i znaczenie danych

| Encja | Znaczenie |
| --- | --- |
| Zgłoszona awaria | `on`, gdy API Taurona zwraca `Present: true`; `off`, gdy zwraca `false` |
| Początek przerwy | Data i godzina początku wybranego komunikatu |
| Przewidywany koniec przerwy | Termin podany przez Tauron, nie potwierdzenie przywrócenia dostaw |
| Komunikat | Treść skrócona do 255 znaków; pełne komunikaty w atrybucie `outages` |

Encje należą do jednego urządzenia dla ulicy. Nazwy identyfikatorów nadaje HA; wybierz je z listy w edytorze automatyzacji. Czujniki dat rozpoznają format `od 21.10.2026 godz. 01:00 do 22.10.2026 godz. 10:00`, z uwzględnieniem strefy Europe/Warsaw. Jeśli dat nie da się jednoznacznie odczytać, wartość to `unknown`, a komunikat nadal jest widoczny.

W atrybucie `outages` dostępne są wszystkie komunikaty: `address`, `reply`, `details`, `start`, `end`. Przy wielu komunikatach czujniki wybierają najpierw trwający lub bez rozpoznanych dat, potem najbliższy przyszły, a ostatecznie ostatni zakończony.

**„Zgłoszona awaria” odzwierciedla publikację Taurona**, także komunikat przyszły lub pozostawiony po terminie. Nie wyłącza się samoczynnie po przewidywanym końcu: upływ terminu nie potwierdza usunięcia awarii. Integracja nie mierzy fizycznej dostawy ciepła i nie filtruje numerów budynków. Komunikat dla ulicy może dotyczyć tylko części budynków — sprawdź pełną treść.

Błąd sieci, limit zapytań, nieprawidłowy JSON lub zmiana formatu API powodują `unavailable`, a nie `off`. Wszystkie encje danej ulicy korzystają z jednego odczytu. Żądania mają limit czasu 25 sekund.

## Ograniczenie źródła

Dane pochodzą z publicznych endpointów używanych przez [wyszukiwarkę Taurona](https://cieplo.tauron.pl/wylaczenia-i-awarie): `city/getcities`, `street/GetStreets`, `warmoutage/getoutages` pod `/iapi/`. To nieudokumentowane API, którego Tauron może zmienić.

Integracja czyta wyniki wyszukiwarki dla ulicy. Ogólne ogłoszenia nad formularzem (np. dla całego miasta lub dzielnic), których Tauron nie wprowadzi do wyników dla ulicy, nie zostaną wykryte. Brak komunikatu w API oznacza brak informacji, nie gwarancję dostawy.

## Weryfikacja

W katalogu projektu: `python -m pip install aiohttp tzdata`, następnie `python -m unittest discover -s tests -v`.

Testy obejmują prawdziwe odpowiedzi API z 22.10.2026 dla przerwy w Dąbrowie Górniczej i braku awarii w Katowicach, błędne odpowiedzi, daty, czas zimowy i wiele komunikatów. Testy parsera i klienta HTTP wykonano lokalnie; nie wykonano jeszcze testu instalacji na działającym Home Assistant ani pobrania przez HACS z opublikowanego repozytorium.

Dokumentacja: [integracje HACS](https://www.hacs.dev/docs/publish/integration/), [pobieranie danych w HA](https://developers.home-assistant.io/docs/integration_fetching_data/).
