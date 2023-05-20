#!/usr/bin/env python

"""Tests for `ragnarok` package."""

import unittest
from zpywallet import wallet


class TestZPyWallet(unittest.TestCase):
    """Tests for `ragnarok` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""
        hdw = wallet.create_wallet()
        assert hdw
