"""
Description:
    Issue Transaction
Usage:
    from neocore.Core.TX.IssueTransaction import IssueTransaction
"""
from neocore.Core.TX.Transaction import Transaction, TransactionType
from neocore.Fixed8 import Fixed8


class IssueTransaction(Transaction):
    Nonce = None

    """docstring for IssueTransaction"""

    def __init__(self, *args, **kwargs):
        """
        Create an instance.

        Args:
            *args:
            **kwargs:
        """
        super(IssueTransaction, self).__init__(*args, **kwargs)
        self.Type = TransactionType.IssueTransaction  # 0x40

    def SystemFee(self):
        """
        Get the system fee.

        Returns:
            Fixed8:
        """
        if self.Version >= 1:
            return Fixed8.Zero()

        # if all outputs are NEO or gas, return 0
        all_neo_gas = True
        for output in self.outputs:
            from neocore.Core.Blockchain import Blockchain
            if output.AssetId != Blockchain.GetInstance().GetSystemCoin().Hash and output.AssetId != Blockchain.GetInstance().GetSystemShare().Hash:
                all_neo_gas = False
        if all_neo_gas:
            return Fixed8.Zero()

        return super(IssueTransaction, self).SystemFee()

    def GetScriptHashesForVerifying(self):
        pass

    def DeserializeExclusiveData(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neocore.IO.BinaryReader):
        """

        self.Type = TransactionType.IssueTransaction

        if self.Version > 1:
            raise Exception('Invalid TX Type')

    def SerializeExclusiveData(self, writer):
        pass
