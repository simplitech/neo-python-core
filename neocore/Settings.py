"""
These are the core network and system settings. For user-preferences, take a
look at `UserPreferences.py`.

The settings are dynamically configurable, for instance to set them depending
on CLI arguments. By default these are the testnet settings, but you can
reconfigure them by calling the `setup(..)` methods.
"""
import json
import logging
import os
import sys
import pip
from neocore.Cryptography import Helper
from neocore import __version__


dir_current = os.path.dirname(os.path.abspath(__file__))

# ROOT_INSTALL_PATH is the root path of neo-python, whether installed as package or from git.
ROOT_INSTALL_PATH = os.path.abspath(os.path.join(dir_current, ".."))

# This detects if we are running from an 'editable' version (like ``python neo/bin/prompt.py``)
# or from a packaged install version from pip
IS_PACKAGE_INSTALL = 'site-packages/neo' in dir_current

# The filenames for various files. Might be improved by using system
# user directories: https://github.com/ActiveState/appdirs
FILENAME_PREFERENCES = os.path.join(ROOT_INSTALL_PATH, 'neocore/Data/preferences.json')

# The protocol json files are always in the project root
FILENAME_SETTINGS_MAINNET = os.path.join(ROOT_INSTALL_PATH, 'neocore/Data/protocol.mainnet.json')
FILENAME_SETTINGS_TESTNET = os.path.join(ROOT_INSTALL_PATH, 'neocore/Data/protocol.testnet.json')
FILENAME_SETTINGS_PRIVNET = os.path.join(ROOT_INSTALL_PATH, 'neocore/Data/protocol.privnet.json')
FILENAME_SETTINGS_COZNET = os.path.join(ROOT_INSTALL_PATH, 'neocore/Data/protocol.coz.json')
FILENAME_SETTINGS_UNITTEST_NET = os.path.join(ROOT_INSTALL_PATH, 'neocore/Data/protocol.unittest-net.json')


class PrivnetConnectionError(Exception):
    pass


class SystemCheckError(Exception):
    pass


def check_depdendencies():
    """
    Makes sure that all required dependencies are installed in the exact version
    (as specified in requirements.txt)
    """
    # Get installed packages
    installed_packages = pip.get_installed_distributions(local_only=False)
    installed_packages_list = sorted(["%s==%s" % (i.key, i.version) for i in installed_packages])

    # Now check if each package specified in requirements.txt is actually installed
    deps_filename = os.path.join(ROOT_INSTALL_PATH, "requirements.txt")
    with open(deps_filename, "r") as f:
        for dep in f.read().split():
            if not dep.lower() in installed_packages_list:
                raise SystemCheckError("Required dependency %s is not installed. Please run 'pip install -e .'" % dep)


class SettingsHolder:
    """
    This class holds all the settings. Needs to be setup with one of the
    `setup` methods before using it.
    """
    MAGIC = None
    ADDRESS_VERSION = None
    STANDBY_VALIDATORS = None
    SEED_LIST = None
    RPC_LIST = None

    ENROLLMENT_TX_FEE = None
    ISSUE_TX_FEE = None
    PUBLISH_TX_FEE = None
    REGISTER_TX_FEE = None

    DATA_DIR_PATH = None
    LEVELDB_PATH = None
    NOTIFICATION_DB_PATH = None

    RPC_PORT = None
    NODE_PORT = None
    WS_PORT = None
    URI_PREFIX = None
    BOOTSTRAP_FILE = None
    NOTIF_BOOTSTRAP_FILE = None

    ALL_FEES = None
    USE_DEBUG_STORAGE = False
    DEBUG_STORAGE_PATH = 'Chains/debugstorage'

    ACCEPT_INCOMING_PEERS = False
    CONNECTED_PEER_MAX = 5

    SERVICE_ENABLED = True

    COMPILER_NEP_8 = True

    VERSION_NAME = "/NEO-PYTHON:%s/" % __version__

    # Logging settings
    log_level = None
    log_smart_contract_events = False
    log_vm_instructions = False

    # Emit Notify events when smart contract execution failed. Use for debugging purposes only.
    emit_notify_events_on_sc_execution_error = False

    rotating_filehandler = None

    @property
    def chain_leveldb_path(self):
        self.check_chain_dir_exists(warn_migration=True)
        return os.path.abspath(os.path.join(self.DATA_DIR_PATH, self.LEVELDB_PATH))

    @property
    def notification_leveldb_path(self):
        self.check_chain_dir_exists()
        return os.path.abspath(os.path.join(self.DATA_DIR_PATH, self.NOTIFICATION_DB_PATH))

    @property
    def debug_storage_leveldb_path(self):
        self.check_chain_dir_exists()
        return os.path.abspath(os.path.join(self.DATA_DIR_PATH, self.DEBUG_STORAGE_PATH))

    # Helpers
    @property
    def is_mainnet(self):
        """ Returns True if settings point to MainNet """
        return self.NODE_PORT == 10333 and self.MAGIC == 7630401

    @property
    def is_testnet(self):
        """ Returns True if settings point to TestNet """
        return self.NODE_PORT == 20333 and self.MAGIC == 1953787457

    @property
    def is_coznet(self):
        """ Returns True if settings point to CoZnet """
        return self.NODE_PORT == 20333 and self.MAGIC == 1010102

    @property
    def net_name(self):
        if self.MAGIC is None:
            return 'None'
        if self.is_mainnet:
            return 'MainNet'
        if self.is_testnet:
            return 'TestNet'
        if self.is_coznet:
            return 'CozNet'
        return 'PrivateNet'

    # Setup methods
    def setup(self, config_file):
        #TODO
        # """ Setup settings from a JSON config file """
        # if not self.DATA_DIR_PATH:
        #     # Setup default data dir
        #     self.set_data_dir(None)

        with open(config_file) as data_file:
            data = json.load(data_file)

        config = data['ProtocolConfiguration']
        self.MAGIC = config['Magic']
        self.ADDRESS_VERSION = config['AddressVersion']
        self.STANDBY_VALIDATORS = config['StandbyValidators']
        self.SEED_LIST = config['SeedList']
        self.RPC_LIST = config['RPCList']

        fees = config['SystemFee']
        self.ALL_FEES = fees
        self.ENROLLMENT_TX_FEE = fees['EnrollmentTransaction']
        self.ISSUE_TX_FEE = fees['IssueTransaction']
        self.PUBLISH_TX_FEE = fees['PublishTransaction']
        self.REGISTER_TX_FEE = fees['RegisterTransaction']

        config = data['ApplicationConfiguration']
        self.LEVELDB_PATH = config['DataDirectoryPath']
        self.RPC_PORT = int(config['RPCPort'])
        self.NODE_PORT = int(config['NodePort'])
        self.WS_PORT = config['WsPort']
        self.URI_PREFIX = config['UriPrefix']
        self.ACCEPT_INCOMING_PEERS = config.get('AcceptIncomingPeers', False)

        self.BOOTSTRAP_FILE = config['BootstrapFile']
        self.NOTIF_BOOTSTRAP_FILE = config['NotificationBootstrapFile']

        Helper.ADDRESS_VERSION = self.ADDRESS_VERSION

        self.USE_DEBUG_STORAGE = config.get('DebugStorage', True)
        self.DEBUG_STORAGE_PATH = config.get('DebugStoragePath', 'Chains/debugstorage')
        self.NOTIFICATION_DB_PATH = config.get('NotificationDataPath', 'Chains/notification_data')
        self.SERVICE_ENABLED = config.get('ServiceEnabled', False)
        self.COMPILER_NEP_8 = config.get('CompilerNep8', False)

    def setup_mainnet(self):
        """ Load settings from the mainnet JSON config file """
        self.setup(FILENAME_SETTINGS_MAINNET)

    def setup_testnet(self):
        """ Load settings from the testnet JSON config file """
        self.setup(FILENAME_SETTINGS_TESTNET)

    def setup_privnet(self, host=None):
        """
        Load settings from the privnet JSON config file

        Args:
            host (string, optional): if supplied, uses this IP or domain as neo nodes. The host must
                                     use these standard ports: P2P 20333, RPC 30333.
        """
        self.setup(FILENAME_SETTINGS_PRIVNET)
        if isinstance(host, str):
            if ":" in host:
                raise Exception("No protocol prefix or port allowed in host, use just the IP or domain.")
            print("Using custom privatenet host:", host)
            self.SEED_LIST = ["%s:20333" % host]
            self.RPC_LIST = ["http://%s:30333" % host]
            print("- P2P:", ", ".join(self.SEED_LIST))
            print("- RPC:", ", ".join(self.RPC_LIST))
        self.check_privatenet()

    def setup_unittest_net(self, host=None):
        """ Load settings from privnet JSON config file. """
        self.setup(FILENAME_SETTINGS_UNITTEST_NET)

    def setup_coznet(self):
        """ Load settings from the coznet JSON config file """
        self.setup(FILENAME_SETTINGS_COZNET)

# Settings instance used by external modules
settings = SettingsHolder()

# Load testnet settings as default. This is useful to provide default data/db directories
# to any code using "from neo.Settings import settings"
settings.setup_testnet()

# By default, set loglevel to INFO. DEBUG just print a lot of internal debug statements
#TODO
#settings.set_loglevel(logging.INFO)

# System check: Are dependencies must be installed in the correct version
# Can be bypassed with `SKIP_DEPS_CHECK=1 python prompt.py`
# this causes so many headaches when developing between boa and neo and core... :(
# if not os.getenv("SKIP_DEPS_CHECK") and not IS_PACKAGE_INSTALL:
#     check_depdendencies()

# System check: Python 3.6+
if not os.getenv("SKIP_PY_CHECK"):
    if sys.version_info < (3, 6):
        raise SystemCheckError("Needs Python 3.6+. Currently used: %s" % sys.version)
