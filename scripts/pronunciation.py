# -*- coding: utf-8 -*-
"""Pair reader-facing English with provisional Thai pronunciations."""
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TERMS = json.loads((ROOT/'content/pronunciations.json').read_text())['terms']
READINGS = {k.casefold():v for k,v in TERMS.items()}
PATTERN = re.compile(r'(?<![A-Za-z])('+'|'.join(re.escape(k) for k in sorted(TERMS,key=len,reverse=True))+r')(?![A-Za-z])',re.I)


def reading(term):
    return READINGS[term.casefold()]


def annotate(text, markup=False):
    parts=[]
    previous=0
    for match in PATTERN.finditer(text):
        term=match.group()
        thai=reading(term)
        parts.append(html.escape(text[previous:match.start()]) if markup else text[previous:match.start()])
        original=html.escape(term) if markup else term
        # Rebuilding or importing an already annotated sentence must be idempotent.
        if re.match(r'\s*\('+re.escape(thai)+r'\)',text[match.end():]):
            parts.append(original)
        elif markup:
            parts.append(original+f'<span class="pronunciation" lang="th"> ({html.escape(thai)})</span>')
        else:
            parts.append(original+' ('+thai+')')
        previous=match.end()
    parts.append(html.escape(text[previous:]) if markup else text[previous:])
    return ''.join(parts)


RAW_KEYS={'id','slug','category','kingdom','related','status','visibility','kind','language','color','url','viewBox','version'}


def annotate_data(value,key=''):
    if key in RAW_KEYS:
        return value
    if isinstance(value,str):
        return annotate(value)
    if isinstance(value,list):
        return [annotate_data(item,key) for item in value]
    if isinstance(value,dict):
        return {k:annotate_data(v,k) for k,v in value.items()}
    return value


class PronunciationHTML(HTMLParser):
    VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    RAW={'script','style','pre','code','svg'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out=[]
        self.stack=[]

    def start(self,tag,attrs,closed=False):
        attrs=dict(attrs)
        for key in ('title','alt','aria-label','placeholder'):
            if attrs.get(key): attrs[key]=annotate(attrs[key])
        if tag=='meta' and (attrs.get('name')=='description' or attrs.get('property') in ('og:title','og:description','og:site_name')):
            attrs['content']=annotate(attrs.get('content',''))
        serial=''.join(' '+k+('="'+html.escape(v,quote=True)+'"' if v is not None else '') for k,v in attrs.items())
        self.out.append('<'+tag+serial+('/>' if closed else '>'))
        if not closed and tag not in self.VOID:
            self.stack.append((tag,attrs))

    def handle_starttag(self,tag,attrs): self.start(tag,attrs)
    def handle_startendtag(self,tag,attrs): self.start(tag,attrs,True)

    def handle_endtag(self,tag):
        self.out.append('</'+tag+'>')
        for index in range(len(self.stack)-1,-1,-1):
            if self.stack[index][0]==tag:
                del self.stack[index:]
                break

    def handle_data(self,text):
        if any(tag in ('script','style') for tag,_ in self.stack):
            self.out.append(text)
        elif any(tag in self.RAW or attrs.get('data-reading-ready')=='true' or 'pronunciation' in attrs.get('class','').split() for tag,attrs in self.stack):
            self.out.append(html.escape(text))
        else:
            self.out.append(annotate(text,markup=not any(tag in ('title','option','textarea') for tag,_ in self.stack)))

    def handle_decl(self,decl): self.out.append('<!'+decl+'>')
    def handle_comment(self,text): self.out.append('<!--'+text+'-->')


def annotate_html(source):
    parser=PronunciationHTML()
    parser.feed(source)
    return ''.join(parser.out)
