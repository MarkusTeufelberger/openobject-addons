import sys
import chilkat
import os
from manager import ustr

def generateEML(mail):
    sub = (mail.Subject).replace(' ','')
    body = mail.Body.encode("utf-8")
    recipients=mail.Recipients
    sender=mail.SenderEmailAddress
    attachments=mail.Attachments

    email = chilkat.CkEmail()
    email.put_Subject(ustr(sub).encode('iso-8859-1'))
    email.put_Body(ustr(body).encode('utf-8'))
    email.put_From(ustr(sender).encode('iso-8859-1'))

    for i in xrange(1, recipients.Count+1):
        name = ustr(recipients.Item(i).Name).encode('iso-8859-1')
        address = ustr(recipients.Item(i).Address).encode('iso-8859-1')
        email.AddTo(name,address)

    eml_name= ustr(sub).encode('iso-8859-1')+'-'+str(mail.EntryID)[-9:]
    ls = ['*', '/', '\\', '<', '>', ':', '?', '"', '|']

    attachments_folder_path = os.path.abspath(os.path.dirname(__file__)+"\\dialogs\\resources\\attachments\\")
    if not os.path.exists(attachments_folder_path):
        os.makedirs(attachments_folder_path)
    for i in xrange(1, attachments.Count+1):
        fn = eml_name + '-' + ustr(attachments[i].FileName).encode('iso-8859-1')
        for c in ls:
            fn = fn.replace(c,'')
        if len(fn) > 64:
            l = 64 - len(fn)
            f = fn.split('-')
            fn = '-'.join(f[1:])
            if len(fn) > 64:
                l = 64 - len(fn)
                f = fn.split('.')
                fn = f[0][0:l] + '.' + f[-1]
        att_file = os.path.join(attachments_folder_path, fn)
        if os.path.exists(att_file):
            os.remove(att_file)
        f1  = att_file
        attachments[i].SaveAsFile(att_file)
        contentType = email.addFileAttachment(att_file)
        if (contentType == None ):
            print mail.lastErrorText()
            sys.exit()

    mails_folder_path = os.path.abspath(os.path.dirname(__file__)+"\\dialogs\\resources\\mails\\")
    if not os.path.exists(mails_folder_path):
        os.makedirs(mails_folder_path)
    for c in ls:
        eml_name = eml_name.replace(c,'')
    if len(eml_name) > 64:
       l = 64 - len(eml_name)
       f = eml_name.split('-')
       eml_name = f[0][0:l] + '.' + f[-1]
    eml_path = ustr(os.path.join(mails_folder_path,eml_name+".eml")).encode('iso-8859-1')
    success = email.SaveEml(eml_path)
    if (success == False):
        print email.lastErrorText()
        sys.exit()

    print "Saved EML!",eml_path
    return eml_path