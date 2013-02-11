"""
Apollo smoke test
"""

import sys, os, time, traceback, logging, re, string, urllib, datetime
import requests, websocket
from optparse import OptionParser


def verify(condition, error_description):
    """
    Ensures that specified condition is performed. Otherwise raises an exception
    """
    if not condition:
        raise AssertionError, error_description

def verify2(actual, expected, error_description):
    verify(actual == expected, '%s Actual is "%s". Expected is "%s' % (error_description, actual, expected))


def setupLog(name):
    """
    Performs configuration for the logging system.
    """
    cur_time = time.time()
    date_s = time.strftime('%y%m%d', time.localtime(cur_time))
    time_s = time.strftime('%H%M%S', time.localtime(cur_time))
    msec_s = '%03d' % ((cur_time-long(cur_time))*1000,)
    datetime_s = '%s_%s.%s' % (date_s, time_s, msec_s)
    
    dir_name = os.path.dirname(os.path.abspath(__file__)) + "/log"
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)
    
    logging.basicConfig(filename = dir_name + "/log_" + datetime_s +".txt",
                        format    = "%(asctime)s,%(msecs)03d [%(threadName)-6.6s] [%(levelname)3.3s] %(name)s: %(message)s",
                        datefmt   = "%m/%d/%Y %H:%M:%S",
                        level     = logging.DEBUG)
    
    return logging.getLogger(name)


class SocketIOClient():
    """
    Class encapsulating the behaviour of socket.io protocol
    """

    _logger = logging.getLogger('Socket.io')

    SOCKET_IO_CONFIGURATION = "http://%s/socket.io/1"
    SOCKET_IO_END_POINT_URL_MASK = "ws://%s/socket.io/1/websocket/%s"

    DISCONNECTED = '0'
    CONNECTED = '1'
    HEARTBEAT = '2'
    EVENT = '5'

    RECV_PATTERN = '(?P<code>\d):(?P<packet_id>\d*):(?P<channel_name>\d*):(?P<data>.*)'
    SEND_PATTERN = '%d:%d:%d%%s'

    def __init__(self, server, agent):
        """
        Constructor

        @param server: server
        @param agent: RestAgent instance to perform Handshake
        """
        
        url = self.SOCKET_IO_CONFIGURATION % server
        data = {'t' : ''.join(str(time.time()).split('.')) + '0'}
        session_id = agent.get(url, data, absolute_path = True).text.split(':')[0]
        self.connection = websocket.create_connection(self.SOCKET_IO_END_POINT_URL_MASK % (server, session_id))
        self.recv(SocketIOClient.CONNECTED)
        self._logger.info('Connect to (%s) session id (%s)' % (server, session_id))
    
    def send(self, data):
        self._logger.info('Message to sent: %s' % (data))
        self.connection.send(data)
    
    def recv(self, msg_type = EVENT, wait_timeout = 5):
        """
        @return: received string data from the server
        
        @param msg_type: message type
        @param wait_timeout (optional): timeout to wait for
        """
        end_time = time.time() + wait_timeout
        while time.time() < end_time:
            msg = self.connection.recv()
            self._logger.info('Message received: %s' % (msg))
            code, _packet_id, _channel_name, data = re.match(self.RECV_PATTERN, msg).groups()

            if code == msg_type:
                return string.replace(data, ' ', '')
            elif code in (self.HEARTBEAT, self.CONNECTED, self.DISCONNECTED):
                continue
            else:
                raise Exception("Code %s is not supported" % code)
        
        else:
            raise Exception("No message in timeout %s sec." % wait_timeout)


class RestAgent():
    """
    Class encapsulating the behaviour of RestAgent application
    """
    _logger     = logging.getLogger('RestAgent')
    BASE_HEADER = {'Content-Type': 'application/json'}
    
    AGENT_STATES = ("ready-call-vm", "ready-call", "ready-vm",
                    "break", "email", "fax", "follow-up-work", "meal", "meeting", "team-meeting", "training")
    AGENT_CALL_STATE      = (  'Available', 'ready-call')
    AGENT_NOT_READY_STATE = ('Unavailable', 'break')
    
    def __init__(self, user_name, password, station, station_type, webui_server):
        self.user_name    = user_name
        self.password     = password
        self.station      = station
        self.station_type = station_type
        self.webui_server = webui_server
        
        self.base_url  = 'http://%s' % (webui_server,)
        self.cookies   = None    
        self.socket_io = None
        

    def _checkRequestResult(self, request, result, exp_status_code):
        """
        Check request result

        @param request: request url
        @param result: result
        """
        self._logger.info('Response "%s" status: "%s"' % (request, result.status_code))
        self._logger.info('         header: "%s"' % (result.headers,))
        self._logger.info('         result: "%s"' % (result.text,))
        self._logger.info('         cookies:"%s"' % (result.cookies,))
        
        verify(result.status_code in exp_status_code, 'Problem occured during "%s". Status code: (%s); expectation is %s' % (request, result.status_code, exp_status_code))        
    
    def post(self, url, data = None, headers = None, exp_status_code = (200,)):
        """
        Perform HTTP POST request
        
        @return: request result 

        @param url: relative url
        @param data: dictionary with data
        @param headers: headers
        @param exp_status_code: list of expected status codes 
        """
        if data:
            data = urllib.urlencode(data)
            
        h = headers or self.BASE_HEADER
        
        self._logger.info('Post "%s" data: "%s"' %(self.base_url + url, data))
        
        result = requests.post(self.base_url + url, data, headers = h, cookies = self.cookies)
        
        self.cookies = result.cookies
        self.headers = result.headers
        
        self._checkRequestResult(url, result, exp_status_code)

        return result
        
    def get(self, url, data = None, headers = None, cookies = None, absolute_path = False):
        """
        Perform HTTP GET request
        
        @return: request result 

        @param url: relative url
        @param data: dictionaly with data
        @param cookies: cookies
        """
        if absolute_path:
            call_url = url
        else:
            call_url = self.base_url + url

        if data:
            call_url += '/?%s' % urllib.urlencode(data)

        result = requests.get(call_url, cookies = cookies or self.cookies)
        self._checkRequestResult(url, result, exp_status_code = (200,))
        
        return result

    
    def login(self):
        """
        Performs RestAgent login, and initiates Socket.IO connection

        @return: None
        """
        login_options = {'username':self.user_name,'password':self.password,'extension':self.station,'connectionType':self.station_type}
        login_result = self.post("/login", login_options).json()
        verify2(login_result['firstName'], "John", "Error on checking 'firstName' in Login response.")
        verify2(login_result['lastName'],  "Doe",  "Error on checking 'lastName' in Login response.")
        login_data = login_result["loginDate"]
        datetime.datetime.strptime(login_data, "%Y-%m-%dT%H:%M:%SZ")
        
        self.user_id       = self.cookies['userId']
        _session_token = self.cookies['sessionToken']
        
        self.socket_io = SocketIOClient(self.webui_server, self)
        

    def logout(self):
        """
        Logs out RestAgent

        @return: None
        """
        try:
            login_result = self.post("/logout", exp_status_code = [200, 204]).text
            verify(login_result == "", "Logout Response should not have Content, but actually: %s" % (login_result,))
        finally:
            self.socket_io.connection.close()

        
    def setState(self, status, status_code):
        """
        Change current agent's ready state

        @param status: status to set
        @param status_code: status code (state) to set
        """
        data = '5:::{"name":"agent:status:set","args":[{"agentId":"%s","status":"%s","statusCode":"%s"}]}' % (self.user_id, status, status_code)
        self.socket_io.send(data)
        result = string.lower(self.socket_io.recv())
        expected_result = string.lower('{"name":"agent:status:updated","args":{"agentId":"%s","status":"%s","statusCode":"ready-call"}}'  % (self.user_id, status))
        verify2(result, expected_result, "Error on setting state to '%s:%s'." % (status, status_code,))      


def main(name, pwd, server):
    logger = setupLog('SmokeTest')
    logger.info("Started with parameters %s:%s@%s" % (name, pwd, server))
    
    def printTest(action, args = ()):
        log_str = action + ("()" if args == () else "%s" % str(args))
        logger.info('---- ' + log_str + ':')
        print log_str
        
    def printLastExceptionStackTrace():
        print >> sys.stderr, "\n" + traceback.format_exc() + "\n"
        sys.stderr.flush()
        logger.error(traceback.format_exc())

    agent = RestAgent(name, pwd, '3005000000', 'PSTN', server)
    try:
        printTest("Login", (name, pwd, 'PSTN, 3005000000'))
        agent.login()
                
        for state in [agent.AGENT_CALL_STATE, agent.AGENT_NOT_READY_STATE]:
            printTest("Set Agent State", state)
            agent.setState(*state)
        
        printTest("Logout")
        agent.logout()

        print 'TEST PASSED'
        logger.info('---- TEST PASSED ----')
    except:
        printLastExceptionStackTrace()
        print 'TEST FAILED'
        logger.info('---- TEST FAILED ----')
        exit(1)


if __name__ == "__main__":

    parser = OptionParser(usage='rest_api_smoke_test.py [options]',
                          description = "Basic test implements scenario: Login - Get Current State - Set all available States - Logout")

    parser.add_option('-u', '--user',     help = "Agent's name")
    parser.add_option('-p', '--password', help = "Agent's password")
    parser.add_option('-s', '--server',   help = "Server address. Examples: 10.5.78.3:8500")

    (options, args) = parser.parse_args()

    if not all([options.user, options.password, options.server]):
        parser.print_help()
        exit(1)

    main(options.user, options.password, options.server)
    exit(0)
#EOF
