# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from . import manager
from . import utils


try:
    from unittest import mock
except ImportError:  # pragma: no cover
    import mock  # NOQA


MagicMock = mock.MagicMock
patch = mock.patch
call = mock.call


class AMIProtocol(manager.AMIProtocol):

    debug_count = [0]

    def connection_made(self, transport):
        super(AMIProtocol, self).connection_made(transport)
        self.transport = MagicMock()

    def send(self, data, as_list=False):
        utils.IdGenerator.reset(uid='transaction_uid')
        future = super(AMIProtocol, self).send(data, as_list=as_list)
        if self.factory.stream is not None:
            with open(self.factory.stream, 'rb') as fd:
                for resp in fd.read().split(b'\n\n'):
                    self.data_received(resp + b'\n\n')
                    if future.done():
                        break
            if not future.done():  # pragma: no cover
                print(self.responses)
                raise AssertionError("Future's result was never set")
        return future


class Manager(manager.Manager):

    fixtures_dir = None

    def __init__(self, **config):
        self.defaults.update(
            protocol_factory=AMIProtocol,
            stream=None)
        super(Manager, self).__init__(**config)

        self.stream = self.config.get('stream')
        self.loop = utils.asyncio.get_event_loop()

        protocol = AMIProtocol()
        protocol.factory = manager
        protocol.connection_made(mock.MagicMock())
        future = utils.asyncio.Future()
        future.set_result((mock.MagicMock(), protocol))
        self.protocol = protocol
        self.connection_made(future)

        utils.IdGenerator.reset(uid='transaction_uid')
        utils.EOL = '\n'
