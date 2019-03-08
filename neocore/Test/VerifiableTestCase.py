
import os

from neocore.Test.NeoTestCase import NeoTestCase


class VerifiableTestCase(NeoTestCase):

    #LEVELDB_TESTPATH = os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    _blockchain = None

    #TODO
    # @classmethod
    # def setUpClass(self):
    #
    #     Blockchain.DeregisterBlockchain()
    #
    #     os.makedirs(self.LEVELDB_TESTPATH, exist_ok=True)
    #     self._blockchain = LevelDBBlockchain(path=self.LEVELDB_TESTPATH, skip_version_check=True)
    #     Blockchain.RegisterBlockchain(self._blockchain)
    #
    # @classmethod
    # def tearDownClass(cls):
    #
    #     Blockchain.Default().DeregisterBlockchain()
    #     if cls._blockchain is not None:
    #         cls._blockchain.Dispose()
    #
    #     shutil.rmtree(cls.LEVELDB_TESTPATH)
