# -*- coding: utf-8 -*-
# ChriCar Beteiligungs- und Beratungs- GmbH
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
from osv import fields,osv

class chricar_view_id(osv.osv):
    _name = "chricar_view_id"
    _columns = {
        'name': fields.char('Name', size=32),
    }

    def init(self, cr):

        #install plpgsql languge in to the data database
        cr.execute("SELECT true FROM pg_catalog.pg_language WHERE lanname = 'plpgsql';")
        if not cr.fetchall():
            cr.execute("create language plpgsql;")

        #Create a table to record the unique ids for the view
        cr.execute("SELECT count(*) FROM pg_class WHERE relname = 'unique_view_id'")
        if cr.fetchone()[0] == 0:
#            cr.execute("""CREATE TABLE unique_view_id (id serial, view_name varchar(128) NOT NULL, id_1 integer, id_2 integer, id_3 integer);""")
            cr.execute("""CREATE TABLE unique_view_id (id serial, view_name varchar(128) NOT NULL,
                            id_1 integer NOT NULL default 0,
                            id_2 integer NOT NULL default 0,
                            id_3 integer NOT NULL default 0,
                            id_4 integer NOT NULL default 0);""")
            cr.execute("""create unique index unique_view_id_1 on unique_view_id(view_name,id_1,id_2,id_3,id_4);""")

        # create a funtion wich will return a unique ID
        cr.execute("""CREATE OR REPLACE FUNCTION get_id(view varchar, id1 integer, id2 integer, id3 integer, id4 integer ) RETURNS integer AS $$
                      DECLARE
                          res_id integer;
                      BEGIN
                          SELECT id INTO res_id FROM unique_view_id
                          WHERE view_name=view
                                  AND id_1=coalesce(id1,0)
                                  AND id_2=coalesce(id2,0)
                                  AND id_3=coalesce(id3,0)
                                  AND id_4=coalesce(id4,0);

                          IF res_id IS NULL THEN
                              INSERT INTO unique_view_id(id, view_name, id_1, id_2, id_3, id_4)
                                  VALUES(default, view,
                                      coalesce(id1,0),
                                      coalesce(id2,0),
                                      coalesce(id3,0),
                                      coalesce(id4,0));
                              SELECT id INTO res_id FROM unique_view_id
                              WHERE view_name=view
                                      AND id_1=coalesce(id1,0)
                                      AND id_2=coalesce(id2,0)
                                      AND id_3=coalesce(id3,0)
                                      AND id_4=coalesce(id3,0);
                          END IF;

                          RETURN coalesce(res_id,0);
                      END;
                  $$ LANGUAGE plpgsql;""")

chricar_view_id()

