import os.path

_SCRIPT = os.path.dirname(os.path.realpath(__file__))
_UI = os.path.join(_SCRIPT,'ui')
_ASSETS = os.path.join(_SCRIPT,'ui','assets')

_IMAGE_NAMES = [
    'dpad_norm',
    'dpad_right',
    'dpad_up',
    'dpad_left',
    'dpad_down',
    'center_norm',
    'center_act',
    'mobius_reset_norm',
    'mobius_reset_act',
    'mobius_norm',
    'mobius_act',
    'plus_norm',
    'plus_act',
    'minus_norm',
    'minus_act',
    'dual_graph_norm',
    'dual_graph_act',
]

image = {
    k: os.path.join(_ASSETS,k+'.png') for k in _IMAGE_NAMES
}

_UI_NAMES = [
    'widget',
    'list_dialog',
    'dropdown_dialog',
    'progress_dialog',
]

ui = {
    k: os.path.join(_UI,k+'.ui') for k in _UI_NAMES
}

wordfile = os.path.join(_SCRIPT,'data','words','g2-commgen-pared-norm50.txt.bz2')

