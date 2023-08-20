import time
import datetime
from brownie import *

network.connect('avax-main')
user = accounts.load('test_account')

print(user.balance()/(10**18))

router = Contract.from_explorer('0x60aE616a2155Ee3d9A68541Ba4544862310933d4')
mim = Contract.from_explorer('0x130966628846bfd36ff31a822705796e8cb8c18d')
dai = Contract.from_explorer('0xd586e7f844cea2f87f50152665bcbc2c279d8d70')
wavax = Contract.from_explorer('0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7')

print('mim balance', mim.balanceOf(user.address))
print('dai balance', dai.balanceOf(user.address))
print('min allowance', mim.allowance(user.address, router.address))
print('dai allowance', dai.allowance(user.address, router.address))
