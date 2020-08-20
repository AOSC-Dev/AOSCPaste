#! /usr/bin/python3 -B

import cgi
import datetime
import json
import os
import pygments
import pygments.formatters.html
import pygments.lexers
import urllib.error as ue
import urllib.request as ur

translateLanguage = {
        'clike': 'c',
        'htmlmixed': 'html',
        'jinja2': 'jinja'
        }

template_head = '<!DOCTYPE html>\n<html lang="en-us">\n<head>\n\t<meta name="generator" content="Hugo 0.68.3" />\n\t<meta charset="utf-8" />\n\t<meta http-equiv="X-UA-Compatible" content="IE=edge" />\n\t<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=7" />\n    <link href="https://aosc.io/css/main.min.css" rel="stylesheet" />\n    <link href="https://paste.aosc.io/pastebin.css" rel="stylesheet" />\n    <title>Pastebin | AOSC Pastebin</title>\n    <link rel="icon" href="https://aosc.io/img/aosc.png" />\n    <link rel="icon" sizes="any" type="image/svg+xml" href="https://aosc.io/img/aosc.min.svg" />\n\t<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600&display=swap" rel="stylesheet" />\n\t<style>body{font-family:\'Noto Serif SC\',serif;}</style>\n<link rel="stylesheet" href="https://paste.aosc.io/highlight.css" />\n</head>\n\n<body>\n\t<div class="wrapper">\n\t\t<nav class="header">\n\t\t\t<div class="columns" style="align-items: start;">\n\t\t\t\t<div class="columns" style="display: flex;">\n                    <a class="clear-link" href="https://aosc.io/">\n                        <table>\n                            <tbody>\n                                <tr>\n                                    <td>\n                                        <img alt="AOSC Logo" class="logo"\n                                            width="40" height="40" src="https://aosc.io/img/aosc.png"\n                                            style="height: 40px; width: 40px;" />\n                                    </td>\n                                    <td style="vertical-align: bottom;"><h1 class="page-title">/Paste</h1></td>\n                                </tr>\n                            </tbody>\n                        </table>\n                    </a>\n\t\t\t\t</div>\n\t\t<ul class="column is-two-thirds" style="word-break: keep-all;">\n                    \n                    <li><a href="https://aosc.io/news">News</a>\n                    </li><li><a href="https://aosc.io/people">People</a>\n                    </li><li><a href="https://packages.aosc.io">Packages</a>\n                    </li><li><a href="https://wiki.aosc.io">Wiki</a>\n                    </li><li><a href="https://aosc.io/about">About</a>\n                    </li><li><a href="https://aosc.io/downloads">Downloads</a>\n                    </li><li><a href="https://aosc.io/repo">Mirrors</a>\n                    </li><li><a href="https://github.com/AOSC-Dev/">Git</a>\n                    </li><li><a href="https://aosc.io/mail">Mail</a>\n                    </li><li><a href="https://paste.aosc.io/">Pastebin</a>\n                    </li>\n\t\t</ul>\n\t\t\t</div>\n\t\t</nav>\n\t\t<hr class="hr-nav" />\n\n<div class="pastebin">\n'
template_tail = '</div>\n\t\t\t<hr />\n\t\t\t<div class="center footer">\n\t\t\t\t<span>Copyleft 2011 — 2020, Members of the Community <!--| &nbsp; <a href="/lingua">Site Language</a>--></span>\n\t\t\t</div>\n\t\t</div>\n\t</body>\n</html>\n'

def printPaste(resp,rid=None):
    print('Content-Type: text/html; charset=UTF-8\n')
    print(template_head)
    print('<h1>'+resp['title']+'</h1>')
    if rid:
        print('<div id="deactivate">')
        print('\t<h2>Deactivate Paste</h2>')
        print('\t<p>Are you sure that you want to deactivate this paste?</p>')
        print('\t<a class="button" href="https://paste.aosc.io/deactivate-confirm/'+resp['paste_id_repr']+'/'+rid+'"><button type="button">Yes</button></a><a class="button" href="https://paste.aosc.io/paste/'+resp['paste_id_repr']+'"><button type="button" >No</button></a>\n</div>')
    if 'deactivation_token' in resp:
        print('<div id="deactivate">')
        print('\t<h2>Deactivation Key</h2>')
        print('\t<p>The paste deactivation URL is shown below. Make sure to keep it somewhere safe; this is the only time you\'ll see it!</p>')
        print('\t<p><a href="https://paste.aosc.io/deactivate/'+resp['paste_id_repr']+'/'+resp['deactivation_token']+'">https://paste.aosc.io/deactivate/'+resp['paste_id_repr']+'/'+resp['deactivation_token']+'</a></p>')
        print('\t<h2>Paste URL</h2>')
        print('\t<a href="https://paste.aosc.io/paste/'+resp['paste_id_repr']+'">https://paste.aosc.io/paste/'+resp['paste_id_repr']+'</a>')
        print('</div>')
    if 'attachments' in resp and resp['attachments']:
        print('<div id="attach">')
        print('\t<h2>Attachments</h2>')
        print('\t<ul id="attach">')
        for item in resp['attachments']:
            if 'deactivation_token' in resp:
                print('\t\t<li><a href="https://pastebin.aosc.io/paste/'+resp['paste_id_repr']+'/attachment/'+item['name']+'">'+item['name']+' (Size: '+str(item['size'])+')</a></li>')
            else:
                print('\t\t<li><a href="https://pastebin.aosc.io/paste/'+resp['paste_id_repr']+'/attachment/'+item['file_name']+'">'+item['file_name']+' (Size: '+str(item['file_size'])+')</a></li>')
        print('\t</ul>')
        print('</div>')
    pasteinfo = '<p id="pasteinfo">Type: '+resp['language']+' | Posted: '+datetime.datetime.fromtimestamp(resp['post_time']).isoformat()
    if resp['expiry_time']:
        pasteinfo += ' | Expires: '+datetime.datetime.fromtimestamp(resp['expiry_time']).isoformat()
    pasteinfo += ' | '+str(resp['views'])+' view'+('s' if resp['views'] != 1 else '')+'</p>'
    print(pasteinfo)
    print('<p><a href="https://pastebin.aosc.io/paste/'+resp['paste_id_repr']+'/raw'+('?password='+resp['password'] if 'password' in resp else '')+'">View raw</a> | <a href="https://pastebin.aosc.io/paste/'+resp['paste_id_repr']+'">View with fancy JavaScript UI</a></p>')
    lang = translateLanguage[resp['language']] if resp['language'] in translateLanguage else resp['language']
    print(pygments.highlight(resp['contents'],pygments.lexers.get_lexer_by_name(lang),pygments.formatters.HtmlFormatter()))
#    print('<pre id="content">'+(html.escape(str(resp['contents'])) if resp['contents'] else "")+'</pre>')
#    print('<textarea class="debug">',resp,'</textarea>')
    print('<textarea class="debug">')
    for item in resp:
        print(item,resp[item],sep='\t')
    print('</textarea>')
    if 'deactivation_token' in resp:
        print('<!-- FOR CLI Users:')
        print('Deactivation Page: https://paste.aosc.io/deactivate/'+resp['paste_id_repr']+'/'+resp['deactivation_token'])
        print('Paste URL: https://paste.aosc.io/paste/'+resp['paste_id_repr'])
        print('-->')
    print(template_tail)

def main():
    pasteid = None
    revokeid = None
    pastepass = None
    confirmrevoke = False
    if len(os.environ['REQUEST_URI']) > 7 and os.environ['REQUEST_URI'][:7] == '/paste/':
        pasteid = os.environ['REQUEST_URI'][7:]
    elif len(os.environ['REQUEST_URI']) > 13 and os.environ['REQUEST_URI'][:13] == '/secretpaste/':
        tmp = os.environ['REQUEST_URI'][13:].split('/')
        stdin = cgi.FieldStorage()
        pastepass = stdin.getvalue('password')
        pasteid = tmp[0]
        if not pastepass and len(tmp) == 2:
            pastepass = tmp[1]
    elif len(os.environ['REQUEST_URI']) > 12 and os.environ['REQUEST_URI'][:12] == '/deactivate/':
        tmp = os.environ['REQUEST_URI'][12:].split('/')
        if len(tmp) == 2:
            pasteid = tmp[0]
            revokeid = tmp[1]
    elif len(os.environ['REQUEST_URI']) > 20 and os.environ['REQUEST_URI'][:20] == '/deactivate-confirm/':
        tmp = os.environ['REQUEST_URI'][20:].split('/')
        if len(tmp) == 2:
            pasteid = tmp[0]
            revokeid = tmp[1]
            confirmrevoke = True
    elif len(os.environ['REQUEST_URI']) >= 21 and os.environ['REQUEST_URI'][:21] == '/cgi-bin/pasteview.py':
        stdin = cgi.FieldStorage()
        pasteid = stdin.getvalue('pid')
        revokeid = stdin.getvalue('rid')
    if not pasteid:
        print('Status: 400')
        print('Content-Type: text/html; charset=UTF-8\n')
        print(template_head)
        print('<h1>Bad Request</h1>')
        print('<p>It seems you did not tell me the Paste ID you are looking for.</p>')
        print('<p>Please access the paste via https://paste.aosc.io/paste/YOUR_PASTE_ID or https://paste.aosc.io/cgi-bin/pasteview.py?pid=YOUR_PASTE_ID.</p>')
        print('<p>'+os.environ['REQUEST_URI']+'</p>')
        print(template_tail)
        exit()
    else:
        req = ur.Request("https://pastebin.aosc.io/api/paste/details",method="POST")
        req.data = json.dumps({'paste_id':pasteid}).encode('UTF-8')
        if pastepass:
            req.data = json.dumps({'paste_id':pasteid,'password':pastepass}).encode('UTF-8')
        req.add_header('Content-Type','application/json')
        try:
            resp = ur.urlopen(req).read().decode('UTF-8')
        except ue.HTTPError as e:
            if e.code == 404:
                print('Status: 404')
            elif e.code == 401:
                print('Status: 401')
            else:
                print('Status: 502')
            print('Content-Type: text/html; charset=UTF-8\n')
            print(template_head)
            if e.code == 404:
                print("<h1>Paste Not Found</h1>")
                print("<p>The paste ID you have entered ("+pasteid+") is not found in our pastebin. Please double check you have entered a correct paste ID, and the paste is not deactivated or expired.</p>")
            elif e.code == 401:
                print('<h1>Secret Paste</h1>')
                print('<p>The paste you tried to access is password protected. Please enter the password below.</p>')
                print('<form action="https://paste.aosc.io/secretpaste/'+pasteid+'" method="POST"><label for="pass">Password: </label><input type="password" id="pass" name="password" /><input type="submit"></form>')
            else:
                print("<h1>Paste API Error</h1>")
                print("<p>The AOSC Pastebin service seems to be unavailable now. Please try again later or contact AOSC Infra for more help.</p>")
                print("<pre>",e,"</pre>")
            print(template_tail)
            exit()
        if revokeid and confirmrevoke:
            req = ur.Request("https://pastebin.aosc.io/api/paste/deactivate",method="POST")
            req.data = json.dumps({'paste_id':pasteid,'deactivation_token':revokeid}).encode('UTF-8')
            req.add_header('Content-Type','application/json')
            try:
                resp = ur.urlopen(req).read().decode('UTF-8')
            except ue.HTTPError as e:
                print('Status: '+str(e.code))
                print('Content-Type: text/html; charset=UTF-8\n')
                print(template_head)
                print("<h1>Deactivate Paste Failed</h1>")
                print('<p>The attempt to deactivate your paste failed with the following Error Code:',e,'</p>')
                print(template_tail)
            else:
                print('Content-Type: text/html; charset=UTF-8\n')
                print(template_head)
                print('<h1>Paste Deactivated</h1>')
                print('<p>Your paste has been deactivated successfully. To create a new paste, please visit the following website: <a href="https://paste.aosc.io/">https://paste.aosc.io/</a></p>')
                print('<textarea class="debug">',resp,'</textarea>')
                print(template_tail)
        elif revokeid:
            resp = json.loads(resp)
            printPaste(resp['details'],revokeid)
        else:
            resp = json.loads(resp)
            if pastepass:
                resp['details']['password'] = pastepass
            printPaste(resp['details'])
            req = ur.urlopen("https://pastebin.aosc.io/paste/"+pasteid)

if __name__ == '__main__':
    main()
