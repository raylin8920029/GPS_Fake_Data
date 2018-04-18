
def get_gps_data(cmd_name, **kwargs):
    cmd_template = globals().get(cmd_name)
    if cmd_template is not None:
        sentance = str(cmd_template % kwargs)
        return sentance + checksum(sentance)
    else:
        return None


def checksum(sentance):
    chksum = 0
    for ch in sentance:
        if ch == '$' or ch == '*':
            continue
        chksum ^= ord(ch)
    return '*%02X' % chksum

GPRMC = '''\
$GPRMC,%(Time)s,%(Status)s,%(Latitude)s,%(Latitude_Hemisphere)s,%(Longitude)s,%(Longitude_Hemisphere)s,%(Speed)s,50.9,%(Date)s,5,E,A'''

GPGGA = '''\
$GPGGA,%(Time)s,%(Latitude)s,%(Latitude_Hemisphere)s,%(Longitude)s,%(Longitude_Hemisphere)s,1,04,5.6,292.9,M,34.5,M,,'''