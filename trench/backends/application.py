from trench.backends import AbstractMessageDispatcher
from trench.utils import create_qr_link


class ApplicationBackend(AbstractMessageDispatcher):
    def dispatch_message(self):
        return {'qr_link': create_qr_link(self.obj.secret, self.user)}
