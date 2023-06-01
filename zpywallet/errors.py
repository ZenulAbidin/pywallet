class KeyParseError(Exception):
    pass


class ChecksumException(Exception):
    """
    Raised when the generated checksum of an address or public key
    does not match the expected checksum.
    """


class IncompatibleNetworkException(Exception):
    """
    Raised when importing a piece of network data
    into the wrong network.
    """


class InvalidChildException(Exception):
    """
    Raised when an invalid child key is passed.
    """


class WatchOnlyWalletError(Exception):
    """
    Raised when a wallet does not contain a private key when
    performing an operation that requires a public key.
    """

class SegwitError(Exception):
    """
    Raised when a network does not support Segwit (P2WPKH).
    """

class InvalidPathError(Exception):
    """
    Raised when the provided derivation path is invalid.
    """

class NetworkException(Exception):
    """
    Raised when a network request fails.
    """

def incompatible_network_bytes_exception_factory(
        network_name, expected_prefix, given_prefix):
    """A factory function for IncompatibleNetworkException."""
    return IncompatibleNetworkException(
        f"Incorrect network. {network_name} expects a byte prefix of "
        f"{expected_prefix}, but you supplied {given_prefix}")


def unsupported_feature_exception_factory(
        network_name, feature):
    """Another factory function for IncompatibleNetworkException."""
    return IncompatibleNetworkException(
        f"{network_name} does not support feature: {feature}")