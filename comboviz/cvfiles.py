
#This file is part of ComboViz.
#
#ComboViz is a program for recording and visualizing measurements from a
#direct entry fence lock during manipulation.
#
#Copyright (C) 2013  Eric Beanland
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Classes for reading and writing ComboViz files."""

import json

from misc import LockException


class CVLockFile(object):
    """Save and load program state from text files formated as json. 
    CVFile.props is a list of attributes you can retreive from CVFile objects.
    The CVFile.dumped flag specifies whether or not a file should be written
    to disk"""

    props = {'rows':[],
             'dial_size':100.0,
             'wheels':3.0,
             'scale':5.0,
             'draw_grid':True,
             'file_ver':0}

    
    def __init__(self, filepath = None):
        self.path = filepath
        self.dumped = True #flag for if data has been changed or not
        self.__dict__.update(self.props)

        if filepath:
            self.load()


    def load(self):
        """Load the program state from the file specified by CVFile.path"""
        try:
            with open(self.path, 'r+') as file_:
                data = json.load(file_)
                for key in self.props:
                    setattr(self, key, data[key])
            self.dumped = True

        except IOError as ex:
            msg = ('The file {} could not be opened.'.format(self.path),
                    'Error: "{}"'.format(ex.args[1]))
            raise LockException(*msg)

        except KeyError as ex:
            msg = ('The file {} could not be loaded.'.format(self.path),
                    'The item "{}" is missing.'.format(ex.args[0]))
            raise LockException(*msg)

        except ValueError:
            msg = ('The file {} is not valid.'.format(self.path),
                    'The file is incorrect type or is damaged.')
            raise LockException(*msg)


    def dump(self):
        """Dump the program state to the file specified by CVFile.path"""
        data = {k:v for (k,v) in self.__dict__.items() if k in self.props}
        try:
            with open(self.path, 'w') as file_:
                json.dump(data, file_, indent=4, separators=(',', ': '))

            self.dumped = True

        except IOError as ex:
            msg = ('The file {} could not be written.'.format(self.path),
                    'Error: "{}"'.format(ex.args[1]))
            raise LockException(*msg)


