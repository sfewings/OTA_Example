# 1000 x dank aan Evelien die mijn in deze tijden gesteund heeft
# ohja, en er is ook nog tante suker (Jana Dej.) die graag kinderen wilt maar het zelf nog niet beseft

import usocket
import os
import gc
import machine
import ulogging
import utime        #support logging exception time reporting

class OTAUpdater:

    def __init__(self, github_repo, module='', main_dir='main', OTAupdateTextList= []):
        self.http_client = HttpClient()
        self.github_repo = github_repo.rstrip('/').replace('https://github.com', 'https://api.github.com/repos')
        self.main_dir = main_dir
        self.module = module.rstrip('/')

        self.log = ulogging.getLogger("OTA updater")
        self.log.setLevel(ulogging.DEBUG)
        self.OTAupdateTextList = OTAupdateTextList


    @staticmethod
    def using_network(ssid="", password=""):
        import network
        sta_if = network.WLAN(network.STA_IF)
        if not sta_if.isconnected():
            print('connecting to network...')
            sta_if.active(True)
            sta_if.connect(ssid, password)
            while not sta_if.isconnected():
                pass
        print('network config:', sta_if.ifconfig())

    def OTA_print(self, text):
        print(text)
        self.OTAupdateTextList.append(text)


    def check_for_update_to_install_during_next_reboot(self):
        current_version = self.get_version(self.modulepath(self.main_dir))
        latest_version = self.get_latest_version()

        self.OTA_print('Checking version... ')
        self.OTA_print('\tCurrent version: {}'.format( current_version ))
        self.OTA_print('\tLatest version: {}'.format( latest_version ))
        if latest_version > current_version:
            self.OTA_print('New version available, will download and install on next reboot')
            try:
                os.mkdir(self.modulepath('next'))
            except OSError as e:
                self.OTA_print("Unable to create path {}\\next".format(self.modulepath(self.main_dir)))
                #self.log.exc(e, "%.3f %s %r" % (utime.time(), "Unable to create path {}\\next".format(self.modulepath(self.main_dir)), e))

            with open(self.modulepath('next/.version_on_reboot'), 'w') as versionfile:
                versionfile.write(latest_version)
                versionfile.close()
        else:
            self.OTA_print('Already have the latest version. No update required')          

    def download_and_install_update_if_available(self, ssid, password):
        if 'next' in os.listdir(self.module):
            if '.version_on_reboot' in os.listdir(self.modulepath('next')):
                latest_version = self.get_version(self.modulepath('next'), '.version_on_reboot')
                self.OTA_print('New update found: {} '.format(latest_version) )
                self._download_and_install_update(latest_version, ssid, password)
        else:
            self.OTA_print('No new updates found...')

    def _download_and_install_update(self, latest_version, ssid, password):
        OTAUpdater.using_network(ssid, password)

        self.download_all_files(self.github_repo + '/contents/' + self.main_dir, latest_version)
        if 'OTABackup' in os.listdir(self.module):
            self.rmtree(self.modulepath("OTABackup"))
        try:
            os.rename(self.modulepath(self.main_dir), self.modulepath('OTABackup'))
        except OSError as e:
            self.OTA_print("Unable to rename \\{} as \\OTABackup".format(self.main_dir))
        os.rename(self.modulepath('next/.version_on_reboot'), self.modulepath('next/.version'))
        os.rename(self.modulepath('next'), self.modulepath(self.main_dir))
        self.OTA_print('Update installed ( {} ), will reboot now'.format(latest_version) )
        #machine.reset()

    def apply_pending_updates_if_available(self):
        if 'next' in os.listdir(self.module):
            if '.version' in os.listdir(self.modulepath('next')):
                pending_update_version = self.get_version(self.modulepath('next'))
                self.OTA_print('Pending update found: {}'.format( pending_update_version) )
                self.rmtree(self.modulepath(self.main_dir))
                os.rename(self.modulepath('next'), self.modulepath(self.main_dir))
                self.OTA_print('Update applied ( {} ), ready to rock and roll'.format(pending_update_version))
            else:
                self.OTA_print('Corrupt pending update found, discarding...')
                self.rmtree(self.modulepath('next'))
        else:
            self.OTA_print('No pending update found')

    def download_updates_if_available(self):
        current_version = self.get_version(self.modulepath(self.main_dir))
        latest_version = self.get_latest_version()

        self.OTA_print('Checking version... ')
        self.OTA_print('\tCurrent version: {}'.format(current_version))
        self.OTA_print('\tLatest version:  {}'.format(latest_version))
        if latest_version > current_version:
            self.OTA_print('Updating...')
            os.mkdir(self.modulepath('next'))
            self.download_all_files(self.github_repo + '/contents/' + self.main_dir, latest_version)
            with open(self.modulepath('next/.version'), 'w') as versionfile:
                versionfile.write(latest_version)
                versionfile.close()

            return True
        return False

    def rmtree(self, directory):
        for entry in os.ilistdir(directory):
            is_dir = entry[1] == 0x4000
            if is_dir:
                self.rmtree(directory + '/' + entry[0])

            else:
                os.remove(directory + '/' + entry[0])
        os.rmdir(directory)

    def get_version(self, directory, version_file_name='.version'):
        try:
            if version_file_name in os.listdir(directory):
                f = open(directory + '/' + version_file_name)
                version = f.read()
                f.close()
                return version
        except OSError as e:
            self.OTA_print("Unable to create path get current {} from {}. Assuming version 0.0. {}".format(version_file_name, directory, e))
        return '0.0'

    def get_latest_version(self):
        #print(self.github_repo + '/releases/latest')
        latest_release = self.http_client.get(self.github_repo + '/releases/latest')
        #print(latest_release)
        try:
            version = latest_release.json()['tag_name']
        except KeyError:
            version = '0.0'
        finally:
            latest_release.close()
        return version

    def download_all_files(self, root_url, version):
        file_list = self.http_client.get(root_url + '?ref=refs/tags/' + version)
        for file in file_list.json():
            if file['type'] == 'file':
                download_url = file['download_url']
                download_path = self.modulepath('next/' + file['path'].replace(self.main_dir + '/', ''))
                self.download_file(download_url.replace('refs/tags/', ''), download_path)
            elif file['type'] == 'dir':
                path = self.modulepath('next/' + file['path'].replace(self.main_dir + '/', ''))
                os.mkdir(path)
                self.download_all_files(root_url + '/' + file['name'], version)

        file_list.close()

    def download_file(self, url, path):
        self.OTA_print('\tDownloading: {}'.format(path))
        with open(path, 'w') as outfile:
            try:
                response = self.http_client.get(url)
                outfile.write(response.text)
            finally:
                response.close()
                outfile.close()
                gc.collect()

    def modulepath(self, path):
        return self.module + '/' + path if self.module else path


class Response:

    def __init__(self, f):
        self.raw = f
        self.encoding = 'utf-8'
        self._cached = None

    def close(self):
        if self.raw:
            self.raw.close()
            self.raw = None
        self._cached = None

    @property
    def content(self):
        if self._cached is None:
            try:
                self._cached = self.raw.read()
            finally:
                self.raw.close()
                self.raw = None
        return self._cached

    @property
    def text(self):
        return str(self.content, self.encoding)

    def json(self):
        import ujson
        return ujson.loads(self.content)


class HttpClient:

    def request(self, method, url, data=None, json=None, headers={}, stream=None):
        try:
            proto, dummy, host, path = url.split('/', 3)
        except ValueError:
            proto, dummy, host = url.split('/', 2)
            path = ''
        if proto == 'http:':
            port = 80
        elif proto == 'https:':
            import ussl
            port = 443
        else:
            raise ValueError('Unsupported protocol: ' + proto)

        if ':' in host:
            host, port = host.split(':', 1)
            port = int(port)

        ai = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)
        ai = ai[0]

        s = usocket.socket(ai[0], ai[1], ai[2])
        try:
            s.connect(ai[-1])
            if proto == 'https:':
                s = ussl.wrap_socket(s, server_hostname=host)
            s.write(b'%s /%s HTTP/1.0\r\n' % (method, path))
            if not 'Host' in headers:
                s.write(b'Host: %s\r\n' % host)
            # Iterate over keys to avoid tuple alloc
            for k in headers:
                s.write(k)
                s.write(b': ')
                s.write(headers[k])
                s.write(b'\r\n')
            # add user agent
            s.write('User-Agent')
            s.write(b': ')
            s.write('MicroPython OTAUpdater')
            s.write(b'\r\n')
            if json is not None:
                assert data is None
                import ujson
                data = ujson.dumps(json)
                s.write(b'Content-Type: application/json\r\n')
            if data:
                s.write(b'Content-Length: %d\r\n' % len(data))
            s.write(b'\r\n')
            if data:
                s.write(data)

            l = s.readline()
            #print("received:"+str(l))
            l = l.split(None, 2)
            status = int(l[1])
            reason = ''
            if len(l) > 2:
                reason = l[2].rstrip()
            while True:
                l = s.readline()
                if not l or l == b'\r\n':
                    break
                #print("received:"+str(l))
                if l.startswith(b'Transfer-Encoding:'):
                    if b'chunked' in l:
                        raise ValueError('Unsupported ' + l)
                elif l.startswith(b'Location:') and not 200 <= status <= 299:
                    raise NotImplementedError('Redirects not yet supported')
        except OSError:
            s.close()
            raise

        resp = Response(s)
        resp.status_code = status
        resp.reason = reason
        return resp

    def head(self, url, **kw):
        return self.request('HEAD', url, **kw)

    def get(self, url, **kw):
        return self.request('GET', url, **kw)

    def post(self, url, **kw):
        return self.request('POST', url, **kw)

    def put(self, url, **kw):
        return self.request('PUT', url, **kw)

    def patch(self, url, **kw):
        return self.request('PATCH', url, **kw)

    def delete(self, url, **kw):
        return self.request('DELETE', url, **kw)
