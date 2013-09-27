#!/usr/bin/python
"""Download transaction history from Lloyds Bank website
Outputs a CSV, pipe it somewhere or something.
"""

import argparse
import datetime
import getpass
import mechanize
import os.path

def prompt(prompt, password=False):
    if password:
        return getpass.getpass(prompt)
    else:
        print prompt,
        return raw_input()

def extract(data, before, after):
    start = data.index(before) + len(before)
    end   = data.index(after, start)
    return data[start:end]

def download(user_id, date_ranges=[]):
    # a new browser and open the login page
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.addheaders = [('User-agent', 'LBG Statement Downloader http://github.com/bitplane/tsb-downloader')]

    br.open('https://online.lloydsbank.co.uk/personal/logon/login.jsp?WT.ac=hpIBlogon')
    #br.open('https://www.halifax-online.co.uk/personal/logon/login.jsp?WT.ac=hpIBlogon')
    title = br.title()
    while 'Enter Memorable Information' not in title:
        print br.title()
        br.select_form(name='frmLogin')
        br['frmLogin:strCustomerLogin_userID'] = str(user_id)
        br['frmLogin:strCustomerLogin_pwd']    = prompt('Enter password: ', True)
        response = br.submit() # attempt log-in
        title    = br.title()

    # We're logged in, now enter memorable information
    print br.title()
    br.select_form('frmentermemorableinformation1')
    data   = response.read()
    field  = 'frmentermemorableinformation1:strEnterMemorableInformation_memInfo{0}'
    before = '<label for="{0}">'
    after  = '</label>'

    for i in range(1, 4):
        br[field.format(i)] = ['&nbsp;' + prompt(extract(data, before.format(field.format(i)), after))]
    response = br.submit()

    # hopefully now we're logged in...        
    title = br.title()

    # dismiss any nagging messages
    if 'Mandatory Messages' in title:
        for link in br.links():
            if 'lkcont_to_your_acc' in link.url:
                br.follow_link(link)
                break
    
    title = br.title() #'Personal Account Overview' in title
    
    links = []
    # Get a list of account links
    for link in br.links():
        attrs = {attr[0]:attr[1] for attr in link.attrs}
        if 'id' in attrs and 'lkImageRetail1' in attrs['id']:
            links.append(link)

    # allow user to choose one
    print 'Accounts:'
    for i in range(len(links)):
        print '{0}:'.format(i), links[i].text.split('[')[0]

    n = prompt('Please select an account:')
    link = links[int(n)]
    response = br.follow_link(link)

    print br.title()
    export_link = br.find_link(text='Export')
    br.follow_link(export_link)

    for (from_date, to_date) in date_ranges:
        for (f, t) in split_range(from_date, to_date):
            download_range(br, f, t)

def split_range(from_date, to_date):
    THREE_MONTHS = datetime.timedelta(days=(28 * 3))
    ONE_DAY = datetime.timedelta(days=1)

    assert from_date <= to_date

    while to_date - from_date > THREE_MONTHS:
        yield (from_date, from_date + THREE_MONTHS)
        from_date += (THREE_MONTHS + ONE_DAY)

    yield (from_date, to_date)

def download_range(br, from_date, to_date):
    print br.title()
    print 'Exporting {0} to {1}'.format(from_date, to_date)
    br.select_form(name='frmTest')
    # "Date range" as opposed to "Current view of statement"
    br['frmTest:rdoDateRange'] = ['1']

    def setDate(field_name, date):
        br[field_name] = [date.strftime('%d')]
        br[field_name + '.month'] = [date.strftime('%m')]
        br[field_name + '.year'] = [date.strftime('%Y')]

    setDate('frmTest:dtSearchFromDate', from_date)
    setDate('frmTest:dtSearchToDate', to_date)

    response = br.submit()
    info = response.info()

    if info.gettype() != 'application/csv':
        print info.headers
        print response.getcode()
        print response.read()
        raise Exception('Did not get a CSV back (maybe there are more than 150 transactions?)')

    disposition = info.getheader('Content-Disposition')
    PREFIX='attachment; filename='
    if disposition.startswith(PREFIX):
        suggested_prefix, ext = os.path.splitext(disposition[len(PREFIX):])
        filename = '{0} {1:%Y-%m-%d} {2:%Y-%m-%d}{3}'.format(
            suggested_prefix, from_date, to_date, ext)

        with open(filename, 'a') as f:
            for line in response:
                f.write(line)

        print 'Saved transactions to "{0}"'.format(filename)

    else:
        raise Exception('Missing "Content-Disposition: attachment" header')

    br.back()

def parse_date(string):
    try:
        yyyy, mm, dd = string.split('/', 2)
        return datetime.date(int(yyyy), int(mm), int(dd))
    except ValueError:
        raise argparse.ArgumentTypeError(
            '"{0}" is not a valid date in the form YYYY/MM/DD'.format(string))

def parse_date_range(string):
    try:
        frm, to = string.split('--', 1)
        from_date = parse_date(frm)
        to_date = parse_date(to)
    except ValueError:
        raise argparse.ArgumentTypeError(
            '"{0}" is not a valid date range (YYYY/MM/DD--YYYY/MM/DD)'.format(string))

    if from_date > to_date:
        raise argparse.ArgumentTypeError(
            '"{0}" is after "{1}"'.format(frm, to))

    return (from_date, to_date)

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user-id', type=int, required=True)
    parser.add_argument('date_ranges', nargs='+', metavar='YYYY/MM/DD--YYYY/MM/DD',
                        type=parse_date_range,
                        help="""One or more date ranges to download statements
                                for (FROM--TO). Note that Lloyds's web
                                interface refuses to export a CSV with more
                                than 150 elements so you might want to make
                                your ranges smallish.""")

    args = parser.parse_args()

    download(user_id=args.user_id, date_ranges=args.date_ranges)
