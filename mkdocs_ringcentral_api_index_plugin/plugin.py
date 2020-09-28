import os
import sys
import fnmatch
from timeit import default_timer as timer
from datetime import datetime, timedelta

from mkdocs import utils as mkdocs_utils
from mkdocs.config import config_options, Config
from mkdocs.plugins import BasePlugin
import mkdocs.structure.files

#from swagger_parser import SwaggerParser

import yaml
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from jinja2 import Environment, FileSystemLoader, select_autoescape, Markup

import requests
import markdown
import json
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError
    
class APIIndexPlugin(BasePlugin):

    config_scheme = (
        ('do_nothing', mkdocs.config.config_options.Type(str, default='')),
        ('spec_url', config_options.Type(str, default='https://netstorage.ringcentral.com/dpw/api-reference/specs/rc-platform.yml')),
        ('sort_index', config_options.Type(str, default='tag')),
        ('outfile', config_options.Type(str, default='docs/quick-reference.md'))
    )

    def __init__(self):
        self.enabled = True
        self.total_time = 0

    def print_api_tree( self, tree ):
        current = ''
        for item in tree:
            first = item['id'][0]
            if (first != current):
                if (first != ''):
                    print()
                current = first
                print( current.capitalize() )
            print( item['id'] + ": " + item['summary'] )

    def build_api_tree( self, data, sort_index ):
        api_tree = []
        for path, paths in data['paths'].items():
            for method, methods in paths.items():
                if methods['operationId']:
                    opId = methods['operationId']
                    tag = methods['tags'][0].replace(' ','-')
                    params = []
                    if 'parameters' in methods:
                        for param in methods['parameters']:
                            p = {
                                'name':         param['name']
                                ,'description': param['description'] if 'description' in param else ''
                                ,'type':        param['type'] if 'type' in param else ''
                                ,'required':    param['required'] if 'required' in param else 'false'
                                ,'default':     param['default'] if 'default' in param else ''
                            }
                            params.append( p )
                    endpoint = {
                        'id':            opId
                        ,'tag':          methods['tags'][0]
                        ,'availability': methods['x-availability'] if 'x-availability' in methods else 'High'
                        ,'method':       method
                        ,'parameters':   sorted( params, key=lambda ps: ps[ 'name' ].capitalize() )
                        ,'path':         path
                        ,'endpoint':     'https://platform.ringcentral.com' + path
                        ,'summary':      methods['summary']
                        ,'uri_path':     tag + "/" + opId
                        ,'docs_url':     'https://developers.ringcentral.com/api-reference/' + tag + "/" + opId
                        ,'description':  methods['description'] if 'description' in methods else ''
                        ,'user_perms':    methods['x-user-permission'] if 'x-user-permission' in methods else ''
                        ,'app_perms':     methods['x-app-permission'] if 'x-app-permission' in methods else ''
                        }
                    api_tree.append( endpoint )
        return sorted( api_tree, key=lambda ops: ops[ sort_index ].capitalize() )

    def build_api_index( self, tree, sort_index ):
        index = {}
        current = ''
        for item in tree:
            idx = item[ sort_index ]
            if (idx != current):
                current = idx
                index[ current ] = []
            index[ current ].append( item )
        return index

#    def download_spec(spec_url, spec_file):
#        r = requests.get(spec_url, allow_redirects=True)
#        open( spec_file, 'wb').write(r.content)
       
    def on_post_build(self, config):
        spec_url    = self.config['spec_url']
        outfile     = self.config['outfile']
        sort_index  = self.config['sort_index']
        print("Generating API index for spec: " + spec_url)

        try:
            uri_parsed = urlparse( spec_url )
            if uri_parsed.scheme in ['https', 'http']:
                url = urlopen( spec_url )
                yaml_data = url.read()
        except URLError as e:
            print(e)

        env = Environment(
            loader=FileSystemLoader('tmpl'),
            autoescape=select_autoescape(['html', 'xml'])
        )
        md = markdown.Markdown()
        env.filters['markdown'] = lambda text: Markup(md.convert(text))
    
        #stream = open( spec_file, 'r' )
        #data = load(stream, Loader=Loader)

        try:
            data = yaml.safe_load( yaml_data )
        except yaml.YAMLError as e:
            print(e)

        tree = self.build_api_tree( data, sort_index )
        index = self.build_api_index( tree, sort_index )
        template = env.get_template('api-index.md.tmpl')
        tmpl_out = template.render( index=index )
        with open(outfile, "w") as fh:
            fh.write(tmpl_out)

