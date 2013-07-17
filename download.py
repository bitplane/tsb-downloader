#!/usr/bin/python
"""Download transaction history from Lloyds TSB website
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

def download(user_id, from_date, to_date):
    # a new browser and open the login page
    br = mechanize.Browser()
    br.set_handle_robots(False)

    br.open('https://online.lloydstsb.co.uk/personal/logon/login.jsp?WT.ac=hpIBlogon')
    title = br.title()
    while 'Enter Memorable Information' not in title:
        print br.title()
        br.select_form(name='frmLogin')
        br['frmLogin:strCustomerLogin_userID'] = str(user_id)
        br['frmLogin:strCustomerLogin_pwd']    = prompt("Enter password:", True)
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

    # and hopefully we're now logged in...        
    title = br.title() #'Personal Account Overview' in title
    
    links = []
    # Get a list of account links
    for link in br.links():
        attrs = {attr[0]:attr[1] for attr in link.attrs}
        if 'id' in attrs and 'lkImageRetail1' in attrs['id']:
            links.append(link)

    # allow user to choose one
    print "Accounts:"
    for i in range(len(links)):
        print "{0}:".format(i), links[i].text.split('[')[0]

    n = prompt("Please select an account:")
    link = links[int(n)]
    response = br.follow_link(link)

    print br.title()
    export_link = br.find_link(text='Export')
    br.follow_link(export_link)

    print br.title()
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
        print response
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

        print "Saved transactions to '%s'" % filename

    else:
        print response
        raise Exception('Missing "Content-Disposition: attachment" header')

def parse_date(string):
    try:
        yyyy, mm, dd = string.split('/', 2)
        return datetime.date(int(yyyy), int(mm), int(dd))
    except ValueError:
        raise argparse.ArgumentTypeError(
            "'%s' is not a valid date in the form YYYY/MM/DD" % string)

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user-id', type=int, required=True)
    parser.add_argument('-f', '--from', type=parse_date, metavar='YYYY/MM/DD', required=True)
    parser.add_argument('-t', '--to',   type=parse_date, metavar='YYYY/MM/DD', required=True)
    args = parser.parse_args()

    download(user_id=args.user_id, from_date=getattr(args, 'from'), to_date=args.to)
