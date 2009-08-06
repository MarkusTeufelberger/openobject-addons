import wizard
import pooler
import tools
import time
import datetime
import mx.DateTime

mail_form='''<?xml version="1.0"?>
<form string="Interview Mail">
    <field name="smtp_server" colspan="4"/>
    <field name="subject" colspan="4"/>
    <field name="mail_body" colspan="4"/>
</form>'''

mail_fields = {
    'smtp_server':{'string':'SMTP Server','type':'many2one','relation': 'email.smtpclient','required':True},
    'subject': {'string': 'Subject', 'type':'char', 'size': 64, 'required':True},
    'mail_body': {'string': 'Body', 'type': 'text_tag', 'required':True}
}

class wizard_email_interview(wizard.interface):
    
    def _send_mail(self, cr, uid, data, context={}):
        smtp_obj = pooler.get_pool(cr.dbname).get('email.smtpclient')
        subject = data['form']['subject']
        body = data['form']['mail_body']
        ids = data['ids']
        hr_candidate_obj = pooler.get_pool(cr.dbname).get('hr.interview')
        hr_candidates = hr_candidate_obj.browse(cr,uid,ids)
        for hr_candidate in hr_candidates:
             body = body.replace("__candidate__",hr_candidate.name)
             try:
                 print "hr_candidate.date",hr_candidate.date
                 d1 = mx.DateTime.strptime(str(hr_candidate.date),'%Y-%m-%d %H:%M:%S')
                 body = body.replace("__date__",d1.strftime('on %B %d,%Y at %H:%M %p'))
             except Exception,e:
                 print "eee",e    
             to = hr_candidate.email
             files = smtp_obj.send_email(cr, uid, data['form']['smtp_server'], to, subject, body)
             print "::FILES::",files
        return {}     
            
    def _default_params(self, cr, uid, data, context={}):
        ids = data['ids']
        hr_candidates = pooler.get_pool(cr.dbname).get('hr.interview').browse(cr,uid,ids)
        body = "Hello __candidate__ ,\n\n" + "Congratulations!\n\n"
        for hr_candidate in hr_candidates:
            if hr_candidate.state == 'scheduled':
                body = body + "Your resume has been short listed in the qualifying candidates.\n"\
                            + "Your interview has been scheduled on __date__\n\n"
                subject = "A call for Interview !"
            elif hr_candidate.state == 'selected':
                body = body + "You have been selected .\n"\
                            + "Your date of joining is :  __date__\n\n"
                subject = "Congratulations! A call for Joining!"           
                
        data['mail_body'] = body + "Regards,\n" + "Management\n"
        data['subject'] = subject           
        return data
        
    states = {
        'init': {
            'actions': [_default_params],
            'result': {'type':'form', 'arch':mail_form, 'fields':mail_fields, 'state':[('end','Cancel'),('sendmail','Send Mail')]}
        },
        'sendmail': {
            'actions': [_send_mail],
            'result': {'type':'state', 'state':'end'}
        }
    }
wizard_email_interview('hr.email.interview')