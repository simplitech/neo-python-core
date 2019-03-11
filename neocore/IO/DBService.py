from neocore.IO.DBCollection import DBCollection


class DBService:
    def loadDB(self, storagePath : str, createIfMissing = True):
        self.storagePath = storagePath
        self.createIfMissing = createIfMissing

    def getPrefixBlock(self):
        return b'\x01'

    def getPrefixTransaction(self):
        return b'\x02'

    def getPrefixAccount(self):
        return b'\x40'

    def getPrefixCoin(self):
        return b'\x44'

    def getPrefixSpentCoin(self):
        return b'\x45'

    def getPrefixValidator(self):
        return b'\x48'

    def getPrefixAsset(self):
        return b'\x4c'

    def getPrefixContract(self):
        return b'\x50'

    def getPrefixStorage(self):
        return b'\x70'

    def getPrefixHeaderHashList(self):
        return b'\x80'

    def getKeyCurrentBlock(self):
        return b'\xc0'

    def getKeyCurrentHeader(self):
        return b'\xc1'

    def getKeySystemVersion(self):
        return b'\xf0'

    def get(self, key):
        try:
            return self._db.get(key)
        except:
            return 0

    def put(self, key, value):
        self._db.put(key, value)

    def delete(self, key):
        self._db.delete(key)

    def getCurrentHeader(self):
        return self.get(self.getKeyCurrentHeader())

    def getSystemVersion(self):
        return -1

    def getBlock(self, hash):
        return self.get(self.getPrefixBlock() + hash)

    def getTransaction(self, hash):
        return self.get(self.getPrefixTransaction() + hash)

    def updateSystemVersion(self, sysVersion):
        return

    def getAccountsCollection(self) -> DBCollection:
        return None

    def getCoinsCollection(self) -> DBCollection:
        return None

    def getSpentCoinsCollection(self) -> DBCollection:
        return None

    def getValidatorsCollection(self) -> DBCollection:
        return None

    def getAssetsCollection(self) -> DBCollection:
        return None

    def getContractCollection(self) -> DBCollection:
        return None

    def getStorageCollection(self) -> DBCollection:
        return

    def getWriter(self):
        return

    def getDBIterator(self):
        return

    def getSnapshot(self):
        return

    def getDbIteratorForPrefix(self, prefix, include_value = False):
        return

    def getHeaderListIterator(self):
        return None

    def getBlockListIterator(self):
        return

    def getStorageListIterator(self, includeValue = False):
        return

    def GetStates(self, prefix, classref):
        return DBCollection(self._db, prefix, classref)

    def close(self):
        return

    def getInnerDB(self):
        return None








