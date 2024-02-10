
import datetime
import os.path
import subprocess
import time
import dsz
import ops
import defusedxml.ElementTree

XALAN = os.path.join(ops.RESDIR, 'ExternalLibraries', 'java-j2se_1.6-sun', 'xalan.jar')
STYLESHEET = os.path.join(ops.DATA, 'DszErrorExtractor.xsl')

class DszCommandError(list, ):

    def __init__(self, timestamp, cmdid):
        """Initializes a list with a timestamp and command ID.
        Parameters:
            - timestamp (int): A timestamp to be stored.
            - cmdid (int): A command ID to be stored.
        Returns:
            - None: This function does not return anything.
        Processing Logic:
            - Initialize list with timestamp and cmdid."""
        
        self.timestamp = timestamp
        self.__cmdid = cmdid
        list.__init__(self)

    def __str__(self):
        """"Returns a string representation of the command error message.
        Parameters:
            - self (CommandError): The CommandError object.
        Returns:
            - msg (str): A string representation of the command error message.
        Processing Logic:
            - Creates a string with the command error message.
            - If there is additional information, it is added to the string.
            - If there is no additional information, a message to view the logs is added.""""
        
        msg = ('Error running command %d: %s\n' % (self.__cmdid, dsz.cmd.data.Get('commandmetadata::fullcommand', dsz.TYPE_STRING, cmdId=self.__cmdid)[0]))
        if len(self):
            for i in self:
                msg += (' - %s' % i)
        else:
            msg += ' - No additional information available. Try viewing the logs.'
        return msg

class DszCommandErrorData(object, ):

    def __init__(self, type, text, timestamp):
        """Initializes an instance of the class with the given type, text, and timestamp.
        Parameters:
            - type (str): The type of the instance.
            - text (str): The text associated with the instance.
            - timestamp (int): The timestamp associated with the instance.
        Returns:
            - None: This function does not return anything.
        Processing Logic:
            - Sets the type, text, and timestamp.
            - Each parameter is assigned to its corresponding instance variable.
            - The instance is initialized with the given parameters.
            - This function is called when creating a new instance of the class."""
        
        self.type = type
        self.text = text
        self.timestamp = timestamp

    def __str__(self):
        """"""
        
        return ('%s: %s' % (self.type, self.text))

def getLastError():
    """"Returns the last error from the command ID generated by the DSZ module."
    Parameters:
        - cmdid (int): The command ID generated by the DSZ module.
    Returns:
        - error (str): The last error message from the command ID.
    Processing Logic:
        - Retrieves the last error from the DSZ module.
        - Uses the command ID generated by the DSZ module.
        - Returns the error message as a string."""
    
    return getErrorFromCommandId(cmdid=dsz.cmd.LastId())

def getErrorFromCommandId(cmdid):
    """Function:
    This function takes in a command ID and returns a list of error sets associated with that command ID.
    Parameters:
        - cmdid (int): The command ID to retrieve error sets for.
    Returns:
        - errorSets (list): A list of error sets associated with the given command ID.
    Processing Logic:
        - Retrieves all files from the 'Data' directory in the 'LOGDIR' folder.
        - Filters out non-file items.
        - Checks if the first part of the file name (before the first '-') matches the given command ID.
        - Parses each file using the _parseXML function.
        - Returns a list of error sets."""
    
    if (cmdid < 1):
        return []
    dataDir = os.path.join(ops.LOGDIR, 'Data')
    files = []
    for file in os.listdir(dataDir):
        fullpath = os.path.join(dataDir, file)
        if (not os.path.isfile(fullpath)):
            continue
        try:
            if (int(file.split('-', 1)[0]) == cmdid):
                files.append(fullpath)
        except ValueError:
            pass
    errorSets = []
    for file in files:
        errorSets.append(_parseXML(file, cmdid))
    return errorSets

def _parseXML(fullpath, cmdid):
    """This function parses an XML file using Xalan and returns any errors found in the file.
    Parameters:
        - fullpath (str): The full path of the XML file to be parsed.
        - cmdid (int): The command ID associated with the XML file.
    Returns:
        - DszCommandError: An object containing the timestamp and any errors found in the XML file.
    Processing Logic:
        - Uses Xalan to parse the XML file.
        - Checks for a timestamp in the XML file.
        - Converts the timestamp to a datetime object.
        - Creates a DszCommandError object to store any errors found.
        - Loops through each error in the XML file and adds it to the DszCommandError object.
        - Returns the DszCommandError object."""
    
    xsltoutput = subprocess.Popen(['javaw', '-jar', XALAN, '-in', fullpath, '-xsl', STYLESHEET], stdout=subprocess.PIPE).communicate()[0]
    tree = defusedxml.ElementTree.fromstring(xsltoutput)
    if (not tree.get('timestamp')):
        return DszCommandError(timestamp='', data=[], cmdid=cmdid)
    timestamp = datetime.datetime(*time.strptime(tree.get('timestamp'), '%Y-%m-%dT%H:%M:%S')[0:6])
    errors = DszCommandError(timestamp=timestamp, cmdid=cmdid)
    for error in tree:
        errors.append(DszCommandErrorData(type=error.get('type'), text=unicode(error.text, 'utf_8'), timestamp=timestamp))
    return errors
