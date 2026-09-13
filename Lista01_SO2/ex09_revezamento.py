import argparse
import random
import threading
import time


def medir(k, rodadas=20, seed=900):
    completas = {"n": 0}
    lock = threading.Lock()

    def terminou_rodada():
        with lock:
            completas["n"] += 1

    barreira = threading.Barrier(k, action=terminou_rodada)

    def atleta(i):
        rng = random.Random(seed + i)
        for _ in range(rodadas):
            time.sleep(rng.uniform(0.001, 0.004))
            barreira.wait()

    ts = [threading.Thread(target=atleta, args=(i,)) for i in range(k)]
    t0 = time.perf_counter()
    for t in ts: t.start()
    for t in ts: t.join()
    elapsed = time.perf_counter() - t0
    assert completas["n"] == rodadas
    rpm = rodadas / elapsed * 60
    return elapsed, rpm


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--equipes", type=int, nargs="*", default=[2, 4, 8])
    p.add_argument("--rodadas", type=int, default=20)
    a = p.parse_known_args()[0]
    print("K threads | Tempo(s) | Rodadas/min")
    print("-" * 38)
    for k in a.equipes:
        e, rpm = medir(k, a.rodadas)
        print(f"{k:9d} | {e:8.4f} | {rpm:11.2f}")
