#!/usr/bin/python3

'''
Implementation of Daniel van Flynn's blockchain introduction tutorial.
Source: https://hackernoon.com/learn-blockchains-by-building-one-117428612f46
'''

import hashlib
import json
from time import time
from urllib.parse import urlparse

import requests


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        #Seed block
        self.new_block(previous_hash=1, proof=100)


    def register_node(self, address):
        """
        Register a new node
        :param address: <str> Address of node, e.g.: 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)


    def valid_chain(self, chain):
        """
        Reach consensus on the authoratitive chain by using the longest valid one.
        :param chain: <list> A blockchain
        :return: <bool> True if valid, else False
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print('\n--------------\n')

            #Check the hash of block is valid
            if block['previous_hash'] != self.hash(last_block):
                return False
            #Check the proof of work is valid
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1
        return True

    
    def resolve_conflicts(self):
        """
        This is our consensus algo.
        It replaces our chain with the longest known one in the network.
        :return: <bool> True if the chain is replaced, else False
        """

        neighbors = self.nodes
        new_chain = None

        #only look for chains longer than our own
        max_length = len(self.chain)

        #get and verify all chains from all nodes
        for node in neighbors:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        
        if new_chain:
            self.chain = new_chain
            return True
        return False


    def new_block(self, proof, previous_hash=None):
        """
        Create a new block and add it to the chain
        :param proof: <int> Result from proof of work algo
        :param previous_hash: (Optional) <str> Hash of previous block
        :return: <dict> New block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        #Reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block


    def new_transaction(self, sender, recipient, amount):
        """
        Add a new transaction to the list of transactions
        :param sender: <str> Address of the sender
        :param recipient: <str> Address of the recipient
        :param amount: <int> Amount
        :return: <int> The index of the block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1


    @staticmethod
    def hash(block):
        """
        Create a SHA-256 hash of a block
        :param block: <dict> block
        :return: <str>
        """

        #If the <dict> block is not sorted it will produce unreliable hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


    @property
    def last_block(self):
        """Return the last block in the chain"""
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        Find a number p' such that hash(pp\') contains 4 leading zeros, where 
        p is the previous proof
        p' is the new proof
        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof


    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates that hash(last_proof, proof) contains 4 leading zeros
        :param last_proof: <int> Previous p
        :param proof: <int> Current p
        :return: <bool> True if there are 4 leading zeros, else False
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'
