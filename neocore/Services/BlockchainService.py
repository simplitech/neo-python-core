from datetime import datetime
from functools import lru_cache
from itertools import groupby

import pytz
from neocore.Core.AssetType import AssetType
from neocore.Core.Block import Block
from neocore.Core.Contract.Contract import Contract
from neocore.Core.State.SpentCoinState import SpentCoin
from neocore.Core.TX.IssueTransaction import IssueTransaction
from neocore.Core.TX.MinerTransaction import MinerTransaction
from neocore.Core.TX.RegisterTransaction import RegisterTransaction
from neocore.Core.TX.Transaction import TransactionOutput
from neocore.Core.VM.OpCode import PUSHT, PUSHF
from neocore.Core.Witness import Witness
from neocore.Cryptography.Crypto import Crypto
from neocore.Cryptography.ECCurve import ECDSA
from neocore.Fixed8 import Fixed8
from neocore.IO import DBService
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256


class BlockchainService:
    def __init__(self, settings):
        self.secondsPerBlock = 15
        self.decrementInterval = 2000000
        self.generationAmount = [8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.validators = []
        self.settings = settings
        self.genesisBlock = None


    def StandbyValidators(self):
        if len(self.validators) < 1:
            vlist = self.settings.STANDBY_VALIDATORS
            for pkey in vlist:
                self.validators.append(ECDSA.decode_secp256r1(pkey).G)

        return self.validators

    def GetConsensusAddress(self, validators):
        """
                Get the script hash of the consensus node.

                Args:
                    validators (list): of Ellipticcurve.ECPoint's

                Returns:
                    UInt160:
                """
        vlen = len(validators)
        script = Contract.CreateMultiSigRedeemScript(vlen - int((vlen - 1) / 3), validators)
        return Crypto.ToScriptHash(script)


    @lru_cache(maxsize=2)
    def SystemShare(self):
        """
        Register AntShare.

        Returns:
            RegisterTransaction:
        """
        amount = Fixed8.FromDecimal(sum(self.generationAmount) * self.decrementInterval)
        owner = ECDSA.secp256r1().Curve.Infinity

        admin = Crypto.ToScriptHash(PUSHT)

        return RegisterTransaction([], [], AssetType.GoverningToken,
                                   "[{\"lang\":\"zh-CN\",\"name\":\"小蚁股\"},{\"lang\":\"en\",\"name\":\"AntShare\"}]",
                                   amount, 0, owner, admin)

    @lru_cache(maxsize=2)
    def SystemCoin(self):
        """
        Register AntCoin

        Returns:
            RegisterTransaction:
        """
        amount = Fixed8.FromDecimal(sum(self.generationAmount) * self.decrementInterval)

        owner = ECDSA.secp256r1().Curve.Infinity

        precision = 8
        admin = Crypto.ToScriptHash(PUSHF)

        return RegisterTransaction([], [], AssetType.UtilityToken,
                                   "[{\"lang\":\"zh-CN\",\"name\":\"小蚁币\"},{\"lang\":\"en\",\"name\":\"AntCoin\"}]",
                                   amount, precision, owner, admin)

    def GetAssetState(self, assetId):
        pass

    def GetAccountState(self):
        pass

    def GetStorageItem(self, storage_key):
        pass

    def GetAccountState(self, address):
        pass

    def GenesisBlock(self) -> Block:
        """
        Create the GenesisBlock.

        Returns:
            BLock:
        """
        prev_hash = UInt256(data=bytearray(32))
        timestamp = int(datetime(2016, 7, 15, 15, 8, 21, tzinfo=pytz.utc).timestamp())
        index = 0
        consensus_data = 2083236893  # Pay tribute To Bitcoin
        next_consensus = self.GetConsensusAddress(self.StandbyValidators())
        script = Witness(bytearray(0), bytearray(PUSHT))

        mt = MinerTransaction()
        mt.Nonce = 2083236893

        output = TransactionOutput(
            self.SystemShare().Hash,
            self.SystemShare().Amount,
            Crypto.ToScriptHash(Contract.CreateMultiSigRedeemScript(int(len(self.StandbyValidators()) / 2) + 1,
                                                                    self.StandbyValidators()))
        )

        it = IssueTransaction([], [output], [], [script])

        return Block(prev_hash, timestamp, index, consensus_data,
                     next_consensus, script,
                     [mt, self.SystemShare(), self.SystemCoin(), it],
                     True)

    def GetContract(self, hash: UInt160):
        pass

    def GetHeaderHash(self, height):
        pass

    def GetAllUnspent(self, hash):
        pass

    def GetScript(self, script_hash):
        pass

    def GetStorageItem(self, storage_key):
        pass

    def GetSysFeeAmount(self, hash):
        pass

    def GetSysFeeAmountByHeight(self, height):
        """
                Get the system fee for the specified block.

                Args:
                    height (int): block height.

                Returns:
                    int:
                """
        hash = self.GetBlockHash(height)
        return self.GetSysFeeAmount(hash)

    def GetTransaction(self, hash):
        pass

    def GetUnclaimed(self, hash):
        pass

    def Height(self):
        pass

    def CurrentBlock(self):
        pass

    def GetBlockHeight(self):
        pass

    def GetBlockHash(self, index):
        pass


class NodeService(BlockchainService):

    def __init__(self, dbService : DBService, settings):
        super().__init__(settings)
        self.dbService = dbService

    def CalculateBonusIgnoreClaimed(self, inputs, ignore_claimed=True):
        unclaimed = []

        for hash, group in groupby(inputs, lambda x: x.PrevHash):
            claimable = self.GetUnclaimed(hash)
            if claimable is None or len(claimable) < 1:
                if ignore_claimed:
                    continue
                else:
                    raise Exception("Error calculating bonus without ignoring claimed")

            for coinref in group:
                if coinref.PrevIndex in claimable:
                    claimed = claimable[coinref.PrevIndex]
                    unclaimed.append(claimed)
                else:
                    if ignore_claimed:
                        continue
                    else:
                        raise Exception("Error calculating bonus without ignoring claimed")

        return self.CalculateBonusInternal(unclaimed)

    def CalculateBonus(self, inputs, height_end):
        unclaimed = []

        for hash, group in groupby(inputs, lambda x: x.PrevHash):
            from neocore.Core.Blockchain import Blockchain
            tx, height_start = Blockchain.Default().GetTransaction(hash)

            if tx is None:
                raise Exception("Could Not calculate bonus")

            if height_start == height_end:
                continue

            for coinref in group:
                if coinref.PrevIndex >= len(tx.outputs) or tx.outputs[
                    coinref.PrevIndex].AssetId != Blockchain.SystemShare().Hash:
                    raise Exception("Invalid coin reference")
                spent_coin = SpentCoin(output=tx.outputs[coinref.PrevIndex], start_height=height_start,
                                       end_height=height_end)
                unclaimed.append(spent_coin)

        return Blockchain.CalculateBonusInternal(unclaimed)

    def CalculateBonusInternal(self, unclaimed):
        amount_claimed = Fixed8.Zero()

        decInterval = self.decrementInterval
        genAmount = self.generationAmount
        genLen = len(genAmount)

        for coinheight, group in groupby(unclaimed, lambda x: x.Heights):
            amount = 0
            ustart = int(coinheight.start / decInterval)

            if ustart < genLen:

                istart = coinheight.start % decInterval
                uend = int(coinheight.end / decInterval)
                iend = coinheight.end % decInterval

                if uend >= genLen:
                    iend = 0

                if iend == 0:
                    uend -= 1
                    iend = decInterval

                while ustart < uend:
                    amount += (decInterval - istart) * genAmount[ustart]
                    ustart += 1
                    istart = 0

                amount += (iend - istart) * genAmount[ustart]

            endamount = self.GetSysFeeAmountByHeight(coinheight.end - 1)
            from neocore.Core.Blockchain import Blockchain
            startamount = 0 if coinheight.start == 0 else Blockchain.Default().GetSysFeeAmountByHeight(
                coinheight.start - 1)
            amount += endamount - startamount

            outputSum = 0

            for spentcoin in group:
                outputSum += spentcoin.Value.value

            outputSum = outputSum / 100000000
            outputSumFixed8 = Fixed8(int(outputSum * amount))
            amount_claimed += outputSumFixed8

        return amount_claimed

    def CurrentHeaderHash(self):
        pass

    def HeaderHeight(self):
        pass

    def CurrentBlock(self):
        pass

    def AddBlock(self, block):
        pass

    def AddBlockDirectly(self, block, do_persist_complete=True):
        pass

    def AddHeaders(self, headers):
        pass

    def BlockRequests(self):
        pass

    def ResetBlockRequests(self):
        pass

    def ContainsBlock(self, hash):
        pass

    def ContainsTransaction(self, hash):
        pass

    def ContainsUnspent(self, hash, index):
        pass

    def Dispose(self):
        pass

    def GetStates(self, prefix, classref):
        pass

    def GetAccountStateByIndex(self, index):
        pass

    def SearchAssetState(self, query):
        pass

    def GetBlockByHeight(self, height):
        pass

    def GetBlock(self, height_or_hash):
        pass

    def GetBlockByHash(self, hash):
        pass

    def GetBlockHash(self, height):
        # abstract
        pass

    def GetHeaderBy(self, height_or_hash):
        pass

    def GetSpentCoins(self, tx_hash):
        pass

    def GetAllSpentCoins(self):
        pass

    def SearchContracts(self, query):
        pass

    def ShowAllContracts(self):
        pass

    def ShowAllAssets(self):
        pass

    def GetContract(self, hash):
        pass

    def GetEnrollments(self):
        pass

    def GetHeader(self, hash):
        pass

    def GetHeaderByHeight(self, height):
        pass



    def GetValidators(self, others):
        pass

    def GetNextBlockHash(self, hash):
        pass

    def GetUnspent(self, hash, index):
        pass

    def GetVotes(self, transactions):
        pass

    def IsDoubleSpend(self, tx):
        pass

    def OnPersistCompleted(self, block):
        pass

    def BlockCacheCount(self):
        pass

    def Pause(self):
        pass

    def Resume(self):
        pass

    def GetGenesis(self):
        pass

    def GetSystemCoin(self):
        pass

    def GetSystemShare(self):
        pass

    def GetStateReader(self):
        pass


