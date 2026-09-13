import argparse
import random
import threading
import time


class Banco:
    def __init__(self, m, saldo_inicial=10_000):
        self.saldos = [saldo_inicial] * m
        self.locks = [threading.Lock() for _ in range(m)]

    def transferir_seguro(self, origem, destino, valor):
        a, b = sorted((origem, destino))
        with self.locks[a]:
            with self.locks[b]:
                if self.saldos[origem] >= valor:
                    self.saldos[origem] -= valor
                    self.saldos[destino] += valor

    def transferir_inseguro(self, origem, destino, valor):
        # Cópias + yields deliberados evidenciam lost update mesmo sob o GIL.
        so = self.saldos[origem]
        sd = self.saldos[destino]
        if so >= valor:
            time.sleep(0)
            self.saldos[origem] = so - valor
            time.sleep(0)
            self.saldos[destino] = sd + valor


def executar(m=10, t=8, operacoes=2000, seguro=True, seed=99):
    banco = Banco(m)
    soma_inicial = sum(banco.saldos)

    def worker(tid):
        rng = random.Random(seed + tid)
        for _ in range(operacoes):
            origem, destino = rng.sample(range(m), 2)
            valor = rng.randint(1, 50)
            if seguro:
                banco.transferir_seguro(origem, destino, valor)
            else:
                banco.transferir_inseguro(origem, destino, valor)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(t)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    soma_final = sum(banco.saldos)
    print(f"Modo: {'COM TRAVAS' if seguro else 'SEM TRAVAS'}")
    print(f"Soma inicial: {soma_inicial}")
    print(f"Soma final:   {soma_final}")
    print(f"Diferença:    {soma_final - soma_inicial}")
    if seguro:
        assert soma_final == soma_inicial, "Invariante monetária violada"
        print("ASSERT OK: soma global permaneceu constante.")
    else:
        print("Condição de corrida evidenciada." if soma_final != soma_inicial else
              "Nesta execução a soma coincidiu; repita para observar a corrida.")
    return soma_inicial, soma_final


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--modo", choices=["ambos", "seguro", "inseguro"], default="ambos")
    parser.add_argument("--contas", type=int, default=10)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--operacoes", type=int, default=2000)
    args = parser.parse_known_args()[0]

    if args.modo in ("ambos", "seguro"):
        executar(args.contas, args.threads, args.operacoes, True)
        print()
    if args.modo in ("ambos", "inseguro"):
        executar(args.contas, args.threads, args.operacoes, False)
