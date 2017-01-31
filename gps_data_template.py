
def get_gps_data(cmd_name, **kwargs):
    cmd_template = globals().get(cmd_name)
    if cmd_template is not None:
        return str(cmd_template % kwargs)
    else:
        return None

GPRMC = '''\
$GPRMC,%(Time)s,A,%(Latitude)s,%(Latitude_Hemisphere)s,%(Longitude)s,%(Longitude_Hemisphere)s,12370.8,50.9,%(Date)s,5,E,A*39'''

GPGGA = '''\
$GPGGA,%(Time)s,%(Latitude)s,%(Latitude_Hemisphere)s,%(Longitude)s,%(Longitude_Hemisphere)s,1,04,5.6,292.9,M,34.5,M,,*4A'''