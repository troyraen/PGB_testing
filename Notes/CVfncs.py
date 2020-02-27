import pandas as pd
import urllib.request


http://www.astronomerstelegram.org/?read=13450
http://www.astronomerstelegram.org/?read=

def get_cvs_from_at():
    """ Scrapes Astronomers Telegram bulletins
        looking for CVs confused with other things.
    """
    url = 'http://www.astronomerstelegram.org/?read=' # base url
    Ntot = 13488 # most recent telegram number
    sbjct = '<div id="subjects"><p class="subjects">Subjects: '
    slen = len(sbjct)

    for n in range(Ntot):
        print(f'{url}{n}')
        html = urllib.request.urlopen(f'{url}{n}').read()
        lines = html.splitlines(False) # split lines, don't preserve line endings

        # print(len(lines))
        for l in lines:
            # print(l[:slen])
            if l[:slen] != sbjct: continue
            l = l[slen+1:]
            print(l)

            break
        break
