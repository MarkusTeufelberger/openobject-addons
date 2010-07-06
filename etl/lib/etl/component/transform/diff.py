# -*- encoding: utf-8 -*-
##############################################################################
#
#    ETL system- Extract Transfer Load system
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
"""
 Used to find difference between Data.

 Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
 GNU General Public License.
"""

from etl.component import component

class diff(component):
    """
        This is an ETL Component that finds difference.
        Takes 2 flows in input and detect a difference between these two flows
        using computed keys (based on data records) to compare elements that may not
        have to be in the same order.

        Type                  : Data Component.
        Computing Performance : Semi-Streamline.
        Input Flows           : 2.
        * main                : The main flow.
        * .*                  : The second flow.
        Output Flows          : 0-x.
        * same                : Returns all elements that are the same in both input flows.
        * updated             : Returns all updated elements
        * removed             : Returns all elements that where in main and not in the second flow.
        * added               : Returns all elements from the second flow that are not in the main channel.
    """
    def __init__(self, keys, name='component.process.diff', transformer=None, row_limit=0):
        """
        Required  Parameters
        keys  : Keys for differentiating.

        Extra Parameters
        name          : Name of Component.
        """
        super(diff, self).__init__(name=name, transformer=transformer, row_limit=row_limit)
        self._type = 'component.transfer.diff'
        self.keys = keys
        self.row = {}
        self.diff = []
        self.same = []

    def __copy__(self):
        res = diff(self.key, self.name, self.transformer, self.row_limit)
        return res

    def __getstate__(self):
        res = super(diff, self).__getstate__()
        res.update({'keys':self.keys})# to be chk for other values in init
        return res

    def __setstate__(self, state):
        super(diff, self).__setstate__(state)
        self.__dict__ = state

    # Return the key of a row
    def key_get(self, row):
        result = []
        for k in self.keys:
            result.append(row[k]) # should be chk...it add value not key here
        return tuple(result)

    def process(self):
        self.row = {}
        for channel, transition in self.input_get().items():
            if channel not in self.row:
                self.row[channel] = {}
            other = None
            for key in self.row.keys():
                if key <> channel:
                    other = key
                    break
            for iterator in transition:
                for r in iterator:
                    key = self.key_get(r)
                    if other and (key in self.row[other]):
                        if self.row[other][key] == r:
                            yield r, 'same'
                        else:
                            yield r, 'update'
                        del self.row[other][key]
                    else:
                        self.row[channel][key] = r
        todo = ['add','remove']
        for k in self.row:
            channel= todo.pop()
            for v in self.row[k].values():
                yield v,channel

def test():
    from etl_test import etl_test
    from etl import transformer
    input_part = [
    {'id': 1L, 'name': 'Fabien', 'address': 'france'},
    {'id': 1L, 'name': 'Fabien', 'address': 'belgium'},
    {'id': 3L, 'name': 'harshad', 'address': 'india'},
    ]
    modify = [
    {'id': 1L, 'name': 'Fabien', 'address': 'india'},
    {'id': 1L, 'name': 'Fabien', 'address': 'belgium'},
    {'id': 3L, 'name': 'harshad', 'address': 'india'},
    ]

    add = [
    {'id': 4L, 'name': 'henry', 'address': 'spain'}
    ]


    modify = [
    {'id': 1L, 'name': 'Fabien', 'address': 'india'}
    ]

    remove = [
    {'id': 1L, 'name': 'Fabien', 'address': 'belgium'},
    ]
    test = etl_test.etl_component_test(diff(['id']))
    test.check_input({'main':input_part})
    test.check_output(modify, 'main')

if __name__ == '__main__':
    test()
