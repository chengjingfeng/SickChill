import tvmaze

import html
import json
import re
import traceback

import requests

import sickchill.start
from sickchill import logger, settings
from sickchill.tv import TVEpisode

from .base import Indexer
from .wrappers import ExceptionDecorator


class TVMAZE(Indexer):
    def __init__(self):
        super(TVMAZE, self).__init__()
        self.name = "tvmaze"
        self.slug = "tvmaze"
        self.icon = "images/indexers/tvmaze.png"
        self.api = tvmaze.api.Api()

    def search(self, name, language=None):
        self.api.search.shows(name)

    def get_series_by_id(self, indexerid, language=None):
        pass

    def get_series_by_name(self, indexerid, language=None):
        pass

    def episodes(self, show, season):
        pass

    def episode(self, show, season, episode):
        pass

    @property
    def languages(self):
        pass

    @property
    def lang_dict(self):
        pass
