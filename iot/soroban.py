"""Helper function to call the Soroban Contract

Based on
https://github.com/StellarCN/py-stellar-base/blob/main/examples/soroban_payment.py
"""
import time

from stellar_sdk import Keypair, Network, SorobanServer, TransactionBuilder, scval
from stellar_sdk import xdr as stellar_xdr
from stellar_sdk.exceptions import PrepareTransactionException
from stellar_sdk.soroban_rpc import GetTransactionStatus, SendTransactionStatus

rpc_server_url = "https://soroban-testnet.stellar.org:443"
soroban_server = SorobanServer(rpc_server_url)
network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE


def soroban_claim(secret_key: str, contract_id: str, level: int):
    address_kp = Keypair.from_secret(secret_key)
    address_source = soroban_server.load_account(address_kp.public_key)

    args = [
        # claimant
        scval.to_address(address_kp.public_key),
        # pumping_level
        scval.to_int128(level),
    ]

    tx = (
        TransactionBuilder(address_source, network_passphrase, base_fee=500)
        .add_time_bounds(0, 0)
        .append_invoke_contract_function_op(
            contract_id=contract_id,
            function_name="claim",
            parameters=args,
        )
        .build()
    )

    try:
        tx = soroban_server.prepare_transaction(tx)
    except PrepareTransactionException as e:
        print(f"Got exception: {e.simulate_transaction_response}")
        raise e

    tx.sign(address_kp)
    print(f"Signed XDR:\n{tx.to_xdr()}")

    send_transaction_data = soroban_server.send_transaction(tx)
    print(f"sent transaction: {send_transaction_data}")
    if send_transaction_data.status != SendTransactionStatus.PENDING:
        raise Exception("send transaction failed")
    while True:
        print("waiting for transaction to be confirmed...")
        get_transaction_data = soroban_server.get_transaction(send_transaction_data.hash)
        if get_transaction_data.status != GetTransactionStatus.NOT_FOUND:
            break
        time.sleep(3)

    print(f"transaction: {get_transaction_data}")

    if get_transaction_data.status == GetTransactionStatus.SUCCESS:
        assert get_transaction_data.result_meta_xdr is not None
        transaction_meta = stellar_xdr.TransactionMeta.from_xdr(
            get_transaction_data.result_meta_xdr
        )
        if transaction_meta.v3.soroban_meta.return_value.type == stellar_xdr.SCValType.SCV_VOID:  # type: ignore[union-attr]
            print("send success")
    else:
        print(f"Transaction failed: {get_transaction_data.result_xdr}")
