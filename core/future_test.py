# -*- coding: utf-8 -*-

import unittest

import numpy as np
from wolfox.fengine.core.future import * 

class ModuleTest(unittest.TestCase):
    def test_mm_ratio(self):
        shigh = np.array([200,250,200,400])
        slow = np.array([100,200,100,200])
        sclose = np.array([150,220,180,300])
        amfe,amae = mm_ratio(sclose,shigh,slow,2,1)
        self.assertEquals([700,800,0,0],amfe.tolist())
        self.assertEquals([-300,400,0,0],amae.tolist())        
        #self.assertEquals([100,100,120,250],atr(sclose,shigh,slow,1).tolist())
        
    def test_decline(self):
        sclose = np.array([1000,1005,1007,990,940,920,900,910,960,930,915,990,1020,990])
        self.assertEquals((107,4),decline(sclose))
        sclose = np.array([1000,1005,1007,990,940,920,900,910,960,930,891,990,1020,990])
        self.assertEquals((116,8),decline(sclose))
        sclose = np.array([1000,1005,1007,990,940,920,900,910,960,1030,1050,990,970,930,935,915,990,1040,1080])
        self.assertEquals((135,5),decline(sclose))


if __name__ == "__main__":
    import logging
    logging.basicConfig(filename="test.log",level=logging.DEBUG,format='%(name)s:%(funcName)s:%(lineno)d:%(asctime)s %(levelname)s %(message)s')
    unittest.main()

