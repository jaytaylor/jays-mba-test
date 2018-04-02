#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import collections
import json
import spacy

from flask import Flask
from flask import jsonify
from flask import request

app = Flask(__name__)

nlp_sm = spacy.load('en_core_web_sm')
nlp_lg = None
#nlp = spacy.load('en_core_web_lg')

@app.route('/')
def index():
    return 'Hello world'

def clean_ents(ents):
    """
    Filter out undesirable entities and emit an ordered JSON-serializable
    structure.
    """
    by_freq = {}
    for ent in ents:
        if ent.label_ in (u'CARDINAL', u'ORDINAL', u'PERCENT', u'QUANTITY', u'DATE', u'MONEY'):
            continue
        if ent.text in by_freq:
            by_freq[ent.text][0] += 1
        else:
            by_freq[ent.text] = [1, ent.text, ent.label_, ent.root.tag_]

    final = map(
        lambda (freq, ent, label, pos): {
            'entity': ent,
            'label': label,
            'frequency': freq,
            'pos': pos,
        },
        list(
            collections.OrderedDict(
                sorted(by_freq.items(), key=lambda tup: tup[1][0], reverse=True)
            ).values()
        )
    )
    return final


@app.route('/v1/named-entities', methods=['POST'])
def named_entities():
    global nlp_lg

    if request.args.get('instance') == 'lg':
        if not nlp_lg:
            nlp_lg = spacy.load('en_core_web_lg')
        nlp_instance = nlp_lg
    else:
        nlp_instance = nlp_sm

    if request.headers.get('Content-Type') == 'application/json':
        payload = json.loads(request.data)
        if not isinstance(payload, dict) or 'text' not in payload:
            raise Exception('missing "text" field in JSON payload')
        text = payload['text'].encode('utf-8')
    else:
        if not len(request.data):
            raise Exception('no data')

        text = request.values.keys()[0].encode('utf-8')

    doc = nlp_instance(text.decode('utf-8'))
    ents = doc.ents
    return jsonify(clean_ents(ents))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)

