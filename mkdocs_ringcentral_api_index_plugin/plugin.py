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
import logging
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError

LOG = logging.getLogger("mkdocs.plugins." + __name__)

class APIIndexPlugin(BasePlugin):

    config_scheme = (
        ('do_nothing', mkdocs.config.config_options.Type(str, default='')),
        ('spec_url', config_options.Type(str, default='https://netstorage.ringcentral.com/dpw/api-reference/specs/rc-platform.yml')),
        ('enabled_if_env', config_options.Type(str, default='ENABLE_API_INDEX')),
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
                                'name':         param['name'] if 'name' in param else ''
                                ,'description': param['description'] if 'description' in param else ''
                                ,'required':    param['required'] if 'required' in param else 'false'
                            }
                            if 'schema' in param:
                                p['type']    = param['schema']['type'] if 'type' in param['schema'] else ''
                                p['default'] = param['schema']['default'] if 'default' in param['schema'] else ''
                            params.append( p )
                    endpoint = {
                        'id':            opId
                        ,'tag':          methods['tags'][0]
                        ,'method':       method
                        ,'parameters':   sorted( params, key=lambda ps: ps[ 'name' ].capitalize() )
                        ,'path':         path
                        ,'endpoint':     'https://platform.ringcentral.com' + path
                        ,'summary':      methods['summary']
                        ,'uri_path':     tag + "/" + opId
                        ,'docs_url':     'https://developers.ringcentral.com/api-reference/' + tag + "/" + opId
                        ,'description':   methods['description'] if 'description' in methods else ''

                        ,'availability': methods['x-availability'] if 'x-availability' in methods else 'High'
                        ,'user_perms':    methods['x-user-permission'] if 'x-user-permission' in methods else ''
                        ,'app_perms':     methods['x-app-permission'] if 'x-app-permission' in methods else ''
                        ,'throttling_group': methods['x-throttling-group'] if 'x-throttling-group' in methods else ''
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

    def generate_page_contents(self):
        spec_url    = self.config['spec_url']
        sort_index  = self.config['sort_index']

        LOG.info('Generating API index for spec: %s',spec_url)
        try:
            uri_parsed = urlparse( spec_url )
            if uri_parsed.scheme in ['https', 'http']:
                url = urlopen( spec_url )
                yaml_data = url.read()
        except URLError as e:
            LOG.error("An error occured: %s",e)

        env = Environment(
            loader=FileSystemLoader('tmpl'),
            autoescape=select_autoescape(['html', 'xml'])
        )
        md = markdown.Markdown()
        env.filters['markdown'] = lambda text: Markup(md.convert(text))
    
        try:
            data = yaml.safe_load( yaml_data )
        except yaml.YAMLError as e:
            LOG.error("An error occured: %s",e)

        tree = self.build_api_tree( data, sort_index )
        index = self.build_api_index( tree, sort_index )
        template = env.get_template('api-index.md.tmpl')
        tmpl_out = template.render( index=index )
        return tmpl_out
    
    def on_config(self, config):
        if 'enabled_if_env' in self.config:
            env_name = self.config['enabled_if_env']
            if env_name:
                self.enabled = os.environ.get(env_name) == '1'
                if not self.enabled:
                    LOG.info('api-index plugin DISABLED (set environment variable %s to 1 to enable)',format(env_name))
                    return
        LOG.info("api-index plugin ENABLED")

    def on_page_read_source(self, page, config):
        if not self.enabled:
            return None
        
        index_path = os.path.join(config['docs_dir'], self.config['outfile'])
        page_path = os.path.join(config['docs_dir'], page.file.src_path)
        if index_path == page_path:
            contents = self.generate_page_contents()
            return contents

    '''
    def on_pre_build(self, config):
        outfile  = self.config['outfile']
        contents = self.generate_page_contents()
        dest = os.path.join(config['docs_dir'], outfile)
        with open(dest, "w") as fh:
            fh.write(contents)
        return config
    '''
