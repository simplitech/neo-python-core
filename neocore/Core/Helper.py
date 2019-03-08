from base58 import b58decode
import binascii
from neocore.Core.Contract import TriggerType
from neocore.Core.Contract.ApplicationEngine import ApplicationEngine

from neocore.Core.VM.ScriptBuilder import ScriptBuilder
from neocore.Cryptography.Crypto import Crypto
from neocore.IO.BinaryWriter import BinaryWriter
from neocore.UInt160 import UInt160
from neocore.IO.MemoryStream import StreamManager
from neocore.Fixed8 import Fixed8
from neocore.Settings import settings



class Helper:

    @staticmethod
    def WeightedFilter(list):
        raise NotImplementedError()

    @staticmethod
    def WeightedAverage(list):
        raise NotImplementedError()

    @staticmethod
    def GetHashData(hashable):
        """
        Get the data used for hashing.

        Args:
            hashable (neocore.IO.Mixins.SerializableMixin): object extending SerializableMixin

        Returns:
            bytes:
        """
        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)
        hashable.SerializeUnsigned(writer)
        ms.flush()
        retVal = ms.ToArray()
        StreamManager.ReleaseStream(ms)
        return retVal

    @staticmethod
    def Sign(verifiable, keypair):
        """
        Sign the `verifiable` object with the private key from `keypair`.

        Args:
            verifiable:
            keypair (neocore.KeyPair):

        Returns:
            bool: True if successfully signed. False otherwise.
        """
        prikey = bytes(keypair.PrivateKey)
        hashdata = verifiable.GetHashData()
        res = Crypto.Default().Sign(hashdata, prikey)
        return res

    @staticmethod
    def ToArray(value):
        """
        Serialize the given `value` to a an array of bytes.

        Args:
            value (neocore.IO.Mixins.SerializableMixin): object extending SerializableMixin.

        Returns:
            bytes: hex formatted bytes
        """
        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)

        value.Serialize(writer)

        retVal = ms.ToArray()
        StreamManager.ReleaseStream(ms)

        return retVal

    @staticmethod
    def ToStream(value):
        """
        Serialize the given `value` to a an array of bytes.

        Args:
            value (neocore.IO.Mixins.SerializableMixin): object extending SerializableMixin.

        Returns:
            bytes: not hexlified
        """
        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)

        value.Serialize(writer)

        retVal = ms.getvalue()
        StreamManager.ReleaseStream(ms)

        return retVal

    @staticmethod
    def AddrStrToScriptHash(address):
        """
        Convert a public address to a script hash.

        Args:
            address (str): base 58 check encoded public address.

        Raises:
            ValueError: if the address length of address version is incorrect.
            Exception: if the address checksum fails.

        Returns:
            UInt160:
        """
        data = b58decode(address)
        if len(data) != 25:
            raise ValueError('Not correct Address, wrong length.')
        if data[0] != settings.ADDRESS_VERSION:
            raise ValueError('Not correct Coin Version')

        checksum = Crypto.Default().Hash256(data[:21])[:4]
        if checksum != data[21:]:
            raise Exception('Address format error')
        return UInt160(data=data[1:21])

    @staticmethod
    def ToScriptHash(scripts):
        """
        Get a hash of the provided message using the ripemd160 algorithm.

        Args:
            scripts (str): message to hash.

        Returns:
            str: hash as a double digit hex string.
        """
        return Crypto.Hash160(scripts)

    @staticmethod
    def RawBytesToScriptHash(raw):
        """
        Get a hash of the provided raw bytes using the ripemd160 algorithm.

        Args:
            raw (bytes): byte array of raw bytes. i.e. b'\xAA\xBB\xCC'

        Returns:
            UInt160:
        """
        rawh = binascii.unhexlify(raw)
        rawhashstr = binascii.unhexlify(bytes(Crypto.Hash160(rawh), encoding='utf-8'))
        return UInt160(data=rawhashstr)

    @staticmethod
    def VerifyScripts(verifiable):
        """
        Verify the scripts of the provided `verifiable` object.

        Args:
            verifiable (neocore.IO.Mixins.VerifiableMixin):

        Returns:
            bool: True if verification is successful. False otherwise.
        """
        try:
            hashes = verifiable.GetScriptHashesForVerifying()
        except Exception as e:
            raise Exception("Error: couldn't get script hashes %s " % e)

        if len(hashes) != len(verifiable.Scripts):
            return False

        blockchain = GetBlockchain()

        for i in range(0, len(hashes)):
            verification = verifiable.Scripts[i].VerificationScript

            if len(verification) == 0:
                sb = ScriptBuilder()
                sb.EmitAppCall(hashes[i].Data)
                verification = sb.ToArray()

            else:
                verification_hash = Crypto.ToScriptHash(verification, unhex=False)
                if hashes[i] != verification_hash:
                    return False

            state_reader = GetStateReader()
            engine = ApplicationEngine(TriggerType.Verification, verifiable, blockchain, state_reader, Fixed8.Zero())
            engine.LoadScript(verification)
            invocation = verifiable.Scripts[i].InvocationScript
            engine.LoadScript(invocation)

            try:
                success = engine.Execute()
                state_reader.ExecutionCompleted(engine, success)
            except Exception as e:
                state_reader.ExecutionCompleted(engine, False, e)

            if engine.ResultStack.Count != 1 or not engine.ResultStack.Pop().GetBoolean():
                Helper.EmitServiceEvents(state_reader)
                return False

            Helper.EmitServiceEvents(state_reader)

        return True

    @staticmethod
    def IToBA(value):
        return [1 if digit == '1' else 0 for digit in bin(value)[2:]]

    @staticmethod
    def EmitServiceEvents(state_reader):
        return
        #for event in state_reader.events_to_dispatch:
            #TODO
            #events.emit(event.event_type, event)
