from twisted.application.service import IServiceMaker
from twisted.application.strports import service
from twisted.plugin import IPlugin
from twisted.python.usage import Options
from twisted.web.server import Site
from zope.interface import implementer

from soapproxy.proxy import ProxyResource



class ProxyOptions(Options):
    optFlags = [['no-verify-tls', None, 'Disable TLS verification']]
    optParameters = [['endpoint', 'p', None, 'The endpoint to listen on.'],
                     ['uri', 'u', None, 'The URI to proxy to.'],
                    ]



@implementer(IServiceMaker, IPlugin)
class ServiceMaker(object):
    tapname = 'soap-proxy'
    description = 'Simple SOAP reverse proxy'
    options = ProxyOptions

    def makeService(self, options):
        site = Site(ProxyResource(
            uri=options['uri'], verify=not options['no-verify-tls']))
        return service(options['endpoint'], site)
