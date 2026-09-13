import argparse
import random
import threading
import time
from collections import deque


class BufferCircular:
    def __init__(self, capacidade):
        self.capacidade = capacidade
        self.buffer = [None] * capacidade
        self.inicio = 0
        self.fim = 0
        self.qtd = 0
        self.lock = threading.Lock()
        self.nao_vazio = threading.Condition(self.lock)
        self.nao_cheio = threading.Condition(self.lock)

    def colocar(self, item):
        with self.nao_cheio:
            while self.qtd == self.capacidade:
                self.nao_cheio.wait()
            self.buffer[self.fim] = item
            self.fim = (self.fim + 1) % self.capacidade
            self.qtd += 1
            self.nao_vazio.notify()

    def retirar(self):
        with self.nao_vazio:
            while self.qtd == 0:
                self.nao_vazio.wait()
            item = self.buffer[self.inicio]
            self.inicio = (self.inicio + 1) % self.capacidade
            self.qtd -= 1
            self.nao_cheio.notify()
            return item


def experimento(capacidade, total_itens=600, produtores=3, consumidores=3, seed=123):
    buffer = BufferCircular(capacidade)
    contador = {"proximo": 0}
    contador_lock = threading.Lock()
    esperas = []
    esperas_lock = threading.Lock()
    consumidos = []
    consumidos_lock = threading.Lock()

    def produtor(pid):
        rng = random.Random(seed + pid)
        while True:
            with contador_lock:
                if contador["proximo"] >= total_itens:
                    return
                item_id = contador["proximo"]
                contador["proximo"] += 1
            time.sleep(rng.uniform(0.0005, 0.0020))
            t0 = time.perf_counter()
            buffer.colocar((item_id, time.perf_counter()))
            with esperas_lock:
                esperas.append(time.perf_counter() - t0)

    def consumidor(cid):
        rng = random.Random(seed + 100 + cid)
        while True:
            item = buffer.retirar()
            if item is None:
                return
            item_id, criado_em = item
            time.sleep(rng.uniform(0.0008, 0.0025))
            with consumidos_lock:
                consumidos.append((item_id, time.perf_counter() - criado_em))

    t0 = time.perf_counter()
    ts_prod = [threading.Thread(target=produtor, args=(i,)) for i in range(produtores)]
    ts_cons = [threading.Thread(target=consumidor, args=(i,)) for i in range(consumidores)]
    for t in ts_cons + ts_prod:
        t.start()
    for t in ts_prod:
        t.join()
    for _ in ts_cons:
        buffer.colocar(None)
    for t in ts_cons:
        t.join()
    elapsed = time.perf_counter() - t0

    assert len(consumidos) == total_itens
    assert len({x[0] for x in consumidos}) == total_itens
    throughput = total_itens / elapsed
    espera_media_ms = (sum(esperas) / len(esperas)) * 1000 if esperas else 0
    latencia_media_ms = (sum(x[1] for x in consumidos) / len(consumidos)) * 1000
    return elapsed, throughput, espera_media_ms, latencia_media_ms


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--buffers", type=int, nargs="*", default=[1, 5, 10, 20])
    parser.add_argument("--itens", type=int, default=600)
    args = parser.parse_known_args()[0]

    print("Buffer | Tempo(s) | Throughput(it/s) | Espera prod.(ms) | Latência item(ms)")
    print("-" * 76)
    for n in args.buffers:
        r = experimento(n, total_itens=args.itens)
        print(f"{n:6d} | {r[0]:8.4f} | {r[1]:16.2f} | {r[2]:16.3f} | {r[3]:16.3f}")
