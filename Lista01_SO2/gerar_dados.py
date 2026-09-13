import argparse
import random

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--saida", default="dados/numeros.txt")
    p.add_argument("--quantidade", type=int, default=200_000)
    p.add_argument("--seed", type=int, default=2026)
    a = p.parse_known_args()[0]
    rng = random.Random(a.seed)
    with open(a.saida, "w", encoding="utf-8") as f:
        for _ in range(a.quantidade):
            f.write(f"{rng.randint(0, 99)}\n")
    print(f"Gerados {a.quantidade} inteiros em {a.saida}")
