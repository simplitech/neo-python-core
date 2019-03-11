
from itertools import groupby
from datetime import datetime

import pytz
from events import Events
from neocore import Settings

from neocore.Core.Block import Block
from collections import Counter
from functools import lru_cache

from neocore.Services.BlockchainService import BlockchainService, NodeService


class Blockchain:
    _instance = None

    def __init__(self, blockchainService : BlockchainService, nodeService : NodeService):
        self.blockchainServices = blockchainService
        self.nodeServices = nodeService
        self.PersistCompleted = Events()
        self.Notify = Events()

    def Pause(self):
        self.paused = True

    def Resume(self):
        self.paused = False

    def OnNotify(self, notification):
        self.Notify.on_change(notification)

    def OnPersistCompleted(self, block):
        self.PersistCompleted.on_change(block)

    def StandbyValidators(self):
        return self.blockchainServices.StandbyValidators()

    @lru_cache(maxsize=2)
    def SystemShare(self):
        return self.blockchainServices.SystemShare()

    @lru_cache(maxsize=2)
    def SystemCoin(self):
        return self.blockchainServices.SystemCoin()

    def GenesisBlock(self) -> Block:
        return self.blockchainServices.GenesisBlock()

    def GetAccountState(self, address):
        return self.blockchainServices.GetAccountState(address)

    def GetHeaderHash(self, height):
        return self.blockchainServices.GetHeaderHash(height)

    def GetBlockByHeight(self, height):
        return self.blockchainServices.GetBlockByHeight(height)

    def GetBlock(self, height_or_hash):
        return self.blockchainServices.GetBlock(height_or_hash)

    def GetBlockByHash(self, hash):
        return self.blockchainServices.GetBlockByHash(hash)

    def GetBlockHash(self, index):
        return self.blockchainServices.GetBlockHash(index)

    def GetSpentCoins(self, tx_hash):
        return self.blockchainServices.GetSpentCoins(tx_hash)

    def GetAssetState(self, assetId):
        return self.blockchainServices.GetAssetState(assetId)

    def GetContract(self, hash):
        return self.blockchainServices.GetContract(hash)


    def GetHeaderByHeight(self, height):
        return self.blockchainServices.GetHeaderByHeight(height)

    def GetConsensusAddress(self, validators):
        return self.blockchainServices.GetConsensusAddress(validators)

    def GetScript(self, script_hash):
        return self.blockchainServices.GetContract(script_hash)

    def GetStorageItem(self, storage_key):
        return self.blockchainServices.GetContract(storage_key)

    def GetSysFeeAmount(self, hash):
        return self.blockchainServices.GetSysFeeAmount(hash)

    def GetSysFeeAmountByHeight(self, height):
        return self.blockchainServices.GetSysFeeAmountByHeight(height)

    def GetTransaction(self, hash):
        return self.blockchainServices.GetTransaction(hash)

    def GetUnclaimed(self, hash):
        return self.blockchainServices.GetUnclaimed(hash)

    def GetUnspent(self, hash, index):
        return self.blockchainServices.GetUnclaimed(hash, index)

    def GetAllUnspent(self, hash):
        return self.blockchainServices.GetAllUnspent(hash)

    def GetVotes(self, transactions):
        return self.blockchainServices.GetVotes(transactions)

    @staticmethod
    def GetInstance() -> 'Blockchain':
        """
        Get the default registered blockchain instance.

        Returns:
            obj: Currently set to `neocore.Implementations.Blockchains.LevelDB.LevelDBBlockchain`.
        """
        if Blockchain._instance is None:
            Blockchain._instance = Blockchain(BlockchainService(Settings.settings), None)
            Blockchain._instance.GenesisBlock().RebuildMerkleRoot()

        return Blockchain._instance

    @staticmethod
    def RegisterBlockchain(blockchain):
        """
        Register the default block chain instance.

        Args:
            blockchain: a blockchain instance. E.g. neocore.Implementations.Blockchains.LevelDB.LevelDBBlockchain
        """
        if Blockchain._instance is None:
            Blockchain._instance = blockchain

    @staticmethod
    def DeregisterBlockchain():
        # TODO
        # Blockchain.PersistCompleted = Events()
        # Blockchain.Notify = Events()
        Blockchain._instance = None


    def GetHeaderIndex(self):
        if self.nodeServices is not None:
            return self.nodeServices.GetHeaderIndex()
        raise Exception("Local service not configured")

    def GetHeaderBy(self, height_or_hash):
        if self.nodeServices is not None:
            return self.nodeServices.GetHeaderBy(height_or_hash)
        raise Exception("Local service not configured")

    def SetHeaderIndex(self, headerIndex):
        if self.nodeServices is not None:
            return self.nodeServices.SetHeaderIndex(headerIndex)
        raise Exception("Local service not configured")

    def PersistBlocks(self, limit=None):
        if self.nodeServices is not None:
            return self.nodeServices.PersistBlocks()
        raise Exception("Local service not configured")

    @property
    def CurrentBlockHash(self):
        if self.nodeServices is not None:
            return self.nodeServices.CurrentBlock()
        raise Exception("Local service not configured")

    @property
    def CurrentHeaderHash(self):
        if self.nodeServices is not None:
            return self.nodeServices.CurrentBlock()
        raise Exception("Local service not configured")

    @property
    def HeaderHeight(self):
        if self.nodeServices is not None:
            return self.nodeServices.HeaderHeight()
        raise Exception("Local service not configured")

    @property
    def Height(self):
        return self.blockchainServices.Height

    @property
    def CurrentBlock(self):
        return  self.blockchainServices.CurrentBlock()

    def AddBlock(self, block):
        if self.nodeServices is not None:
            return self.nodeServices.AddBlock(block)
        raise Exception("Local service not configured")

    def AddBlockDirectly(self, block, do_persist_complete=True):
        if self.nodeServices is not None:
            return self.nodeServices.AddBlockDirectly( block, do_persist_complete)
        raise Exception("Local service not configured")

    def AddHeaders(self, headers):
        if self.nodeServices is not None:
            return self.nodeServices.AddHeaders(headers)
        raise Exception("Local service not configured")

    @property
    def BlockRequests(self):
        """
        Outstanding block requests.

        Returns:
            set:
        """
        if self.nodeServices is not None:
            return self.nodeServices.BlockRequests()
        raise Exception("Local service not configured")
    #TODO
    # return self._blockrequests

    def ResetBlockRequests(self):
        if self.nodeServices is not None:
            return self.nodeServices.ResetBlockRequests(self)
        raise Exception("Local service not configured")

    def ShowAllAssets(self):
        if self.nodeServices is not None:
            self.nodeServices.ShowAllAssets()
        raise Exception("Local service not configured")

    def CalculateBonusIgnoreClaimed(self, inputs, ignore_claimed=True):
        if self.nodeServices is not None:
            self.nodeServices.CalculateBonusIgnoreClaimed(inputs, ignore_claimed)
        raise Exception("Local service not configured")

    def CalculateBonus(self, inputs, height_end):
        if self.nodeServices is not None:
            self.nodeServices.CalculateBonus(inputs, height_end)
        raise Exception("Local service not configured")

    def ContainsBlock(self, hash):
        if self.nodeServices is not None:
            self.nodeServices.ContainsBlock(hash)
        raise Exception("Local service not configured")

    def ContainsTransaction(self, hash):
        if self.nodeServices is not None:
            self.nodeServices.ContainsTransaction(hash)
        raise Exception("Local service not configured")

    def ContainsUnspent(self, hash, index):
        if self.nodeServices is not None:
            self.nodeServices.ContainsUnspent(hash, index)
        raise Exception("Local service not configured")

    def Dispose(self):
        if self.nodeServices is not None:
            self.nodeServices.Dispose()

    def GetStates(self, prefix, classref):
        if self.nodeServices is not None:
            self.nodeServices.GetStates(hash)
        raise Exception("Local service not configured")

    def GetAccountStateByIndex(self, index):
        if self.nodeServices is not None:
            self.nodeServices.GetAccountStateByIndex(index)
        raise Exception("Local service not configured")

    def SearchAssetState(self, query):
        if self.nodeServices is not None:
            self.nodeServices.SearchAssetState(hash)
        raise Exception("Local service not configured")

    def GetAllSpentCoins(self):
        if self.nodeServices is not None:
            self.nodeServices.GetAllSpentCoins()
        raise Exception("Local service not configured")

    def SearchContracts(self, query):
        if self.nodeServices is not None:
            self.nodeServices.SearchContracts(query)
        raise Exception("Local service not configured")

    def ShowAllContracts(self):
        if self.nodeServices is not None:
            self.nodeServices.ShowAllContracts()
        raise Exception("Local service not configured")

    def GetEnrollments(self):
        if self.nodeServices is not None:
            self.nodeServices.GetEnrollments()
        raise Exception("Local service not configured")

    def GetValidators(self, others):
        votes = Counter([len(vs.PublicKeys) for vs in self.GetVotes(others)]).items()

        # TODO: Sorting here may cost a lot of memory, considering whether to use other mechanisms
        #           votes = GetVotes(others).OrderBy(p => p.PublicKeys.Length).ToArray()
        #            int validators_count = (int)votes.WeightedFilter(0.25, 0.75, p => p.Count.GetData(), (p, w) => new
        #            {
        #                ValidatorsCount = p.PublicKeys.Length,
        #                Weight = w
        #            }).WeightedAverage(p => p.ValidatorsCount, p => p.Weight)
        #            validators_count = Math.Max(validators_count, StandbyValidators.Length)
        #            Dictionary<ECPoint, Fixed8> validators = GetEnrollments().ToDictionary(p => p.PublicKey, p => Fixed8.Zero)
        #            foreach (var vote in votes)
        #            {
        #                foreach (ECPoint pubkey in vote.PublicKeys.Take(validators_count))
        #                {
        #                    if (validators.ContainsKey(pubkey))
        #                        validators[pubkey] += vote.Count
        #                }
        #            }
        #            return validators.OrderByDescending(p => p.Value).ThenBy(p => p.Key).Select(p => p.Key).Concat(StandbyValidators).Take(validators_count)
        #        }

        raise NotImplementedError()

    def GetNextBlockHash(self, hash):
        if self.nodeServices is not None:
            self.nodeServices.GetNextBlockHash(hash)
        raise Exception("Local service not configured")


    def IsDoubleSpend(self, tx):
        if self.nodeServices is not None:
            self.nodeServices.IsDoubleSpend(tx)
        raise Exception("Local service not configured")

    def BlockCacheCount(self):
        if self.nodeServices is not None:
            self.nodeServices.BlockCacheCount()
        raise Exception("Local service not configured")

    def GetGenesis(self):
        return self.blockchainServices.GenesisBlock()

    def GetSystemCoin(self):
        return self.blockchainServices.SystemCoin()

    def GetSystemShare(self):
        return  self.blockchainServices.SystemShare()

    def GetStateReader(self):
        #TODO ?
        from neocore.Core.Contract.StateReader import StateReader
        return StateReader()

    def GetConsensusAddress(self, validators):
        from neocore.Core.Blockchain import Blockchain
        return Blockchain.GettConsensusAddress(self, validators)

