# ZUM_projekt_1
Głosowe sterowanie wiatrakami

## Instrukcja

Ekran główny aplikacji pokazuje temperaturę oraz moc dla każdego skonfigurowanego wiatraka. 
W przypadku zmockowanej aplikacji wykres temperatury to sin(t) a prędkość wiatraka to ostatnie
ustawienie przez komendę.

### mock
- w pliku "src/data/mock_config.json" ustaw: \
"volume_threshold": stopień głośności do przedłużenia nagrywania komendy (0 - akceptuje wszystko, 1 - wszystko ignoruje), \
"record_wait_time": o ile sekund przedłużyć nagrywania w przypadku przekroczenia progu głośności, \
"initial_record_wait_time": początkowy czas nagrywania, przed przedłużeniem nagrywania, \
"max_command_time": czas, po którym nagrywanie nie będzie przedłużane
- uruchom plik "start_mock.sh"
- poczekaj na komunikat "nagrywanie komendy..."

### prawdziwa aplikacja
- w pliku "src/data/config.json":
```json
{
    "fans": [ // podzespołów z wiatrakami na razie wspierane CPU i GPU
        {
            "name": "CPU",
            "mode": [{ // lista rejestrów odpowiedzialnych z tryb wiatraków
                "register": 147, // adres
                "manual": 20, // wartość dla trybu manual
                "auto": 4 // wartość dla trybu auto
            }],
            "write": [{ // lista rejestrów do ustawiania prędkości wiatraków
                "register": 148,
                "min": 255,
                "max": 0
            }],
            "read": [{ // lista rejestrów do czytania prędkości wiatraków
                "register": 149,
                "min": 255,
                "max": 85
            }],
            "temp": 168 // adres rejestru do czytania temperatury
        },
        {
            "name": "GPU",
            "mode": [{ // kolejność rejestrów w polach mode write i read musi się zgadzać
                "register": 150,
                "manual": 20,
                "auto": 4
            },{
                "register": 154,
                "manual": 20,
                "auto": 4
            }],
            "write": [{
                "register": 151,
                "min": 255,
                "max": 29
            },{
                "register": 155,
                "min": 255,
                "max": 0
            }],
            "read": [{
                "register": 152,
                "min": 255,
                "max": 65
            },{
                "register": 156,
                "min": 255,
                "max": 66
            }],
            "temp": 171
        }
    ],
    "max_temp": 110, // maksymalna temperatura do ustalenia górnej granicy wykresu
    "ec_address": "/sys/kernel/debug/ec/ec0/io",
    "volume_threshold": 0.7,
    "record_wait_time": 2,
    "initial_record_wait_time": 4,
    "max_command_time": 10
}
```
- jako root uruchom plik "start_fc.sh"
- poczekaj na komunikat "nagrywanie komendy..."
## komendy
Komendy są definiowane w pliku "src/data/commands/commands.txt". W tej chwili wspierane:
```
ustaw target setting // ustawia wybrany wiatrak na wybraną wartość
manualnie // tryb ręcznego wpisywania komend
wyjście // wychodzi z aplikacji
```
Pierwsze słowo to komenda, kolejne nazwy argumentów. Możliwe wartości argumentów umieszczone są 
w odpowiednich plikach .txt w tym samym folderze. Dzięki tym informacjom wygenerowano wszystkie możliwe 
komendy w pliku "src/data/language/language.txt". Na jego podstawie generowany jest plik arpa. 
Pliki w folderze language są generowane przy starcie aplikacji, jeśli nie są już wygenerowane.

W zmockowanej aplikacji nie jest wspierane ustawienie "automatycznie" dla wiatraków.