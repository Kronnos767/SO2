import argparse
import random
import threading
import time


def simular(modo, duracao=1.5, n=5, seed=77):
    garfos = [threading.Lock() for _ in range(n)]
    limite = threading.Semaphore(4)
    stop = threading.Event()
    refeicoes = [0] * n
    maior_espera = [0.0] * n

    def filosofo(i):
        rng = random.Random(seed + i)
        esq, dir_ = i, (i + 1) % n
        while not stop.is_set():
            time.sleep(rng.uniform(0.0005, 0.002))
            inicio_espera = time.perf_counter()

            if modo == "ordem":
                primeiro, segundo = sorted((esq, dir_))
                with garfos[primeiro]:
                    with garfos[segundo]:
                        espera = time.perf_counter() - inicio_espera
                        maior_espera[i] = max(maior_espera[i], espera)
                        refeicoes[i] += 1
                        time.sleep(rng.uniform(0.0005, 0.0015))
            else:
                # Limita a quatro filósofos simultâneos e usa timeout/backoff para reduzir monopolização.
                with limite:
                    while not stop.is_set():
                        if garfos[esq].acquire(timeout=0.003):
                            if garfos[dir_].acquire(timeout=0.003):
                                try:
                                    espera = time.perf_counter() - inicio_espera
                                    maior_espera[i] = max(maior_espera[i], espera)
                                    refeicoes[i] += 1
                                    time.sleep(rng.uniform(0.0005, 0.0015))
                                finally:
                                    garfos[dir_].release()
                                    garfos[esq].release()
                                break
                            garfos[esq].release()
                        time.sleep(rng.uniform(0.0002, 0.0010))

    threads = [threading.Thread(target=filosofo, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    time.sleep(duracao)
    stop.set()
    for t in threads:
        t.join()

    assert all(x > 0 for x in refeicoes), "Possível starvation: algum filósofo não comeu"
    return refeicoes, maior_espera


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--duracao", type=float, default=1.5)
    a = p.parse_known_args()[0]
    for modo in ("ordem", "semaforo"):
        refeições, esperas = simular(modo, a.duracao)
        print(f"\nSolução: {'ordem global' if modo == 'ordem' else 'semáforo(4) + backoff'}")
        print("Filósofo | Refeições | Maior espera(ms)")
        for i, (r, e) in enumerate(zip(refeições, esperas)):
            print(f"{i:8d} | {r:9d} | {e*1000:15.3f}")
        print("Validação: todos os filósofos fizeram ao menos uma refeição.")
