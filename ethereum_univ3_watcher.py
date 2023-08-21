import asyncio
import brownie
import itertools
import json
import os
import sys
import web3
import websockets


BROWNIE_NETWORK = "mainnet-local-ws"
WEBSOCKET_URI = "ws://localhost:8546"
ETHERSCAN_API_KEY = "[edit me]"

# Create a reusable web3 object (no arguments to WebsocketProvider
# will default to localhost on the default port)
w3 = web3.Web3(web3.WebsocketProvider())

os.environ["ETHERSCAN_TOKEN"] = ETHERSCAN_API_KEY

try:
    brownie.network.connect(BROWNIE_NETWORK)
except:
    sys.exit(
        "Could not connect! Verify your Brownie network settings using 'brownie networks list'"
    )

async def watch_pending_transactions():

    v3_routers = {
        "0xE592427A0AEce92De3Edee1F18E0157C05861564": {
            "name": "UniswapV3: Router"
        },
        "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45": {
            "name": "UniswapV3: Router 2"
        },
    }

    for router_address in v3_routers.keys():
        try:
            router_contract = brownie.Contract(
                router_address
            )
        except:
            router_contract = brownie.Contract.from_explorer(
                router_address
            )
        else:
            v3_routers[router_address]["abi"] = router_contract.abi
            v3_routers[router_address]["web3_contract"] = w3.eth.contract(
                address=router_address,
                abi=router_contract.abi,
            )

        try:
            factory_address = w3.toChecksumAddress(router_contract.factory())
            factory_contract = brownie.Contract(factory_address)
        except:
            factory_contract = brownie.Contract.from_explorer(factory_address)
        else:
            v3_routers[router_address]["factory_address"] = factory_address
            v3_routers[router_address]["factory_contract"] = factory_contract

    print("Starting pending TX watcher loop")

    async for websocket in websockets.connect(uri=WEBSOCKET_URI):

        try:
            await websocket.send(
                json.dumps(
                    {
                        "id": 1,
                        "method": "eth_subscribe",
                        "params": ["newPendingTransactions"],
                    }
                )
            )
        except websockets.WebSocketException:
            print("(pending_transactions) reconnecting...")
            continue
        except Exception as e:
            print(e)
            continue
        else:
            subscribe_result = json.loads(await websocket.recv())
            print(subscribe_result)

        while True:

            try:
                message = json.loads(await websocket.recv())
            except websockets.WebSocketException as e:
                print("(pending_transactions inner) reconnecting...")
                print(e)
                break  # escape the loop to reconnect
            except Exception as e:
                print(e)
                break

            try:
                pending_tx = dict(
                    w3.eth.get_transaction(
                        message.get("params").get("result")
                    )
                )
            except:
                # ignore any transaction that cannot be found
                continue

            # skip post-processing unless the TX was sent to
            # an address on our watchlist
            if pending_tx.get("to") not in v3_routers.keys():
                continue
            else:
                try:
                    # decode the TX using the ABI
                    decoded_tx = (
                        v3_routers.get(
                            w3.toChecksumAddress(pending_tx.get("to"))
                        )
                        .get("web3_contract")
                        .decode_function_input(pending_tx.get("input"))
                    )
                except Exception as e:
                    continue
                else:
                    func, func_args = decoded_tx

            print(f'func: {func.fn_name}')
            print(f'args: {func_args}')


asyncio.run(watch_pending_transactions())
