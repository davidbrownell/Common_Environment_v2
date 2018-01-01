# ---------------------------------------------------------------------------
# |  
# |  SmtpMailer.py
# |  
# |  David Brownell (db@DavidBrownell.com)
# |  
# |  11/29/2015 11:41:34 AM
# |  
# ---------------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2015-18.
# |          
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ---------------------------------------------------------------------------
import mimetypes
import os
import smtplib
import sys

from six.moves import cPickle as pickle

from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from CommonEnvironment import Shell

# ---------------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ---------------------------------------------------------------------------

class SmtpMailer(object):

    EXTENSION                               = ".SmtpMailer"
    
    # ---------------------------------------------------------------------------
    @classmethod
    def GetConfigurations(cls):
        data_dir = Shell.GetEnvironment().UserDirectory
        
        return ( os.path.splitext(item)[0] for item in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, item)) and os.path.splitext(item)[1] == cls.EXTENSION )
        
    # ---------------------------------------------------------------------------
    @classmethod
    def Load(cls, configuration_name):
        environment = Shell.GetEnvironment()
        
        data_filename = environment.CreateDataFilename(configuration_name, suffix=cls.EXTENSION)
        if not os.path.isfile(data_filename):
            raise Exception("'{}' is not a valid filename".format(data_filename))
            
        with open(data_filename, 'rb') as f:
            content = f.read()
            
        if environment.Name == "Windows":
            import win32crypt
            content = win32crypt.CryptUnprotectData(content, None, None, None, 0)   # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
            content = content[1]
            
        return pickle.loads(content)
        
    # ---------------------------------------------------------------------------
    def __init__( self,
                  host,
                  username=None,
                  password=None,
                  port=26,
                  from_name=None,
                  from_email=None,
                  ssl=False,
                ):
        assert from_name or from_email
            
        self.Host                           = host
        self.Username                       = username or ''
        self.Password                       = password or ''
        self.Port                           = port
        self.FromName                       = from_name or ''
        self.FromEmail                      = from_email or ''
        self.Ssl                            = ssl
        
    # ---------------------------------------------------------------------------
    def Save(self, configuration_name):
        environment = Shell.GetEnvironment()
        
        content = pickle.dumps(self)
        
        if environment.Name == "Windows":
            import win32crypt
            content = win32crypt.CryptProtectData(content, '', None, None, None, 0)     # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
            
        data_filename = environment.CreateDataFilename(configuration_name, suffix=self.EXTENSION)
        
        with open(data_filename, 'wb') as f:
            f.write(content)
            
    # ---------------------------------------------------------------------------
    # <Too many braches> pylint: disable = R0912
    def SendMessage( self,
                     recipients,
                     subject,
                     message,
                     attachment_filenames=None,
                     message_format="plain",
                   ):
        if self.Ssl:
            smtp = smtplib.SMTP_SSL()
        else:
            smtp = smtplib.SMTP()
            
        smtp.connect(self.Host, self.Port)
        
        if self.Username and self.Password:
            if not self.Ssl:
                smtp.starttls()
                
            smtp.login(self.Username, self.Password)
            
        assert self.FromName or self.FromEmail
        
        if not self.FromName:
            from_addr = self.FromEmail
        elif not self.FromEmail:
            from_addr = self.FromName
        else:
            from_addr = "{} <{}>".format(self.FromName, self.FromEmail)
            
        msg = MIMEMultipart()
        
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = ', '.join(recipients)
        
        msg.attach(MIMEText(message, message_format))
        
        for attachment_filename in (attachment_filenames or []):            # <Unnecessary parens> pylint: disable = C0325
            ctype, encoding = mimetypes.guess_type(attachment_filename)
            if ctype == None or encoding != None:
                ctype = "application/octet-stream"
                
            maintype, subtype = ctype.split('/', 1)
            
            if maintype == "text":
                attachment = MIMEText(open(attachment_filename).read(), _subtype=subtype)
            elif maintype == "image":
                attachment = MIMEImage(open(attachment_filename, 'rb').read(), _subtype=subtype)
            elif maintype == "audio":
                attachment = MIMEAudio(open(attachment_filename, 'rb').read(), _subtype=subtype)
            else:
                attachment = MIMEBase(maintype, subtype)
                
                attachment.set_payload(open(attachment_filename, 'rb').read())
                encoders.encode_base64(attachment)
                
            attachment.add_header("Content-Disposition", "attachment", filename=os.path.basename(attachment_filename))
            
            msg.attach(attachment)
            
        smtp.sendmail(from_addr, recipients, msg.as_string())
        smtp.close()
        