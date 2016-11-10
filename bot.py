import time
from slackclient import SlackClient
from urlparse import urlparse
import subprocess
import json
import config

slack = SlackClient(config.SLACK_KEY)

def isPhabricatorDifferential(text):
    root = config.PHAB_URL + "/D"
    if root in text or "https://"+root in text or "http://"+root in text:
        return True
    return False

def getPhabricatorUrl(text):
    words = text.split();
    for w in words:
        if isPhabricatorDifferential(w):
            return w
    return ""

def getPhabricatorRev(url):

    if url[0] == "<":
        url = url[1:]

    if url[len(url) - 1]:
        url = url[:-1]

    if "http://" not in url and "https://" not in url:
        url = "https://" + url

    parsed = urlparse(url)
    pathParts = parsed.path.split("/")
    return pathParts[1][1:]

def getPhabricatorDifferential(rev):
    curl = "curl https://" + config.PHAB_URL + "/api/differential.query -d api.token=" + config.PHAB_KEY  + " -d ids[0]=" + str(rev)
    return subprocess.check_output(curl, shell=True)

def parse_slack_output(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output:
                try:
                    if isPhabricatorDifferential(output["text"]):
                        url = getPhabricatorUrl(output["text"])
                        rev = getPhabricatorRev(url)
                        query = json.loads(getPhabricatorDifferential(rev))
                        count = int(query["result"][0]["lineCount"])
                        if count > 1000:
                            print "nasty"
                            emoji = "angryeyes"
                            if count > 3000:
                                emoji = "shit"
                            elif count > 2000:
                                emoji = "vomit"

                            slack.api_call("reactions.add", token=config.SLACK_KEY, channel=output["channel"], name=emoji, timestamp=output["ts"])
                except:
                    print "your shits broken"

# test case
#parse_slack_output([{'text': 'heres my rev <https://' + config.PHAB_URL + '/D69>', 'ts': u'1478567644.000078', 'user': 'U0ER0VB6G', 'team': 'T03SP91MM', 'type': 'message', 'channel': 'G1DQUMK9D'}])
#parse_slack_output([{'text': 'heres my rev https://' + config.PHAB_URL + '/D69', 'ts': u'1478567644.000078', 'user': 'U0ER0VB6G', 'team': 'T03SP91MM', 'type': 'message', 'channel': 'G1DQUMK9D'}])

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack.rtm_connect():
        print("Phantastic connected and running!")
        while True:
            parse_slack_output(slack.rtm_read())
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")


