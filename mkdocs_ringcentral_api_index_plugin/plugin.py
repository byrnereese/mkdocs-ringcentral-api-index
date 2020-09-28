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

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from jinja2 import Environment, FileSystemLoader, select_autoescape, Markup

import requests
import markdown
import json
    
class SwaggerPlugin(BasePlugin):

    config_scheme = (
        ('do_nothing', mkdocs.config.config_options.Type(str, default='')),
        ('spec_url', config_options.Type(str, default=''))
    )

    def __init__(self):
        self.enabled = True
        self.total_time = 0

    def on_post_build(self, config):
        print("In on_post_build.")
        spec = self.config['spec_url']
        print("Spec URL: " + spec)
        stream = open( spec, 'r' )
        data = load(stream, Loader=Loader)
#        parser = SwaggerParser(swagger_path=spec)

        
