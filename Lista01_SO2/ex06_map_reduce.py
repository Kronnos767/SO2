import argparse
import os
import threading
import time
from collections import Counter


def carregar(path):
    with open(path, "r", encoding="utf-8") as f:
        return [int(x) for x in f if x.strip()]


def map_reduce(numeros, p):
    n = len(numeros)
    resultados = [None] * p

    def worker(idx, ini, fim):
        bloco = numeros[ini:fim]
        resultados[idx] = (sum(bloco), Counter(bloco))

    threads = []
    t0 = time.perf_counter()
    for i in range(p):
        ini = i * n // p
        fim = (i + 1) * n // p
        t = threading.Thread(target=worker, args=(i, ini, fim))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    total = 0
    hist = Counter()
    for soma_local, hist_local in resultados:
        total += soma_local
        hist.update(hist_local)
    elapsed = time.perf_counter() - t0
    return total, hist, elapsed


if __name__ == "__main__":
    pa = argparse.ArgumentParser()
    pa.add_argument("--arquivo", default="dados/numeros.txt")
    pa.add_argument("--threads", type=int, nargs="*", default=[1, 2, 4, 8])
    a = pa.parse_known_args()[0]

    if not os.path.exists(a.arquivo):
        raise SystemExit(f"Arquivo não encontrado: {a.arquivo}. Execute gerar_dados.py primeiro.")
    numeros = carregar(a.arquivo)
    referencia_soma = sum(numeros)
    referencia_hist = Counter(numeros)
    medicoes = []

    for p in a.threads:
        total, hist, tempo = map_reduce(numeros, p)
        assert total == referencia_soma
        assert hist == referencia_hist
        medicoes.append((p, tempo))

    t1 = medicoes[0][1]
    print(f"Inteiros lidos: {len(numeros)}")
    print(f"Soma total: {referencia_soma}")
    print("P | Tempo(s) | Speedup")
    print("-" * 28)
    for p, tempo in medicoes:
        print(f"{p:1d} | {tempo:8.6f} | {t1/tempo:7.3f}")
    print("Histograma validado para todas as execuções.")
