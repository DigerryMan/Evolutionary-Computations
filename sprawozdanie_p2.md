# Sprawozdanie P2 - Evolutionary Computations (real encoding)

## Autorzy
- Mateusz Bobula
- Norbert Dziwak
- Jakub Konopka

## 1. Technologie uzyte w projekcie
- Python 3.12+
- PyQt6
- benchmark-functions (Hypersphere)
- ruff
- uv

## 2. Wymagania srodowiskowe
- Python 3.12
- venv z zaleznosciami z pyproject.toml
- uv

Uruchomienie: uv run .\src\main.py

## 3. Porownanie wynikow P1 vs P2 (czas i best_fitness)
P1 (binarna reprezentacja, domyslny config z raportu P1):

| Przebieg | best_fitness | elapsed_seconds |
| --- | ---: | ---: |
| Tournament | 2.60e-05 | 0.12 |
| Best | 4.90e-06 | 0.10 |
| Roulette | 4.63e-06 | 0.11 |
| Population 500 (dodatkowe) | 2.66e-13 | 1.56 |

P2 (reprezentacja rzeczywista, domyslne parametry, tylko zmiana operatorow):

| Przebieg (crossover/mutation) | best_fitness | elapsed_seconds |
| --- | ---: | ---: |
| arithmetic + uniform | 1.27e-01 | 0.028 |
| linear + uniform | 9.41e-10 | 0.041 |
| blend_alpha + uniform | 1.32e-16 | 0.031 |
| blend_alpha_beta + uniform | 2.26e-05 | 0.031 |
| averaging + uniform | 2.54e-04 | 0.027 |
| arithmetic + gaussian | 1.99e-02 | 0.028 |

Wnioski:
- Najlepszy wynik w P2 dal blend_alpha + uniform (1.32e-16) i byl lepszy od wynikow P1 przy krotszym czasie.
- P2 bylo wyraznie szybsze od P1 przy podobnej liczbie epok, ale innej reprezentacji.
- Zmiana operatora w P2 mocno zmienia dokladnosc, bez istotnego wplywu na czas.
- Mutacja Gaussa (dla arithmetic) dala lepszy wynik niz uniform, bo wprowadza mniejsze, ciagle poprawki zamiast losowego skoku w caly zakres.

## 4. Wykres zaleznosci wartosci funkcji celu od iteracji
Wybrany przebieg P2 - blend_alpha + uniform:

![Fitness history - blend_alpha](results/hypersphere_20260512_182359_blend_alpha/fitness_history.svg)
