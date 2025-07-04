# DCC P2P Blockchain Chat

**Integrantes:**
* Vitor Moreira Ramos de Rezende
* Iago da Silva Rodrigues Alves

---

## Resumo do Projeto
Este trabalho prático implementa um sistema de chat distribuído P2P. O sistema utiliza um mecanismo de consenso inspirado em blockchain para garantir a integridade e a ordem do histórico de mensagens compartilhadas entre os nós da rede. Toda a aplicação foi desenvolvida em **Python**, com uso intensivo da biblioteca `asyncio` para gerenciar conexões de rede concorrentes de forma assíncrona.

---

## Arquitetura do Sistema
Cada nó da rede P2P opera de forma independente, executando uma instância da classe `P2PNode`. A comunicação entre os pares é feita via **TCP** através de um protocolo binário customizado. A classe `P2PNode` é o núcleo da aplicação e é responsável por gerenciar:
* A tabela de pares (`peers`) conectados.
* O histórico de chats (`chats`), que funciona como a blockchain do sistema.
* A lógica assíncrona para enviar, receber e processar mensagens.
* O servidor que escuta por novas conexões de entrada.

O script principal `main.py` é responsável por iniciar o nó, configurar seu endereço IP e, opcionalmente, conectá-lo a um nó de *bootstrap* para ingressar na rede. Que nesse caso foi um servidor disponibilizado pelo professor.

---

## Funcionalidades Principais

### 1. Descoberta e Gerenciamento de Pares
- **Bootstrap**: Um nó pode se conectar a um par previamente conhecido (servidor do professor) para obter uma lista de outros nós ativos na rede.
- **Requisições Periódicas**: O nó envia mensagens `PeerRequest` a cada 5 segundos para seus pares conhecidos, a fim de manter sua lista de pares atualizada e identificar nós ativos.
- **Conexões Assíncronas**: O `asyncio` é usado para estabelecer e gerenciar múltiplas conexões TCP simultaneamente, sem a necessidade de múltiplas threads.

### 2. Sincronização de Histórico (Blockchain)
- **Requisição de Arquivo**: Ao se conectar a um novo par, um nó envia uma mensagem `ArchiveRequest` para solicitar o histórico completo de chats.
- **Validação e Adoção**: Ao receber um histórico (`ArchiveResponse`), o nó realiza uma verificação completa de sua integridade. Se o histórico for válido e mais longo que o seu atual, ele é adotado como a nova cadeia canônica.

### 3. Verificação de Histórico (Proof-of-Work)
- A integridade da blockchain é garantida por uma cadeia de hashes **MD5**. Um histórico é considerado válido se, para cada chat, as seguintes condições forem satisfeitas recursivamente:
    - O hash MD5 do último chat na sequência deve começar com **dois bytes nulos** (`0x0000`).
    - Este hash deve ser o resultado do cálculo do MD5 sobre a concatenação dos últimos 20 chats (ou menos, se o histórico for menor), excluindo o campo do próprio hash.
- Esta regra cria um mecanismo de **prova de trabalho (Proof-of-Work)**, onde adicionar um novo chat requer esforço computacional. A verificação é implementada na função `verification_check`.

### 4. Mineração e Envio de Chats
- **Mineração**: Para adicionar um novo chat, um nó deve "minerar" um `código de verificação` (um valor aleatório de 16 bytes). O processo consiste em um loop que gera códigos e calcula o hash MD5 da nova cadeia até que um hash válido (começando com `0x0000`) seja encontrado.
- **Propagação**: Uma vez que um novo chat é minerado e adicionado com sucesso ao seu histórico local, o nó propaga o novo histórico (maior) para todos os seus pares enviando uma mensagem `ArchiveResponse`.

---

## Protocolo de Mensagens
As mensagens trocadas entre os nós seguem um protocolo binário customizado, onde os campos são empacotados usando o módulo `struct` do Python em *network byte order* (big-endian).

* **PeerRequest (`0x01`)**:
    * Nenhum campo adicional. Usada para solicitar a lista de pares.

* **PeerList (`0x02`)**:
    * `count`: Número de pares na lista (inteiro de 4 bytes).
    * `peers`: Uma sequência de endereços IP (4 bytes cada).

* **ArchiveRequest (`0x03`)**:
    * Nenhum campo adicional. Usada para solicitar o histórico de chats.

* **ArchiveResponse (`0x04`)**:
    * `count`: Número de chats no histórico (inteiro de 4 bytes).
    * `chats`: Uma sequência de estruturas de chat.
        * **Estrutura de um Chat**:
            * `length`: Comprimento da mensagem de texto (inteiro de 1 byte).
            * `text`: Mensagem em ASCII (N bytes).
            * `verification_code`: Código minerado (16 bytes).
            * `md5`: Hash MD5 do bloco (16 bytes).

---

## Desafios e Soluções Adotadas

### 1. Gerenciamento de Concorrência
* **Desafio:** Lidar com múltiplas conexões de rede simultâneas (envio, recebimento e escuta) de forma eficiente e sem conflitos.
* **Solução:** Adoção do **`asyncio`**. Em vez de gerenciar threads complexas e locks, um único loop de eventos trata todas as operações de I/O de forma não-bloqueante. O uso de `asyncio.Lock` garante o acesso seguro a estruturas de dados compartilhadas (como a lista de pares e o histórico), prevenindo *race conditions*.

### 2. Implementação do Proof-of-Work
* **Desafio:** Integrar um processo computacionalmente intensivo (mineração) em uma aplicação assíncrona sem bloquear o loop de eventos, o que congelaria toda a comunicação de rede.
* **Solução:** A função de mineração (`put_chat_in_queue`) implementa um loop síncrono que serve como uma prova de conceito funcional do algoritmo de mineração.

### 3. Conectividade em Redes com NAT
* **Desafio:** Nós em redes domésticas geralmente estão atrás de um NAT, o que impede que recebam conexões de entrada diretamente, dificultando a formação de uma rede P2P totalmente conectada.
* **Solução:** Nosso código reconhece essa limitação. A estratégia é garantir que os nós possam iniciar conexões de saída (para o *bootstrap*) e que a execução para testes de recepção ocorra em ambientes sem NAT conforme recomendado na especificação do trabalho.

---

## Testes Realizados
Os testes foram focados em validar os principais componentes do sistema em um ambiente de rede local:
* **Conexão e Descoberta**: Inicialização de um nó e sua conexão a um nó de *bootstrap* para receber a lista de pares.
* **Sincronização de Histórico**: Verificação de que um novo nó solicita e adota corretamente o histórico de chats mais longo e válido da rede.
* **Validação da Blockchain**: Testes unitários na função `verification_check` para garantir que históricos válidos são aceitos e inválidos são rejeitados.
* **Mineração e Propagação**: Execução do processo de mineração para adicionar um novo chat e observação de sua propagação para outros nós na rede local.
* **Estabilidade**: Simulação com múltiplos nós locais (`127.0.0.1`, `127.0.0.2`, etc.) para verificar a estabilidade das conexões e a consistência do estado distribuído.

---

## Conclusão
O desenvolvimento deste projeto proporcionou uma compreensão prática e aprofundada sobre o funcionamento de redes P2P, programação assíncrona e os princípios fundamentais de tecnologias blockchain, como o consenso por prova de trabalho. A implementação de um protocolo binário customizado, o gerenciamento do estado distribuído e os desafios inerentes à concorrência e mineração solidificaram conceitos teóricos de redes de computadores e sistemas distribuídos, resultando em uma experiência de aprendizado completa e desafiadora.

---

## Execução do Projeto
Para executar um nó, utilize o seguinte comando no terminal:

```bash
python main.py <MEU_IP> [BOOTSTRAP_IP]