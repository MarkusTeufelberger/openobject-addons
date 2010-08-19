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
import time
import netsvc
from osv import fields, osv


#assumptions
#for moves with state posted
#* debit/credit of move_lines cant' be altered
#* move_lines can't be delted
#
class triggger(osv.osv):
    _name = "triggger"
    def init(self, cr):

#----------------- THIS CODE WILL BE RELEASED IN A SEPARATE MODULE -------------
# This block of code will create the functionality to create a unique id for the records in views.
# This block included in this function just because, this is the first function to execute in this file.
#
#        #install plpgsql languge in to the data database
#        cr.execute("SELECT true FROM pg_catalog.pg_language WHERE lanname = 'plpgsql';")
#        if not cr.fetchall():
#            cr.execute("create language plpgsql;")

#        #Create a table to record the unique ids for the view
#        cr.execute("SELECT count(*) FROM pg_class WHERE relname = 'unique_view_id'")
#        if cr.fetchone()[0] == 0:
#            cr.execute("""CREATE TABLE unique_view_id (id serial, view_name varchar(128) NOT NULL,
#            id_1 integer NOT NULL default 0,
#            id_2 integer NOT NULL default 0,
#            id_3 integer NOT NULL default 0);""")
#            cr.execute("""create unique index unique_view_id_1 on unique_view_id(view_name,id_1,id_2,id_3);""")

        # create a funtion wich will return a unique ID
 #       cr.execute("""CREATE OR REPLACE FUNCTION get_id(view varchar, id1 integer, id2 integer, id3 integer,0 ) RETURNS integer AS $$
#                    DECLARE
#                        res_id integer;
#                   BEGIN
#                       SELECT id INTO res_id FROM unique_view_id
#                        WHERE view_name=view
#                          AND id_1=coalesce(id1,0)
#                          AND id_2=coalesce(id2,0)
#                          AND id_3=coalesce(id3,0);
#                       IF res_id IS NULL THEN
#                           INSERT INTO unique_view_id(id, view_name, id_1, id_2, id_3)
#                           VALUES(default, view,
#                           coalesce(id1,0),
#                           coalesce(id2,0),
#                           coalesce(id3,0));
#                           SELECT id INTO res_id FROM unique_view_id
#                            WHERE view_name=view
#                              AND id_1=coalesce(id1,0)
#                              AND id_2=coalesce(id2,0)
#                              AND id_3=coalesce(id3,0);
#                       END IF;
#                       RETURN coalesce(res_id,0);
#                   END;
#                  $$ LANGUAGE plpgsql;""")
#-------------------------------------------------------------------------------




        cr.execute("""
CREATE OR REPLACE FUNCTION account_period_sum_update(move_id_i integer,add_sub_i integer) RETURNS void  AS
$$
DECLARE
debit_p  numeric(16,2);
credit_p numeric(16,2);

close_method_p varchar;
period_00_p    varchar;



move_rec record;
period_00_rec record;
BEGIN
/*
to be sure
*/
debit_p  :=0;
credit_p :=0;
/*
loop for all move_line of this move
*/
for move_rec in
  select * from account_move_line
    where move_id = move_id_i
     order by account_id -- eventually to avoid dead locks?
     LOOP
     if add_sub_i = 1
       then debit_p  := case when move_rec.debit  is null then 0 else move_rec.debit end;
            credit_p := case when move_rec.credit is null then 0 else move_rec.credit end;
       elsif add_sub_i = -1
         then
            debit_p  := case when move_rec.debit  is null then 0 else -move_rec.debit end;
            credit_p := case when move_rec.credit is null then 0 else -move_rec.credit end;
     end if;
               update account_account_period_sum
                  set debit = debit + debit_p,
                      credit=credit + credit_p
                where account_id = move_rec.account_id
                  and period_id  = move_rec.period_id
                  and name not like '%00';

            IF not found
               then
                   insert into account_account_period_sum
                    (account_id,period_id,debit,credit,name,sum_fy_period_id)
                   select move_rec.account_id, move_rec.period_id, debit_p, credit_p, to_char(date_start,'YYYYMM'),
                   get_id('account_account_period_sum',move_rec.account_id,fiscalyear_id,0,0)
                      from account_period
                     where id = move_rec.period_id;

            END IF;
/*
set account_period_sum_id in move_lines
*/
 update account_move_line m
    set account_period_sum_id = (select id from account_account_period_sum
                                  where account_id=m.account_id
                                    and period_id =m.period_id
                                    and name not like '%00')
  where move_id = move_id_i;


/*
balance carried forward
*/
        select into close_method_p t.close_method
          from account_account a,
               account_account_type t
         where t.id = a.user_type
           and a.id = move_rec.account_id;

        if close_method_p != 'none'
          then
             -- get period id of the first period next year
             for period_00_rec in
             select p00.id as period_id,
                    to_char(yfollow.date_start,'YYYY')||'00' as code,
                    yfollow.id as fiscalyear_id
               from account_period p00,
                    account_period pcurr,
                    account_fiscalyear yfollow
              where pcurr.id = move_rec.period_id
                and yfollow.date_start > pcurr.date_start -- all years start after current period
                and p00.date_start = yfollow.date_start
                --and p00.name like '%00'

                loop

              update account_account_period_sum
                  set debit = debit + debit_p,
                      credit=credit + credit_p
                where account_id = move_rec.account_id
                  and period_id  = period_00_rec.period_id
                  and name = period_00_rec.code;
               IF not found
                 then
                   insert into account_account_period_sum
                    (account_id,period_id,debit,credit,name,sum_fy_period_id)
                   values(
                    move_rec.account_id, period_00_rec.period_id, debit_p, credit_p,period_00_rec.code,
                     get_id('account_account_period_sum',move_rec.account_id,period_00_rec.fiscalyear_id,0 ,0));
               END IF;
           end loop;

        end if;
    END LOOP;
    RETURN;
END;
$$
LANGUAGE plpgsql;
""")


        cr.execute("""
CREATE OR REPLACE FUNCTION account_move_sum_insert() RETURNS trigger  AS
$$
BEGIN
 execute account_period_sum_update(NEW.id,1);
 return NEW;
END;
$$
LANGUAGE plpgsql;
""")


        cr.execute("""
CREATE OR REPLACE FUNCTION account_move_sum_update() RETURNS trigger  AS
$$
DECLARE
add_sub_p integer;
BEGIN
 if    OLD.state !='posted' and   NEW.state  = 'posted'
  then add_sub_p := 1;
 elsif OLD.state = 'posted' and   NEW.state != 'posted'
  then add_sub_p := -1;
 end if;
 execute account_period_sum_update(OLD.id,add_sub_p);
 return NEW;
END;
$$
LANGUAGE plpgsql;
""")

        cr.execute("""
CREATE OR REPLACE FUNCTION account_move_sum_delete() RETURNS trigger  AS
$$
BEGIN
 execute account_period_sum_update(OLD.id,-1);
 return OLD;
END;
$$
LANGUAGE plpgsql;
""")

        cr.execute("SELECT count(*) FROM pg_trigger WHERE tgname = 'trg_account_move_sum_insert'")
        if cr.fetchone()[0] == 1:
            cr.execute("drop trigger trg_account_move_sum_insert ON  account_move ;")

        cr.execute("""
create trigger trg_account_move_sum_insert
AFTER INSERT ON  account_move
FOR EACH ROW EXECUTE PROCEDURE account_move_sum_insert();
""")

        cr.execute("SELECT count(*) FROM pg_trigger WHERE tgname = 'trg_account_move_sum_update'")
        if cr.fetchone()[0] == 1:
            cr.execute("drop trigger trg_account_move_sum_update ON  account_move ;")

        cr.execute("""
create trigger trg_account_move_sum_update
BEFORE UPDATE ON  account_move
FOR EACH ROW EXECUTE PROCEDURE account_move_sum_update();
""")

        cr.execute("SELECT count(*) FROM pg_trigger WHERE tgname = 'trg_account_move_sum_delete'")
        if cr.fetchone()[0] == 1:
            cr.execute("drop trigger trg_account_move_sum_delete ON  account_move;")

        cr.execute("""
create trigger trg_account_move_sum_delete
BEFORE DELETE ON  account_move
FOR EACH ROW EXECUTE PROCEDURE account_move_sum_delete();
""")

#
#on insert of first period of a new year create balance carried forward
#

        cr.execute("""
CREATE OR REPLACE FUNCTION account_period_sum_create(period_id_i integer) RETURNS void  AS
$$
DECLARE
last_fiscalyear_id_p integer;

BEGIN
-- id of the last year
select into last_fiscalyear_id_p fy.id
       from account_fiscalyear fy
       where date_stop = (select max(y.date_stop)
                            from account_fiscalyear y,
                                 account_period p
                           where p.id = period_id_i
                             and y.date_stop < p.date_start );


insert into account_account_period_sum
    (account_id,period_id,debit,credit,name,sum_fy_period_id)
     select
     a.id, period_id_i, sum(debit), sum(credit), to_char(y.date_start,'YYYY')||'00',
     get_id('account_account_period_sum',a.id,y.id,0,0)
     from account_account a,
          account_account_period_sum s,
          account_period p,    --new
          account_fiscalyear y, --new
          account_period lp,
          account_account_type t
    where t.close_method != 'none'
      and t.id = a.user_type
      and p.id = period_id_i     -- current period
      and y.id = p.fiscalyear_id -- current year
      and lp.fiscalyear_id = last_fiscalyear_id_p
      and p.date_start = y.date_start
      and s.period_id = lp.id    -- last years period sums
      and s.account_id = a.id
      group by a.id, period_id_i,y.id, to_char(y.date_start,'YYYY')||'00'
      having sum(debit) !=0 or  sum(credit) !=0;
return;
END;
$$
LANGUAGE plpgsql;
""")

        cr.execute("""
CREATE OR REPLACE FUNCTION account_period_sum_insert() RETURNS trigger  AS
$$
BEGIN
 execute account_period_sum_create(NEW.id);
 return NEW;
END;
$$
LANGUAGE plpgsql;
""")

        cr.execute("SELECT count(*) FROM pg_trigger WHERE tgname = 'trg_account_period_sum_insert'")
        if cr.fetchone()[0] == 1:
            cr.execute("drop trigger trg_account_period_sum_insert ON  account_period;")
        cr.execute("""
create trigger trg_account_period_sum_insert
AFTER INSERT ON  account_period
FOR EACH ROW EXECUTE PROCEDURE account_period_sum_insert();
""")




#
#on change of account close_method
#other logic has to check if changes of close_method are allowed
#IMHO not after closing the first year
#

        cr.execute("""
CREATE OR REPLACE FUNCTION account_close_method_update(account_id_i integer,close_method_i varchar) RETURNS void  AS
$$
DECLARE

BEGIN

if close_method_i != 'none'
 then

   insert into account_account_period_sum
    (account_id,period_id,debit,credit,name,sum_fy_period_id)
     select
     a.id, p.id, sum(debit), sum(credit), y.code||'00',get_id('account_account_period_sum',a.id,y.id,0,0)
     from account_account a,
          account_account_fy_period_sum s,
          account_period p,    --new
          account_fiscalyear y --new
    where s.account_id = a.id
      and a.id = account_id_i
      and s.date_start < y.date_start
      and s.name not like '%00'
      and p.date_start=y.date_start
      group by a.id, p.id, y.id, y.code
      having sum(debit) !=0 or  sum(credit) !=0;

else
 delete from account_account_period_sum
  where account_id = account_id_i
    and name like '%00';

end if;
return;
END;
$$
LANGUAGE plpgsql;
""")

        cr.execute("""
CREATE OR REPLACE FUNCTION account_close_method_update_f() RETURNS trigger  AS
$$
DECLARE
 cm_old varchar;
 cm_new varchar;
BEGIN
-- close_method moved to account_account_type
 select into cm_old close_method
   from account_account_type
  where id = OLD.user_type;
 select into cm_new close_method
   from account_account_type
  where id = NEW.user_type;
-- if NEW.close_method != OLD.close_method
 if cm_old != cm_new
  then
   execute account_close_method_update(NEW.id,cm_new);
 end if;
 RETURN NEW;
END;
$$
LANGUAGE plpgsql;
""")

        cr.execute("SELECT count(*) FROM pg_trigger WHERE tgname = 'trg_account_close_method_update';")
        if cr.fetchone()[0] == 1:
            cr.execute("drop trigger trg_account_close_method_update ON  account_account;")

        cr.execute("""
create trigger trg_account_close_method_update
BEFORE UPDATE ON  account_account
FOR EACH ROW EXECUTE PROCEDURE account_close_method_update_f();
""")



#
#initial - eventually run only once
#
        cr.commit()

        cr.execute("delete from account_account_period_sum;")
        cr.commit()

        cr.execute("delete from unique_view_id where view_name ='account_account_period_sum';")
        cr.commit()


        cr.execute("""
insert into account_account_period_sum(name,sum_fy_period_id,period_id,account_id,credit,debit)
select   p.name,
         get_id('account_account_period_sum', l.account_id, p.fiscalyear_id, 0,0),
         l.period_id,
         account_id,
         sum(coalesce(credit,0)),sum(coalesce(debit,0))
         from account_move_line l,
              account_period p
        where p.id=l.period_id
        group by p.name,l.period_id, account_id ,fiscalyear_id ;
""")
        cr.commit()
        cr.execute("""
update account_move_line m
    set account_period_sum_id = (select id from account_account_period_sum
                                  where account_id=m.account_id
                                    and period_id =m.period_id)

""")
        cr.commit()

        cr.execute("""
select account_period_sum_create(p.id)
  from account_period p,
       account_fiscalyear f
  where p.date_start=f.date_start;
""")
        cr.commit()
triggger()
