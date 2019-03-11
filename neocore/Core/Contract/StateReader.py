from neocore.Core.Contract.ApplicationEngine import ApplicationEngine
from neocore.Core.VM.InteropService import InteropService
from neocore.Core.Contract.Contract import Contract
from neocore.Core.Contract.NotifyEventArgs import NotifyEventArgs
from neocore.Core.Contract.StorageContext import StorageContext
from neocore.Core.State.StorageKey import StorageKey
from neocore.Core.Blockchain import Blockchain
from neocore.Cryptography.Crypto import Crypto
from neocore.BigInteger import BigInteger
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256
from neocore.Core.Contract.SmartContractEvent import SmartContractEvent, NotifyEvent
from neocore.Core.Contract.ContractParameter import ContractParameter, ContractParameterType
from neocore.Cryptography.ECCurve import ECDSA
from neocore.Core.Contract.TriggerType import Application, Verification
from neocore.Core.VM.InteropService import StackItem, ByteArray, Array, Map
from neocore.Core.VM.ExecutionEngine import ExecutionEngine
from neocore.Settings import settings
from neocore.IO.BinaryReader import BinaryReader
from neocore.IO.BinaryWriter import BinaryWriter
from neocore.IO.MemoryStream import StreamManager
from neocore.Core.Contract.Iterable.Wrapper import ArrayWrapper, MapWrapper
from neocore.Core.Contract.Iterable import KeysWrapper, ValuesWrapper
from neocore.Core.Contract.Iterable.ConcatenatedEnumerator import ConcatenatedEnumerator
from neocore.Core.State.ContractState import ContractState
from neocore.Core.State.AccountState import AccountState
from neocore.Core.State.AssetState import AssetState
from neocore.Core.State.StorageItem import StorageItem



class StateReader(InteropService):
    notifications = None

    events_to_dispatch = []

    __Instance = None

    _hashes_for_verifying = None

    _accounts = None
    _assets = None
    _contracts = None
    _storages = None

    @property
    def Accounts(self):
        if not self._accounts:
            prefix = Blockchain.GetInstance().nodeServices.dbService.getPrefixAccount()
            self._accounts = Blockchain.GetInstance().nodeServices.dbService.GetStates(prefix, AccountState)
        return self._accounts

    @property
    def Assets(self):
        if not self._assets:
            prefix = Blockchain.GetInstance().nodeServices.dbService.getPrefixAsset()
            self._assets = Blockchain.Default().GetStates(prefix, AssetState)
        return self._assets

    @property
    def Contracts(self):
        if not self._contracts:
            prefix = Blockchain.GetInstance().nodeServices.dbService.getPrefixContract()
            self._contracts = Blockchain.Default().GetStates(prefix, ContractState)
        return self._contracts

    @property
    def Storages(self):
        if not self._storages:
            prefix = Blockchain.GetInstance().nodeServices.dbService.getPrefixStorage()
            self._storages = Blockchain.Default().GetStates(prefix, StorageItem)
        return self._storages

    @staticmethod
    def Instance():
        if StateReader.__Instance is None:
            StateReader.__Instance = StateReader()
        return StateReader.__Instance

    def __init__(self):

        super(StateReader, self).__init__()

        self.notifications = []
        self.events_to_dispatch = []

        # Standard Library
        self.Register("System.Runtime.GetTrigger", self.Runtime_GetTrigger)
        self.Register("System.Runtime.CheckWitness", self.Runtime_CheckWitness)
        self.Register("System.Runtime.Notify", self.Runtime_Notify)
        self.Register("System.Runtime.Log", self.Runtime_Log)
        self.Register("System.Runtime.GetTime", self.Runtime_GetCurrentTime)
        self.Register("System.Runtime.Serialize", self.Runtime_Serialize)
        self.Register("System.Runtime.Deserialize", self.Runtime_Deserialize)
        self.Register("System.Blockchain.GetHeight", self.Blockchain_GetHeight)
        self.Register("System.Blockchain.GetHeader", self.Blockchain_GetHeader)
        self.Register("System.Blockchain.GetBlock", self.Blockchain_GetBlock)
        self.Register("System.Blockchain.GetTransaction", self.Blockchain_GetTransaction)
        self.Register("System.Blockchain.GetTransactionHeight", self.Blockchain_GetTransactionHeight)
        self.Register("System.Blockchain.GetContract", self.Blockchain_GetContract)
        self.Register("System.Header.GetIndex", self.Header_GetIndex)
        self.Register("System.Header.GetHash", self.Header_GetHash)
        self.Register("System.Header.GetVersion", self.Header_GetVersion)
        self.Register("System.Header.GetPrevHash", self.Header_GetPrevHash)
        self.Register("System.Header.GetTimestamp", self.Header_GetTimestamp)
        self.Register("System.Block.GetTransactionCount", self.Block_GetTransactionCount)
        self.Register("System.Block.GetTransactions", self.Block_GetTransactions)
        self.Register("System.Block.GetTransaction", self.Block_GetTransaction)
        self.Register("System.Transaction.GetHash", self.Transaction_GetHash)
        self.Register("System.Storage.GetContext", self.Storage_GetContext)
        self.Register("System.Storage.GetReadOnlyContext", self.Storage_GetReadOnlyContext)
        self.Register("System.Storage.Get", self.Storage_Get)
        self.Register("System.StorageContext.AsReadOnly", self.StorageContext_AsReadOnly)

        # Neo Specific
        self.Register("neocore.Blockchain.GetAccount", self.Blockchain_GetAccount)
        self.Register("neocore.Blockchain.GetValidators", self.Blockchain_GetValidators)
        self.Register("neocore.Blockchain.GetAsset", self.Blockchain_GetAsset)
        self.Register("neocore.Header.GetMerkleRoot", self.Header_GetMerkleRoot)
        self.Register("neocore.Header.GetConsensusData", self.Header_GetConsensusData)
        self.Register("neocore.Header.GetNextConsensus", self.Header_GetNextConsensus)
        self.Register("neocore.Transaction.GetType", self.Transaction_GetType)
        self.Register("neocore.Transaction.GetAttributes", self.Transaction_GetAttributes)
        self.Register("neocore.Transaction.GetInputs", self.Transaction_GetInputs)
        self.Register("neocore.Transaction.GetOutputs", self.Transaction_GetOutputs)
        self.Register("neocore.Transaction.GetReferences", self.Transaction_GetReferences)
        self.Register("neocore.Transaction.GetUnspentCoins", self.Transaction_GetUnspentCoins)
        self.Register("neocore.Transaction.GetWitnesses", self.Transaction_GetWitnesses)
        self.Register("neocore.InvocationTransaction.GetScript", self.InvocationTransaction_GetScript)
        self.Register("neocore.Witness.GetVerificationScript", self.Witness_GetVerificationScript)
        self.Register("neocore.Attribute.GetUsage", self.Attribute_GetUsage)
        self.Register("neocore.Attribute.GetData", self.Attribute_GetData)
        self.Register("neocore.Input.GetHash", self.Input_GetHash)
        self.Register("neocore.Input.GetIndex", self.Input_GetIndex)
        self.Register("neocore.Output.GetAssetId", self.Output_GetAssetId)
        self.Register("neocore.Output.GetValue", self.Output_GetValue)
        self.Register("neocore.Output.GetScriptHash", self.Output_GetScriptHash)
        self.Register("neocore.Account.GetScriptHash", self.Account_GetScriptHash)
        self.Register("neocore.Account.GetVotes", self.Account_GetVotes)
        self.Register("neocore.Account.GetBalance", self.Account_GetBalance)
        self.Register("neocore.Asset.GetAssetId", self.Asset_GetAssetId)
        self.Register("neocore.Asset.GetAssetType", self.Asset_GetAssetType)
        self.Register("neocore.Asset.GetAmount", self.Asset_GetAmount)
        self.Register("neocore.Asset.GetAvailable", self.Asset_GetAvailable)
        self.Register("neocore.Asset.GetPrecision", self.Asset_GetPrecision)
        self.Register("neocore.Asset.GetOwner", self.Asset_GetOwner)
        self.Register("neocore.Asset.GetAdmin", self.Asset_GetAdmin)
        self.Register("neocore.Asset.GetIssuer", self.Asset_GetIssuer)
        self.Register("neocore.Contract.GetScript", self.Contract_GetScript)
        self.Register("neocore.Contract.IsPayable", self.Contract_IsPayable)
        self.Register("neocore.Storage.Find", self.Storage_Find)
        self.Register("neocore.Enumerator.Create", self.Enumerator_Create)
        self.Register("neocore.Enumerator.Next", self.Enumerator_Next)
        self.Register("neocore.Enumerator.Value", self.Enumerator_Value)
        self.Register("neocore.Enumerator.Concat", self.Enumerator_Concat)
        self.Register("neocore.Iterator.Create", self.Iterator_Create)
        self.Register("neocore.Iterator.Key", self.Iterator_Key)
        self.Register("neocore.Iterator.Keys", self.Iterator_Keys)
        self.Register("neocore.Iterator.Values", self.Iterator_Values)

        # Old Iterator aliases
        self.Register("neocore.Iterator.Next", self.Enumerator_Next)
        self.Register("neocore.Iterator.Value", self.Enumerator_Value)

        # Old API
        # Standard Library
        self.Register("neocore.Runtime.GetTrigger", self.Runtime_GetTrigger)
        self.Register("neocore.Runtime.CheckWitness", self.Runtime_CheckWitness)
        self.Register("neocore.Runtime.Notify", self.Runtime_Notify)
        self.Register("neocore.Runtime.Log", self.Runtime_Log)
        self.Register("neocore.Runtime.GetTime", self.Runtime_GetCurrentTime)
        self.Register("neocore.Runtime.Serialize", self.Runtime_Serialize)
        self.Register("neocore.Runtime.Deserialize", self.Runtime_Deserialize)
        self.Register("neocore.Blockchain.GetHeight", self.Blockchain_GetHeight)
        self.Register("neocore.Blockchain.GetHeader", self.Blockchain_GetHeader)
        self.Register("neocore.Blockchain.GetBlock", self.Blockchain_GetBlock)
        self.Register("neocore.Blockchain.GetTransaction", self.Blockchain_GetTransaction)
        self.Register("neocore.Blockchain.GetTransactionHeight", self.Blockchain_GetTransactionHeight)
        self.Register("neocore.Blockchain.GetContract", self.Blockchain_GetContract)
        self.Register("neocore.Header.GetIndex", self.Header_GetIndex)
        self.Register("neocore.Header.GetHash", self.Header_GetHash)
        self.Register("neocore.Header.GetVersion", self.Header_GetVersion)
        self.Register("neocore.Header.GetPrevHash", self.Header_GetPrevHash)
        self.Register("neocore.Header.GetTimestamp", self.Header_GetTimestamp)
        self.Register("neocore.Block.GetTransactionCount", self.Block_GetTransactionCount)
        self.Register("neocore.Block.GetTransactions", self.Block_GetTransactions)
        self.Register("neocore.Block.GetTransaction", self.Block_GetTransaction)
        self.Register("neocore.Transaction.GetHash", self.Transaction_GetHash)
        self.Register("neocore.Storage.GetContext", self.Storage_GetContext)
        self.Register("neocore.Storage.GetReadOnlyContext", self.Storage_GetReadOnlyContext)
        self.Register("neocore.Storage.Get", self.Storage_Get)
        self.Register("neocore.StorageContext.AsReadOnly", self.StorageContext_AsReadOnly)

        # Very OLD API
        self.Register("AntShares.Runtime.GetTrigger", self.Runtime_GetTrigger)
        self.Register("AntShares.Runtime.CheckWitness", self.Runtime_CheckWitness)
        self.Register("AntShares.Runtime.Notify", self.Runtime_Notify)
        self.Register("AntShares.Runtime.Log", self.Runtime_Log)
        self.Register("AntShares.Blockchain.GetHeight", self.Blockchain_GetHeight)
        self.Register("AntShares.Blockchain.GetHeader", self.Blockchain_GetHeader)
        self.Register("AntShares.Blockchain.GetBlock", self.Blockchain_GetBlock)
        self.Register("AntShares.Blockchain.GetTransaction", self.Blockchain_GetTransaction)
        self.Register("AntShares.Blockchain.GetAccount", self.Blockchain_GetAccount)
        self.Register("AntShares.Blockchain.GetValidators", self.Blockchain_GetValidators)
        self.Register("AntShares.Blockchain.GetAsset", self.Blockchain_GetAsset)
        self.Register("AntShares.Blockchain.GetContract", self.Blockchain_GetContract)
        self.Register("AntShares.Header.GetHash", self.Header_GetHash)
        self.Register("AntShares.Header.GetVersion", self.Header_GetVersion)
        self.Register("AntShares.Header.GetPrevHash", self.Header_GetPrevHash)
        self.Register("AntShares.Header.GetMerkleRoot", self.Header_GetMerkleRoot)
        self.Register("AntShares.Header.GetTimestamp", self.Header_GetTimestamp)
        self.Register("AntShares.Header.GetConsensusData", self.Header_GetConsensusData)
        self.Register("AntShares.Header.GetNextConsensus", self.Header_GetNextConsensus)
        self.Register("AntShares.Block.GetTransactionCount", self.Block_GetTransactionCount)
        self.Register("AntShares.Block.GetTransactions", self.Block_GetTransactions)
        self.Register("AntShares.Block.GetTransaction", self.Block_GetTransaction)
        self.Register("AntShares.Transaction.GetHash", self.Transaction_GetHash)
        self.Register("AntShares.Transaction.GetType", self.Transaction_GetType)
        self.Register("AntShares.Transaction.GetAttributes", self.Transaction_GetAttributes)
        self.Register("AntShares.Transaction.GetInputs", self.Transaction_GetInputs)
        self.Register("AntShares.Transaction.GetOutpus", self.Transaction_GetOutputs)
        self.Register("AntShares.Transaction.GetReferences", self.Transaction_GetReferences)
        self.Register("AntShares.Attribute.GetData", self.Attribute_GetData)
        self.Register("AntShares.Attribute.GetUsage", self.Attribute_GetUsage)
        self.Register("AntShares.Input.GetHash", self.Input_GetHash)
        self.Register("AntShares.Input.GetIndex", self.Input_GetIndex)
        self.Register("AntShares.Output.GetAssetId", self.Output_GetAssetId)
        self.Register("AntShares.Output.GetValue", self.Output_GetValue)
        self.Register("AntShares.Output.GetScriptHash", self.Output_GetScriptHash)
        self.Register("AntShares.Account.GetVotes", self.Account_GetVotes)
        self.Register("AntShares.Account.GetBalance", self.Account_GetBalance)
        self.Register("AntShares.Account.GetScriptHash", self.Account_GetScriptHash)
        self.Register("AntShares.Asset.GetAssetId", self.Asset_GetAssetId)
        self.Register("AntShares.Asset.GetAssetType", self.Asset_GetAssetType)
        self.Register("AntShares.Asset.GetAmount", self.Asset_GetAmount)
        self.Register("AntShares.Asset.GetAvailable", self.Asset_GetAvailable)
        self.Register("AntShares.Asset.GetPrecision", self.Asset_GetPrecision)
        self.Register("AntShares.Asset.GetOwner", self.Asset_GetOwner)
        self.Register("AntShares.Asset.GetAdmin", self.Asset_GetAdmin)
        self.Register("AntShares.Asset.GetIssuer", self.Asset_GetIssuer)
        self.Register("AntShares.Contract.GetScript", self.Contract_GetScript)
        self.Register("AntShares.Storage.GetContext", self.Storage_GetContext)
        self.Register("AntShares.Storage.Get", self.Storage_Get)

    def CheckStorageContext(self, context):
        if context is None:
            return False

        contract = self.Contracts.TryGet(context.ScriptHash.ToBytes())

        if contract is not None:
            if contract.HasStorage:
                return True

        return False

    def ExecutionCompleted(self, engine, success, error=None):
        height = Blockchain.GetInstance().Height + 1
        tx_hash = None

        if engine.ScriptContainer:
            tx_hash = engine.ScriptContainer.Hash

        if not tx_hash:
            tx_hash = UInt256(data=bytearray(32))

        entry_script = None
        try:
            # get the first script that was executed
            # this is usually the script that sets up the script to be executed
            entry_script = UInt160(data=engine.ExecutedScriptHashes[0])

            # ExecutedScriptHashes[1] will usually be the first contract executed
            if len(engine.ExecutedScriptHashes) > 1:
                entry_script = UInt160(data=engine.ExecutedScriptHashes[1])
        except Exception as e:
            raise Exception("Could not get entry script: %s " % e)
            #logger.error("Could not get entry script: %s " % e)

        payload = ContractParameter(ContractParameterType.Array, value=[])
        for item in engine.ResultStack.Items:
            payload.Value.append(ContractParameter.ToParameter(item))

        if success:

            # dispatch all notify events, along with the success of the contract execution
            for notify_event_args in self.notifications:
                self.events_to_dispatch.append(NotifyEvent(SmartContractEvent.RUNTIME_NOTIFY, notify_event_args.State,
                                                           notify_event_args.ScriptHash, height, tx_hash,
                                                           success, engine.testMode))

            if engine.Trigger == Application:
                self.events_to_dispatch.append(SmartContractEvent(SmartContractEvent.EXECUTION_SUCCESS, payload, entry_script,
                                                                  height, tx_hash, success, engine.testMode))
            else:
                self.events_to_dispatch.append(SmartContractEvent(SmartContractEvent.VERIFICATION_SUCCESS, payload, entry_script,
                                                                  height, tx_hash, success, engine.testMode))

        else:
            # when a contract exits in a faulted state
            # we should display that in the notification
            if not error:
                error = 'Execution exited in a faulted state. Any payload besides this message contained in this event is the contents of the EvaluationStack of the current script context.'

            payload.Value.append(ContractParameter(ContractParameterType.String, error))

            # If we do not add the eval stack, then exceptions that are raised in a contract
            # are not displayed to the event consumer
            [payload.Value.append(ContractParameter.ToParameter(item)) for item in engine.CurrentContext.EvaluationStack.Items]

            if engine.Trigger == Application:
                self.events_to_dispatch.append(
                    SmartContractEvent(SmartContractEvent.EXECUTION_FAIL, payload,
                                       entry_script, height, tx_hash, success, engine.testMode))
            else:
                self.events_to_dispatch.append(
                    SmartContractEvent(SmartContractEvent.VERIFICATION_FAIL, payload,
                                       entry_script, height, tx_hash, success, engine.testMode))

        self.notifications = []

    def Runtime_GetTrigger(self, engine):

        engine.CurrentContext.EvaluationStack.PushT(engine.Trigger)

        return True

    def CheckWitnessHash(self, engine, hash):
        if not engine.ScriptContainer:
            return False

        if self._hashes_for_verifying is None:
            container = engine.ScriptContainer
            self._hashes_for_verifying = container.GetScriptHashesForVerifying()

        return True if hash in self._hashes_for_verifying else False

    def CheckWitnessPubkey(self, engine, pubkey):
        scripthash = Contract.CreateSignatureRedeemScript(pubkey)
        return self.CheckWitnessHash(engine, Crypto.ToScriptHash(scripthash))

    def Runtime_CheckWitness(self, engine: ExecutionEngine):
        hashOrPubkey = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        result = False

        if len(hashOrPubkey) == 20:
            result = self.CheckWitnessHash(engine, UInt160(data=hashOrPubkey))

        elif len(hashOrPubkey) == 33:
            point = ECDSA.decode_secp256r1(hashOrPubkey, unhex=False).G
            result = self.CheckWitnessPubkey(engine, point)
        else:
            return False

        engine.CurrentContext.EvaluationStack.PushT(result)

        return True

    def Runtime_Notify(self, engine: ExecutionEngine):
        state = engine.CurrentContext.EvaluationStack.Pop()

        payload = ContractParameter.ToParameter(state)

        args = NotifyEventArgs(
            engine.ScriptContainer,
            UInt160(data=engine.CurrentContext.ScriptHash()),
            payload
        )

        self.notifications.append(args)

        if settings.emit_notify_events_on_sc_execution_error:
            # emit Notify events even if the SC execution might fail.
            tx_hash = engine.ScriptContainer.Hash
            height = Blockchain.GetInstance().Height + 1
            success = None
            self.events_to_dispatch.append(NotifyEvent(SmartContractEvent.RUNTIME_NOTIFY, payload,
                                                       args.ScriptHash, height, tx_hash,
                                                       success, engine.testMode))

        return True

    def Runtime_Log(self, engine: ExecutionEngine):
        message = engine.CurrentContext.EvaluationStack.Pop().GetString()

        hash = UInt160(data=engine.CurrentContext.ScriptHash())

        tx_hash = None

        if engine.ScriptContainer:
            tx_hash = engine.ScriptContainer.Hash
        engine.write_log(str(message))

        # Build and emit smart contract event
        self.events_to_dispatch.append(SmartContractEvent(SmartContractEvent.RUNTIME_LOG,
                                                          ContractParameter(ContractParameterType.String, value=message),
                                                          hash,
                                                          Blockchain.GetInstance().Height + 1,
                                                          tx_hash,
                                                          test_mode=engine.testMode))

        return True

    def Runtime_GetCurrentTime(self, engine: ExecutionEngine):
        BC = Blockchain.GetInstance()
        header = BC.GetHeaderByHeight(BC.Height)
        if header is None:
            header = Blockchain.GenesisBlock()

        engine.CurrentContext.EvaluationStack.PushT(header.Timestamp + Blockchain.SECONDS_PER_BLOCK)
        return True

    def Runtime_Serialize(self, engine: ExecutionEngine):
        stack_item = engine.CurrentContext.EvaluationStack.Pop()

        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)
        try:
            stack_item.Serialize(writer)
        except Exception as e:
            raise Exception("Cannot serialize item %s: %s " % (stack_item, e))

        ms.flush()

        if ms.tell() > ApplicationEngine.maxItemSize:
            return False

        retVal = ByteArray(ms.getvalue())
        StreamManager.ReleaseStream(ms)
        engine.CurrentContext.EvaluationStack.PushT(retVal)

        return True

    def Runtime_Deserialize(self, engine: ExecutionEngine):
        data = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        ms = StreamManager.GetStream(data=data)
        reader = BinaryReader(ms)
        try:
            stack_item = StackItem.DeserializeStackItem(reader)
            engine.CurrentContext.EvaluationStack.PushT(stack_item)
        except ValueError as e:
            # can't deserialize type
            #logger.error("%s " % e)
            return False
        return True

    def Blockchain_GetHeight(self, engine: ExecutionEngine):
        if Blockchain.GetInstance() is None:
            engine.CurrentContext.EvaluationStack.PushT(0)
        else:
            engine.CurrentContext.EvaluationStack.PushT(Blockchain.GetInstance().Height)

        return True

    def Blockchain_GetHeader(self, engine: ExecutionEngine):
        data = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        header = None

        if len(data) <= 5:

            height = BigInteger.FromBytes(data)

            if Blockchain.GetInstance() is not None:

                header = Blockchain.GetInstance().GetHeaderBy(height_or_hash=height)

            elif height == 0:

                header = Blockchain.GenesisBlock().Header

        elif len(data) == 32:

            hash = UInt256(data=data)

            if Blockchain.GetInstance() is not None:

                header = Blockchain.GetInstance().GetHeaderBy(height_or_hash=hash)

            elif hash == Blockchain.GenesisBlock().Hash:

                header = Blockchain.GenesisBlock().Header

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(header))
        return True

    def Blockchain_GetBlock(self, engine: ExecutionEngine):
        data = engine.CurrentContext.EvaluationStack.Pop()

        if data:
            data = data.GetByteArray()
        else:
            return False

        block = None

        if len(data) <= 5:
            height = BigInteger.FromBytes(data)

            if Blockchain.GetInstance() is not None:

                block = Blockchain.GetInstance().GetBlockByHeight(height)

            elif height == 0:

                block = Blockchain.GenesisBlock()

        elif len(data) == 32:

            hash = UInt256(data=data).ToBytes()

            if Blockchain.GetInstance() is not None:

                block = Blockchain.GetInstance().GetBlockByHash(hash=hash)

            elif hash == Blockchain.GenesisBlock().Hash:

                block = Blockchain.GenesisBlock().Header

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(block))
        return True

    def Blockchain_GetTransaction(self, engine: ExecutionEngine):
        data = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        tx = None

        if Blockchain.GetInstance() is not None:
            tx, height = Blockchain.GetInstance().GetTransaction(UInt256(data=data))

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(tx))
        return True

    def Blockchain_GetTransactionHeight(self, engine: ExecutionEngine):
        data = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        height = -1

        if Blockchain.GetInstance() is not None:
            tx, height = Blockchain.GetInstance().GetTransaction(UInt256(data=data))

        engine.CurrentContext.EvaluationStack.PushT(height)
        return True

    def Blockchain_GetAccount(self, engine: ExecutionEngine):
        hash = UInt160(data=engine.CurrentContext.EvaluationStack.Pop().GetByteArray())
        address = Crypto.ToAddress(hash).encode('utf-8')

        account = self.Accounts.GetOrAdd(address, new_instance=AccountState(script_hash=hash))
        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(account))
        return True

    def Blockchain_GetValidators(self, engine: ExecutionEngine):
        validators = Blockchain.GetInstance().GetValidators()

        items = [StackItem(validator.encode_point(compressed=True)) for validator in validators]

        engine.CurrentContext.EvaluationStack.PushT(items)

        return True

    def Blockchain_GetAsset(self, engine: ExecutionEngine):
        data = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        asset = None

        if Blockchain.GetInstance() is not None:
            asset = self.Assets.TryGet(UInt256(data=data))
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(asset))
        return True

    def Blockchain_GetContract(self, engine: ExecutionEngine):
        hash = UInt160(data=engine.CurrentContext.EvaluationStack.Pop().GetByteArray())
        contract = self.Contracts.TryGet(hash.ToBytes())
        if contract is None:
            engine.CurrentContext.EvaluationStack.PushT(bytearray(0))
        else:
            engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(contract))
        return True

    def Header_GetIndex(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.Index)
        return True

    def Header_GetHash(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.Hash.ToArray())
        return True

    def Header_GetVersion(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.Version)
        return True

    def Header_GetPrevHash(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.PrevHash.ToArray())
        return True

    def Header_GetMerkleRoot(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.MerkleRoot.ToArray())
        return True

    def Header_GetTimestamp(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.Timestamp)

        return True

    def Header_GetConsensusData(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.ConsensusData)
        return True

    def Header_GetNextConsensus(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.NextConsensus.ToArray())
        return True

    def Block_GetTransactionCount(self, engine: ExecutionEngine):
        block = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if block is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(len(block.Transactions))
        return True

    def Block_GetTransactions(self, engine: ExecutionEngine):
        block = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if block is None:
            return False

        if len(block.FullTransactions) > ApplicationEngine.maxArraySize:
            return False

        txlist = [StackItem.FromInterface(tx) for tx in block.FullTransactions]
        engine.CurrentContext.EvaluationStack.PushT(txlist)
        return True

    def Block_GetTransaction(self, engine: ExecutionEngine):
        block = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        index = engine.CurrentContext.EvaluationStack.Pop().GetBigInteger()

        if block is None or index < 0 or index > len(block.Transactions):
            return False

        tx = StackItem.FromInterface(block.FullTransactions[index])
        engine.CurrentContext.EvaluationStack.PushT(tx)
        return True

    def Transaction_GetHash(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if tx is None:
            return False

        engine.CurrentContext.EvaluationStack.PushT(tx.Hash.ToArray())
        return True

    def Transaction_GetType(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if tx is None:
            return False

        if isinstance(tx.Type, bytes):
            engine.CurrentContext.EvaluationStack.PushT(tx.Type)
        else:
            engine.CurrentContext.EvaluationStack.PushT(tx.Type.to_bytes(1, 'little'))
        return True

    def Transaction_GetAttributes(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if tx is None:
            return False

        if len(tx.Attributes) > ApplicationEngine.maxArraySize:
            return False

        attr = [StackItem.FromInterface(attr) for attr in tx.Attributes]
        engine.CurrentContext.EvaluationStack.PushT(attr)
        return True

    def Transaction_GetInputs(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if tx is None:
            return False

        if len(tx.inputs) > ApplicationEngine.maxArraySize:
            return False

        inputs = [StackItem.FromInterface(input) for input in tx.inputs]
        engine.CurrentContext.EvaluationStack.PushT(inputs)
        return True

    def Transaction_GetOutputs(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface()

        if tx is None:
            return False

        if len(tx.outputs) > ApplicationEngine.maxArraySize:
            return False

        outputs = []
        for output in tx.outputs:
            stackoutput = StackItem.FromInterface(output)
            outputs.append(stackoutput)

        engine.CurrentContext.EvaluationStack.PushT(outputs)
        return True

    def Transaction_GetReferences(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface()

        if tx is None:
            return False

        if len(tx.inputs) > ApplicationEngine.maxArraySize:
            return False

        refs = [StackItem.FromInterface(tx.References[input]) for input in tx.inputs]

        engine.CurrentContext.EvaluationStack.PushT(refs)
        return True

    def Transaction_GetUnspentCoins(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface()

        if tx is None:
            return False

        outputs = Blockchain.GetInstance().GetAllUnspent(tx.Hash)
        if len(outputs) > ApplicationEngine.maxArraySize:
            return False

        refs = [StackItem.FromInterface(unspent) for unspent in outputs]
        engine.CurrentContext.EvaluationStack.PushT(refs)
        return True

    def Transaction_GetWitnesses(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface()

        if tx is None:
            return False

        if len(tx.scripts) > ApplicationEngine.maxArraySize:
            return False

        witnesses = [StackItem.FromInterface(s) for s in tx.scripts]
        engine.CurrentContext.EvaluationStack.PushT(witnesses)
        return True

    def InvocationTransaction_GetScript(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if tx is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(tx.Script)
        return True

    def Witness_GetVerificationScript(self, engine: ExecutionEngine):
        witness = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if witness is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(witness.VerificationScript)
        return True

    def Attribute_GetUsage(self, engine: ExecutionEngine):
        attr = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if attr is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(attr.Usage)
        return True

    def Attribute_GetData(self, engine: ExecutionEngine):
        attr = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if attr is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(attr.Data)
        return True

    def Input_GetHash(self, engine: ExecutionEngine):
        input = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if input is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(input.PrevHash.ToArray())
        return True

    def Input_GetIndex(self, engine: ExecutionEngine):
        input = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if input is None:
            return False

        engine.CurrentContext.EvaluationStack.PushT(int(input.PrevIndex))
        return True

    def Output_GetAssetId(self, engine: ExecutionEngine):
        output = engine.CurrentContext.EvaluationStack.Pop().GetInterface()

        if output is None:
            return False

        engine.CurrentContext.EvaluationStack.PushT(output.AssetId.ToArray())
        return True

    def Output_GetValue(self, engine: ExecutionEngine):
        output = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if output is None:
            return False

        engine.CurrentContext.EvaluationStack.PushT(output.Value.GetData())
        return True

    def Output_GetScriptHash(self, engine: ExecutionEngine):
        output = engine.CurrentContext.EvaluationStack.Pop().GetInterface()

        if output is None:
            return False

        engine.CurrentContext.EvaluationStack.PushT(output.ScriptHash.ToArray())
        return True

    def Account_GetScriptHash(self, engine: ExecutionEngine):
        account = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if account is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(account.ScriptHash.ToArray())
        return True

    def Account_GetVotes(self, engine: ExecutionEngine):
        account = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if account is None:
            return False

        votes = [StackItem.FromInterface(v.EncodePoint(True)) for v in account.Votes]
        engine.CurrentContext.EvaluationStack.PushT(votes)
        return True

    def Account_GetBalance(self, engine: ExecutionEngine):
        account = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        assetId = UInt256(data=engine.CurrentContext.EvaluationStack.Pop().GetByteArray())

        if account is None:
            return False
        balance = account.BalanceFor(assetId)
        engine.CurrentContext.EvaluationStack.PushT(balance.GetData())
        return True

    def Asset_GetAssetId(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.AssetId.ToArray())
        return True

    def Asset_GetAssetType(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.AssetType)
        return True

    def Asset_GetAmount(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.Amount.GetData())
        return True

    def Asset_GetAvailable(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.Available.GetData())
        return True

    def Asset_GetPrecision(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.Precision)
        return True

    def Asset_GetOwner(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.Owner.EncodePoint(True))
        return True

    def Asset_GetAdmin(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.Admin.ToArray())
        return True

    def Asset_GetIssuer(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.Issuer.ToArray())
        return True

    def Contract_GetScript(self, engine: ExecutionEngine):
        contract = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if contract is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(contract.Code.Script)
        return True

    def Contract_IsPayable(self, engine: ExecutionEngine):
        contract = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if contract is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(contract.Payable)
        return True

    def Storage_GetContext(self, engine: ExecutionEngine):
        hash = UInt160(data=engine.CurrentContext.ScriptHash())
        context = StorageContext(script_hash=hash)

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(context))

        return True

    def Storage_GetReadOnlyContext(self, engine: ExecutionEngine):
        hash = UInt160(data=engine.CurrentContext.ScriptHash())
        context = StorageContext(script_hash=hash, read_only=True)

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(context))

        return True

    def StorageContext_AsReadOnly(self, engine: ExecutionEngine):
        context = engine.CurrentContext.EvaluationStack.Pop.GetInterface()

        if context is None:
            return False

        if not context.IsReadOnly:
            context = StorageContext(script_hash=context.ScriptHash, read_only=True)

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(context))
        return True

    def Storage_Get(self, engine: ExecutionEngine):
        context = None
        try:
            item = engine.CurrentContext.EvaluationStack.Pop()
            context = item.GetInterface()
        except Exception as e:
            #logger.error("could not get storage context %s " % e)
            return False

        if not self.CheckStorageContext(context):
            return False

        key = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        storage_key = StorageKey(script_hash=context.ScriptHash, key=key)
        item = self.Storages.TryGet(storage_key.ToArray())

        keystr = key

        valStr = bytearray(0)

        if item is not None:
            valStr = bytearray(item.Value)

        if len(key) == 20:
            keystr = Crypto.ToAddress(UInt160(data=key))

            try:
                valStr = int.from_bytes(valStr, 'little')
            except Exception as e:
                raise Exception("Could not convert %s to number: %s " % (valStr, e))

        if item is not None:
            engine.CurrentContext.EvaluationStack.PushT(bytearray(item.Value))

        else:
            engine.CurrentContext.EvaluationStack.PushT(bytearray(0))

        tx_hash = None
        if engine.ScriptContainer:
            tx_hash = engine.ScriptContainer.Hash

        self.events_to_dispatch.append(SmartContractEvent(SmartContractEvent.STORAGE_GET, ContractParameter(ContractParameterType.String, value='%s -> %s' % (keystr, valStr)),
                                                          context.ScriptHash, Blockchain.GetInstance().Height + 1, tx_hash, test_mode=engine.testMode))

        return True

    def Storage_Find(self, engine: ExecutionEngine):
        context = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if context is None:
            return False

        if not self.CheckStorageContext(context):
            return False

        prefix = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        prefix = context.ScriptHash.ToArray() + prefix

        iterator = self.Storages.TryFind(prefix)
        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(iterator))

        return True

    def Enumerator_Create(self, engine: ExecutionEngine):
        item = engine.CurrentContext.EvaluationStack.Pop()
        if isinstance(item, Array):
            enumerator = ArrayWrapper(item)
            engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(enumerator))
            return True
        return False

    def Enumerator_Next(self, engine: ExecutionEngine):
        item = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if item is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(item.Next())
        return True

    def Enumerator_Value(self, engine: ExecutionEngine):
        item = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if item is None:
            return False

        engine.CurrentContext.EvaluationStack.PushT(item.Value())
        return True

    def Enumerator_Concat(self, engine: ExecutionEngine):
        item1 = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if item1 is None:
            return False

        item2 = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if item2 is None:
            return False

        result = ConcatenatedEnumerator(item1, item2)
        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(result))
        return True

    def Iterator_Create(self, engine: ExecutionEngine):
        item = engine.CurrentContext.EvaluationStack.Pop()
        if isinstance(item, Map):
            iterator = MapWrapper(item)
            engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(iterator))
            return True
        return False

    def Iterator_Key(self, engine: ExecutionEngine):
        iterator = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if iterator is None:
            return False

        engine.CurrentContext.EvaluationStack.PushT(iterator.Key())
        return True

    def Iterator_Keys(self, engine: ExecutionEngine):
        iterator = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if iterator is None:
            return False
        wrapper = StackItem.FromInterface(KeysWrapper(iterator))
        engine.CurrentContext.EvaluationStack.PushT(wrapper)
        return True

    def Iterator_Values(self, engine: ExecutionEngine):
        iterator = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if iterator is None:
            return False

        wrapper = StackItem.FromInterface(ValuesWrapper(iterator))
        engine.CurrentContext.EvaluationStack.PushT(wrapper)
        return True
