import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from jinja2 import Environment, FileSystemLoader
import subprocess
import threading
import time
import os
import re
import sys
import configparser

config = configparser.ConfigParser(allow_unnamed_section=True)
try:
  config.read('/boot/firmware/ftcdisp.ini')
except FileNotFoundError:
  pass

unnamed = config[UNNAMED_SECTION]
FDPORT = int(unnamed.get('FDPORT', 8080))
START_URL = unnamed.get('START_URL', f"http://localhost:{FDPORT}/display")

TEMPLATE_DIR = "."
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
viewCount = 0;

class MyHandler(http.server.SimpleHTTPRequestHandler):
  def do_GET(self):
    global viewCount
    parsed_url = urlparse(self.path)
    qs = parse_qs(parsed_url.query)
    result = subprocess.run(["ip", "-br", "address"], capture_output=True,
                 text=True, check=True)
    IP_ADDR = []
    for addr in result.stdout.splitlines():
      m = re.match(r"(\w+)\s+(\w+)\s+([0-9.]+)?", addr)
      if not m: continue
      IP_ADDR.append(m.group(1,2,3))

    REMOTE_ADDR = self.client_address[0]
    context = { 
      'REMOTE_ADDR': REMOTE_ADDR,
      'local': REMOTE_ADDR == "127.0.0.1",
      'REMOTE_PORT': self.client_address[1],
      'SERVER_ADDR': self.request.getsockname()[0],
      'IP_ADDR': IP_ADDR,
      'FDPORT': FDPORT,
      'viewCount': viewCount,
      'httpAddr': '',
      'eventCode': '',
      'displayName': 'Field 1',
      'displayType': 'field',
      'bindToField': '(all)',
      'allianceOrientation': 'flipped',
      'source': 'ftclive',
    }
    l = list(context.keys())
    for key in l:
      if key in qs:
        context[key] = qs[key][0]

    if parsed_url.path == "/favicon.ico":
      self.do_exception()
    elif parsed_url.path == "/ip":
      self.do_ip(context)
    elif parsed_url.path == "/click":
      self.do_click(context)
    elif context['source'] == "nexus":
      self.do_nexus(context)
    elif context['source'] == "ftcscoring":
      self.do_ftcscoring(context)
    else:
      self.do_ftclive(context)
      viewCount += 1

  def do_nexus(self, context):
    if context['eventCode'] > '' :
      try:
        subprocess.run(["/usr/bin/pkill", "chromium"])
        time.sleep(1)
        start_chromium(
            f"https://ftc.nexus/en/event/2025{context['eventCode'].lower()}/display/pit"
        )
      except Exception as e:
        self.do_exception()
    return self.do_form(context)

  def do_ftclive(self, context):
    if context['httpAddr'] > '' and context['eventCode'] > '' :
      try:
        subprocess.run(["/usr/bin/pkill", "chromium"])
        time.sleep(1)
        start_chromium(
            f"http://{context['httpAddr']}/event/{context['eventCode']}/display"
            f"?eventcode={context['eventCode']}"
            f"&name={context['displayName']}"
            f"&type={context['displayType']}"
            f"&bindToField={context['bindToField']}"
            f"&allianceOrientation={context['allianceOrientation']}"
            f"&mute=true"
        )
      except Exception as e:
        self.do_exception()
    return self.do_form(context)

  def do_ftcscoring(self, context):
    if context['eventCode'] > '' :
      try:
        subprocess.run(["/usr/bin/pkill", "chromium"])
        time.sleep(1)
        start_chromium(
            f"https://ftc-scoring.firstinspires.org/event/{context['eventCode']}/display/pit"
            f"?type=pit&bindToField=all"
	# &scoringBarLocation=bottom&allianceOrientation=standard&mute=false&muteRandomizationResults=false&fieldStyleTimer=true&overlay=false&overlayColor=%2300FF00&allianceSelectionStyle=classic&awardsStyle=overlay&dualDivisionRankingStyle=sideBySide&rankingsFontSize=larger&showMeetRankings=false&rankingsAllTeams=true"
        )
      except Exception as e:
        self.do_exception()
    return self.do_form(context)

  def do_exception(self):
    self.send_response(500)
    self.send_header("Content-type", "text/plain")
    self.end_headers()
    self.wfile.write(f"Error executing command".encode('utf-8'))

  def do_ip(self, context):
    template = env.get_template('views/ip.html')
    html = template.render(context)
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.end_headers()
    self.wfile.write(html.encode('utf-8'))

  def do_form(self, context):
    template = env.get_template('views/main.html')
    html = template.render(context)
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.end_headers()
    self.wfile.write(html.encode('utf-8'))

  def do_click(self, context):
    # wayland click
    subprocess.run(["/usr/bin/wlrctl", "pointer", "click"])
    self.send_response(200)
    self.send_header('Content-type', 'text/plain')
    self.end_headers()
    self.wfile.write("Mouse clicked".encode('utf-8'))

def start_chromium(url):
  print(f"Starting chromium kiosk display @ {url}", flush=True)
  subprocess.Popen(["/usr/bin/chromium", "--kiosk", 
      "--autoplay-policy=no-user-gesture-required",
      "--disable-session-crashed-bubble",
      "--disable-third-party-cookies-blocking",
      "--incognito",
      "--password-store=basic",
      "--temp-profile",
      url
    ], 
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# print("Killing existing chromium processes", flush=True) 
# subprocess.run(["/usr/bin/pkill", "chromium"])
with socketserver.TCPServer(("", FDPORT), MyHandler) as httpd:
  # start initial chromium window 3 seconds after handling requests
  threading.Timer(3, start_chromium, args=[START_URL]).start()     
  try:
    print(f"Serving at port {FDPORT}", flush=True)
    httpd.serve_forever()
  except KeyboardInterrupt:
    print(f"Received SIGINT", flush=True)
    httpd.shutdown()
    sys.exit(0)

