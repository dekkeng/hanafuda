import asyncio
import json
import time
from web3 import Web3
import aiohttp
import argparse

RPC_URL = "https://mainnet.base.org"
CONTRACT_ADDRESS = "0xC5bf05cD32a14BFfb705Fb37a9d218895187376c"
api_url = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"
AMOUNT_ETH = 0.0000000001  # Amount of ETH to be deposited
GROW_INTERVAL=600 # Amount of seconds to run grow again
web3 = Web3(Web3.HTTPProvider(RPC_URL))

with open("prvkey.txt", "r") as file:
    private_keys = [line.strip() for line in file if line.strip()]

with open("rtoken.txt", "r") as file:
    access_tokens = [line.strip() for line in file if line.strip()]

contract_abi = '''
[
    {
        "constant": false,
        "inputs": [],
        "name": "depositETH",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]
'''

amount_wei = web3.to_wei(AMOUNT_ETH, 'ether')
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=json.loads(contract_abi))

nonces = {key: web3.eth.get_transaction_count(web3.eth.account.from_key(key).address) for key in private_keys}

headers = {
    'Accept': '*/*',
    'Content-Type': 'application/json',
    'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
}

async def colay(session, url, method, payload_data=None):
    async with session.request(method, url, headers=headers, json=payload_data) as response:
        if response.status != 200:
            raise Exception(f'HTTP error! Status: {response.status}')
        return await response.json()

async def refresh_access_token(session, refresh_token):
    api_key = "AIzaSyDipzN0VRfTPnMGhQ5PSzO27Cxm3DohJGY"  
    async with session.post(
        f'https://securetoken.googleapis.com/v1/token?key={api_key}',
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f'grant_type=refresh_token&refresh_token={refresh_token}'
    ) as response:
        if response.status != 200:
            raise Exception("Failed to refresh access token")
        data = await response.json()
        return data.get('access_token')


async def handle_grow_and_garden(session, refresh_token):  
    new_access_token = await refresh_access_token(session, refresh_token)
    headers['authorization'] = f'Bearer {new_access_token}'

    info_query = {
        "query": "query getCurrentUser { "
                  "currentUser { id totalPoint depositCount } "
                  "getGardenForCurrentUser { "
                  "gardenStatus { growActionCount gardenRewardActionCount } "
                  "} "
                  "}",
        "operationName": "getCurrentUser"
    }
    info = await colay(session, api_url, 'POST', info_query)
    
    balance = info['data']['currentUser']['totalPoint']
    deposit = info['data']['currentUser']['depositCount']
    grow = info['data']['getGardenForCurrentUser']['gardenStatus']['growActionCount']
    garden = info['data']['getGardenForCurrentUser']['gardenStatus']['gardenRewardActionCount']

    print(f"POINTS: {balance} | Deposit Counts: {deposit} | Grow left: {grow} | Garden left: {garden}")

    async def grow_action():
        grow_action_query = {
              "query": """
                  mutation executeGrowAction {
                      executeGrowAction(withAll: true) {
                          totalValue
                          multiplyRate
                      }
                      executeSnsShare(actionType: GROW, snsType: X) {
                          bonus
                      }
                  }
              """,
              "operationName": "executeGrowAction"
          }

                        
        try:
            mine = await colay(session, api_url, 'POST', grow_action_query)            
            
            if mine and 'data' in mine and 'executeGrowAction' in mine['data']:
                reward = mine['data']['executeGrowAction']['totalValue']
                return reward
            else:
                print(f"Error: Unexpected response format: {mine}")
                return 0  
        except Exception as e:
            return 0

    if grow > 0:
        
        reward = await grow_action()

        if reward:            
            balance += reward
            grow = 0
            print(f"Rewards: {reward} | Balance: {balance} | Grow left: {grow}")
              
        
    while garden >= 10:
        garden_action_query = {
            "query": "mutation executeGardenRewardAction($limit: Int!) { executeGardenRewardAction(limit: $limit) { data { cardId group } isNew } }",
            "variables": {"limit": 10},
            "operationName": "executeGardenRewardAction"
        }
        mine_garden = await colay(session, api_url, 'POST', garden_action_query)
        card_ids = [item['data']['cardId'] for item in mine_garden['data']['executeGardenRewardAction']]
        print(f"Opened Garden: {card_ids}")
        garden -= 10


async def handle_eth_transactions(session, num_transactions):
    global nonces
    for i in range(num_transactions):
        for private_key in private_keys:
            from_address = web3.eth.account.from_key(private_key).address
            short_from_address = from_address[:4] + "..." + from_address[-4:]

            try:
                transaction = contract.functions.depositETH().build_transaction({
                    'from': from_address,
                    'value': amount_wei,
                    'gas': 100000,
                    'gasPrice': web3.eth.gas_price,
                    'nonce': nonces[private_key],
                })

                signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
                tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                print(f"Transaction {i + 1} sent from {short_from_address} with hash: {tx_hash.hex()}")

                nonces[private_key] += 1
                await asyncio.sleep(1)  

            except Exception as e:
                if 'nonce too low' in str(e):
                    print(f"Nonce too low for {short_from_address}. Fetching the latest nonce...")
                    nonces[private_key] = web3.eth.get_transaction_count(from_address)
                else:
                    print(f"Error sending transaction from {short_from_address}: {str(e)}")

async def main(mode, num_transactions=None):
    async with aiohttp.ClientSession() as session:
        if mode == '1':
            if num_transactions is None:
                num_transactions = int(input("Enter the number of transactions to be executed: "))
            await handle_eth_transactions(session, num_transactions)
        elif mode == '2':
            while True:
                
                for refresh_token in access_tokens:
                    try:
                        await handle_grow_and_garden(session, refresh_token)  
                    except Exception as e:
                        print(f"Error grow: {str(e)}")
                        
                    print(f"All accounts have been processed. Cooling down for 10 minutes...")
                    
                time.sleep(GROW_INTERVAL)  
        else:
            print("Invalid option. Please choose either 1 or 2.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Choose the mode of operation.')
    parser.add_argument('-a', '--action', choices=['1', '2'], help='1: Execute Transactions, 2: Grow and Garden')
    parser.add_argument('-tx', '--transactions', type=int, help='Number of transactions to execute (optional for action 1)')

    args = parser.parse_args()

    if args.action is None:
        args.action = input("Choose action (1: Execute Transactions, 2: Grow and Garden): ")
        while args.action not in ['1', '2']:
            print("Invalid choice. Please select either 1 or 2.")
            args.action = input("Choose action (1: Execute Transactions, 2: Grow and Garden): ")
   
    asyncio.run(main(args.action, args.transactions))
