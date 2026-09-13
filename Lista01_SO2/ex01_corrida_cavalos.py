import argparse
import random
import threading
import time


def executar_corrida(qtd_cavalos=4, chegada=100, aposta=None, seed=42):
    rngs = [random.Random(seed + i) for i in range(qtd_cavalos)]
    posicoes = [0] * qtd_cavalos
    cruzaram_na_rodada = []
    vencedor = {"id": None, "rodada": None}
    rodada = {"n": 0}

    lock = threading.Lock()
    largada = threading.Barrier(qtd_cavalos + 1)
    inicio_rodada = threading.Barrier(qtd_cavalos + 1)
    fim_rodada = threading.Barrier(qtd_cavalos + 1)
    encerrado = threading.Event()

    def cavalo(cid):
        largada.wait()
        while True:
            inicio_rodada.wait()
            if encerrado.is_set():
                break
            passo = rngs[cid].randint(5, 15)
            with lock:
                if posicoes[cid] < chegada:
                    posicoes[cid] = min(chegada, posicoes[cid] + passo)
                    if posicoes[cid] >= chegada:
                        cruzaram_na_rodada.append(cid)
            fim_rodada.wait()

    threads = [threading.Thread(target=cavalo, args=(i,), name=f"Cavalo-{i+1}") for i in range(qtd_cavalos)]
    for t in threads:
        t.start()

    print("=== CORRIDA DE CAVALOS ===")
    if aposta is None:
        aposta = int(input(f"Aposte em um cavalo (1-{qtd_cavalos}): "))
    print(f"Aposta: Cavalo {aposta}")
    print("Todos preparados. Largada sincronizada!")
    largada.wait()

    while vencedor["id"] is None:
        with lock:
            rodada["n"] += 1
            cruzaram_na_rodada.clear()
        inicio_rodada.wait()
        fim_rodada.wait()

        with lock:
            barra = " | ".join(f"C{i+1}:{posicoes[i]:3d}" for i in range(qtd_cavalos))
            print(f"Rodada {rodada['n']:02d}: {barra}")
            if cruzaram_na_rodada:
                # Empates na mesma rodada são resolvidos de forma determinística pelo menor ID.
                vencedor["id"] = min(cruzaram_na_rodada)
                vencedor["rodada"] = rodada["n"]

    encerrado.set()
    # Libera as threads que estão aguardando a próxima rodada para que terminem de forma limpa.
    inicio_rodada.wait()
    for t in threads:
        t.join()

    numero = vencedor["id"] + 1
    print(f"\nVencedor: Cavalo {numero} (rodada {vencedor['rodada']})")
    print("Aposta correta!" if aposta == numero else "Aposta incorreta.")
    return numero


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cavalos", type=int, default=4)
    parser.add_argument("--chegada", type=int, default=100)
    parser.add_argument("--aposta", type=int)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_known_args()[0]
    executar_corrida(args.cavalos, args.chegada, args.aposta, args.seed)
