# -*- coding: utf-8 -*-
import re
from urllib import unquote
import json as python_json
import httplib
import gzip
import StringIO
import urllib
import random
import time


HTTP_CODE = {
    200:    'OK',
    403:    'Forbidden',
    404:    'Not Found',
    500:    'Internal Server Error',
}


def _unicode2str(uni):
    if isinstance(uni, unicode):
        uni = uni.encode('utf-8')
    elif not isinstance(uni, str):
        uni = str(uni)
    return urllib.quote_plus(uni)


def _unicode(strr):
    if not isinstance(strr, unicode):
        strr = str(strr).decode('utf-8')
    return strr


def urlencode(kwargs):
    return '&'.join([
        _unicode2str(k) + '=' + _unicode2str(v)
        for k, v in kwargs.items()
    ])


def _split_url(url):
    """

    :param url:
    :return:
     host
     port
     path
     secure
    """
    if url:
        if isinstance(url, unicode):
            url = url.encode('utf-8')
        protocol_l = url.split('//')
        protocol = protocol_l.pop(0)

        if protocol == 'http:':
            secure = False
        elif protocol == 'https:':
            secure = True
        else:
            raise Exception('Invalid URL %s' % url)

        enpoint_l = ''.join(protocol_l).split('/')
        host_port = enpoint_l.pop(0)
        path = '/' + '/'.join(enpoint_l)

        if ':' in host_port:
            host, port = host_port.split(':')
        else:
            host = host_port
            port = None
        return host, port, path, secure

    else:
        raise


class RequestsResponse(object):
    """
    copy from lawliet
    """
    def __init__(self, response):
        self.response = response

    @property
    def content(self):
        if self.headers.get('content-encoding') == 'gzip':
            return gzip.GzipFile(fileobj=StringIO.StringIO(self.response.read())).read()
        else:
            return self.response.read()

    @property
    def status_code(self):
        return self.response.status

    @property
    def headers(self):
        return {k: v for k, v in self.response.getheaders()}

    @property
    def text(self):
        return self.content


class Requests(object):

    @staticmethod
    def get(url, params=None, headers=None, timeout=None):
        host, port, path, secure = _split_url(url)
        if secure:
            http = httplib.HTTPSConnection(host=host, port=port, timeout=timeout)
        else:
            http = httplib.HTTPConnection(host=host, port=port, timeout=timeout)
        if params:
            if '?' in path:
                path_l = path.split('?')
                path = path_l.pop(0)
                params.update({
                    param.split('=')[0]: param.split('=')[1]
                    for param in '?'.join(path_l).split('&')
                    if len(param.split('=')) == 2
                })

            path += '?%s' % urlencode(params)

        if headers:
            headers.update({
                'accept': '*/*',
                'connection': 'keep-alive',
            })
        else:
            headers = {
                'accept': '*/*',
                'connection': 'keep-alive',
            }

        http.request(method='GET', url=path, body=None, headers=headers)
        return RequestsResponse(http.getresponse())


class Request(object):

    """
    copy from lawliet
    """

    def __init__(self, environ):
        self.environ = environ
        self.content_type = self.environ.get('CONTENT_TYPE', None)
        self.content_length = self.environ.get('CONTENT_LENGTH') or 0
        self.content_length = int(self.content_length)
        self._param = dict()

    def header(self, header):
        http_header = re.sub('-', '_', header).upper()
        if http_header == 'CONTENT_TYPE':
            return self.environ.get(http_header, None)

        else:
            http_header = 'HTTP_' + http_header
            return self.environ.get(http_header, None)

    def get(self, name, default=None, max_length=None):
        if not self._param:
            query_string = self.environ['QUERY_STRING'].split('&')
            for data in query_string:
                key_value = data.split('=')
                if len(key_value) == 2:
                    self._param[unquote(key_value[0])] = unquote(key_value[1])

            if self.content_type == 'application/x-www-form-urlencoded':
                if max_length is not None and max_length < self.content_length:
                    raise Exception()
                output = self.environ.pop('wsgi.input')
                wsgi_file = output.read(self.content_length)
                query_string = wsgi_file.split('&')
                for data in query_string:
                    key_value = data.split('=')
                    if len(key_value) == 2:
                        self._param[unquote(key_value[0])] = unquote(key_value[1])
        return self._param.get(name, default)


class Bridge(object):
    requests = Requests()

    user_agent = [
        'Mozilla/5.0 (X11; Linux x86_64)',
        'Mozilla/5.0 (compatible; suggybot v0.01a,',
        'Mozilla/5.0 (compatible; Speedy Spider;',
        'Mozilla/5.0 (compatible; TweetedTimes Bot/1.0;'
    ]

    url = 'https://www.google.com.hk/search'

    def get_result(self, q, start):
        url_params = {"q": q, "start": start, "hl": "en"}
        headers = {'User-Agent': random.choice(self.user_agent),
                   'accept-encoding': 'gzip',
                   'referer': 'https://www.google.com.hk/'}
        try:
            r = self.requests.get(self.url, params=url_params, headers=headers, timeout=4)
        except Exception as e:
            return {'code': 402, 'msg': str(e)}
        if r.status_code != 200:
            return {'code': 400}
        json_res = dict()
        content = r.content
        with open('content1', 'w') as f:
            f.write(content)
        for _ in range(20):
            find_h3 = re.search(r'<h3 class="r">.*</h3>', content)
            if find_h3:
                result = find_h3.group(0)
                find_a = re.search(r'<a.*</a>', result)
                if find_a:
                    find_url = re.search(r'http.*&', find_a.group(0))
                    if find_url:
                        b = find_url.group(0).split('&')[0]
                        d = re.sub('<b>', '', find_a.group(0))
                        d = re.sub('</b>', '', d)
                        c = re.sub('</a>', '', d).split('>')[-1]
                        json_res[time.time()] = [urllib.unquote(b).decode('utf-8', 'ignore'),
                                                 c.decode('utf-8', 'ignore')]
                        content = ''.join(content.split(result))
            else:
                break

        return json_res

    @staticmethod
    def index(request):
        user_agent = request.header('user_agent')
        is_mobile = False
        for phone in ['Android', 'iPhone', 'iPod', 'iPad', 'Windows Phone', 'MQQBrowser']:
            if phone in user_agent:
                is_mobile = True
                break
        if is_mobile:
            return u"""
                <!DOCTYPE html>\n
                <html lang="zh-cmn-Hans">\n
                <head>\n
                    <meta charset="UTF-8">\n
                    <meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=0">\n
                    <title>Googlebridge-Open</title>\n
                <link rel="stylesheet" href="//cdn.bootcss.com/weui/1.1.1/style/weui.min.css">\n
                <link rel="stylesheet" href="//cdn.bootcss.com/jquery-weui/1.0.1/css/jquery-weui.min.css">\n
                </head>\n
                <body style="background-color:#f8f8f8;">\n
                <div class="weui-search-bar" id="searchBar">\n
                  <form class="weui-search-bar__form" action="/search" method="get">\n
                    <div class="weui-search-bar__box">\n
                      <i class="weui-icon-search"></i>\n
                      <input type="search" class="weui-search-bar__input" id="searchInput" placeholder="search"
                      required="" name="q">\n
                    </div>\n
                    <label class="weui-search-bar__label" id="searchText">\n
                      <i class="weui-icon-search"></i>\n
                      <span>search</span>\n
                    </label>\n
                  </form>\n
                  <a href="/" class="weui-search-bar__cancel-btn" id="searchCancel">Cancel</a>\n
                </div>\n
                <script src="//cdn.bootcss.com/jquery/1.11.0/jquery.min.js"></script>\n
                <script src="//cdn.bootcss.com/jquery-weui/1.0.1/js/jquery-weui.min.js"></script>\n

                </body>\n
                </html>\n
            """
        else:
            return u"""
                <html>\n
                <head>\n
                <meta charset="utf-8" />\n
                <title>Googlebridge-Open</title>\n
                <style type="text/css">\n
                <!--\n
                .STYLE2 {\n
                    font-size: xx-large;\n
                    font-family: Geneva, Arial, Helvetica, sans-serif;\n
                    color: #0066CC;\n
                }\n
                -->\n
                </style>\n
                </head>\n

                <body>\n
                </br></br></br>\n
                <form action="/search" method="get">\n
                        <div align="center">\n
                          <p class="STYLE2">googlebridge Open</p>\n
                          <p>\n
                            <input name="q" type="text" size="80">\n
                            <input type="submit" value="Search">\n
                          </p>\n
                  </div>\n
                </form>\n

                </body>\n
                </html>\n

            """

    def search(self, request):
        q = request.get('q', '')
        q = re.sub(r'\+', ' ', q)
        q = q.strip().lower()
        user_agent = request.header('user_agent')
        if not q:
            content = u'关键词不能为空或者空格键'
            return self.notify(content)

        start = request.get('start')
        start = int(start) if start else 0

        data = self.get_result(q, start)
        code = data.get('code')
        if code:
            if int(code) in [407]:
                content = 'upgrading network, after 30s retry pls'
            elif int(code) == 402:
                content = 'network timeout, pls retry'
            elif int(code) in [404, 400, 403]:
                content = 'serivce failed'
            elif int(code) == 405:
                content = 'used too many, after 1h retry pls'
            elif int(code) == 406:
                content = 'u r a bot?'
            else:
                content = 'unknown error'

            return self.notify(content)
        else:
            context = {'keyword': q, 'data': data, 'start': start}
            is_mobile = False
            for phone in ['Android', 'iPhone', 'iPod', 'iPad', 'Windows Phone', 'MQQBrowser']:
                if phone in user_agent:
                    is_mobile = True
                    break

            return self.render(context, is_mobile=is_mobile)

    @staticmethod
    def render(context, is_mobile=False):
        results = ''
        pages = ''
        keyword = context['keyword']
        data = context['data']
        start = context['start']
        key = sorted(data.keys())
        for i in key:
            url = data[i][0]
            title = data[i][1]
            url_list = url.split('/')
            s_url = url_list[0] + '//' + url_list[2]
            if is_mobile:
                results += u"""
                    <li style="list-style-type:none;">\n
                        <div class="weui-cells">\n
                        <a class="weui-cell weui-cell_access" href="{0}">\n
                    <div class="weui-cell__bd">\n
                      <p>{1}</p>\n
                    </div>\n
                    <div class="weui-cell__ft">\n
                    </div>\n
                     </a>\n
                     </div>\n
                    </li>\n
                """.format(_unicode(url), _unicode(title))

            else:
                results += u"""
                    <li style="list-style-type:none;">\n
                     <h4><a href="{0}">{1}</a></h4>\n
                     <p class="{0}">{2} </p>\n
                    </li>\n
                """.format(_unicode(url), _unicode(title), _unicode(s_url))

        if is_mobile:
            head_page = start - 10
            if start != 0:
                pages += u"""
                    <a class="weui-navbar__item weui_bar__item_on" href="/search?q={}&start={}">\n
                    <p class="STYLE2"><</p>\n
                    </a>\n
                """.format(_unicode(keyword), _unicode(head_page))
            end_page = start + 10
            if (start == 0 and len(data) > 7) or len(data) >= 9:
                pages += u"""
                    <a class="weui-navbar__item weui_bar__item_on" href="/search?q={}&start={}">\n
                    <p class="STYLE2">></p>\n
                    </a>\n
                """.format(_unicode(keyword), _unicode(end_page))

            html = u"""
                <!DOCTYPE html>\n
                <html lang="zh-cmn-Hans">\n
                <head>\n
                    <meta charset="UTF-8">\n
                    <meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=0">\n
                    <title>Googlebridge-Open</title>\n
                <link rel="stylesheet" href="//cdn.bootcss.com/weui/1.1.1/style/weui.min.css">\n
                <link rel="stylesheet" href="//cdn.bootcss.com/jquery-weui/1.0.1/css/jquery-weui.min.css">\n

                    <style type="text/css">\n
                <!--\n
                .STYLE2 {\n
                  font-size: x-large;\n
                    color: #1aad19;\n
                }\n
                -->\n
                </style>\n

                </head>\n
                <body style="background-color:#f8f8f8;">\n
                <div class="weui-search-bar" id="searchBar">\n
                  <form class="weui-search-bar__form" action="/search" method="get">\n
                    <div class="weui-search-bar__box">\n
                      <i class="weui-icon-search"></i>\n
                      <input type="search" class="weui-search-bar__input" id="searchInput"
                      placeholder="search" required="" name="q">\n
                    </div>\n
                    <label class="weui-search-bar__label" id="searchText">\n
                      <i class="weui-icon-search"></i>\n
                      <span>%s</span>\n
                    </label>\n
                  </form>\n
                  <a href="/" class="weui-search-bar__cancel-btn" id="searchCancel">Cancel</a>\n
                </div>\n
                <div>\n
                %s\n
                </div>\n
                </br>\n
                <div class="weui-tab">\n
                <div class="weui-navbar">\n
                %s\n
                </div>\n
                </div>\n
                <script src="//cdn.bootcss.com/jquery/1.11.0/jquery.min.js"></script>\n
                <script src="//cdn.bootcss.com/jquery-weui/1.0.1/js/jquery-weui.min.js"></script>\n

                </body>\n
                </html>\n

            """

        else:
            head_page = start - 10
            if start != 0:
                pages += u'<a href="/search?q={0}&start=' \
                         u'{1}">上一页</a>\n'.format(_unicode(keyword), _unicode(head_page))
            page = (start + 10) / 10
            if page < 6:
                for i in range(1, 11):
                    start_page = i * 10 - 10
                    if i == page:
                        pages += u'<a>{}</a>\n'.format(_unicode(i))
                    else:
                        pages += u'<a href="/search?q={0}&sta' \
                                 u'rt={1}">{2}</a>\n'.format(_unicode(keyword), _unicode(start_page), _unicode(i))
            else:
                for i in range(page - 4, page + 6):
                    start_page = i * 10 - 10
                    if i == page:
                        pages += u'<a>{}</a>\n'.format(_unicode(i))
                    else:
                        pages += u'<a href="/search?q={0}&sta' \
                                 u'rt={1}">{2}</a>\n'.format(_unicode(keyword), _unicode(start_page), _unicode(i))
            end_page = start + 10
            pages += u'<a href="/search?q={0}&sta' \
                     u'rt={1}">下一页</a>\n'.format(_unicode(keyword), _unicode(end_page))

            html = u"""
                <html>\n
                <head>\n
                <meta charset="utf-8" />\n
                <title>Googlebridge-Open</title>\n
                <style type="text/css">\n
                        body{color:#BFFEE3;background:#FEFEFE;padding:0 5em;margin:0}\n
                        h2{padding:2em 1em;background:#FFFFFF}\n
                        h3{color:#0066CC;margin:1em 0}\n
                        h4{color:#000000;margin:1em 0}\n
                        p{color:#000000;margin:1em 0}\n
                </style>\n
                </head>\n
                <body>\n
                <div>\n
                <form action="/search" method="get">\n
                <h3>Googlebridge-Open</h3>\n
                \n
                  <input name="q" type="text" size="70" value="%s">\n
                  <input type="hidden" name="start">\n
                  <input type="submit" value="Search">\n
                </form>\n
                </div>\n
                <div>\n
                <ul>\n
                %s\n
                </ul>\n
                </div>\n
                <div>\n
                <h3>\n
                %s\n
                </h3>\n
                </div>\n
                </body>\n
                </html>\n

            """

        return html % (_unicode(keyword), _unicode(results), _unicode(pages))

    @staticmethod
    def notify(content):
        return u"""
            <html>\n
            <head>\n
            <meta charset="utf-8" />\n
            <title>Googlebridge-Open-Error</title>\n
            <link rel="shortcut icon" type="image/x-icon" href="https://github.com/fluidicon.png"/>\n
            <style type="text/css">\n
            <!--\n
            .STYLE2 {\n
                font-size: xx-large;\n
                font-family: Geneva, Arial, Helvetica, sans-serif;\n
                color: #0066CC;\n
            }\n
            -->\n
            </style>\n
            </head>\n

            <body>\n
            </br></br></br>\n

            <div align="center">\n
                <p class="STYLE2">%s</p>\n
            </div>\n
            </body>\n
            </html>\n

        """ % (_unicode(content))


class App(object):

    """
    copy from lawliet
    """

    debug = True
    get_route = {
        '/': Bridge().index,
        '/search': Bridge().search,
    }

    def __init__(self, environ, start_response):
        self.environ = environ
        self.start = start_response

    def __iter__(self):
        path = self.environ['PATH_INFO']
        method = self.environ['REQUEST_METHOD']
        try:
            try:
                if method == 'GET':
                    func = self.get_route[path]
                else:
                    return self.method_not_allowed()
            except KeyError:
                return self.not_found()
            request = Request(self.environ)
            func = func(request)

            if isinstance(func, unicode):
                return self.response(
                    func,
                    headers=[('Content-type', 'text/html')]
                )
            else:
                return self.response(func)

        except Exception as e:
            if not self.debug:
                return self.server_error()
            else:
                return self.response(repr(e))

    def response(self, res=None, status=None, headers=None):
        if status is None:
            status = '200 OK'
        if headers is None:
            if isinstance(res, dict):
                res = python_json.dumps(res)
                headers = [('Content-type', 'application/json')]
            else:
                headers = [('Content-type', 'text/plain')]
        self.start(status, headers)
        if res is None:
            yield ''
        else:
            if isinstance(res, unicode):
                res = res.encode('utf-8')
            elif isinstance(res, (int, float, long)):
                res = str(res)
            yield res

    def server_error(self):
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'application/json')]
        self.start(status, response_headers)
        yield '{"errcode": 500, "errmsg": "page error"}'

    def not_found(self):
        status = '404 Not Found'
        response_headers = [('Content-type', 'application/json')]
        self.start(status, response_headers)
        yield '{"errcode": 404, "errmsg": "page not find"}'

    def method_not_allowed(self):
        status = '405 Method Not Allowed'
        response_headers = [('Content-type', 'application/json')]
        self.start(status, response_headers)
        yield '{"errcode": 405, "errmsg": "Method Not Allowed"}'


def run(host=None, port=None):
    if host is None:
        host = '127.0.0.1'
    if port is None:
        port = 5000
    from wsgiref.simple_server import make_server
    httpd = make_server(host, port, App)
    sa = httpd.socket.getsockname()
    print 'running ==> http://{0}:{1}/'.format(*sa)
    httpd.serve_forever()


if __name__ == '__main__':
    run('0.0.0.0', 8084)
