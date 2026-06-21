"""Скрипт для тренировки генетического оптимизатора и сохранения лучших весов в data/"""
import argparse
import os
from genetic import GeneticOptimizer
from game_config import DATA_DIR


def main():
    parser = argparse.ArgumentParser(description='Train GA to evolve heuristic weights')
    parser.add_argument('--generations', '-g', type=int, default=10)
    parser.add_argument('--population', '-p', type=int, default=40)
    parser.add_argument('--sims', '-s', type=int, default=5, help='Simulations per chromosome evaluation (increase for quality)')
    parser.add_argument('--moves', '-m', type=int, default=80, help='Moves per simulation')
    parser.add_argument('--out', '-o', type=str, default=os.path.join(DATA_DIR, 'best_ga_weights.json'))
    args = parser.parse_args()

    print(f"Train GA: gens={args.generations}, pop={args.population}, sims={args.sims}, moves={args.moves}")

    opt = GeneticOptimizer(population_size=args.population)
    for gen in range(1, args.generations + 1):
        print(f"Generation {gen}/{args.generations} -> evaluating population...")
        opt.step(sims=args.sims, moves_per_sim=args.moves)
        best_chrom, best_score = opt.best()
        print(f"  Best score: {best_score:.2f}")
        # save intermediate best
        try:
            opt.save(args.out)
            print(f"  Saved best to {args.out}")
        except Exception as e:
            print(f"  Failed to save: {e}")

    print("Training finished.")


if __name__ == '__main__':
    main()
