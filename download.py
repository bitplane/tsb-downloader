#!/usr/bin/python
"""Download transaction history from Lloyds TSB website
Outputs a CSV, pipe it somewhere or something.
"""

import getpass
import mechanize

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

def download():
    # a new browser and open the login page
    br = mechanize.Browser()
    br.set_handle_robots(False)

    br.open('https://online.lloydstsb.co.uk/personal/logon/login.jsp?WT.ac=hpIBlogon')
    title = br.title()
    while 'Enter Memorable Information' not in title:
        print br.title()
        br.select_form(name='frmLogin')
        br['frmLogin:strCustomerLogin_userID'] = prompt("Enter user ID:")
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
    print "Please select an account:"
    for i in range(len(links)):
        print "{0}:".format(i), links[i].text.split('[')[0]
    
    # export this detail
    

def main():
    download()

if __name__=='__main__':
    main()
