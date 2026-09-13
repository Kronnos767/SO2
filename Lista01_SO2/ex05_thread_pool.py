import argparse
import math
import queue
import sys
import threading

POISON = object()


def eh_primo(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    limite = int(math.isqrt(n))
    for d in range(3, limite + 1, 2):
        if n % d == 0:
            return False
    return True


class ThreadPool:
    def __init__(self, n):
        self.fila = queue.Queue()
        self.resultados = {}
        self.lock = threading.Lock()
        self.threads = [threading.Thread(target=self.worker, name=f"worker-{i}") for i in range(n)]
        for t in self.threads:
            t.start()

    def worker(self):
        while True:
            tarefa = self.fila.get()
            try:
                if tarefa is POISON:
                    return
                tid, numero = tarefa
                resultado = eh_primo(numero)
                with self.lock:
                    self.resultados[tid] = (numero, resultado)
            finally:
                self.fila.task_done()

    def submit(self, tid, numero):
        self.fila.put((tid, numero))

    def fechar(self):
        self.fila.join()
        for _ in self.threads:
            self.fila.put(POISON)
        self.fila.join()
        for t in self.threads:
            t.join()


def executar(n_workers=4, demo=False):
    if demo:
        numeros = [2, 17, 18, 97, 1009, 1024, 7919, 99991, 99999, 104729]
    else:
        print("Digite inteiros, um por linha. Finalize com EOF (Ctrl+D no Linux/macOS ou Ctrl+Z+Enter no Windows).", file=sys.stderr)
        numeros = [int(l.strip()) for l in sys.stdin if l.strip()]

    pool = ThreadPool(n_workers)
    for i, n in enumerate(numeros):
        pool.submit(i, n)
    pool.fechar()

    assert len(pool.resultados) == len(numeros)
    for i in range(len(numeros)):
        n, r = pool.resultados[i]
        print(f"{n}: {'primo' if r else 'não primo'}")
    print(f"Tarefas concluídas: {len(pool.resultados)}/{len(numeros)}")
    print("Validação OK: nenhuma tarefa foi perdida.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--threads", type=int, default=4)
    p.add_argument("--demo", action="store_true")
    a = p.parse_known_args()[0]
    executar(a.threads, a.demo)
