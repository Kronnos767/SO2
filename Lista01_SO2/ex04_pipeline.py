import argparse
import threading
import time
from collections import deque

POISON = object()


class FilaLimitada:
    def __init__(self, capacidade):
        self.capacidade = capacidade
        self.itens = deque()
        self.lock = threading.Lock()
        self.nao_vazia = threading.Condition(self.lock)
        self.nao_cheia = threading.Condition(self.lock)

    def put(self, item):
        with self.nao_cheia:
            while len(self.itens) >= self.capacidade:
                self.nao_cheia.wait()
            self.itens.append(item)
            self.nao_vazia.notify()

    def get(self):
        with self.nao_vazia:
            while not self.itens:
                self.nao_vazia.wait()
            item = self.itens.popleft()
            self.nao_cheia.notify()
            return item


def executar(n=100, capacidade=8):
    q1 = FilaLimitada(capacidade)
    q2 = FilaLimitada(capacidade)
    gravados = []

    def captura():
        for i in range(n):
            q1.put(i)
        q1.put(POISON)

    def processamento():
        while True:
            item = q1.get()
            if item is POISON:
                q2.put(POISON)
                return
            q2.put((item, item * item))

    def gravacao():
        while True:
            item = q2.get()
            if item is POISON:
                return
            gravados.append(item)

    t0 = time.perf_counter()
    threads = [threading.Thread(target=captura), threading.Thread(target=processamento), threading.Thread(target=gravacao)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - t0

    assert len(gravados) == n
    assert [x[0] for x in gravados] == list(range(n))
    assert all(v == i * i for i, v in gravados)
    print(f"Itens processados: {len(gravados)}/{n}")
    print(f"Tempo: {elapsed:.6f}s")
    print("Validação OK: nenhum item perdido, ordem preservada e encerramento limpo por poison pill.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--itens", type=int, default=100)
    p.add_argument("--capacidade", type=int, default=8)
    a = p.parse_known_args()[0]
    executar(a.itens, a.capacidade)
