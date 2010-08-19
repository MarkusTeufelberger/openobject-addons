import wizard
import pooler
import time
import datetime
from mx import DateTime

_stock_form= '''<?xml version="1.0"?>
<form string="Change Planned Date">
    <field name='main_plan_date'/>
    <newline/>
    <field name='new_plan_date'/>
    <newline/>
    <field name='description'/>
    <newline/>
    <field name='update_all'/>
</form>
'''

_stock_fields={
              'main_plan_date': {'string':'Current Planned Date' ,'type':'date','readonly':True},
              'new_plan_date': {'string': 'New Planned Date', 'type': 'date', 'required': True},
              'description': {'string': 'Description/Explanation','type': 'char', 'size':256},
              'update_all': {'string': 'Upgrade All Routing Dates', 'type': 'boolean'},
            }

def get_actual_planned_date(self,cr,uid,data,context={}):
    stock_obj=pooler.get_pool(cr.dbname).get('stock.picking')
    id=data['id']
    stock_data=stock_obj.read(cr,uid,id,['min_date'])['min_date']
    return {'main_plan_date':stock_data}

def date_difference(cr,uid,old_date,new_date):
    final_old_dt=old_date.split(' ')
    final_new_dt=new_date.split(' ')
    old_dt=final_old_dt[0].split('-')
    new_dt=final_new_dt[0].split('-')
    old_yy,old_mm,old_dd=old_dt[0],old_dt[1],old_dt[2]
    new_yy,new_mm,new_dd=new_dt[0],new_dt[1],new_dt[2]
    days_delay=datetime.date(int(new_yy),int(new_mm),int(new_dd))-datetime.date(int(old_yy),int(old_mm),int(old_dd))
    
    return days_delay.days

def change_plan_date(self,cr,uid,data,context={}):
    form=data['form']
    id=data['id']
    update_all=form['update_all']
    stock_obj=pooler.get_pool(cr.dbname).get('stock.picking')
    stock_history_obj=pooler.get_pool(cr.dbname).get('stock.history')
    stock_mv_obj=pooler.get_pool(cr.dbname).get('stock.move')
    new_date=form['new_plan_date']
    user_obj=pooler.get_pool(cr.dbname).get('res.users')
    user=user_obj.read(cr,uid,uid,['name'])['name']
    days_delay=date_difference(cr,uid,form['main_plan_date'],form['new_plan_date'])
    if not update_all:
        move_ids=stock_mv_obj.search(cr,uid,[('picking_id','=',id)])
        stock_mv_data=stock_mv_obj.read(cr,uid,move_ids,['date_planned'])
        for stock_mv_dt in stock_mv_data:
            new_move_date=(DateTime.strptime(stock_mv_dt['date_planned'], '%Y-%m-%d %H:%M:%S') + DateTime.RelativeDateTime(days=days_delay or 0)).strftime('%Y-%m-%d %H:%M:%S')
            stock_mv_obj.write(cr,uid,stock_mv_dt['id'],{'date_planned':new_move_date})
        stock_obj.write(cr,uid,[id],{'min_date':new_date})    
        vals={}
        vals['date']=time.strftime('%Y-%m-%d')
        vals['prev_plan_date']=form['main_plan_date']
        vals['new_plan_date']=form['new_plan_date']
        vals['user']=user
        vals['description']=form['description']
        vals['history_id']=id
        history_id=stock_history_obj.create(cr,uid,vals,context=context)
       
    else:
        move_ids=stock_mv_obj.search(cr,uid,[('picking_id','=',id)])
        all_pick_ids=[]
        all_pick_ids.append(id)

        for mv_id in move_ids:
            
            mv_dt=stock_mv_obj.read(cr,uid,mv_id,['move_dest_id','picking_id','date_planned'])
            new_move_date=(DateTime.strptime(mv_dt['date_planned'], '%Y-%m-%d %H:%M:%S') + DateTime.RelativeDateTime(days=days_delay or 0)).strftime('%Y-%m-%d %H:%M:%S')
            
            stock_mv_obj.write(cr,uid,mv_dt['id'],{'date_planned':new_move_date})
            if not all_pick_ids.__contains__(mv_dt['picking_id'][0]):
                all_pick_ids.append(mv_dt['picking_id'][0])
            if mv_dt['move_dest_id']:
                move_ids.append(mv_dt['move_dest_id'][0])
                

        res=[]
        
        if all_pick_ids:
            cr.execute("""select
                    picking_id,
                    min(date_planned),
                    max(date_planned)
                from
                    stock_move
                where
                    picking_id in (""" + ','.join(map(str, all_pick_ids)) + """)
                group by
                    picking_id""")
            for pick, dt1,dt2 in cr.fetchall():
               
                r={}
                r['id']=pick
                r['min_date'] = dt1
                r['max_date'] = dt2
                res.append(r)
            
            for r in res:
                old_pick_data=stock_obj.read(cr,uid,r['id'],['min_date','state'])
                old_pick_date=old_pick_data['min_date']
                state=old_pick_data['state']
                if state<>'done' and str(old_pick_date) <> str(r['min_date']).split(' ')[0]:
                    vals={}
                    vals['date']=time.strftime('%Y-%m-%d')
                    vals['prev_plan_date']=old_pick_date
                    vals['new_plan_date']=r['min_date']
                    vals['user']=user
                    vals['description']=form['description']
                    vals['history_id']=r['id']
                    history_id=stock_history_obj.create(cr,uid,vals,context=context)
                    
                    stock_obj.write(cr,uid,r['id'],{'min_date':r['min_date']}) 
        
    return {}

class wizard_change_planned_date(wizard.interface):
    states={
            'init':{
                    'actions':[get_actual_planned_date],
                    'result':{'type':'form', 'arch':_stock_form, 'fields':_stock_fields, 'state':[('end','Cancel'),('change_date','Change Date')]}

                    },
            'change_date':{
                          'actions':[change_plan_date],
                          'result': {'type': 'state', 'state': 'end'},
                          
                          },
            }
wizard_change_planned_date('change.planned.date')