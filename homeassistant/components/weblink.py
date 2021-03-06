# -*- coding: utf-8 -*-
"""
homeassistant.components.weblink
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Adds links to external webpage

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/webpage/
"""

# The domain of your component. Should be equal to the name of your component
import logging

from homeassistant.helpers.entity import Entity
from homeassistant.util import slugify

DOMAIN = "weblink"

# List of component names (string) your component depends upon
DEPENDENCIES = []

ATTR_NAME = 'name'
ATTR_URL = 'url'
ATTR_ICON = 'icon'

_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    """ Setup weblink component. """

    # States are in the format DOMAIN.OBJECT_ID

    links = config.get(DOMAIN)

    for link in links.get('entities'):
        if ATTR_NAME not in link or ATTR_URL not in link:
            _LOGGER.error("You need to set both %s and %s to add a %s",
                          ATTR_NAME, ATTR_URL, DOMAIN)
            continue
        Link(hass, link.get(ATTR_NAME), link.get(ATTR_URL),
             link.get(ATTR_ICON))

    # return boolean to indicate that initialization was successful
    return True


class Link(Entity):
    """ Represent a link """

    def __init__(self, hass, name, url, icon):
        """ Represents a link. """
        self.hass = hass
        self._name = name
        self._url = url
        self._icon = icon
        self.entity_id = DOMAIN + '.%s' % slugify(name)
        self.update_ha_state()

    @property
    def icon(self):
        return self._icon

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._url
