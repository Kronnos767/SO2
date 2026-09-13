import threading
import time


def demonstrar_deadlock(timeout=0.4):
    """Cria um deadlock intencional e uma thread watchdog para detectá-lo."""
    recurso_a = threading.Lock()
    recurso_b = threading.Lock()

    estado_lock = threading.Lock()
    progresso = {"ultimo": time.perf_counter()}
    estado = {
        "T1": "iniciando",
        "T2": "iniciando",
        "A": "livre",
        "B": "livre",
    }

    parar_watchdog = threading.Event()
    deadlock_detectado = threading.Event()

    def registrar(chave, valor):
        with estado_lock:
            estado[chave] = valor
            progresso["ultimo"] = time.perf_counter()

    def t1():
        recurso_a.acquire()
        registrar("A", "possuído por T1")
        registrar("T1", "possui A; aguardará B")
        time.sleep(0.08)

        # A partir daqui T1 fica bloqueada caso T2 já possua B.
        recurso_b.acquire()
        try:
            registrar("B", "possuído por T1")
            registrar("T1", "possui A e B")
        finally:
            recurso_b.release()
            recurso_a.release()

    def t2():
        recurso_b.acquire()
        registrar("B", "possuído por T2")
        registrar("T2", "possui B; aguardará A")
        time.sleep(0.08)

        # A partir daqui T2 fica bloqueada caso T1 já possua A.
        recurso_a.acquire()
        try:
            registrar("A", "possuído por T2")
            registrar("T2", "possui B e A")
        finally:
            recurso_a.release()
            recurso_b.release()

    workers = [
        threading.Thread(target=t1, name="T1", daemon=True),
        threading.Thread(target=t2, name="T2", daemon=True),
    ]

    def watchdog():
        """Detecta ausência de progresso enquanto as workers continuam vivas."""
        while not parar_watchdog.is_set():
            time.sleep(0.05)
            with estado_lock:
                sem_progresso = time.perf_counter() - progresso["ultimo"]
                snapshot = dict(estado)

            if sem_progresso >= timeout and all(t.is_alive() for t in workers):
                print("[WATCHDOG] Ausência de progresso detectada.")
                print(f"  T1: {snapshot['T1']}")
                print(f"  T2: {snapshot['T2']}")
                print(f"  Recurso A: {snapshot['A']}")
                print(f"  Recurso B: {snapshot['B']}")
                print("  Suspeita: espera circular entre recursos A e B.")
                deadlock_detectado.set()
                return

    watchdog_thread = threading.Thread(target=watchdog, name="watchdog")

    for t in workers:
        t.start()
    watchdog_thread.start()

    # O watchdog deve terminar após detectar o deadlock. Os workers ficam
    # propositalmente bloqueados e são daemon para não impedir o encerramento.
    watchdog_thread.join(timeout=timeout + 1.0)
    parar_watchdog.set()

    return deadlock_detectado.is_set()


def executar_corrigido(iteracoes=100):
    """Corrige o problema impondo uma ordem total de aquisição de locks."""
    locks = [threading.Lock(), threading.Lock()]
    contador = {"n": 0}
    contador_lock = threading.Lock()

    def worker(ordem_original):
        for _ in range(iteracoes):
            # Independente da ordem solicitada, todos seguem 0 -> 1.
            ids = sorted(ordem_original)
            with locks[ids[0]]:
                with locks[ids[1]]:
                    with contador_lock:
                        contador["n"] += 1

    t1 = threading.Thread(target=worker, args=((0, 1),), name="T1-corrigida")
    t2 = threading.Thread(target=worker, args=((1, 0),), name="T2-corrigida")

    t0 = time.perf_counter()
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    elapsed = time.perf_counter() - t0

    assert contador["n"] == iteracoes * 2
    print(f"Versão corrigida: {contador['n']} regiões críticas concluídas em {elapsed:.6f}s.")
    print("Sem deadlock: todos os locks foram adquiridos na ordem total 0 -> 1.")


if __name__ == "__main__":
    print("=== Versão propositalmente sujeita a deadlock ===")
    detectado = demonstrar_deadlock()
    print(f"Watchdog detectou problema: {'SIM' if detectado else 'NÃO'}")

    print("\n=== Versão corrigida ===")
    executar_corrigido()
