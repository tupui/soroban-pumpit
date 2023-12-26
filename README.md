# Pumpit

A random project to play with IOT and Soroban (Stellar Smart Contract).

![Raspberry Pi diagram](doc/diagram.png)

## Raspberry Pi

### Hardware

I am using a Raspberry Pi Zero 2 W. BOM:

- Raspberry Pi Zero 2 W
- Water flow meter (+1x ... and +1x ... resistances)
- Button (+1x ... resistance)
- Green LED (+1x ... resistance)
- RED LED (+1x ... resistance)
- RGB LED (+3x ... resistance)

### Python service

After a classical headless setup of the Raspberry Pi, install everything:
```bash
ssh grogu@pumpit -i .ssh/raspberrypi_zero
sudo apt-get install libopenblas-dev
cd iot
python -m venv venv
source venv/bin/activate
pip install .
```

Then to run the service (depends on the Rust part):

```bash
python pumpit.py
```

## Soroban - Stellar Smart Contract

### Setup
Following the Soroban [doc](https://soroban.stellar.org/docs), we setup a
Soroban local environment and install all dependencies:
```bash
cd contract
make install
```

We create two accounts on testnet and add some funds (in XLM).

```bash
make prepare
```

We can check on the explorer our addresses:

https://testnet.steexp.com/account/

![Accounts on Stellar Explorer](doc/stellar_explorer_fund.png)

After our contract is written/tested/ready, we can build and upload it to
Soroban testnet:

```bash
make deploy
```

This will build the WASM file, upload it to Soroban and create the contract.
The last two operations are distinct transactions on the network, hence there
are 2 fees associated to it (at the time of writing, around 100k stroop.)

![Upload contract and see in Stellar Explorer](doc/stellar_explorer_contract_create.png)

Now we can interact with our contract!

### Init contract

```bash

```
make init_contract