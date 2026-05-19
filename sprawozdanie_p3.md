# Sprawozdanie P3 - Evolutionary Computations (PyGAD)

## Autorzy
- Mateusz Bobula
- Norbert Dziwak
- Jakub Konopka

## 1. Cel projektu
Celem tej czesci projektu jest optymalizacja funkcji testowej z wykorzystaniem
biblioteki PyGAD w jezyku Python. Zachowano funkcje celu uzywana w P1 i P2,
czyli `Hypersphere`.

Funkcja celu:

![Wzor funkcji Hypersphere](wzor.png)

Minimum globalne funkcji znajduje sie w punkcie `(0, ..., 0)`, a wartosc funkcji
w minimum wynosi `0`.

## 2. Implementacja
Nowa implementacja znajduje sie w plikach:

- `src/algorithms/pygad_algorithm.py` - konfiguracja, dekodowanie osobnikow,
  funkcja fitness, uruchamianie PyGAD oraz budowanie zestawu eksperymentow.
- `src/reporting/pygad_result_files.py` - zapis wynikow, historii i wykresow.
- `src/run_pygad_experiments.py` - skrypt uruchamiajacy wszystkie testowane
  konfiguracje.

Poniewaz PyGAD maksymalizuje fitness, a problem jest problemem minimalizacji,
zastosowano transformacje:

```python
fitness = 1.0 / (objective_value + epsilon)
```

W historii eksperymentu zapisywane sa jednak oryginalne wartosci funkcji celu,
czyli `f(x)`, a nie odwrocony fitness PyGAD.

## 3. Reprezentacje osobnikow
Przetestowano dwie reprezentacje.

### Reprezentacja binarna
- `gene_type = int`
- `init_range_low = 0`
- `init_range_high = 2`
- `gene_space = [0, 1]`
- domyslnie `60` bitow, czyli `3` zmienne po `20` bitow

Kazde `20` bitow jest dekodowane do jednej zmiennej rzeczywistej z przedzialu
`[-5, 5]`.

### Reprezentacja rzeczywista
- `gene_type = float`
- liczba genow rowna liczbie wymiarow funkcji
- wartosci genow sa ograniczone do przedzialu `[-5, 5]`

Ten wariant nie wymaga dekodowania bitowego, bo osobnik jest bezposrednio
wektorem argumentow funkcji celu.

## 4. Testowane konfiguracje
Testowane metody selekcji:

| Nazwa w raporcie | Nazwa w PyGAD |
| --- | --- |
| turniejowa | `tournament` |
| kolo ruletki | `rws` |
| losowa | `random` |

Testowane metody krzyzowania:

| Nazwa w raporcie | Nazwa w PyGAD |
| --- | --- |
| jednopunktowe | `single_point` |
| dwupunktowe | `two_points` |
| jednorodne | `uniform` |

Testowane metody mutacji:

| Nazwa w raporcie | Nazwa w PyGAD |
| --- | --- |
| losowa | `random` |
| zamiana indeksow | `swap` |

Dodatkowo zaimplementowano:

- wlasne krzyzowanie jednopunktowe `custom_single_point`,
- mutacje Gaussa `gaussian` dla reprezentacji rzeczywistej.

## 5. Uruchamianie eksperymentow
Eksperymenty uruchamia komenda:

```bash
uv run .\src\run_pygad_experiments.py
```

Skrypt tworzy katalog:

```text
results/pygad_suite_*
```

W katalogu zbiorczym znajduja sie:

- `suite_summary.csv` - tabela wynikow wszystkich konfiguracji,
- `suite_summary.md` - gotowa tabela Markdown do sprawozdania.

Dla kazdego pojedynczego przebiegu zapisywane sa:

- `summary.json` - konfiguracja i najlepszy wynik,
- `history.csv` - historia `best`, `average`, `std`, `min`, `max`,
- `objective_stats.svg` - wykres wartosci funkcji celu, sredniej i odchylenia
  standardowego.

## 6. Porownanie konfiguracji
Obliczenia wykonano dla konfiguracji:

| Parametr | Wartosc |
| --- | --- |
| funkcja | Hypersphere |
| dimensions | 3 |
| domain | [-5, 5] |
| binary bits | 3 x 20 = 60 |
| num_generations | 100 |
| sol_per_pop | 80 |
| num_parents_mating | 50 |
| mutation_num_genes | 1 |
| keep_elitism | 1 |
| K_tournament | 3 |
| seed | 2026 |

Pelna tabela wynikow znajduje sie w pliku:

```text
results/pygad_suite_20260519_082533_058395/suite_summary.md
```

Najlepsze konfiguracje z calej serii:

| # | representation | selection | crossover | mutation | best f(x) | avg last | std last |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | binary | tournament | two_points | random | 6.82122e-11 | 1.57192 | 4.91018 |
| 2 | binary | rws | single_point | random | 6.82122e-11 | 1.38911 | 4.86317 |
| 3 | binary | rws | two_points | random | 6.82122e-11 | 1.38911 | 4.86317 |
| 4 | binary | rws | uniform | random | 6.82122e-11 | 1.38911 | 4.86317 |
| 5 | binary | tournament | custom_single_point | random | 2.50112e-10 | 1.39316 | 4.85970 |
| 6 | binary | tournament | single_point | random | 7.95809e-10 | 1.45158 | 4.85530 |
| 7 | binary | tournament | uniform | random | 1.15961e-09 | 1.43395 | 4.85904 |
| 8 | binary | rws | uniform | swap | 5.44675e-07 | 0.728026 | 3.06000 |
| 9 | real | rws | two_points | gaussian | 2.12568e-06 | 1.10412 | 1.74584 |
| 10 | real | rws | single_point | gaussian | 3.11006e-06 | 1.10396 | 1.74523 |

Najlepsze wyniki w podziale na reprezentacje:

| Reprezentacja | Najlepsza konfiguracja | best f(x) |
| --- | --- | ---: |
| binary | tournament + two_points + random | 6.82122e-11 |
| real | rws + two_points + gaussian | 2.12568e-06 |

## 7. Wnioski do analizy
Reprezentacja binarna pozwala kontrolowac dokladnosc przez liczbe bitow na
wymiar, ale tworzy dluzszy chromosom. Dla konfiguracji domyslnej sa to `60`
genow, wiec operatory dzialaja na dlugim ciagu bitow.

Reprezentacja rzeczywista ma krotszy chromosom, bo dla trzech wymiarow zawiera
tylko `3` geny. Zwykle powinna szybciej zblizac sie do optimum dla funkcji
ciaglych takich jak Hypersphere, szczegolnie przy mutacji Gaussa.

Selekcja turniejowa ma wyzsza presje selekcyjna niz losowa, wiec zwykle szybciej
poprawia wynik, ale moze tez szybciej ograniczac roznorodnosc populacji. `rws`
jest posrednia, bo wybor zalezy od proporcji fitness osobnikow. Selekcja losowa
jest dobrym punktem odniesienia, ale zwykle powinna dawac slabsze wyniki.

Krzyzowanie jednorodne miesza geny najmocniej, natomiast jedno- i dwupunktowe
lepiej zachowuja sasiednie fragmenty chromosomu. Dla reprezentacji binarnej moze
to miec wieksze znaczenie niz dla rzeczywistej, bo fragment bitow wspoltworzy
jedna dekodowana zmienna.

Mutacja `random` wprowadza nowe wartosci, dlatego lepiej wspiera eksploracje.
Mutacja `swap` tylko zamienia pozycje genow, wiec nie tworzy nowych wartosci.
Dla funkcji symetrycznej takiej jak Hypersphere moze byc mniej szkodliwa niz dla
funkcji niesymetrycznych, ale nadal ma mniejsza zdolnosc do lokalnej poprawy.

W wykonanej serii najlepsze wyniki uzyskala reprezentacja binarna z mutacja
`random`. Najlepsze konfiguracje binarne zeszly do wartosci okolo `6.82e-11`,
czyli bardzo blisko minimum globalnego.

Dla reprezentacji rzeczywistej najlepsza okazala sie konfiguracja `rws +
two_points + gaussian`, z wynikiem `2.13e-06`. Mutacja Gaussa byla tu lepsza od
losowej w najlepszych przebiegach rzeczywistych, bo wykonywala mniejsze,
lokalne poprawki zamiast losowego skoku po calym przedziale.

Mutacja `swap` w reprezentacji rzeczywistej czesto prowadzila do bardzo malego
odchylenia standardowego w ostatniej populacji. Oznacza to szybka utrate
roznorodnosci, poniewaz operator tylko zamienia kolejnosc genow i nie tworzy
nowych wartosci.

Selekcja losowa byla wyraznie slabsza od `tournament` i `rws`. Najlepszy wynik
dla losowej selekcji byl gorszy o kilka rzedow wielkosci od najlepszych
konfiguracji binarnych oraz od najlepszej konfiguracji rzeczywistej z mutacja
Gaussa.

## 8. Uwaga wykonawcza
W docelowym srodowisku projektowym zalecane uruchomienie to:

```bash
uv run .\src\run_pygad_experiments.py --seed 2026
```

Podczas przygotowania raportu `uv` nie bylo dostepne w `PATH`, dlatego
obliczenia zostaly uruchomione bezposrednio przez lokalne polecenie `python` po
doinstalowaniu bibliotek `pygad` i `benchmark-functions`.
