import time
import random
from zjsn_uncensor.MITMproxy.addon import cache_for

@cache_for(1)
def test():
    return random.random()


print(test())
print(test())
time.sleep(0.5)
print(test())
time.sleep(1)
print(test())
