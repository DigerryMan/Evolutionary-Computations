# Sprawozdanie P4 - Evolutionary Computations (MealPy / PSO)

## Autorzy
- Mateusz Bobula
- Norbert Dziwak
- Jakub Konopka

## 1. Cel projektu
Celem projektu jest optymalizacja tej samej funkcji testowej co w P1-P3,
wykorzystujac biblioteke MealPy oraz wybrany algorytm PSO (Particle Swarm
Optimization). Pozwala to na bezposrednie porownanie wynikow z poprzednimi
projektami.

## 2. Funkcja testowa
Uzyta funkcja: `Hypersphere`.

![Wzor funkcji Hypersphere](wzor.png)

Wlasciwosci:
- Minimum globalne znajduje sie w punkcie (0, ..., 0).
- Wartosc funkcji w minimum wynosi 0.
- Funkcja jest separowalna i wypukla.

## 3. Wybrany algorytm: PSO
PSO modeluje populacje czastek (particles), ktore poruszaja sie w przestrzeni
rozwiazan. Kazda czastka ma:
- pozycje x (kandydat rozwiazania),
- predkosc v,
- najlepsza lokalna pozycje pbest,
- najlepsza pozycje globalna gbest.

Aktualizacja w kolejnej iteracji:

v_i(t+1) = w * v_i(t) + c1 * r1 * (pbest_i - x_i(t)) + c2 * r2 * (gbest - x_i(t))

x_i(t+1) = x_i(t) + v_i(t+1)

Parametry:
- w: inercja (balans eksploracji i eksploatacji),
- c1, c2: wagi skladowych poznawczej i spolecznej,
- r1, r2: losowe wartosci z (0, 1).

W MealPy problem jest ustawiony jako minimalizacja (minmax="min"),
wiec wartosc funkcji celu jest uzywana bezposrednio.

## 4. Implementacja
Nowe elementy projektu:
- src/algorithms/mealpy_algorithm.py - konfiguracja PSO, uruchamianie MealPy,
  pobieranie najlepszego wyniku i historii.
- src/reporting/mealpy_result_files.py - zapis wynikow (summary.json,
  history.csv, objective_history.svg) oraz podsumowanie suite.
- src/run_mealpy_experiments.py - skrypt uruchamiajacy serie konfiguracji.

## 5. Konfiguracja eksperymentow
Bazowa konfiguracja:
- function: Hypersphere
- dimensions: 3
- domain: [-5, 5]
- epochs: 100
- pop_size: 80
- w: 0.7
- c1 = c2 = 1.5
- seed: brak (losowe uruchomienia)

W ramach eksperymentu wykonano sweep:
- w: 0.4, 0.7, 0.9
- c1 = c2: 1.2, 1.8, 2.4
- pop_size: 40, 80, 120

Uruchomienie:

```bash
uv run .\src\run_mealpy_experiments.py
```

## 6. Wyniki (MealPy PSO)
Pelne zestawienie: results/mealpy_suite_20260519_160016_301207/suite_summary.md

Najlepsze konfiguracje z zestawu:

| # | w | c1 | c2 | pop | best f(x) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.4 | 1.5 | 1.5 | 80 | 1.53286e-35 |
| 2 | 0.7 | 1.2 | 1.2 | 80 | 1.19559e-15 |
| 3 | 0.7 | 1.5 | 1.5 | 120 | 2.9218e-14 |
| 4 | 0.7 | 1.5 | 1.5 | 40 | 9.99359e-13 |
| 5 | 0.7 | 1.5 | 1.5 | 80 | 4.16173e-12 |

Przyklad wykresu z najlepszego przebiegu:

![MealPy PSO best run](results/mealpy_suite_20260519_160016_301207/002_pso_w0p4_c11p5_c21p5_pop80/objective_history.svg)

## 7. Porownanie z poprzednimi projektami
Najlepsze wyniki z dotychczasowych raportow:

| Projekt | Algorytm | Najlepsza konfiguracja | best f(x) |
| --- | --- | --- | ---: |
| P1 | GA (binary) | population 500 | 2.66e-13 |
| P2 | GA (real) | blend_alpha + uniform | 1.32e-16 |
| P3 | PyGAD | binary + tournament + two_points + random | 6.82122e-11 |
| P4 | MealPy | PSO, w=0.4, c1=c2=1.5, pop=80 | 1.53286e-35 |

## 8. Wnioski
- PSO w MealPy szybko zbiega do bardzo malych wartosci funkcji celu.
- Niska inercja (w=0.4) dala najlepszy wynik w tej serii.
- Zbyt wysoka inercja (w=0.9) oraz duze wspolczynniki c1/c2 pogarszaly jakosc.
- W porownaniu z P1-P3, PSO osiagnelo najnizsze wartosci f(x) dla Hypersphere.
