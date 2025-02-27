"""
:mod:`app` -- Rest App
===================================
.. moduleauthor:: ilya Barinov <i-barinov@it-serv.ru>
"""

from ext_kit_shop.di.rest import RestDI

di = RestDI()

di.init_resources()
app = di.app
