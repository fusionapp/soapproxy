from OpenSSL import SSL
from twisted.internet import reactor
from twisted.internet.interfaces import IOpenSSLClientConnectionCreator
from twisted.internet.ssl import PrivateCertificate, CertificateOptions
from twisted.python.filepath import FilePath
from twisted.python.urlpath import URLPath
from twisted.web.client import (
    Agent, FileBodyProducer, HTTPConnectionPool, PartialDownloadError,
    readBody)
from twisted.web.http_headers import Headers
from twisted.web.iweb import IPolicyForHTTPS
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from zope.interface import implementer



@implementer(IPolicyForHTTPS)
class StupidPolicyForHTTPS(object):
    """
    TLS connection creator factory that always returns the same creator.
    """
    def __init__(self, creator):
        self._creator = creator


    def creatorForNetloc(self, hostname, port):
        return self._creator



@implementer(IOpenSSLClientConnectionCreator)
class InsecureTLSOptions(object):
    """
    TLS client creator that does not verify the peer.
    """
    def __init__(self, clientCert=None):
        if clientCert is None:
            options = CertificateOptions()
        else:
            options = clientCert.options()
        self._ctx = options.getContext()


    def clientConnectionForTLS(self, tlsProtocol):
        connection = SSL.Connection(self._ctx, None)
        connection.set_app_data(tlsProtocol)
        return connection



class ProxyResource(Resource):
    """
    Resource that proxies SOAP requests.
    """
    isLeaf = True

    def __init__(self, uri, verify, timeout=600, reactor=reactor, clientCert=None):
        Resource.__init__(self)
        self._uri = URLPath.fromString(uri)
        self._verify = verify
        self._timeout = timeout
        self._reactor = reactor
        pool = HTTPConnectionPool(reactor)
        if clientCert is not None:
            clientCert = PrivateCertificate.loadPEM(
                FilePath(clientCert).getContent())
        self._agent = Agent(
            reactor,
            StupidPolicyForHTTPS(InsecureTLSOptions(clientCert)),
            pool=pool)


    def render(self, request):
        """
        Forward the request.
        """
        def writeResponse(response):
            request.setResponseCode(response.code)
            request.setHeader(
                'content-type',
                response.headers.getRawHeaders(
                    'content-type', ['application/xml'])[0])
            return readBody(response).addErrback(eatPartial).addCallback(write)

        def eatPartial(f):
            f.trap(PartialDownloadError)
            return f.value.response

        def writeError(f):
            request.setResponseCode(500)
            request.write(f.getTraceback())
            request.finish()

        def write(r):
            request.setHeader('content-length', '%d' % (len(r),))
            request.write(r)
            request.finish()

        def notify(reason):
            if reason is not None:
                d.cancel()

        uri = URLPath.fromString(request.uri)
        uri.scheme = self._uri.scheme
        uri.netloc = self._uri.netloc
        if request.method in {'GET', 'HEAD', 'DELETE'}:
            body = None
        else:
            body = FileBodyProducer(request.content)
        d = self._agent.request(
            request.method,
            str(uri),
            Headers({'user-agent': ['Fusion SOAP proxy'],
                     'content-type': request.requestHeaders.getRawHeaders(
                         'content-type', ['application/xml']),
                     'soapaction': request.requestHeaders.getRawHeaders(
                         'soapaction', ['']),
                     'authorization': request.requestHeaders.getRawHeaders(
                         'authorization', [])}),
            body)
        call = self._reactor.callLater(self._timeout, d.cancel)
        def cancelTimeout(result):
            if call.active():
                call.cancel()
            return result
        d.addCallback(writeResponse)
        d.addBoth(cancelTimeout)
        d.addErrback(writeError)
        request.notifyFinish().addCallback(notify)
        return NOT_DONE_YET
