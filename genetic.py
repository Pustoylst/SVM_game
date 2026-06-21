"""Простая реализация генетического алгоритма для эволюции весов эвристики ходов"""
import random
import json
import math
from copy import deepcopy
from game_logic import GameBoard


def default_chromosome(n=6):
    # Набор весов: вес за длину совпадения, центровая предвзятость, вес для потенциальных падений, разношерстные коэффициенты
    return [random.uniform(-1.0, 1.0) for _ in range(n)]


def evaluate_chromosome(chromosome, sims=10, moves_per_sim=80):
    """Оценить хромосому: запустить несколько симуляций и вернуть средний набранных очков (damage суммарно)."""
    total_score = 0.0
    for _ in range(sims):
        board = GameBoard()
        score = 0
        for _ in range(moves_per_sim):
            # Найти лучший ход по эвристике
            best_move = None
            best_value = -1e18
            for y in range(len(board.grid)):
                for x in range(len(board.grid[0])):
                    for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                        ny, nx = y+dy, x+dx
                        if 0 <= ny < len(board.grid) and 0 <= nx < len(board.grid[0]):
                            board.swap_blocks((y,x),(ny,nx))
                            matches = board.find_matches()
                            value = heuristic_value(board, matches, chromosome)
                            board.swap_blocks((y,x),(ny,nx))
                            if value > best_value:
                                best_value = value
                                best_move = ((y,x),(ny,nx))
            if best_move is None:
                # No moves - regenerate
                board.create_grid()
                continue
            # Apply move
            board.swap_blocks(best_move[0], best_move[1])
            matches = board.find_matches()
            if matches:
                removed = board.remove_matches(matches)
                dmg = board.calculate_damage(len(matches))
                score += dmg
                board.collapse_grid()
            else:
                # Penalize for wasted move
                score -= 5
        total_score += score
    return total_score / sims


def heuristic_value(board, matches, chromosome):
    """Простая эвристика: учитывает длину совпадения, количество совпадений, близость к центру и потенциальные падения."""
    if not matches:
        # оценивать пустой ход как -inf
        return -1e9
    # weight mapping
    w_len = chromosome[0] if len(chromosome) > 0 else 1.0
    w_count = chromosome[1] if len(chromosome) > 1 else 0.5
    w_center = chromosome[2] if len(chromosome) > 2 else 0.1
    w_fall = chromosome[3] if len(chromosome) > 3 else 0.2
    # compute metrics
    match_len = len(matches)
    count = len(set(matches))
    # center: prefer matches closer to center of board
    rows = len(board.grid)
    cols = len(board.grid[0]) if rows>0 else rows
    center_r = rows/2
    center_c = cols/2
    avg_r = sum(p[0] for p in matches)/len(matches)
    avg_c = sum(p[1] for p in matches)/len(matches)
    center_dist = math.hypot(avg_r-center_r, avg_c-center_c)
    center_score = -center_dist
    # fall heuristic: naive estimate - how many new empty cells will appear in columns
    fall_potential = 0
    cols_with_matches = set(p[1] for p in matches)
    for c in cols_with_matches:
        # count how many non-matching tiles above matched tiles
        for r in range(rows):
            if board.grid[r][c] == -1:
                continue
            # if any matched tile below, count
            if any(r2 > r and r2 < rows and (r2, c) in matches for r2 in range(r+1, rows)):
                fall_potential += 1
    # combine
    value = (w_len * match_len) + (w_count * count) + (w_center * center_score) + (w_fall * fall_potential)
    return value


class GeneticOptimizer:
    def __init__(self, population_size=40, chromosome_size=6, elitism=2, mutation_rate=0.08):
        self.population_size = population_size
        self.chromosome_size = chromosome_size
        self.elitism = elitism
        self.mutation_rate = mutation_rate
        self.population = [default_chromosome(chromosome_size) for _ in range(population_size)]
        self.scores = [None]*population_size

    def evaluate_population(self, sims=5, moves_per_sim=80):
        for i, chrom in enumerate(self.population):
            self.scores[i] = evaluate_chromosome(chrom, sims=sims, moves_per_sim=moves_per_sim)

    def select_parent(self):
        # tournament selection
        a, b = random.sample(range(self.population_size), 3), random.sample(range(self.population_size), 3)
        ia = min(a, key=lambda i: - (self.scores[i] if self.scores[i] is not None else -1e9))
        ib = min(b, key=lambda i: - (self.scores[i] if self.scores[i] is not None else -1e9))
        return deepcopy(self.population[ia if self.scores[ia] >= self.scores[ib] else ib])

    def crossover(self, a, b):
        # one-point crossover
        if len(a) != len(b):
            return deepcopy(a), deepcopy(b)
        pt = random.randint(1, len(a)-1)
        child1 = a[:pt] + b[pt:]
        child2 = b[:pt] + a[pt:]
        return child1, child2

    def mutate(self, chrom):
        for i in range(len(chrom)):
            if random.random() < self.mutation_rate:
                chrom[i] += random.uniform(-0.3, 0.3)
        return chrom

    def step(self, sims=3, moves_per_sim=80):
        # Ensure scores are computed
        self.evaluate_population(sims=sims, moves_per_sim=moves_per_sim)
        paired = sorted(list(range(self.population_size)), key=lambda i: -(self.scores[i] if self.scores[i] is not None else -1e9))
        new_pop = []
        # elitism
        for i in range(self.elitism):
            new_pop.append(deepcopy(self.population[paired[i]]))
        # fill rest
        while len(new_pop) < self.population_size:
            p1 = self.select_parent()
            p2 = self.select_parent()
            c1, c2 = self.crossover(p1, p2)
            c1 = self.mutate(c1)
            c2 = self.mutate(c2)
            new_pop.append(c1)
            if len(new_pop) < self.population_size:
                new_pop.append(c2)
        self.population = new_pop
        self.scores = [None]*self.population_size

    def best(self):
        # evaluate if necessary
        if any(s is None for s in self.scores):
            self.evaluate_population(sims=3)
        best_idx = max(range(self.population_size), key=lambda i: self.scores[i])
        return deepcopy(self.population[best_idx]), self.scores[best_idx]

    def save(self, path):
        best_chrom, best_score = self.best()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'chromosome': best_chrom, 'score': best_score}, f, ensure_ascii=False, indent=2)

    def load(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('chromosome'), data.get('score')
