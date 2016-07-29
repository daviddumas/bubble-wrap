
import math

def swift_in_out(v):
    return 1-(math.cos(math.pi*v)/2+0.5)**(3*v)

def expo_in(v):
    return (10**v-1)/9

def expo_out(v):
    if v == 0:
        return 0
    return math.log(v*10,10)/2+0.5


def cubic_in(v):
    return 1-(1-v**3)


def quadratic_in(v):
    return 1-(1-v**2)
