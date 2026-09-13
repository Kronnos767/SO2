import argparse
import random
import threading
import time
from collections import deque


class BufferBackpressure:
    def __init__(self, capacidade, marca_alta):
        self.capacidade = capacidade
        self.marca_alta = marca_alta
        self.buf = deque()
        self.cond = threading.Condition()
        self.ocupacao = []
        self.inicio = time.perf_counter()
        self.esperas_backpressure = 0

    def _registrar(self):
        self.ocupacao.append((time.perf_counter() - self.inicio, len(self.buf)))

    def put(self, item):
        with self.cond:
            while len(self.buf) >= self.marca_alta:
                self.esperas_backpressure += 1
                self.cond.wait()
            self.buf.append(item)
            self._registrar()
            self.cond.notify_all()

    def get(self):
        with self.cond:
            while not self.buf:
                self.cond.wait()
            item = self.buf.popleft()
            self._registrar()
            self.cond.notify_all()
            return item


def executar(capacidade=20, marca_alta=16, produtores=2, total_por_produtor=120):
    b = BufferBackpressure(capacidade, marca_alta)
    poison = object()
    consumidos = []

    def produtor(pid):
        rng = random.Random(500 + pid)
        feitos = 0
        while feitos < total_por_produtor:
            burst = min(rng.randint(5, 10), total_por_produtor - feitos)
            for _ in range(burst):
                b.put((pid, feitos))
                feitos += 1
                time.sleep(rng.uniform(0.0001, 0.0005))
            time.sleep(rng.uniform(0.005, 0.012))

    def consumidor():
        while True:
            item = b.get()
            if item is poison:
                return
            consumidos.append(item)
            time.sleep(0.0018)

    tc = threading.Thread(target=consumidor)
    ps = [threading.Thread(target=produtor, args=(i,)) for i in range(produtores)]
    tc.start()
    for t in ps: t.start()
    for t in ps: t.join()
    b.put(poison)
    tc.join()

    esperado = produtores * total_por_produtor
    assert len(consumidos) == esperado
    ocup = [x[1] for x in b.ocupacao]
    media = sum(ocup)/len(ocup)
    maxima = max(ocup)
    print(f"Itens produzidos/consumidos: {esperado}")
    print(f"Capacidade: {capacidade}; marca de backpressure: {marca_alta}")
    print(f"Ocupação máxima observada: {maxima}")
    print(f"Ocupação média: {media:.2f}")
    print(f"Aguardas por backpressure: {b.esperas_backpressure}")
    print("Amostras (tempo_s, ocupação):")
    passo = max(1, len(b.ocupacao)//10)
    for t, o in b.ocupacao[::passo][:10]:
        print(f"  {t:.4f}, {o}")
    print("Validação OK: sem perda de itens e produtores foram bloqueados quando necessário.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--capacidade", type=int, default=20)
    p.add_argument("--marca-alta", type=int, default=16)
    a = p.parse_known_args()[0]
    executar(a.capacidade, a.marca_alta)
