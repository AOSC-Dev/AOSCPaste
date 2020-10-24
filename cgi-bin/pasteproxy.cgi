#! /usr/bin/python3 -B

import base64
import cgi
import datetime
import json
import mimetypes
import pasteview
import urllib.request as ur
import urllib.parse as up

template_head = pasteview.template_head
template_tail = pasteview.template_tail

def main():
    stdin = cgi.FieldStorage()
    formdata = {}
    formfile = None
    for item in ('title','lang','text','password'):
        formdata[item] = stdin.getvalue(item)
    formdata['attachments'] = []

    ## Preprocessing some fields for formatting and others
    if 'attach' in stdin:
        formfile = [{'name':item.filename,'data':item.value} for item in stdin['attach']] if type(stdin['attach']) is list else [{'name':stdin['attach'].filename,'data':stdin['attach'].value}]
        ## If the user only uploaded a file that is a text, it shall become the paste
        if not formdata['text']:
            try:
                text = formfile[0]['data'].decode('UTF-8')
            except UnicodeDecodeError:
                pass
            else:
                formdata['text'] = text
                formfile[0].pop('data')
            if not formdata['title'] or formdata['title'] == 'Untitled':
                formdata['title'] = formfile[0]['name']
        ## Otherwise base64 it and attach the file
        if not ('data' in formfile[0] and formfile[0]['data']):
            formfile = formfile[1:]
        if formfile:
            for item in formfile:
                item['size'] = len(item['data'])
                item['data'] = base64.b64encode(item['data']).decode('ASCII')
                if mimetypes.guess_type(item['name'])[0] is not None:
                    item['mime_type'] = mimetypes.guess_type(item['name'])[0]
            formdata['attachments'] = formfile
        else:
            formfile = None
    if 'precexp' in stdin and stdin.getvalue('precexp') == 'imprecexp' and 'impexp' in stdin and stdin.getvalue('impexp'):
        if stdin.getvalue('impexp') == 'an_hour':
            formdata['exp'] = datetime.datetime.today()+datetime.timedelta(0,3600)
        elif stdin.getvalue('impexp') == 'a_day':
            formdata['exp'] = datetime.datetime.today()+datetime.timedelta(1)
        elif stdin.getvalue('impexp') == 'a_week':
            formdata['exp'] = datetime.datetime.today()+datetime.timedelta(7)
        elif stdin.getvalue('impexp') == 'a_month':
            t = datetime.datetime.today()
            try:
                formdata['exp'] = datetime.datetime(t.year,t.month+1,t.day,t.hour,t.minute,t.second)
            except ValueError:
                formdata['exp'] = datetime.datetime.today()+datetime.timedelta(30)
        elif stdin.getvalue('impexp') == 'a_year':
            t = datetime.datetime.today()
            try:
                formdata['exp'] = datetime.datetime(t.year+1,t.month,t.day,t.hour,t.minute,t.second)
            except ValueError:
                formdata['exp'] = datetime.datetime.today()+datetime.timedelta(365.25)
        else:
            formdata['exp'] = None
        if formdata['exp'] is not None:
            formdata['exp'] = int(formdata['exp'].timestamp())
    elif ('precexp' not in stdin or not stdin.getvalue('precexp')) and 'exp' in stdin and stdin.getvalue('exp'):
        try:
            formdata['exp'] = int(datetime.datetime.fromisoformat(stdin.getvalue('exp')).timestamp())
        except ValueError:
            formdata['exp'] = None
    else:
        formdata['exp'] = None
    formdata['expiry_time'] = formdata.pop('exp')
    if 'password' not in formdata or not formdata['password']:
        formdata['password'] = None

    ## Check if the user is really pasting something
    if not (formdata['text'] or formdata['attachments']):
        print('Status: 400')
        print('Content-Type: text/html; charset=UTF-8\n')
        print(template_head)
        print("<h1>Empty Paste</h1>")
        print("<p>It seems you are trying to create a paste with no content nor any attachments. Please at least write something.</p>")
        print(template_tail)
        exit()
    ## Now starting to build the actual query
    formdata['contents'] = formdata.pop('text')
    formdata['language'] = formdata.pop('lang')

    req = ur.Request('https://pastebin.aosc.io/api/paste/submit',method='POST')
    req.data = json.dumps(formdata).encode('UTF-8')
    req.add_header('Content-Type','application/json')
    try:
        resp = ur.urlopen(req).read().decode('UTF-8')
    except ue.HTTPError:
        print('Status: 502')
        print('Content-Type: text/html; charset=UTF-8\n')
        print(template_head)
        print("<h1>Paste API Error</h1>")
        print("<p>The AOSC Pastebin service seems to be unavailable now. Please try again later or contact AOSC Infra for more help.</p>")
        print(template_tail)
        exit()
    resp = json.loads(resp)
    if stdin.getvalue("urlonly") is not None:
        print("Status: 302")
        print("Location: https://paste.aosc.io/paste/"+resp['paste_id_repr'])
        print("Content-Type: text/plain; charset=UTF-8\n")
        print("Paste URL:")
        print("https://paste.aosc.io/paste/"+resp["paste_id_repr"])
        print("Revoke URL:")
        print("https://paste.aosc.io/deactivate/"+resp["paste_id_repr"]+"/"+resp['deactivation_token'])
    else:
        pasteview.printPaste(resp)

if __name__ == '__main__':
    main()
