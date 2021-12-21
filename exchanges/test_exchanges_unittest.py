import unittest
from exchange_base import MetaMarket
import warnings



class TestBinance(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super(TestBinance, self).__init__(methodName)
        self.binance = Binance("ADA", 'BTC')

    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed.*<ssl.SSLSocket.*>") 

    def test_init(self):
        self.assertEqual(type(self.binance), Binance)

    def test_historic(self):
        a = Binance(*"BNB/ONG".split('/'))
        self.assertEqual(a._check_historic(), None)

    def test_get_price(self):
        self.assertTrue(self.binance.price)
        self.assertTrue(self.binance.price>0)



if __name__ == '__main__':
    unittest.main()