# Laboratório 01 — Exercícios sobre Sistemas Operacionais 2

**Aluno:** Guilherme Emanuel Oliveira Guimaraes  
**Disciplina:** Sistemas Operacionais 2  
**Linguagem utilizada:** Python 3  

## 1. Objetivo

Este repositório apresenta a resolução dos 10 exercícios da Lista 01 de Sistemas Operacionais 2. O objetivo é demonstrar, por meio de programas executáveis, conceitos de concorrência e sincronização com threads: exclusão mútua, variáveis de condição, semáforos, barreiras, filas concorrentes, condições de corrida, deadlock, watchdog, backpressure e processamento paralelo.

Foram utilizados apenas módulos da biblioteca padrão do Python. Os principais mecanismos usados foram:

- `threading.Thread` para criação das threads;
- `threading.Lock` para exclusão mútua;
- `threading.Condition` para espera bloqueante, sem espera ativa;
- `threading.Semaphore` para limitar concorrência;
- `threading.Barrier` para sincronização de fases;
- `queue.Queue` para fila concorrente thread-safe.

Os resultados mostrados neste relatório foram obtidos executando os próprios programas do repositório. Valores de tempo podem variar entre máquinas e entre execuções por causa do escalonamento das threads.

---

## 2. Exercício 1 — Corrida de cavalos

**Arquivo:** `ex01_corrida_cavalos.py`

### Implementação

Cada cavalo é representado por uma `Thread`. Antes da corrida, o usuário informa sua aposta. Uma `Barrier` garante que todos os cavalos estejam prontos antes da largada.

A corrida é dividida em rodadas. Em cada rodada, cada cavalo avança um número pseudoaleatório de posições. O placar compartilhado é protegido por `Lock`, impedindo alterações concorrentes inconsistentes.

Para evitar condição de corrida no registro do primeiro colocado, todos os cavalos concluem a rodada antes da escolha do vencedor. Se dois ou mais cruzarem a linha de chegada na mesma rodada, o desempate é determinístico: vence o cavalo de menor identificador.

### Execução

```bash
python ex01_corrida_cavalos.py --aposta 1
```

Sem `--aposta`, o programa solicita a aposta pelo teclado.

### Resultado observado

```text
Rodada 09: C1: 79 | C2: 90 | C3: 83 | C4: 77
Rodada 10: C1: 92 | C2:100 | C3: 91 | C4: 89

Vencedor: Cavalo 2 (rodada 10)
Aposta incorreta.
```

A largada foi sincronizada, o placar foi atualizado de forma protegida e apenas um vencedor foi registrado.

---

## 3. Exercício 2 — Buffer circular com produtores e consumidores

**Arquivo:** `ex02_produtor_consumidor.py`

### Implementação

Foi implementado um buffer circular de tamanho `N`. O buffer mantém índices de entrada e saída, quantidade de elementos e um vetor circular.

O acesso ao estado compartilhado é protegido por `Lock`. Foram usadas duas variáveis de condição:

- `nao_vazio`: consumidores aguardam quando o buffer está vazio;
- `nao_cheio`: produtores aguardam quando o buffer está cheio.

A espera é bloqueante, portanto não há espera ativa.

O programa mede:

- tempo total;
- throughput em itens por segundo;
- tempo médio de espera do produtor;
- latência média dos itens.

### Execução

```bash
python ex02_produtor_consumidor.py
```

### Experimento observado

| Tamanho do buffer | Tempo (s) | Throughput (it/s) | Espera do produtor (ms) | Latência do item (ms) |
|---:|---:|---:|---:|---:|
| 1 | 0.3561 | 1684.96 | 0.438 | 2.680 |
| 5 | 0.3621 | 1656.80 | 0.402 | 4.989 |
| 10 | 0.3553 | 1688.61 | 0.393 | 7.699 |
| 20 | 0.3584 | 1674.18 | 0.384 | 13.103 |

### Análise

Nesta execução, aumentar o buffer reduziu levemente a espera média dos produtores, porque havia mais espaço disponível antes de eles precisarem bloquear. Em contrapartida, a latência média dos itens aumentou, pois eles puderam permanecer mais tempo aguardando no buffer. O throughput permaneceu próximo entre as quatro configurações.

---

## 4. Exercício 3 — Transferências bancárias e condições de corrida

**Arquivo:** `ex03_transferencias.py`

### Implementação

São criadas `M` contas e `T` threads. Cada thread realiza transferências aleatórias entre contas.

Na versão correta existe um `Lock` para cada conta. Para impedir deadlock, as duas travas envolvidas na transferência são sempre adquiridas em ordem crescente de identificador.

Ao final da execução protegida, a soma global é validada com uma asserção:

```python
assert soma_final == soma_inicial
```

A versão incorreta não utiliza travas. Pequenas trocas de contexto são inseridas entre leitura e escrita para tornar atualizações perdidas (`lost updates`) observáveis.

### Execução

```bash
python ex03_transferencias.py
```

### Resultado observado

```text
Modo: COM TRAVAS
Soma inicial: 100000
Soma final:   100000
Diferença:    0
ASSERT OK: soma global permaneceu constante.

Modo: SEM TRAVAS
Soma inicial: 100000
Soma final:   113529
Diferença:    13529
Condição de corrida evidenciada.
```

### Análise

Com exclusão mútua, a quantidade total de dinheiro permaneceu constante. Sem travas, atualizações concorrentes sobrescreveram outras atualizações, violando a invariante global e evidenciando uma condição de corrida.

---

## 5. Exercício 4 — Pipeline com captura, processamento e gravação

**Arquivo:** `ex04_pipeline.py`

### Implementação

Foram criadas três threads:

1. **captura** — produz os itens;
2. **processamento** — recebe cada item e calcula seu quadrado;
3. **gravação** — registra os resultados.

Os estágios são conectados por duas filas limitadas implementadas com `deque`, `Lock` e `Condition`.

O encerramento utiliza uma **poison pill**. A captura envia o marcador especial ao terminar; o processamento reconhece o marcador e o repassa à segunda fila; a gravação encerra quando recebe o marcador.

### Execução

```bash
python ex04_pipeline.py
```

### Resultado observado

```text
Itens processados: 100/100
Validação OK: nenhum item perdido, ordem preservada e encerramento limpo por poison pill.
```

O programa contém asserções que verificam quantidade, ordem e conteúdo dos itens. As três threads terminam normalmente após o protocolo de encerramento, demonstrando ausência de deadlock e perda de itens.

---

## 6. Exercício 5 — Pool fixo de threads

**Arquivo:** `ex05_thread_pool.py`

### Implementação

Foi criado um pool fixo com `N` workers. As tarefas são armazenadas em `queue.Queue`, que fornece operações thread-safe para inserção e retirada.

Cada tarefa recebe um inteiro e executa um teste de primalidade, que funciona como tarefa CPU-bound. No modo normal, os números são lidos da entrada padrão até EOF.

Os resultados são armazenados em um dicionário protegido por `Lock`. Ao final, uma poison pill é enviada para cada worker para encerrar o pool de forma limpa.

Uma asserção confirma que o número de resultados é exatamente igual ao número de tarefas enviadas.

### Execução pela entrada padrão

Linux/macOS:

```bash
printf "13\n20\n29\n" | python ex05_thread_pool.py --threads 3
```

No Windows também é possível digitar os valores manualmente e finalizar com `Ctrl+Z` seguido de `Enter`.

### Resultado observado

```text
13: primo
20: não primo
29: primo
Tarefas concluídas: 3/3
Validação OK: nenhuma tarefa foi perdida.
```

Para demonstração rápida também existe:

```bash
python ex05_thread_pool.py --demo
```

A execução de demonstração processou 10 de 10 tarefas sem perda.

---

## 7. Exercício 6 — Soma e histograma com Map/Reduce

**Arquivos:**

- `gerar_dados.py` — gera o arquivo de inteiros;
- `ex06_map_reduce.py` — executa o processamento paralelo.

### Implementação

O arquivo de teste contém 200.000 inteiros. O vetor lido é dividido em `P` blocos. Cada thread executa localmente:

- soma dos valores do bloco;
- histograma local usando `Counter`.

Cada thread escreve apenas na sua própria posição do vetor de resultados, evitando disputa por uma estrutura global durante o `map`.

Depois de `join()`, a thread principal realiza o `reduce`: soma os resultados locais e combina os histogramas. Assim, não é necessário manter um `Lock` global durante o processamento dos blocos, o que reduz a exclusão mútua ao mínimo.

### Execução

```bash
python gerar_dados.py
python ex06_map_reduce.py
```

### Resultado observado

Foram processados **200.000 inteiros**, com soma total de **9.884.192**.

| P | Tempo (s) | Speedup |
|---:|---:|---:|
| 1 | 0.008049 | 1.000 |
| 2 | 0.008547 | 0.942 |
| 4 | 0.007136 | 1.128 |
| 8 | 0.007059 | 1.140 |

O speedup é calculado por:

```text
S(P) = T(1) / T(P)
```

### Análise

Nesta execução, 4 e 8 threads apresentaram pequeno ganho em relação a uma thread, enquanto 2 threads foram um pouco mais lentas. Em CPython, tarefas CPU-bound podem ser limitadas pelo GIL e pelo overhead de criação e sincronização de threads, portanto o aumento de `P` não garante crescimento proporcional de desempenho.

As somas e os histogramas de todas as execuções foram comparados com uma referência sequencial por asserções.

---

## 8. Exercício 7 — Problema dos filósofos

**Arquivo:** `ex07_filosofos.py`

Cada garfo é representado por um `Lock`.

### Solução A — Ordem global de aquisição

Cada filósofo sempre adquire primeiro o garfo de menor ID e depois o de maior ID. Como todos obedecem à mesma ordem, não se forma um ciclo de espera entre recursos e o deadlock é evitado.

### Solução B — Semáforo de quatro filósofos

Foi utilizado:

```python
threading.Semaphore(4)
```

Assim, no máximo quatro filósofos podem disputar garfos simultaneamente.

Também foi utilizado `timeout` ao tentar adquirir garfos e um pequeno backoff aleatório. Caso o segundo garfo não seja obtido, o primeiro é liberado e o filósofo tenta novamente depois. Essa estratégia diminui monopolização de recursos e ajuda a mitigar starvation.

### Execução

```bash
python ex07_filosofos.py
```

### Resultado observado — ordem global

| Filósofo | Refeições | Maior espera (ms) |
|---:|---:|---:|
| 0 | 435 | 13.943 |
| 1 | 453 | 3.014 |
| 2 | 469 | 3.390 |
| 3 | 484 | 2.285 |
| 4 | 439 | 4.363 |

### Resultado observado — semáforo(4) + backoff

| Filósofo | Refeições | Maior espera (ms) |
|---:|---:|---:|
| 0 | 476 | 4.511 |
| 1 | 475 | 3.811 |
| 2 | 473 | 4.745 |
| 3 | 469 | 4.438 |
| 4 | 473 | 9.080 |

Todos os filósofos realizaram refeições nas duas estratégias. O programa verifica isso por asserção para identificar uma possível starvation extrema.

---

## 9. Exercício 8 — Bursts, ociosidade e backpressure

**Arquivo:** `ex08_backpressure.py`

### Implementação

Os produtores geram itens em rajadas aleatórias de 5 a 10 itens e depois entram em pequenos períodos de ociosidade. O consumidor trabalha em uma taxa inferior, fazendo a ocupação do buffer crescer durante os bursts.

O buffer possui capacidade física 20, mas uma marca alta de 16. Quando a ocupação atinge essa marca, os produtores aguardam por uma `Condition`. Eles só continuam quando o consumidor reduz a ocupação. Isso implementa backpressure.

Cada inserção e retirada registra a ocupação do buffer ao longo do tempo.

### Execução

```bash
python ex08_backpressure.py
```

### Resultado observado

```text
Itens produzidos/consumidos: 240
Capacidade: 20; marca de backpressure: 16
Ocupação máxima observada: 16
Ocupação média: 14.74
Aguardas por backpressure: 283
Validação OK: sem perda de itens e produtores foram bloqueados quando necessário.
```

### Análise

A ocupação máxima não ultrapassou a marca de backpressure. Isso mostra que, quando a produção passou a superar a capacidade de consumo, os produtores foram bloqueados em vez de continuar preenchendo indefinidamente o buffer. Todos os 240 itens foram consumidos.

---

## 10. Exercício 9 — Corrida de revezamento com barreira

**Arquivo:** `ex09_revezamento.py`

### Implementação

Para cada configuração são criadas `K` threads. Em cada rodada, todas executam sua etapa e chamam `Barrier.wait()`. A próxima rodada só é liberada depois que todos os integrantes alcançam a barreira.

A `Barrier` possui uma ação executada quando o último integrante chega, incrementando o número de rodadas concluídas.

O programa executa 20 rodadas e calcula a taxa equivalente de rodadas por minuto para diferentes tamanhos de equipe.

### Execução

```bash
python ex09_revezamento.py
```

### Resultado observado

| K threads | Tempo para 20 rodadas (s) | Rodadas/min |
|---:|---:|---:|
| 2 | 0.0628 | 19109.80 |
| 4 | 0.0697 | 17227.11 |
| 8 | 0.0787 | 15249.84 |

### Análise

A taxa diminuiu à medida que a equipe ficou maior. Isso ocorre porque cada rodada depende da chegada de todos os integrantes: a barreira precisa aguardar a thread mais lenta antes de liberar a próxima rodada.

---

## 11. Exercício 10 — Deadlock e thread watchdog

**Arquivo:** `ex10_deadlock_watchdog.py`

### Cenário propositalmente incorreto

Foram criados dois recursos, `A` e `B`, e duas threads:

- `T1` adquire `A` e depois tenta adquirir `B`;
- `T2` adquire `B` e depois tenta adquirir `A`.

Quando as duas chegam nessa situação, surge uma espera circular.

Também foi criada uma terceira thread chamada **watchdog**. Ela acompanha o instante do último progresso do sistema. Se as duas workers continuam vivas e nenhuma mudança ocorre por determinado tempo, o watchdog informa as threads e os recursos suspeitos.

### Resultado observado

```text
[WATCHDOG] Ausência de progresso detectada.
  T1: possui A; aguardará B
  T2: possui B; aguardará A
  Recurso A: possuído por T1
  Recurso B: possuído por T2
  Suspeita: espera circular entre recursos A e B.
Watchdog detectou problema: SIM
```

### Correção

Na versão corrigida foi imposta uma ordem total de travamento:

```text
Lock 0 -> Lock 1
```

Mesmo quando uma thread recebe os recursos na ordem inversa, ela os ordena antes da aquisição. Dessa forma, todas seguem a mesma ordem e a espera circular deixa de ser possível.

### Resultado da versão corrigida

```text
Versão corrigida: 200 regiões críticas concluídas.
Sem deadlock: todos os locks foram adquiridos na ordem total 0 -> 1.
```

---

## 12. Conclusão

Os 10 exercícios foram implementados e executados. Os experimentos demonstraram:

- sincronização de largada e fases com `Barrier`;
- exclusão mútua com `Lock`;
- espera bloqueante com `Condition`;
- limitação de concorrência com `Semaphore`;
- filas concorrentes e encerramento com poison pill;
- condições de corrida na ausência de sincronização;
- preservação de invariantes por asserções;
- processamento no modelo map/reduce;
- prevenção de deadlock por ordem global de aquisição;
- detecção de ausência de progresso por uma thread watchdog;
- backpressure em cenários com rajadas de produção;
- comparação de desempenho com diferentes quantidades de threads.

As saídas completas utilizadas como evidência das execuções estão armazenadas na pasta `resultados/`.
